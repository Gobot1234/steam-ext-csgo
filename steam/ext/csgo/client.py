from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import ClassVar

from ... import utils
from ...client import Client
from ...ext import commands
from ...game import CSGO, Game
from .models import ClientUser, User
from .state import GCState

__all__ = (
    "Client",
    "Bot",
)


class Client(Client):
    GAME: ClassVar = CSGO
    user: ClientUser

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

    async def _handle_ready(self) -> None:
        self._connection._unpatched_inventory = self.user.inventory
        self.http.user = ClientUser(self._connection, await self.http.get_user(self.user.id64))
        super()._handle_ready()

    if TYPE_CHECKING:

        def get_user(self, id: utils.Intable) -> User | None:
            ...

        async def fetch_user(self, id: utils.Intable) -> User | None:
            ...


class Bot(commands.Bot, Client):
    ...
