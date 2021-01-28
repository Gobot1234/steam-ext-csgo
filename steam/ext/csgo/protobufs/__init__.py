from steam.protobufs import PROTOBUFS

from ..enums import Language
from . import base_gcmessages as cso_messages, cstrike15_gcmessages, gcsdk_gcmessages as so_messages

PROTOBUFS.update(
    {
        Language.ClientConnectionStatus: so_messages.CMsgConnectionStatus,
        Language.ClientHelloPartner: so_messages.CMsgClientHello,
        Language.ClientHelloPW: so_messages.CMsgClientHello,
        Language.ClientHelloR2: so_messages.CMsgClientHello,
        Language.ClientHelloR3: so_messages.CMsgClientHello,
        Language.ClientHelloR4: so_messages.CMsgClientHello,
        Language.ClientRequestWatchInfoFriends2: cstrike15_gcmessages.CMsgGccStrike15V2ClientRequestWatchInfoFriends,
        Language.ClientGlobalStats: cstrike15_gcmessages.GlobalStatistics,
    }
)
