from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any

from typing_extensions import Literal
from .protobufs import cstrike15_gcmessages as cstrike
from .protobufs.cstrike15_gcmessages import CEconItemPreviewDataBlockSticker as ProtoSticker


class Sticker:
    __slots__ = tuple(ProtoSticker.__annotations__)

    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            if key not in self.__slots__:
                raise TypeError()

            setattr(self, key, value)

    slot: Literal[1, 2, 3, 4, 5]
    sticker_id: int
    wear: Optional[float] = None
    scale: Optional[float] = None
    rotation: Optional[float] = None

    @classmethod
    def get_attrs(cls):
        attrs = list(ProtoSticker.__annotations__)
        del attrs[0]
        del attrs[0]

        cls.get_attrs = lambda: attrs
        return attrs


if TYPE_CHECKING:

    @dataclass
    class Sticker(Sticker, ProtoSticker):
        ...


class AccountInfo:
    def __init__(self, msg: cstrike.CMsgGccStrike15V2MatchmakingGc2ClientHello):
        self.on_going_match = msg.ongoingmatch
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
        self._current_xp = msg.player_cur_xp
        self.xp_bonus_flags = msg.player_xp_bonus_flags
        self.rankings = msg.rankings

    @property
    def level(self) -> int:
        """:class:`int`: The user's current level."""
        return math.floor((self.current_xp - 327680000) / 5000)
