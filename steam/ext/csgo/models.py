from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

from typing_extensions import Literal

from ... import utils
from ...game import CSGO, Game
from ...trade import Inventory
from ...user import ClientUser
from .protobufs import cstrike15_gcmessages as cstrike
from .protobufs.cstrike15_gcmessages import CEconItemPreviewDataBlockSticker as ProtoSticker

if TYPE_CHECKING:
    from .backpack import BackPack


@dataclass
class Sticker:
    __slots__ = tuple(ProtoSticker.__annotations__)

    slot: Literal[1, 2, 3, 4, 5]  # TODO: enum these
    sticker_id: int
    wear: float | None
    scale: float | None
    rotation: float | None

    @classmethod
    def get_attrs(cls):
        attrs = list(ProtoSticker.__annotations__)
        del attrs[0]
        del attrs[0]
        return attrs


if TYPE_CHECKING:

    class Sticker(Sticker, ProtoSticker):
        ...


class CSGOClientUser(ClientUser):
    def __init__(self, client_user: ClientUser, msg: cstrike.CMsgGccStrike15V2MatchmakingGc2ClientHello):  # noqa
        self.in_match = msg.ongoingmatch
        self.global_stats = msg.global_stats
        self.penalty_seconds = msg.penalty_seconds
        self.penalty_reason = msg.penalty_reason
        self.vac_banned = msg.vac_banned
        self.ranking = msg.ranking
        self.commendation = msg.commendation
        self.medals = msg.medals
        self.current_event = msg.my_current_event
        self.current_event_teams = msg.my_current_event_teams
        self.current_team = msg.my_current_team
        self.current_event_stages = msg.my_current_event_stages
        self.survey_vote = msg.survey_vote
        self.activity = msg.activity
        self.player_level = msg.player_level
        self.current_xp = msg.player_cur_xp
        self.xp_bonus_flags = msg.player_xp_bonus_flags
        self.rankings = msg.rankings

        utils.update_class(client_user, self)

    @property
    def percentage_of_current_level(self) -> int:
        """The user's current level."""
        return math.floor((self.current_xp - 327680000) / 5000)

    @overload
    async def inventory(self, game: Literal[CSGO]) -> BackPack:
        ...

    @overload
    async def inventory(self, game: Game) -> Inventory:
        ...

    async def inventory(self, game: Game) -> Inventory | BackPack:
        return await super().inventory(game)


class AccountInfo:
    def __init__(self, msg: cstrike.CMsgGccStrike15V2MatchmakingGc2ClientHello):
        self.in_match = msg.ongoingmatch
        self.global_stats = msg.global_stats
        self.penalty_seconds = msg.penalty_seconds
        self.penalty_reason = msg.penalty_reason
        self.vac_banned = msg.vac_banned
        self.ranking = msg.ranking
        self.commendation = msg.commendation
        self.medals = msg.medals
        self.current_event = msg.my_current_event
        self.current_event_teams = msg.my_current_event_teams
        self.current_team = msg.my_current_team
        self.current_event_stages = msg.my_current_event_stages
        self.survey_vote = msg.survey_vote
        self.activity = msg.activity
        self.current_xp = msg.player_cur_xp
        self.player_level = msg.player_level
        self.xp_bonus_flags = msg.player_xp_bonus_flags
        self.rankings = msg.rankings
