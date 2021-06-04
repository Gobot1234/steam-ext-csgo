# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Literal, Optional, Union, overload

from typing_extensions import Final

from steam import CSGO, Client, ClientUser, Game, Inventory
from steam.ext import commands

from .backpack import BackPack
from .state import GCState

__all__ = (
    "Client",
    "Bot",
)


class Client(Client):
    GAME: Final[Game] = CSGO

    def __init__(self, **options: Any):
        game = options.pop("game", None)
        if game is not None:  # don't let them overwrite the main game
            try:
                options["games"].append(game)
            except (TypeError, KeyError):
                options["games"] = [game]
        options["game"] = self.GAME
        self._original_games: Optional[list[Game]] = options.get("games")
        super().__init__(**options)
        self._connection = GCState(client=self, **options)

    # boring subclass stuff

    def _handle_ready(self) -> None:
        self._connection._unpatched_inventory = self.user.inventory
        super()._handle_ready()

    @property
    def user(self):
        old_user = super().user()
        return CSGOClientUser(old_user) if old_user is not None else None


class Bot(commands.Bot, Client):
    ...
