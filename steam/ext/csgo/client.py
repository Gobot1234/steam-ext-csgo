# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional, overload, Union, Literal

from steam.ext import commands
from typing_extensions import Final
from steam import CSGO, Client, Game, ClientUser, Inventory

from .backpack import BackPack
from .state import GCState

__all__ = (
    "Client",
    "Bot",
)


class CSGOClientUser(ClientUser):
    @overload
    async def inventory(self, game: Literal[CSGO]) -> BackPack:
        ...

    @overload
    async def inventory(self, game: Game) -> Inventory:
        ...

    async def inventory(self, game: Game) -> Union[Inventory, BackPack]:
        return await super().inventory(game)


class Client(Client):
    GAME: Final[Game] = CSGO
    user: Optional[CSGOClientUser]

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


class Bot(commands.Bot, Client):
    ...
