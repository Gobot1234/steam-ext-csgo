# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: gcsdk_gcmessages.proto
# plugin: python-betterproto

from dataclasses import dataclass
from typing import List

import betterproto


class GcClientLauncherType(betterproto.Enum):
    Default = 0
    PerfectWorld = 1
    SteamChina = 2


class GcConnectionStatus(betterproto.Enum):
    HaveSession = 0
    GCGoingDown = 1
    NoSession = 2
    NoSessionInLogonQueue = 3
    NoSteam = 4


@dataclass(eq=False, repr=False)
class IDOwner(betterproto.Message):
    type: int = betterproto.uint32_field(1)
    id: int = betterproto.uint64_field(2)


@dataclass(eq=False, repr=False)
class SingleObject(betterproto.Message):
    type_id: int = betterproto.int32_field(2)
    object_data: bytes = betterproto.bytes_field(3)
    version: int = betterproto.fixed64_field(4)
    owner_soid: "IDOwner" = betterproto.message_field(5)


@dataclass(eq=False, repr=False)
class MultipleObjects(betterproto.Message):
    objects_modified: List["MultipleObjectsSingleObject"] = betterproto.message_field(2)
    version: int = betterproto.fixed64_field(3)
    owner_soid: "IDOwner" = betterproto.message_field(6)


@dataclass(eq=False, repr=False)
class MultipleObjectsSingleObject(betterproto.Message):
    type_id: int = betterproto.int32_field(1)
    object_data: bytes = betterproto.bytes_field(2)


@dataclass(eq=False, repr=False)
class CacheSubscribed(betterproto.Message):
    objects: List["CacheSubscribedSubscribedType"] = betterproto.message_field(2)
    version: int = betterproto.fixed64_field(3)
    owner_soid: "IDOwner" = betterproto.message_field(4)


@dataclass(eq=False, repr=False)
class CacheSubscribedSubscribedType(betterproto.Message):
    type_id: int = betterproto.int32_field(1)
    object_data: List[bytes] = betterproto.bytes_field(2)


@dataclass(eq=False, repr=False)
class CacheUnsubscribed(betterproto.Message):
    owner_soid: "IDOwner" = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class CacheSubscriptionCheck(betterproto.Message):
    version: int = betterproto.fixed64_field(2)
    owner_soid: "IDOwner" = betterproto.message_field(3)


@dataclass(eq=False, repr=False)
class CacheSubscriptionRefresh(betterproto.Message):
    owner_soid: "IDOwner" = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class CacheVersion(betterproto.Message):
    version: int = betterproto.fixed64_field(1)


@dataclass(eq=False, repr=False)
class AccountDetails(betterproto.Message):
    valid: bool = betterproto.bool_field(1)
    account_name: str = betterproto.string_field(2)
    public_profile: bool = betterproto.bool_field(4)
    public_inventory: bool = betterproto.bool_field(5)
    vac_banned: bool = betterproto.bool_field(6)
    cyber_cafe: bool = betterproto.bool_field(7)
    school_account: bool = betterproto.bool_field(8)
    free_trial_account: bool = betterproto.bool_field(9)
    subscribed: bool = betterproto.bool_field(10)
    low_violence: bool = betterproto.bool_field(11)
    limited: bool = betterproto.bool_field(12)
    trusted: bool = betterproto.bool_field(13)
    package: int = betterproto.uint32_field(14)
    time_cached: int = betterproto.fixed32_field(15)
    account_locked: bool = betterproto.bool_field(16)
    community_banned: bool = betterproto.bool_field(17)
    trade_banned: bool = betterproto.bool_field(18)
    eligible_for_community_market: bool = betterproto.bool_field(19)


@dataclass(eq=False, repr=False)
class MultiplexMessage(betterproto.Message):
    msgtype: int = betterproto.uint32_field(1)
    payload: bytes = betterproto.bytes_field(2)
    steamids: List[int] = betterproto.fixed64_field(3)
    replytogc: bool = betterproto.bool_field(4)


@dataclass(eq=False, repr=False)
class MultiplexMessageResponse(betterproto.Message):
    msgtype: int = betterproto.uint32_field(1)


@dataclass(eq=False, repr=False)
class ToGcMsgMasterAck(betterproto.Message):
    dir_index: int = betterproto.uint32_field(1)
    gc_type: int = betterproto.uint32_field(2)


