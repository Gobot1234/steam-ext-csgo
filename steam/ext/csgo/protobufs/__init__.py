from dataclasses import dataclass
from typing import List

import betterproto
from steam.protobufs import PROTOBUFS

from ..enums import Language
from . import (
    base_gcmessages as cso_messages,
    cstrike15_gcmessages as cstrike,
    gcsdk_gcmessages as so_messages,
    econ_gcmessages,
)


PROTOBUFS.update(
    {
        Language.ClientConnectionStatus: so_messages.CMsgConnectionStatus,
        Language.ClientRequestWatchInfoFriends2: cstrike.CMsgGccStrike15V2ClientRequestWatchInfoFriends,
        Language.ClientWelcome: so_messages.CMsgClientWelcome,
        Language.MatchmakingGC2ClientHello: cstrike.CMsgGccStrike15V2MatchmakingGc2ClientHello,
        Language.MatchList: cstrike.CMsgGccStrike15V2MatchList,
        Language.PlayersProfile: cstrike.CMsgGccStrike15V2PlayersProfile,
        Language.Client2GCEconPreviewDataBlockResponse: cstrike.CMsgGccStrike15V2Client2GcEconPreviewDataBlockResponse,
        Language.ItemCustomizationNotification: econ_gcmessages.CMsgGcItemCustomizationNotification,
        Language.SOCreate: so_messages.CMsgSoSingleObject,
        Language.SOUpdate: so_messages.CMsgSoSingleObject,
        Language.SODestroy: so_messages.CMsgSoSingleObject,
        Language.SOUpdateMultiple: so_messages.CMsgSoMultipleObjects,
    }
)


@dataclass(eq=False, repr=False)
class UpdateMultipleItems(betterproto.Message):
    owner: int = betterproto.fixed64_field(1)
    objects: List["InnerItem"] = betterproto.message_field(2)
    version: float = betterproto.fixed64_field(3)


@dataclass(eq=False, repr=False)
class InnerItem(betterproto.Message):
    type_id: int = betterproto.uint32_field(1)
    inner: "cso_messages.CsoEconItem" = betterproto.message_field(2)
