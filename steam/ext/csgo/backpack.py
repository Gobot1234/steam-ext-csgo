from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from typing_extensions import Self, TypeAlias

from ... import utils
from ...protobufs import GCMsgProto
from ...trade import BaseInventory, Item
from .enums import ItemCustomizationNotification as ItemCustomizationNotificationEnum, Language
from .models import Sticker
from .protobufs.base import Item as ProtoItem, ItemAttribute, ItemEquipped
from .protobufs.econ import ItemCustomizationNotification as ItemCustomizationNotificationProto

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "BackpackItem",
    "Backpack",
)


class Paint:
    index: float
    seed: float
    wear: float

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} index={self.index} seed={self.seed} wear={self.wear}>"


class BaseItem:
    __slots__ = (
        "position",
        "paint",
        "tradable_after",
        "stickers",
    ) + tuple(ProtoItem.__annotations__)

    position: int
    paint: Paint
    tradeable_after: datetime
    stickers: list[Sticker]
    id: int
    account_id: int
    inventory: int
    def_index: int
    quantity: int
    level: int
    quality: int
    flags: int
    origin: int
    custom_name: str
    custom_desc: str
    attribute: list[ItemAttribute]
    interior_item: Item
    in_use: bool
    style: int
    original_id: int
    equipped_state: list[ItemEquipped]
    rarity: int


class CasketItem(BaseItem):
    casket_id: int


class BaseInspectedItem:
    id: int
    def_index: int
    paint: Paint
    position: int
    rarity: int
    quality: int
    kill_eater_score_type: int
    kill_eater_value: int
    custom_name: str
    stickers: list[Sticker]
    inventory: int
    origin: int
    quest_id: int
    drop_reason: int
    music_index: int
    ent_index: int


class InspectedItem(BaseItem, Item):
    ...


class BackpackItem(Item, BaseItem):
    """A class to represent an item from the client's backpack."""

    __slots__ = ("_state",)
    _state: GCState

    REPR_ATTRS = (*Item.REPR_ATTRS, "position")

    @classmethod
    def from_item(cls, item: Item) -> Self:
        self = copy(item)
        self.__class__ = cls
        return self

    async def rename_to(self, name: str, tag: BackpackItem) -> None:
        ...

    async def delete(self) -> None:
        ...

    async def add_to(self, casket: Casket) -> None:
        ...

    async def remove_from(self, casket: Casket) -> None:
        ...

    async def inspect(self) -> InspectedItem:
        basic = await self._state.client.inspect_item(url=self.inspect_url)
        return utils.update_class(self, basic)  # type: ignore


class Casket(BackpackItem):
    contained_item_count: int

    async def contents(self) -> list[CasketItem]:
        """This casket's contents"""
        if not self.contained_item_count:
            return []

        contained_items = [item for item in self._state.casket_items.values() if item.casket_id == self.id]
        if len(contained_items) == self.contained_item_count:
            return contained_items

        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemLoadContents, casket_item_id=self.id, item_item_id=self.id)
        )

        notification: ItemCustomizationNotificationProto = await self._state.client.wait_for(  # type: ignore
            "item_customization_notification",
            check=lambda n: n.item_id[0] == self.id and n.request == ItemCustomizationNotificationEnum.CasketContents,
            timeout=30,
        )

        contained_items = []
        for item_id in notification.item_id[1:]:
            while True:
                try:
                    contained_items.append(self._state.casket_items[item_id])
                except KeyError:  # not been added by SOCreate yet
                    await asyncio.sleep(0)  # yield back to the event loop to let the parser add this
                else:
                    break
        return contained_items  # type: ignore


Backpack: TypeAlias = BaseInventory[BackpackItem]
"""A class to represent the client's backpack."""
