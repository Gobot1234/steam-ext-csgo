# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional, Union

import vdf
from multidict import MultiDict
from typing_extensions import Final

from steam import CSGO, Client, Game

from .enums import Language
from .state import GCState

__all__ = ("Client",)


class Client(Client):
    VDF_DECODER: Callable[[str], MultiDict] = vdf.loads  #: The default VDF decoder to use
    VDF_ENCODER: Callable[[str], MultiDict] = vdf.dumps  #: The default VDF encoder to use
    GAME: Final[Game] = CSGO

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None, **options: Any):
        game = options.pop("game", None)
        if game is not None:  # don't let them overwrite the main game
            try:
                options["games"].append(game)
            except (TypeError, KeyError):
                options["games"] = [game]
        options["game"] = self.GAME
        self._original_games: list[Game] = options.get("games")
        super().__init__(loop, **options)
        self._connection = GCState(client=self, http=self.http, **options)

    def set_language(self, file: Union[Path, str]) -> None:
        """Set the localization files for your bot.

        This isn't necessary in most situations.
        """
        file = Path(file).resolve()
        self._connection.language = self.VDF_DECODER(file.read_text())

    # boring subclass stuff

    async def close(self) -> None:
        try:
            if self.ws:
                await self.change_presence(game=Game(id=0))  # disconnect from games
        finally:
            await super().close()
