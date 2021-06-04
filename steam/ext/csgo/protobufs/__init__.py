from steam.protobufs import PROTOBUFS

from ..enums import Language
from . import (
    base_gcmessages as cso_messages,
    cstrike15_gcmessages as cstrike,
    econ_gcmessages,
    gcsdk_gcmessages as so_messages,
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
