from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import ClassVar

from ... import utils
from ...ext import commands
from ...game import CSGO
from .._gc import Client as Client_
from .enums import Language
from .models import ClientUser, User
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

    def _get_state(self, **options: Any) -> GCState:
        return GCState(client=self, **options)

    def _get_gc_message(self) -> GCMsgProto[ClientHello]:
        return GCMsgProto(Language.ClientHello)

    async def _handle_ready(self) -> None:
        self.http.user = ClientUser(self._connection, await self.http.get_user(self.user.id64))
        await super()._handle_ready()

    if TYPE_CHECKING:

        def get_user(self, id: utils.Intable) -> User | None:
            ...

        async def fetch_user(self, id: utils.Intable) -> User | None:
            ...


class Bot(commands.Bot, Client):
    ...
