from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, overload, Type

from typing_extensions import ClassVar

from ... import utils
from ...client import Client as Client_
from ...ext import commands
from ...game import CSGO, Game
from ...abc import SteamID
from .enums import Language
from .models import ClientUser, User
from .state import GCState
from .protobufs.cstrike import PreviewDataBlock

__all__ = (
    "Client",
    "Bot",
)

from ...protobufs import GCMsgProto


class Client(Client_):
    GAME: ClassVar = CSGO
    user: ClientUser
    _connection: GCState

    def __init__(self, **options: Any):
        game = options.pop("game", None)
        if game is not None:  # don't let them overwrite the main game
            try:
                options["games"].append(game)
            except (TypeError, KeyError):
                options["games"] = [game]
        options["game"] = self.GAME
        self._original_games: list[Game] | None = options.get("games")
        super().__init__(**options)

    # boring subclass stuff

    def _get_state(self, **options: Any) -> GCState:
        return GCState(client=self, **options)

    async def connect(self):
        async def ping():
            await self.wait_until_ready()
            while not self.is_closed():
                await self.ws.send_gc_message(GCMsgProto(Language.ClientHello))
                await asyncio.sleep(30)

        await asyncio.gather(
            super().connect(),
            ping(),
        )

    async def _handle_ready(self) -> None:
        self._connection._unpatched_inventory = self.user.inventory
        self.http.user = ClientUser(self._connection, await self.http.get_user(self.user.id64))
        await super()._handle_ready()

    @overload
    async def inspect_item(self, *, owner: Type[SteamID], asset_id: int, d: int) -> PreviewDataBlock:
        ...

    @overload
    async def inspect_item(self, *, s: int, a: int, d: int) -> PreviewDataBlock:
        ...

    @overload
    async def inspect_item(self, *, m: int, a: int, d: int) -> PreviewDataBlock:
        ...

    @overload
    async def inspect_item(self, *, url: str) -> PreviewDataBlock:
        ...

    async def inspect_item(
            self,
            *,
            owner: SteamID | None = None,
            asset_id: int | None = None,
            s: int = 0,
            a: int = 0,
            d: int = 0,
            m: int = 0,
            url: str = "",
            timeout: int=10
    ) -> PreviewDataBlock:
        """
        The parameters can be taken from `inspect` links either from an inventory or market.
        The market has the `m` parameter, while the inventory one has `s`.
        :param s: steam id64 of owner
        :param a: item (asset) id
        :param d: inspect id (Unknown d number)
        :param m: market id
        """
        if owner:
            s = owner.id64
        if asset_id:
            a = asset_id

        if url:
            search = re.search(r'[SM](\d+)A(\d+)D(\d+)$', url)
            s = int(search[1]) if search[0].startswith("S") else 0
            m = int(search[1]) if search[0].startswith("M") else 0
            a = int(search[2])
            d = int(search[3])

        if s == 0 and m == 0:
            raise TypeError(f"Missing required keyword-only argument: {'s' if not s else 'm'}")

        params = {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
        }
        await self.ws.send_gc_message(GCMsgProto(Language.Client2GCEconPreviewDataBlockRequest, **params))

        return await self.wait_for(
            "inspect_item_info",
            timeout=timeout,
            check=lambda item: item.itemid == a
        )

    if TYPE_CHECKING:

        def get_user(self, id: utils.Intable) -> User | None:
            ...

        async def fetch_user(self, id: utils.Intable) -> User | None:
            ...


class Bot(commands.Bot, Client):
    ...
