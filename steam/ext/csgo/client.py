from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, overload

from typing_extensions import ClassVar

from ... import utils
from ...abc import SteamID
from ...ext import commands
from ...game import CSGO
from .._gc import Client as Client_
from .enums import Language
from .models import ClientUser, User
from .protobufs.cstrike import PreviewDataBlock
from .state import GCState

if TYPE_CHECKING:
    from .protobufs.gcsdk import ClientHello


__all__ = (
    "Client",
    "Bot",
)

from ...protobufs import GCMsgProto


class Client(Client_):
    _GAME: ClassVar = CSGO
    user: ClientUser
    _connection: GCState

    def _get_state(self, **options: Any) -> GCState:
        return GCState(client=self, **options)

    def _get_gc_message(self) -> GCMsgProto[ClientHello]:
        return GCMsgProto(Language.ClientHello)

    async def _handle_ready(self) -> None:
        self.http.user = ClientUser(self._connection, await self.http.get_user(self.user.id64))
        await super()._handle_ready()

    @overload
    async def inspect_item(self, *, owner: SteamID, asset_id: int, d: int) -> PreviewDataBlock:
        ...

    @overload
    async def inspect_item(self, *, market_id: int, asset_id: int, d: int) -> PreviewDataBlock:
        ...

    @overload
    async def inspect_item(self, *, url: str) -> PreviewDataBlock:
        ...

    async def inspect_item(
        self,
        *,
        owner: SteamID | None = None,
        asset_id: int = 0,
        d: int = 0,
        market_id: int = 0,
        url: str = "",
    ) -> PreviewDataBlock:
        """
        The parameters can be taken from `inspect` links either from an inventory or market.
        The market has the `m` parameter, while the inventory one has `s`.
        """

        if url:
            try:
                search = re.search(r"[SM](\d+)A(\d+)D(\d+)$", url)
                owner = SteamID(int(search[1]) if search[0].startswith("S") else 0)
                market_id = int(search[1]) if search[0].startswith("M") else 0
                asset_id = int(search[2])
                d = int(search[3])
            except TypeError:
                raise ValueError("Inspect url is invalid")

        elif owner is None and market_id == 0:
            raise TypeError(f"Missing required keyword-only argument: 'owner' or 'market_id'")
        elif d == 0 or asset_id == 0:
            raise TypeError(f"Missing required keyword-only argument: {'d' if not d else 'asset_id'}")

        await self.ws.send_gc_message(
            GCMsgProto(
                Language.Client2GCEconPreviewDataBlockRequest,
                param_s=owner.id64 if owner else 0,
                param_a=asset_id,
                param_d=d,
                param_m=market_id,
            )
        )

        return await self.wait_for("inspect_item_info", timeout=60.0, check=lambda item: item.itemid == asset_id)

    if TYPE_CHECKING:

        def get_user(self, id: utils.Intable) -> User | None:
            ...

        async def fetch_user(self, id: utils.Intable) -> User | None:
            ...


class Bot(commands.Bot, Client):
    ...
