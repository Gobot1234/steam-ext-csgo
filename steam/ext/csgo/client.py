from __future__ import annotations

from typing import Any

from typing_extensions import ClassVar

from ...client import Client
from ...ext import commands
from ...game import CSGO, Game
from .models import CSGOClientUser
from .state import GCState

__all__ = (
    "Client",
    "Bot",
)


class Client(Client):
    GAME: ClassVar = CSGO

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

    def _handle_ready(self) -> None:
        self._connection._unpatched_inventory = self.user.inventory
        super()._handle_ready()

    @property
    def user(self) -> CSGOClientUser:
        old_user = super().user
        return CSGOClientUser(old_user) if old_user is not None else None  # type: ignore


class Bot(commands.Bot, Client):
    ...
