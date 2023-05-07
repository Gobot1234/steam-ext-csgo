"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

import math
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from typing_extensions import Literal, Self

from ... import abc, user
from ..._gc.client import ClientUser as ClientUser_
from ...app import CSGO, App
from ...game_server import GameServer
from ...utils import DateTime
from ..commands.converters import Converter, UserConverter
from .protobufs import cstrike

if TYPE_CHECKING:
    from ...enums import Language
    from ...trade import Inventory, Item
    from .backpack import Backpack
    from .state import GCState


UserT = TypeVar("UserT", bound=abc.PartialUser)

__all__ = (
    "PartialUser",
    "User",
    "ClientUser",
    "ProfileInfo",
)


class MatchInfo:
    def __init__(self, state: GCState, match_info: cstrike.MatchInfo) -> None:
        self._state = state
        self.id = match_info.matchid
        self.created_at = DateTime.from_timestamp(match_info.matchtime)
        self.server_ip = IPv4Address(match_info.watchablematchinfo.server_ip)
        # TODO consider adding these
        # tv_port: int = betterproto.uint32_field(2)
        # tv_spectators: int = betterproto.uint32_field(3)
        # tv_time: int = betterproto.uint32_field(4)
        # tv_watch_password: bytes = betterproto.bytes_field(5)
        # cl_decryptdata_key: int = betterproto.uint64_field(6)
        # cl_decryptdata_key_pub: int = betterproto.uint64_field(7)
        self.type = match_info.watchablematchinfo.game_type
        self.map_group = match_info.watchablematchinfo.game_mapgroup
        self.map = match_info.watchablematchinfo.game_map
        self.server_id = match_info.watchablematchinfo.server_id

        self.round_stats = match_info.roundstatsall

    async def server(self) -> GameServer:
        server = await self._state.client.fetch_server(ip=str(self.server_ip))
        assert server is not None
        return server


@dataclass
class Matches:
    matches: list[MatchInfo]
    streams: list["cstrike.TournamentTeam"]
    tournament_info: "cstrike.TournamentInfo"


class PartialUser(abc.PartialUser):
    __slots__ = ()
    _state: GCState

    async def csgo_profile(self) -> ProfileInfo[Self]:
        msg = await self._state.fetch_user_csgo_profile(self.id)
        if not msg.account_profiles:
            raise ValueError
        return ProfileInfo(self, msg.account_profiles[0])


class User(PartialUser, user.User):
    __slots__ = ()

    async def recent_matches(self) -> Matches:
        await self._state.ws.send_gc_message(cstrike.MatchListRequestRecentUserGames(accountid=self.id))
        msg = await self._state.ws.gc_wait_for(
            cstrike.MatchList, check=lambda msg: isinstance(msg, cstrike.MatchList) and msg.accountid == self.id
        )

        return Matches([MatchInfo(self._state, match) for match in msg.matches], msg.streams, msg.tournamentinfo)


class ClientUser(PartialUser, ClientUser_):
    __slots__ = ("_profile_info_msg",)

    if TYPE_CHECKING:

        @overload
        async def inventory(self, app: Literal[CSGO], *, language: object = ...) -> Backpack:  # type: ignore
            ...

        @overload
        async def inventory(self, app: App, *, language: Language | None = None) -> Inventory[Item[Self], Self]:
            ...

    async def csgo_profile(self) -> ProfileInfo[Self]:
        return ProfileInfo(self, self._profile_info_msg)

    async def live_games(self) -> ...:
        ...


class ProfileInfo(Generic[UserT]):
    def __init__(self, user: UserT, proto: cstrike.MatchmakingClientHello | cstrike.PlayersProfileProfile):
        self.user = user
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
        """The user's current percentage of their current level."""
        return math.floor(max(self.current_xp - 327680000, 0) / 5000)

    def __repr__(self) -> str:
        return f"<ProfileInfo user={self.user!r}>"


class CSGOUserConverter(Converter[User]):
    convert = UserConverter.convert  # type: ignore
