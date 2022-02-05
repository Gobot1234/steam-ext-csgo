from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address
from pprint import pprint
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from typing_extensions import Literal, Self

from ... import abc, user
from ...game import CSGO, Game
from ...game_server import GameServer
from ...protobufs import GCMsgProto
from ...trade import Inventory
from .enums import Language
from .protobufs import cstrike

if TYPE_CHECKING:
    from .backpack import Backpack
    from .state import GCState


UserT = TypeVar("UserT", bound=abc.BaseUser)


class Sticker:
    __slots__ = ("slot", "id", "wear", "scale", "rotation", "tint_id")

    def __init__(
        self,
        slot: Literal[1, 2, 3, 4, 5],  # TODO: enum these
        id: int,
        wear: float | None = None,
        scale: float | None = None,
        rotation: float | None = None,
        tint_id: float | None = None,
    ):
        self.slot = slot
        self.id = id
        self.wear = wear
        self.scale = scale
        self.rotation = rotation
        self.tint_id = tint_id

    _decodeable_attrs = (
        "wear",
        "scale",
        "rotation",
    )


class MatchInfo:
    def __init__(self, match_info: cstrike.MatchInfo, state: GCState) -> None:
        self._state = state
        self.id = match_info.matchid
        self.created_at = datetime.utcfromtimestamp(match_info.matchtime)
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

        self.reservation = match_info.roundstats_legacy
        # round: int = betterproto.int32_field(4)
        # kills: List[int] = betterproto.int32_field(5)
        # assists: List[int] = betterproto.int32_field(6)
        # deaths: List[int] = betterproto.int32_field(7)
        # scores: List[int] = betterproto.int32_field(8)
        # pings: List[int] = betterproto.int32_field(9)
        # round_result: int = betterproto.int32_field(10)
        # match_result: int = betterproto.int32_field(11)
        # team_scores: List[int] = betterproto.int32_field(12)
        # confirm: "MatchmakingServerConfirm" = betterproto.message_field(13)
        # reservation_stage: int = betterproto.int32_field(14)
        # match_duration: int = betterproto.int32_field(15)
        # enemy_kills: List[int] = betterproto.int32_field(16)
        # enemy_headshots: List[int] = betterproto.int32_field(17)
        # enemy_3_ks: List[int] = betterproto.int32_field(18)
        # enemy_4_ks: List[int] = betterproto.int32_field(19)
        # enemy_5_ks: List[int] = betterproto.int32_field(20)
        # mvps: List[int] = betterproto.int32_field(21)
        # spectators_count: int = betterproto.uint32_field(22)
        # spectators_count_tv: int = betterproto.uint32_field(23)
        # spectators_count_lnk: int = betterproto.uint32_field(24)
        # enemy_kills_agg: List[int] = betterproto.int32_field(25)
        # drop_info: "MatchmakingServerRoundStatsDropInfo" = betterproto.message_field(26)
        # switched_teams: bool = betterproto.bool_field(27)
        # enemy_2_ks: List[int] = betterproto.int32_field(28)
        # player_spawned: List[int] = betterproto.int32_field(29)
        # team_spawn_count: List[int] = betterproto.int32_field(30)
        # roundstats_legacy: "MatchmakingServerRoundStats" = betterproto.message_field(4)
        # round_stats_all: List["MatchmakingServerRoundStats"] = betterproto.message_field(5)
        pprint(match_info.to_dict())

    async def server(self) -> GameServer:
        await self._state.client.fetch_game_server(ip=str(self.server_ip))


@dataclass
class Matches:
    matches: list[MatchInfo]
    streams: list["TournamentTeam"]
    tournament_info: "TournamentInfo"


class BaseUser(abc.BaseUser):
    __slots__ = ()
    _state: GCState

    async def csgo_profile(self) -> ProfileInfo[Self]:
        msg = await self._state.fetch_user_csgo_profile(self.id)
        if not msg.account_profiles:
            raise ValueError("This should be unreachable?")
        return ProfileInfo(self, msg.account_profiles[0])


class User(BaseUser, user.User):
    __slots__ = ()

    async def recent_matches(self) -> Matches:
        await self._state.ws.send_gc_message(GCMsgProto(Language.MatchListRequestRecentUserGames, accountid=self.id))
        msg: GCMsgProto[cstrike.MatchList] = await self._state.gc_wait_for(
            Language.MatchList, check=lambda msg: msg.body.accountid == self.id
        )
        pprint(msg.body.to_dict())
        # return Matches(msg.body)


class ClientUser(BaseUser, user.ClientUser):
    __slots__ = ("_profile_info_msg",)

    if TYPE_CHECKING:

        @overload
        async def inventory(self, game: Literal[CSGO]) -> Backpack:  # type: ignore
            ...

        @overload
        async def inventory(self, game: Game) -> Inventory:  # type: ignore
            ...

    async def csgo_profile(self) -> ProfileInfo[Self]:
        return ProfileInfo(self, self._profile_info_msg)

    async def live_games(self) -> ...:
        ...


class ProfileInfo(Generic[UserT]):
    def __init__(self, user: UserT, proto: cstrike.MatchmakingClientHello):
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