@dataclass(eq=False, repr=False)
class ToGcMsgMasterAckResponse(betterproto.Message):
    eresult: int = betterproto.int32_field(1)


@dataclass(eq=False, repr=False)
class ToGcMsgMasterStartupComplete(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class ToGcMsgRouted(betterproto.Message):
    msg_type: int = betterproto.uint32_field(1)
    sender_id: int = betterproto.fixed64_field(2)
    net_message: bytes = betterproto.bytes_field(3)
    ip: int = betterproto.uint32_field(4)


@dataclass(eq=False, repr=False)
class ToGcMsgRoutedReply(betterproto.Message):
    msg_type: int = betterproto.uint32_field(1)
    net_message: bytes = betterproto.bytes_field(2)


@dataclass(eq=False, repr=False)
class UpdateSessionIp(betterproto.Message):
    steamid: int = betterproto.fixed64_field(1)
    ip: int = betterproto.fixed32_field(2)


@dataclass(eq=False, repr=False)
class RequestSessionIp(betterproto.Message):
    steamid: int = betterproto.fixed64_field(1)


@dataclass(eq=False, repr=False)
class RequestSessionIpResponse(betterproto.Message):
    ip: int = betterproto.fixed32_field(1)


@dataclass(eq=False, repr=False)
class CacheHaveVersion(betterproto.Message):
    soid: "IDOwner" = betterproto.message_field(1)
    version: int = betterproto.fixed64_field(2)


@dataclass(eq=False, repr=False)
class ClientHello(betterproto.Message):
    version: int = betterproto.uint32_field(1)
    socache_have_versions: List["CacheHaveVersion"] = betterproto.message_field(2)
    client_session_need: int = betterproto.uint32_field(3)
    client_launcher: int = betterproto.uint32_field(4)
    partner_srcid: int = betterproto.uint32_field(5)
    partner_accountid: int = betterproto.uint32_field(6)
    partner_accountflags: int = betterproto.uint32_field(7)
    partner_accountbalance: int = betterproto.uint32_field(8)
    steam_launcher: int = betterproto.uint32_field(9)


@dataclass(eq=False, repr=False)
class ServerHello(betterproto.Message):
    version: int = betterproto.uint32_field(1)
    socache_have_versions: List["CacheHaveVersion"] = betterproto.message_field(2)
    legacy_client_session_need: int = betterproto.uint32_field(3)
    client_launcher: int = betterproto.uint32_field(4)
    legacy_steamdatagram_routing: bytes = betterproto.bytes_field(6)
    required_internal_addr: int = betterproto.uint32_field(7)
    steamdatagram_login: bytes = betterproto.bytes_field(8)


@dataclass(eq=False, repr=False)
class ClientWelcome(betterproto.Message):
    version: int = betterproto.uint32_field(1)
    game_data: bytes = betterproto.bytes_field(2)
    outofdate_subscribed_caches: List["CacheSubscribed"] = betterproto.message_field(3)
    uptodate_subscribed_caches: List["CacheSubscriptionCheck"] = betterproto.message_field(4)
    location: "ClientWelcomeLocation" = betterproto.message_field(5)
    game_data2: bytes = betterproto.bytes_field(6)
    rtime32_gc_welcome_timestamp: int = betterproto.uint32_field(7)
    currency: int = betterproto.uint32_field(8)
    balance: int = betterproto.uint32_field(9)
    balance_url: str = betterproto.string_field(10)
    txn_country_code: str = betterproto.string_field(11)


@dataclass(eq=False, repr=False)
class ClientWelcomeLocation(betterproto.Message):
    latitude: float = betterproto.float_field(1)
    longitude: float = betterproto.float_field(2)
    country: str = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class ConnectionStatus(betterproto.Message):
    status: "GcConnectionStatus" = betterproto.enum_field(1)
    client_session_need: int = betterproto.uint32_field(2)
    queue_position: int = betterproto.int32_field(3)
    queue_size: int = betterproto.int32_field(4)
    wait_seconds: int = betterproto.int32_field(5)
    estimated_wait_seconds_remaining: int = betterproto.int32_field(6)


@dataclass(eq=False, repr=False)
class PopulateItemDescriptionsRequest(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    languages: List["PopulateItemDescriptionsRequestItemDescriptionsLanguageBlock"] = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class PopulateItemDescriptionsRequestSingleItemDescription(betterproto.Message):
    gameitemid: int = betterproto.uint32_field(1)
    item_description: str = betterproto.string_field(2)
    one_per_account: bool = betterproto.bool_field(3)


@dataclass(eq=False, repr=False)
class PopulateItemDescriptionsRequestItemDescriptionsLanguageBlock(betterproto.Message):
    language: str = betterproto.string_field(1)
    descriptions: List["PopulateItemDescriptionsRequestSingleItemDescription"] = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class GetContributorsRequest(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    gameitemid: int = betterproto.uint32_field(2)


@dataclass(eq=False, repr=False)
class GetContributorsResponse(betterproto.Message):
    contributors: List[int] = betterproto.fixed64_field(1)


@dataclass(eq=False, repr=False)
class SetItemPaymentRulesRequest(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    gameitemid: int = betterproto.uint32_field(2)
    associated_workshop_files: List["SetItemPaymentRulesRequestWorkshopItemPaymentRule"] = betterproto.message_field(3)
    partner_accounts: List["SetItemPaymentRulesRequestPartnerItemPaymentRule"] = betterproto.message_field(4)
    validate_only: bool = betterproto.bool_field(5)
    make_workshop_files_subscribable: bool = betterproto.bool_field(6)
    associated_workshop_file_for_direct_payments: "SetItemPaymentRulesRequestWorkshopDirectPaymentRule" = (
        betterproto.message_field(7)
    )


@dataclass(eq=False, repr=False)
class SetItemPaymentRulesRequestWorkshopItemPaymentRule(betterproto.Message):
    workshop_file_id: int = betterproto.uint64_field(1)
    revenue_percentage: float = betterproto.float_field(2)
    rule_description: str = betterproto.string_field(3)
    rule_type: int = betterproto.uint32_field(4)


@dataclass(eq=False, repr=False)
class SetItemPaymentRulesRequestWorkshopDirectPaymentRule(betterproto.Message):
    workshop_file_id: int = betterproto.uint64_field(1)
    rule_description: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class SetItemPaymentRulesRequestPartnerItemPaymentRule(betterproto.Message):
    account_id: int = betterproto.uint32_field(1)
    revenue_percentage: float = betterproto.float_field(2)
    rule_description: str = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class SetItemPaymentRulesResponse(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class CGameServersAggregationQueryRequest(betterproto.Message):
    filter: str = betterproto.string_field(1)
    group_fields: List[str] = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class CGameServersAggregationQueryResponse(betterproto.Message):
    groups: List["CGameServersAggregationQueryResponseGroup"] = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class CGameServersAggregationQueryResponseGroup(betterproto.Message):
    group_values: List[str] = betterproto.string_field(1)
    servers_empty: int = betterproto.uint32_field(2)
    servers_full: int = betterproto.uint32_field(3)
    servers_total: int = betterproto.uint32_field(4)
    players_humans: int = betterproto.uint32_field(5)
    players_bots: int = betterproto.uint32_field(6)
    player_capacity: int = betterproto.uint32_field(7)


@dataclass(eq=False, repr=False)
class AddSpecialPaymentRequest(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    gameitemid: int = betterproto.uint32_field(2)
    date: str = betterproto.string_field(3)
    payment_us_usd: int = betterproto.uint64_field(4)
    payment_row_usd: int = betterproto.uint64_field(5)


@dataclass(eq=False, repr=False)
class AddSpecialPaymentResponse(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class SetRichPresenceLocalizationRequest(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    languages: List["SetRichPresenceLocalizationRequestLanguageSection"] = betterproto.message_field(2)
    steamid: int = betterproto.uint64_field(3)


@dataclass(eq=False, repr=False)
class SetRichPresenceLocalizationRequestToken(betterproto.Message):
    token: str = betterproto.string_field(1)
    value: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class SetRichPresenceLocalizationRequestLanguageSection(betterproto.Message):
    language: str = betterproto.string_field(1)
    tokens: List["SetRichPresenceLocalizationRequestToken"] = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class SetRichPresenceLocalizationResponse(betterproto.Message):
    pass