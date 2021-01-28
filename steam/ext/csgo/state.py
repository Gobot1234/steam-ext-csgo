# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from multidict import MultiDict
from steam.models import EventParser, register
from steam.protobufs import EMsg, GCMsg, GCMsgProto, MsgProto
from steam.state import ConnectionState

from steam import utils

from .enums import Language
from .protobufs import base_gcmessages as cso_messages, gcsdk_gcmessages as so_messages

if TYPE_CHECKING:
    from steam.protobufs.steammessages_clientserver_2 import CMsgGcClient

    from .client import Client

log = logging.getLogger(__name__)


class GCState(ConnectionState):
    gc_parsers: dict[Language, EventParser[Language]] = {}
    client: Client

    __slots__ = ("_connected",)

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(client, **kwargs)
        self.schema: Optional[MultiDict] = None
        self._connected = asyncio.Event()

        language = kwargs.get("language")
        if language is not None:
            client.set_language(language)

    @register(EMsg.ClientFromGC)
    async def parse_gc_message(self, msg: MsgProto[CMsgGcClient]) -> None:
        if msg.body.appid != self.client.GAME.id:
            return

        try:
            language = Language(utils.clear_proto_bit(msg.body.msgtype))
        except ValueError:
            return log.info(
                f"Ignoring unknown msg type: {msg.body.msgtype} ({utils.clear_proto_bit(msg.body.msgtype)})"
            )

        try:
            msg = (
                GCMsgProto(language, msg.body.payload)
                if utils.is_proto(msg.body.msgtype)
                else GCMsg(language, msg.body.payload)
            )
        except Exception as exc:
            return log.error(f"Failed to deserialize message: {language!r}, {msg.body.payload!r}", exc_info=exc)
        else:
            if log.isEnabledFor(logging.DEBUG):
                log.debug(f"Socket has received GC message {msg!r} from the websocket.")

        try:
            func = self.gc_parsers[language]
        except KeyError:
            if log.isEnabledFor(logging.DEBUG):
                log.debug(f"Ignoring event {msg!r}")
        else:
            await utils.maybe_coroutine(func, msg)

    @register(Language.ClientWelcome)
    def parse_gc_client_connect(self, _) -> None:
        if not self._connected.is_set():
            self.dispatch("gc_connect")
            self._connected.set()

    @register(Language.ClientGoodbye)
    def parse_client_goodbye(self, _=None) -> None:
        self.dispatch("gc_disconnect")
        self._connected.clear()
