from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

from typing_extensions import Literal

from ... import abc, user
from ...game import CSGO, Game
from ...trade import Inventory
from .protobufs import cstrike

if TYPE_CHECKING:
    from .backpack import Backpack
    from .state import GCState


@dataclass
class Sticker:
    __slots__ = tuple(cstrike.PreviewDataBlockSticker.__annotations__)

    slot: Literal[1, 2, 3, 4, 5]  # TODO: enum these
    id: int
    wear: float | None
    scale: float | None
    rotation: float | None
    tint_id: float

    @classmethod
    def _get_attrs(cls) -> list[str]:
        return cls.__slots__[2:]  # the attributes to decode on


class BaseUser(abc.BaseUser):
    __slots__ = ()
    _state: GCState

    async def csgo_profile(self) -> ProfileInfo:
        msg = await self._state.fetch_user_csgo_profile(self.id64)
        return ProfileInfo(msg)


class User(BaseUser, user.User):
    __slots__ = ()

    async def recent_games(self) -> ...:
        ...


class ClientUser(BaseUser, user.ClientUser):
    __slots__ = ("_profile_info_msg",)

    if TYPE_CHECKING:

        @overload
        async def inventory(self, game: Literal[CSGO]) -> Backpack:
            ...

        @overload
        async def inventory(self, game: Game) -> Inventory:  # type: ignore
            ...

    async def csgo_profile(self) -> ProfileInfo:
        return ProfileInfo(self._profile_info_msg)

    async def live_games(self) -> ...:
        ...


class ProfileInfo:
    def __init__(self, proto: cstrike.MatchmakingClientHello):
        self.in_match = proto.ongoingmatch
        self.global_stats = proto.global_stats
        self.penalty_seconds = proto.penalty_seconds
        self.penalty_reason = proto.penalty_reason
        self.vac_banned = proto.vac_banned
        self.ranking = proto.ranking
        self.commendation = proto.commendation
        self.medals = proto.medals
        self.current_event = proto.my_current_event
        self.current_event_teams = proto.my_current_event_teams
        self.current_team = proto.my_current_team
        self.current_event_stages = proto.my_current_event_stages
        self.survey_vote = proto.survey_vote
        self.activity = proto.activity
        self.current_xp = proto.player_cur_xp
        self.level = proto.player_level
        self.xp_bonus_flags = proto.player_xp_bonus_flags
        self.rankings = proto.rankings

    @property
    def percentage_of_current_level(self) -> int:
        """The user's current level."""
        return math.floor((self.current_xp - 327680000) / 5000)
