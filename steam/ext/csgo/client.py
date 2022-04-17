from __future__ import annotations

import re
import struct
from datetime import datetime
from typing import TYPE_CHECKING, Any, overload

from typing_extensions import Final, Literal

from ... import utils
from ...abc import Message, SteamID
from ...ext import commands
from ...game import CSGO
from ...gateway import GCMsgsT, Msgs
from ...invite import ClanInvite, UserInvite
from ...protobufs import GCMsgProto
from ...trade import TradeOffer
from .._gc import Client as Client_
from .backpack import BackpackItem, Paint, Sticker
from .enums import ItemOrigin, ItemQuality, Language
from .models import ClientUser, User
from .protobufs import cstrike
from .state import GCState

if TYPE_CHECKING:
    from ...comment import Comment
    from ...ext import csgo
    from .backpack import BaseInspectedItem
    from .protobufs.sdk import ClientHello


__all__ = (
    "Client",
    "Bot",
)


class Client(Client_):
    """Represents a client connection that connects to Steam. This class is used to interact with the Steam API, CMs
    and the CSGO Game Coordinator.

    :class:`Client` is a subclass of :class:`steam.Client`, so whatever you can do with :class:`steam.Client` you can
    do with :class:`Client`.
    """

    _GAME: Final = CSGO
    user: ClientUser
    _connection: GCState
    _GC_HEART_BEAT = 10.0

    def _get_state(self, **options: Any) -> GCState:
        return GCState(client=self, **options)

    def _get_gc_message(self) -> GCMsgProto[ClientHello]:
        return GCMsgProto(Language.ClientHello)

    async def _handle_ready(self) -> None:
        self.http.user = ClientUser(self._connection, await self.http.get_user(self.user.id64))
        await super()._handle_ready()

    @overload
    async def inspect_item(self, *, owner: SteamID, asset_id: int, d: int) -> BaseInspectedItem:
        ...

    @overload
    async def inspect_item(self, *, market_id: int, asset_id: int, d: int) -> BaseInspectedItem:
        ...

    @overload
    async def inspect_item(self, *, url: str) -> BaseInspectedItem:
        ...

    async def inspect_item(
        self,
        *,
        owner: SteamID | None = None,
        asset_id: int = 0,
        d: int = 0,
        market_id: int = 0,
        url: str = "",
    ) -> BaseInspectedItem:
        """Inspect an item.

        Parameters
        ----------
        owner
            The owner of the item.
        asset_id
            The asset id of the item.
        d
            The "D" number following the "D" character.
        market_id
            The id of the item on the steam community market.
        url
            The full inspect url to be parsed.
        """

        if url:
            search = re.search(r"[SM](\d+)A(\d+)D(\d+)$", url)
            if search is None:
                raise ValueError("Inspect url is invalid")

            owner = SteamID(int(search[1]) if search[0].startswith("S") else 0)
            market_id = int(search[1]) if search[0].startswith("M") else 0
            asset_id = int(search[2])
            d = int(search[3])

        elif owner is None and market_id == 0:
            raise TypeError("Missing required keyword-only argument: 'owner' or 'market_id'")
        elif d == 0 or asset_id == 0:
            raise TypeError(f"Missing required keyword-only argument: {'asset_id' if d else 'd'}")

        future = self._connection.gc_wait_for(
            Language.Client2GCEconPreviewDataBlockResponse,
            check=lambda msg: msg.body.iteminfo.itemid == asset_id,
        )
        await self.ws.send_gc_message(
            GCMsgProto(
                Language.Client2GCEconPreviewDataBlockRequest,
                param_s=owner.id64 if owner else 0,
                param_a=asset_id,
                param_d=d,
                param_m=market_id,
            )
        )

        msg: GCMsgProto[cstrike.Client2GcEconPreviewDataBlockResponse] = await future  # type: ignore

        item = msg.body.iteminfo
        # decode the wear
        packed_wear = struct.pack(">l", item.paintwear)
        (paint_wear,) = struct.unpack(">f", packed_wear)
        return BaseInspectedItem(
            id=item.itemid,
            def_index=item.defindex,
            paint=Paint(index=item.paintindex, wear=paint_wear, seed=item.paintseed),
            rarity=item.rarity,
            quality=ItemQuality.try_value(item.quality),
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
            origin=ItemOrigin.try_value(item.origin),
            quest_id=item.questid,
            drop_reason=item.dropreason,
            music_index=item.musicindex,
            ent_index=item.entindex,
        )

    if TYPE_CHECKING:

        def get_user(self, id: utils.Intable) -> User | None:
            ...

        async def fetch_user(self, id: utils.Intable) -> User | None:
            ...

        async def on_gc_connect(self) -> None:
            """Called after the client receives the welcome message from the GC.

            Warning
            -------
            This is called every time we craft an item and disconnect so same warnings apply to
            :meth:`steam.Client.on_connect`
            """

        async def on_gc_disconnect(self) -> None:
            """Called after the client receives the goodbye message from the GC.

            Warning
            -------
            This is called every time we craft an item and disconnect so same warnings apply to
            :meth:`steam.Client.on_connect`
            """

        async def on_gc_ready(self) -> None:
            """Called after the client connects to the GC and has the :attr:`schema`, :meth:`Client.user.inventory` and
            set up and account info (:meth:`is_premium` and :attr:`backpack_slots`).

            Warning
            -------
            This is called every time we craft an item and disconnect so same warnings apply to
            :meth:`steam.Client.on_connect`
            """

        async def on_item_receive(self, item: csgo.BackpackItem) -> None:
            """Called when the client receives an item.

            Parameters
            ----------
            item: :class:`.BackpackItem`
                The received item.
            """

        async def on_item_remove(self, item: csgo.BackpackItem) -> None:
            """Called when the client has an item removed from its backpack.

            Parameters
            ----------
            item: :class:`.BackpackItem`
                The removed item.
            """

        async def on_item_update(self, before: csgo.BackpackItem, after: csgo.BackpackItem) -> None:
            """Called when the client has an item in its backpack updated.

            Parameters
            ----------
            before: :class:`.BackpackItem`
                The item before being updated.
            after: :class:`.BackpackItem`
                The item now.
            """

        @overload
        async def wait_for(  # type: ignore
            self,
            event: Literal[
                "connect",
                "disconnect",
                "ready",
                "login",
                "logout",
                "gc_connect",
                "gc_disconnect",
                "gc_ready",
            ],
            *,
            check: "() -> bool" = ...,
            timeout: float | None = ...,
        ) -> None:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["error"],
            *,
            check: "(str, Exception, tuple[Any, ...], dict[str, Any]) -> bool" = ...,
            timeout: float | None = ...,
        ) -> tuple[str, Exception, tuple[Any, ...], dict[str, Any]]:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["message"],
            *,
            check: "(Message) -> bool" = ...,
            timeout: float | None = ...,
        ) -> Message:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["comment"],
            *,
            check: "(Comment) -> bool" = ...,
            timeout: float | None = ...,
        ) -> Comment:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["user_update"],
            *,
            check: "(User, User) -> bool" = ...,
            timeout: float | None = ...,
        ) -> tuple[User, User]:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["typing"],
            *,
            check: "(User, datetime) -> bool" = ...,
            timeout: float | None = ...,
        ) -> tuple[User, datetime]:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal[
                "trade_receive",
                "trade_send",
                "trade_accept",
                "trade_decline",
                "trade_cancel",
                "trade_expire",
                "trade_counter",
            ],
            *,
            check: "(TradeOffer)-> bool" = ...,
            timeout: float | None = ...,
        ) -> TradeOffer:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["user_invite"],
            *,
            check: "(UserInvite) -> bool" = ...,
            timeout: float | None = ...,
        ) -> UserInvite:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal["clan_invite"],
            *,
            check: "(ClanInvite) -> bool" = ...,
            timeout: float | None = ...,
        ) -> ClanInvite:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal[
                "socket_receive",
                "socket_send",
            ],
            *,
            check: "(Msgs) -> bool" = ...,
            timeout: float | None = ...,
        ) -> Msgs:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal[
                "gc_message_receive",
                "gc_message_send",
            ],
            *,
            check: "(GCMsgsT) -> bool" = ...,
            timeout: float | None = ...,
        ) -> GCMsgsT:
            ...

        @overload
        async def wait_for(
            self,
            event: Literal[
                "item_receive",
                "item_remove",
                "item_update",
            ],
            *,
            check: "(BackpackItem) -> bool" = ...,
            timeout: float | None = ...,
        ) -> BackpackItem:
            ...


class Bot(commands.Bot, Client):
    """Represents a Steam bot.

    :class:`Bot` is a subclass of :class:`~steam.ext.commands.Bot`, so whatever you can do with
    :class:`~steam.ext.commands.Bot` you can do with :class:`Bot`.
    """
