# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import logging
import math
import struct
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Callable, Coroutine

from steam.models import EventParser, register
from steam.protobufs import EMsg, GCMsg, GCMsgProto, MsgProto
from steam.state import ConnectionState

from steam import utils, Inventory, Game, CSGO

from .enums import Language
from .backpack import BackPack
from .models import Sticker, AccountInfo
from .protobufs import (
    base_gcmessages as cso_messages,
    gcsdk_gcmessages as so_messages,
    cstrike15_gcmessages as cstrike,
    econ_gcmessages,
    UpdateMultipleItems,
)

if TYPE_CHECKING:
    from steam.protobufs.steammessages_clientserver_2 import CMsgGcClient

    from .client import Client

log = logging.getLogger(__name__)


class GCState(ConnectionState):
    gc_parsers: dict[Language, EventParser[Language]] = {}
    client: Client

    __slots__ = ("_connected", "_unpatched_inventory", "backpack")

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(client, **kwargs)
        self._unpatched_inventory: Optional[Callable[[Game], Coroutine[None, None, Inventory]]] = None
        self._connected = asyncio.Event()
        self.backpack: Optional[BackPack] = None

    @register(EMsg.ClientFromGC)
    async def parse_gc_message(self, msg: MsgProto[CMsgGcClient]) -> None:
        if msg.body.appid != self.client.GAME.id:
            return

        try:
            language = Language(utils.clear_proto_bit(msg.body.msgtype))
        except ValueError:
            return log.info(
                f"Ignoring unknown msg type: {msg.body.msgtype} ({utils.clear_proto_bit(msg.body.msgtype)})"
            )

        try:
            msg = (
                GCMsgProto(language, msg.body.payload)
                if utils.is_proto(msg.body.msgtype)
                else GCMsg(language, msg.body.payload)
            )
        except Exception as exc:
            return log.error(f"Failed to deserialize message: {language!r}, {msg.body.payload!r}", exc_info=exc)
        else:
            if log.isEnabledFor(logging.DEBUG):
                log.debug(f"Socket has received GC message {msg!r} from the websocket.")

        try:
            func = self.gc_parsers[language]
        except KeyError:
            if log.isEnabledFor(logging.DEBUG):
                log.debug(f"Ignoring event {msg!r}")
        else:
            await utils.maybe_coroutine(func, msg)

    @register(Language.ClientWelcome)
    def parse_gc_client_connect(self, _) -> None:
        if not self._connected.is_set():
            self.dispatch("gc_connect")
            self._connected.set()

    @register(Language.ClientGoodbye)
    def parse_client_goodbye(self, _=None) -> None:
        self.dispatch("gc_disconnect")
        self._connected.clear()

    @register(Language.ClientWelcome)
    def parse_gc_client_connect(self, msg: GCMsgProto[so_messages.CMsgClientWelcome]) -> None:
        if msg.body.outofdate_subscribed_caches:
            for cache in msg.body.outofdate_subscribed_caches[0].objects:
                if cache.type_id == 1:
                    await self.update_backpack(
                        *(cso_messages.CsoEconItem().parse(item_data) for item_data in cache.object_data)
                    )
                else:
                    log.debug(f"Unknown item {cache!r} updated")
        if self._connected.is_set():
            self.dispatch("gc_ready")

    @register(Language.ClientGoodbye)
    def parse_client_goodbye(self, _=None) -> None:
        self.dispatch("gc_disconnect")
        self._connected.clear()

    def patch_user_inventory(self, new_inventory: Inventory) -> None:
        async def inventory(_, game: Game) -> Inventory:
            if game != CSGO:
                return await self._unpatched_inventory(game)

            return new_inventory

        self.client.user.__class__.inventory = inventory

    async def update_backpack(self, *items: cso_messages.CsoEconItem) -> BackPack:
        await self.client.wait_until_ready()
        backpack = BackPack(await self._unpatched_inventory(CSGO))
        for item in backpack:
            for backpack_item in items:
                if item.asset_id == backpack_item.id:
                    for attribute_name in backpack_item.__annotations__:
                        setattr(item, attribute_name, getattr(backpack_item, attribute_name))

                    is_new = (item.inventory >> 30) & 1
                    item.position = 0 if is_new else item.inventory & 0xFFFF

                    # is the item contained in a casket?
                    casket_id_low = utils.find(lambda a: a.def_index == 272, item.attribute)
                    casket_id_high = utils.find(lambda a: a.def_index == 273, item.attribute)
                    if casket_id_low and casket_id_high:
                        item.casket_id = int(
                            f"{bin(struct.unpack('<I', casket_id_low.value_bytes)[0])}"
                            f"{bin(struct.unpack('<I', casket_id_high.value_bytes)[0])}",
                            2,
                        )

                    custom_name = utils.find(lambda a: a.def_index == 111, item.attribute)
                    if custom_name and not item.custom_name:
                        item.custom_name = custom_name.value_bytes[2:].decode("utf-8")

                    paint_index = utils.find(lambda a: a.def_index == 6, item.attribute)
                    if paint_index:
                        item.paint_index = struct.unpack("<f", paint_index.value_bytes)[0]

                    paint_seed = utils.find(lambda a: a.def_index == 7, item.attribute)
                    if paint_seed:
                        item.paint_seed = math.floor(struct.unpack("<f", paint_seed.value_bytes)[0])

                    paint_wear = utils.find(lambda a: a.def_index == 8, item.attribute)
                    if paint_wear:
                        item.paint_wear = struct.unpack("<f", paint_wear.value_bytes)[0]

                    tradable_after_date = utils.find(lambda a: a.def_index == 75, item.attribute)
                    if tradable_after_date:
                        item.tradable_after = datetime.utcfromtimestamp(
                            struct.unpack("<I", tradable_after_date.value_bytes)[0]
                        )

                    item.stickers = []
                    attrs = Sticker.get_attrs()
                    for i in range(1, 6):
                        sticker_id = utils.find(lambda a: a.def_index == 113 + (i * 4), item.attribute)
                        if sticker_id:
                            sticker = Sticker(
                                slot=i,
                                sticker_id=struct.unpack("<I", sticker_id.value_bytes)[0],
                            )

                            for idx, attr in enumerate(attrs):
                                attribute = utils.find(lambda a: a.def_index == 114 + (i * 4) + idx, item.attribute)
                                if attribute:
                                    setattr(sticker, attribute, struct.unpack("<f", attribute.value_bytes)[0])

                            item.sticker.append(sticker)

                    if item.def_index == 1201:  # storage unit
                        item.casket_contained_item_count = 0
                        item_count = utils.find(lambda a: a.def_index == 270, item.attribute)
                        if item_count:
                            item.casket_contained_item_count = struct.unpack("<I", item_count.value_bytes)[0]

                    break

        self.patch_user_inventory(backpack)
        self.backpack = backpack
        return backpack

    @register(Language.MatchmakingGC2ClientHello)
    def handle_matchmaking_client_hello(self, msg: GCMsgProto[cstrike.CMsgGccStrike15V2MatchmakingGc2ClientHello]):
        self.account_info = AccountInfo(msg.body)
        self.dispatch("account_info", self.account_info)

    @register(Language.MatchList)
    def handle_match_list(self, msg: GCMsgProto[cstrike.CMsgGccStrike15V2MatchList]):
        self.dispatch("match_list", msg.body.matches, msg.body)

    @register(Language.PlayersProfile)
    def handle_players_profile(self, msg: GCMsgProto[cstrike.CMsgGccStrike15V2PlayersProfile]):
        if not msg.body.account_profiles:
            return

        profile = msg.body.account_profiles[0]

        self.dispatch("players_profile", profile)

    @register(Language.Client2GCEconPreviewDataBlockResponse)
    def handle_client_preview_data_block_response(
        self, msg: GCMsgProto[cstrike.CMsgGccStrike15V2Client2GcEconPreviewDataBlockResponse]
    ):
        # decode the wear
        buffer = utils.BytesBuffer()
        buffer.write_uint32(msg.body.iteminfo.paintwear)
        item = utils.get(self.backpack, id=msg.body.iteminfo.itemid)
        item.paint_wear = buffer.read_struct("<f")  # TODO add as method to BytesBuffer
        self.dispatch("inspect_item_info", item)

    @register(Language.ItemCustomizationNotification)
    def handle_item_customization_notification(
        self, msg: GCMsgProto[econ_gcmessages.CMsgGcItemCustomizationNotification]
    ):
        if not msg.body.item_id or not msg.body.request:
            return

        self.dispatch("item_customization_notification", msg.body.item_id, msg.body.request)

    @register(Language.SOCreate)
    def handle_so_create(self, msg: GCMsgProto[so_messages.CMsgSoSingleObject]):

        if msg.body.type_id != 1:
            return  # Not an item

        received_item = cso_messages.CsoEconItem().parse(msg.body.object_data)
        new_item = utils.find(lambda i: i.asset_id == received_item.id, await self.update_backpack(received_item))

        if new_item is None:
            await self.restart_csgo()

        self.dispatch("item_receive", new_item)

    async def restart_csgo(self) -> None:
        await self.client.change_presence(game=Game(id=0))
        self.parse_client_goodbye()
        await self.client.change_presence(game=CSGO, games=self.client._original_games)

    @register(Language.SOUpdate)
    def handle_so_update(self, msg: GCMsgProto[so_messages.CMsgSoSingleObject]):
        if msg.body.type_id != 1:
            return

        item = cso_messages.CsoEconItem().parse(msg.body.object_data)

        before = utils.find(lambda i: i.asset_id == item.id, self.backpack)
        after = utils.find(lambda i: i.asset_id == item.id, await self.update_backpack(item))
        self.dispatch("item_update", before, after)

    @register(Language.SOUpdateMultiple)
    def handle_so_update_multiple(self, msg: GCMsgProto[so_messages.CMsgSoMultipleObjects]):
        try:
            type_id = msg.body.objects[0].type_id
        except IndexError:
            pass  # would be weird
        else:
            if type_id == 1:
                msg.body = UpdateMultipleItems().parse(msg.payload)  # TODO is this correct?
        for item in msg.body.objects:
            if item.type_id == 1:
                old_item = utils.find(lambda i: i.asset_id == int(item.inner.id), self.backpack)
                new_item = utils.find(
                    lambda i: i.asset_id == int(item.inner.id), await self.update_backpack(item.inner)
                )
                new_item.position = item.inventory & 0x0000FFFF
                self.dispatch("item_update", old_item, new_item)
            else:
                log.debug(f"Unknown item {item!r} updated")

    @register(Language.SODestroy)
    def handle_so_destroy(self, msg: GCMsgProto[so_messages.CMsgSoSingleObject]):
        if msg.body.type_id != 1 or not self.backpack:
            return

        deleted_item = cso_messages.CsoEconItem().parse(msg.body.object_data)
        for item in self.backpack:
            if item.asset_id == deleted_item.id:
                for attribute_name in deleted_item.__annotations__:
                    setattr(item, attribute_name, getattr(deleted_item, attribute_name))
                self.backpack.items.remove(item)
                self.dispatch("item_remove", item)
                break
