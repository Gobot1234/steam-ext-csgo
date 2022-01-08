from __future__ import annotations

import logging
import math
import struct
import sys
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ... import utils
from ...abc import UserDict
from ...game import CSGO
from ...gateway import READ_U32
from ...models import register
from ...protobufs import GCMsgProto
from .._gc import GCState as GCState_
from .backpack import Backpack, BaseInspectedItem, Casket, CasketItem, Paint
from .enums import Language
from .models import Sticker, User
from .protobufs import base, cstrike, econ, sdk

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)
READ_F32 = struct.Struct("<f").unpack_from


class GCState(GCState_):
    gc_parsers: dict[Language, Callable]
    client: Client
    Language: type[Language] = Language
    backpack: Backpack

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(client, **kwargs)
        self.casket_items: dict[int, CasketItem] = {}

    def _store_user(self, data: UserDict) -> User:
        try:
            user = self._users[int(data["steamid"])]
        except KeyError:
            user = User(state=self, data=data)
            self._users[user.id64] = user
        else:
            user._update(data)
        return user

    @register(Language.ClientConnectionStatus)
    def parse_client_goodbye(self, msg: GCMsgProto[sdk.ConnectionStatus] | None = None) -> None:
        if msg is None or msg.body.status == sdk.GcConnectionStatus.NoSession:
            self.dispatch("gc_disconnect")
            self._gc_connected.clear()
            self._gc_ready.clear()

    @register(Language.ClientWelcome)
    async def parse_gc_client_connect(self, msg: GCMsgProto[sdk.ClientWelcome]) -> None:
        if msg.body.outofdate_subscribed_caches:
            for cache in msg.body.outofdate_subscribed_caches[0].objects:
                if cache.type_id == 1:
                    await self.update_backpack(*(base.Item().parse(item_data) for item_data in cache.object_data))
                else:
                    log.debug(f"Unknown item {cache!r} updated")
        if not self._gc_ready.is_set():
            self._gc_ready.set()
            self.dispatch("gc_ready")

    def set(self, name: str, value: Any) -> None:
        # would be nice if this was a macro
        locals = sys._getframe(1).f_locals
        item = locals["item"]
        if item is not None:
            setattr(item, name, value)
        if locals["is_casket_item"]:
            setattr(locals["cso_item"], name, value)

    async def update_backpack(self, *cso_items: base.Item, is_cache_subscribe: bool = False) -> Backpack:
        await self.client.wait_until_ready()

        backpack = self.backpack if self.backpack is not None else await self.fetch_backpack(Backpack)

        for cso_item in cso_items:  # merge the two items
            item = utils.get(backpack, asset_id=cso_item.id)
            is_casket_item = False
            if item is None:
                # is the item contained in a casket?
                casket_id_low = utils.get(cso_item.attribute, def_index=272)
                casket_id_high = utils.get(cso_item.attribute, def_index=273)
                if not (casket_id_low and casket_id_high):
                    log.info("Received an item that isn't our inventory %r", cso_item)
                    continue  # the item has been removed (gc sometimes sends you items that you have deleted)
                is_casket_item = True
                cso_item.__class__ = CasketItem
                cso_item.casket_id = int(
                    f"{READ_U32(casket_id_low.value_bytes)[0]:032b}{READ_U32(casket_id_high.value_bytes)[0]:032b}",
                    base=2,
                )
            else:
                for attribute_name in cso_item.__annotations__:
                    setattr(item, attribute_name, getattr(cso_item, attribute_name))

            is_new = is_cache_subscribe and (cso_item.inventory >> 30) & 1
            self.set("position", 0 if is_new else cso_item.inventory & 0xFFFF)

            custom_name = utils.get(cso_item.attribute, def_index=111)
            if custom_name:
                self.set("custom_name", custom_name.value_bytes[2:].decode("utf-8"))

            paint_index = utils.get(cso_item.attribute, def_index=6)
            paint_seed = utils.get(cso_item.attribute, def_index=7)
            paint_wear = utils.get(cso_item.attribute, def_index=8)
            if any((paint_index, paint_seed, paint_wear)):
                paint = Paint()
                self.set("paint", paint)
            if paint_index:
                paint.index, *_ = READ_F32(paint_index.value_bytes)
            if paint_seed:
                paint.seed = math.floor(*READ_F32(paint_seed.value_bytes))
            if paint_wear:
                paint.wear, *_ = READ_F32(paint_wear.value_bytes)

            tradable_after_date = utils.get(cso_item.attribute, def_index=75)
            if tradable_after_date:
                self.set("tradable_after", datetime.utcfromtimestamp(READ_U32(tradable_after_date.value_bytes)[0]))

            stickers = []
            self.set("stickers", stickers)
            attrs = Sticker._get_attrs()
            for i in range(1, 6):
                sticker_id = utils.get(cso_item.attribute, def_index=113 + (i * 4))
                if sticker_id:
                    sticker = Sticker(slot=i, id=READ_U32(sticker_id.value_bytes)[0])

                    for idx, attr in enumerate(attrs):
                        attribute = utils.get(cso_item.attribute, def_index=114 + (i * 4) + idx)
                        if attribute:
                            setattr(sticker, attr, READ_F32(attribute.value_bytes)[0])

                    stickers.append(sticker)

            if cso_item.def_index == 1201:  # storage unit
                item = utils.update_class(item, Casket.__new__(Casket))  # __class__ assignment doesn't work here
                backpack.items[backpack.items.index(item)] = item  # type: ignore
                item_count = utils.get(cso_item.attribute, def_index=270)
                self.set("contained_item_count", READ_U32(item_count.value_bytes)[0] if item_count is not None else 0)

            if is_casket_item:
                self.casket_items[cso_item.id] = cso_item

        self.backpack = backpack  # type: ignore
        return backpack

    @register(Language.MatchmakingGC2ClientHello)
    def handle_matchmaking_client_hello(self, msg: GCMsgProto[cstrike.MatchmakingClientHello]):
        self.client.user._profile_info_msg = msg.body

    @register(Language.MatchList)
    def handle_match_list(self, msg: GCMsgProto[cstrike.MatchList]):
        self.dispatch("match_list", msg.body.matches, msg.body)

    @register(Language.PlayersProfile)
    def handle_players_profile(self, msg: GCMsgProto[cstrike.PlayersProfile]):
        if not msg.body.account_profiles:
            return

        profile = msg.body.account_profiles[0]

        self.dispatch("players_profile", profile)

    @register(Language.Client2GCEconPreviewDataBlockResponse)
    def handle_client_preview_data_block_response(self, msg: GCMsgProto[cstrike.Client2GcEconPreviewDataBlockResponse]):
        # decode the wear
        item = msg.body.iteminfo
        packed_wear = struct.pack(">l", item.paintwear)
        inspected_item = BaseInspectedItem(
            id=item.itemid,
            def_index=item.defindex,
            paint=Paint(index=item.paintindex, wear=struct.unpack(">f", packed_wear)[0], seed=item.paintseed),
            rarity=item.rarity,
            quality=item.quality,
            kill_eater_score_type=item.killeaterscoretype,
            kill_eater_value=item.killeatervalue,
            custom_name=item.customname,
            stickers=[
                Sticker(
                    slot=sticker.slot,  # type: ignore
                    id=sticker.sticker_id,
                    wear=sticker.wear,
                    scale=sticker.scale,
                    rotation=sticker.rotation,
                    tint_id=sticker.tint_id,
                )
                for sticker in item.stickers
            ],
            inventory=item.inventory,
            origin=item.origin,
            quest_id=item.questid,
            drop_reason=item.dropreason,
            music_index=item.musicindex,
            ent_index=item.entindex,
        )
        self.dispatch("inspect_item_info", inspected_item)

    @register(Language.ItemCustomizationNotification)
    def handle_item_customization_notification(self, msg: GCMsgProto[econ.ItemCustomizationNotification]):
        if not msg.body.item_id or not msg.body.request:
            return

        self.dispatch("item_customization_notification", msg.body)

    @register(Language.SOCreate)
    async def handle_so_create(self, msg: GCMsgProto[sdk.SingleObject]):
        if msg.body.type_id != 1:
            return  # Not an item

        cso_item = base.Item().parse(msg.body.object_data)
        backpack = await self.fetch_backpack(Backpack)  # refresh the backpack
        item = utils.get(backpack, asset_id=cso_item.id)
        if item is None:
            return log.info("Received an item that isn't our inventory %r", cso_item)

        self.backpack.items.append(item)  # type: ignore
        await self.update_backpack(cso_item)
        if isinstance(cso_item, CasketItem):
            return log.debug("Received a casket item %r", cso_item)

        self.dispatch("item_receive", item)

    @register(Language.SOUpdate)
    async def handle_so_update(self, msg: GCMsgProto[sdk.SingleObject]):
        await self._handle_so_update(msg.body)

    @register(Language.SOUpdateMultiple)
    async def handle_so_update_multiple(self, msg: GCMsgProto[sdk.MultipleObjects]):
        for object in msg.body.objects_modified:
            await self._handle_so_update(object)  # type: ignore

    async def _handle_so_update(self, object: sdk.SingleObject):  # this should probably be a protocol
        if object.type_id != 1:
            return log.debug("Unknown item %r updated", object)

        cso_item = base.Item().parse(object.object_data)

        before = utils.get(self.backpack, asset_id=cso_item.id)
        if before is None:
            return log.info("Received an item that isn't our inventory %r", object)
        after = await self.update_backpack(cso_item)
        self.dispatch("item_update", before, after)

    @register(Language.SODestroy)
    def handle_so_destroy(self, msg: GCMsgProto[sdk.SingleObject]):
        if msg.body.type_id != 1 or not self.backpack:
            return

        deleted_item = base.Item().parse(msg.body.object_data)
        item = utils.get(self.backpack, asset_id=deleted_item.id)
        if item is None:
            return log.info("Received an item that isn't our inventory %r", deleted_item)
        for attribute_name in deleted_item.__annotations__:
            setattr(item, attribute_name, getattr(deleted_item, attribute_name))
        self.backpack.items.remove(item)  # type: ignore
        self.dispatch("item_remove", item)

    # @register(Language.SOCacheSubscribed)
    # def handle_so_cache_subscribed(self, msg):
    #     ...
