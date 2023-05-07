"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

import re
import struct
from typing import TYPE_CHECKING, Any, Final, overload

from typing_extensions import Self

from ..._const import timeout
from ..._gc import Client as Client_
from ...app import CSGO
from ...enums import Type
from ...ext import commands
from ...id import ID
from ...types.id import Intable
from ...utils import cached_property
from .backpack import Paint, Sticker
from .enums import ItemOrigin, ItemQuality
from .models import ClientUser, MatchInfo, User
from .protobufs import cstrike
from .state import GCState

if TYPE_CHECKING:
    from ...ext import csgo
    from ...types.user import IndividualID
    from .backpack import BaseInspectedItem


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

    _APP: Final = CSGO  # type: ignore
    _ClientUserCls = ClientUser
    user: cached_property[Self, ClientUser]
    _state: GCState
    _GC_HEART_BEAT = 10.0

    @overload
    async def inspect_item(self, *, owner: IndividualID, asset_id: int, d: int) -> BaseInspectedItem:
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
        owner: IndividualID | None = None,
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

            owner = ID(int(search[1]) if search[0].startswith("S") else 0, type=Type.Individual)
            market_id = int(search[1]) if search[0].startswith("M") else 0
            asset_id = int(search[2])
            d = int(search[3])

        elif owner is None and market_id == 0:
            raise TypeError("Missing required keyword-only argument: 'owner' or 'market_id'")
        elif d == 0 or asset_id == 0:
            raise TypeError(f"Missing required keyword-only argument: {'asset_id' if d else 'd'}")

        future = self.ws.gc_wait_for(
            cstrike.Client2GcEconPreviewDataBlockResponse,
            check=lambda msg: isinstance(msg, cstrike.Client2GcEconPreviewDataBlockResponse)
            and msg.iteminfo.itemid == asset_id,
        )
        await self._state.ws.send_gc_message(
            cstrike.Client2GcEconPreviewDataBlockRequest(
                param_s=owner.id64 if owner else 0,
                param_a=asset_id,
                param_d=d,
                param_m=market_id,
            )
        )

        msg = await future

        item = msg.iteminfo
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

    async def fetch_match(self, id: int, *, outcome_id: int, token: int) -> MatchInfo:
        """Fetch a match by its id."""
        future = self.ws.gc_wait_for(
            cstrike.MatchInfo, check=lambda msg: isinstance(msg, cstrike.MatchList) and msg.matchid == id
        )
        await self.ws.send_gc_message(cstrike.MatchListRequestFullGameInfo(id, outcome_id, token))
        async with timeout(30):
            return MatchInfo(self._state, await future)

    if TYPE_CHECKING:

        def get_user(self, id: Intable) -> User | None:
            ...

        async def fetch_user(self, id: Intable) -> User:
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
            item
                The received item.
            """

        async def on_item_remove(self, item: csgo.BackpackItem) -> None:
            """Called when the client has an item removed from its backpack.

            Parameters
            ----------
            item
                The removed item.
            """

        async def on_item_update(self, before: csgo.BackpackItem, after: csgo.BackpackItem) -> None:
            """Called when the client has an item in its backpack updated.

            Parameters
            ----------
            before
                The item before being updated.
            after
                The item now.
            """


class Bot(commands.Bot, Client):
    """Represents a Steam bot.

    :class:`Bot` is a subclass of :class:`~steam.ext.commands.Bot`, so whatever you can do with
    :class:`~steam.ext.commands.Bot` you can do with :class:`Bot`.
    """
