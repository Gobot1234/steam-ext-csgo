from steam.protobufs import PROTOBUFS

from ..enums import Language
from . import base, cstrike, econ, sdk, struct_messages

PROTOBUFS.update(  # type: ignore
    {
        Language.ClientConnectionStatus: sdk.ConnectionStatus,
        Language.ClientRequestWatchInfoFriends2: cstrike.ClientRequestWatchInfoFriends,
        Language.ClientWelcome: sdk.ClientWelcome,
        Language.ClientHello: sdk.ClientHello,
        Language.MatchmakingGC2ClientHello: cstrike.MatchmakingClientHello,
        Language.MatchList: cstrike.MatchList,
        Language.PlayersProfile: cstrike.PlayersProfile,
        Language.ClientRequestPlayersProfile: cstrike.ClientRequestPlayersProfile,
        Language.MatchListRequestRecentUserGames: cstrike.MatchListRequestRecentUserGames,
        Language.Client2GCEconPreviewDataBlockRequest: cstrike.Client2GcEconPreviewDataBlockRequest,
        Language.Client2GCEconPreviewDataBlockResponse: cstrike.Client2GcEconPreviewDataBlockResponse,
        Language.ItemCustomizationNotification: econ.ItemCustomizationNotification,
        Language.CasketItemAdd: econ.CasketItem,
        Language.CasketItemExtract: econ.CasketItem,
        Language.CasketItemLoadContents: econ.CasketItem,
        Language.SOCreate: sdk.SingleObject,
        Language.SOUpdate: sdk.SingleObject,
        Language.SODestroy: sdk.SingleObject,
        Language.SOUpdateMultiple: sdk.MultipleObjects,
        Language.StorePurchaseInit: base.StorePurchaseInit,
        # struct messages
        Language.NameItem: struct_messages.NameItemRequest,
        Language.Delete: struct_messages.DeleteItemRequest,
    }
)
