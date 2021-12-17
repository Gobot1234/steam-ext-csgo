from steam.protobufs import PROTOBUFS

from ..enums import Language
from . import base, cstrike, econ, gcsdk

PROTOBUFS.update(
    {
        Language.ClientConnectionStatus: gcsdk.ConnectionStatus,
        Language.ClientRequestWatchInfoFriends2: cstrike.ClientRequestWatchInfoFriends,
        Language.ClientWelcome: gcsdk.ClientWelcome,
        Language.ClientHello: gcsdk.ClientHello,
        Language.MatchmakingGC2ClientHello: cstrike.MatchmakingClientHello,
        Language.MatchList: cstrike.MatchList,
        Language.PlayersProfile: cstrike.PlayersProfile,
        Language.Client2GCEconPreviewDataBlockRequest: cstrike.Client2GcEconPreviewDataBlockRequest,
        Language.Client2GCEconPreviewDataBlockResponse: cstrike.Client2GcEconPreviewDataBlockResponse,
        Language.ItemCustomizationNotification: econ.ItemCustomizationNotification,
        Language.CasketItemLoadContents: econ.CasketItem,
        Language.SOCreate: gcsdk.SingleObject,
        Language.SOUpdate: gcsdk.SingleObject,
        Language.SODestroy: gcsdk.SingleObject,
        Language.SOUpdateMultiple: gcsdk.MultipleObjects,
    }
)
