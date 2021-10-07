from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ... import utils
from ...abc import SteamID
from ...protobufs import GCMsgProto
from ...trade import BaseInventory, Inventory, Item
from .enums import ItemCustomizationNotification, Language
from .models import Sticker
from .protobufs.base import Item as ProtoItem, ItemAttribute, ItemEquipped

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "BackpackItem",
    "Backpack",
)


class BackpackItem(Item):
    """A class to represent an item from the client's backpack."""

    __slots__ = (
        "_state",
        "position",
        "casket_id",
        "paint_index",
        "paint_seed",
        "paint_wear",
        "tradable_after",
        "stickers",
        "casket_contained_item_count",
    ) + tuple(ProtoItem.__annotations__)

    REPR_ATTRS = (*Item.REPR_ATTRS, "position")

    position: int
    casket_id: int | None
    paint_index: float
    paint_seed: float
    paint_wear: float
    tradable_after: datetime
    stickers: list[Sticker]
    casket_contained_item_count: int
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

    def __init__(self, item: Item, *, _state: GCState | None = None):  # noqa
        utils.update_class(item, self)
        self._state = _state
        self.casket_id = None

    def __hash__(self):
        return hash(self.id)

    async def rename_to(self, name: str, tag: BackpackItem):
        ...

    async def delete(self):
        ...

    async def add_to(self, casket: BackpackItem):
        ...

    async def remove_from(self, casket: BackpackItem):
        ...

    async def contents(self) -> list[BackpackItem]:
        if not self.casket_contained_item_count:
            return []

        contained_items = [item for item in self._state.casket_items if item.casket_id == self.id]
        if len(contained_items) == self.casket_contained_item_count:
            return contained_items

        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemLoadContents, casket_item_id=self.id, item_item_id=self.id)
        )
        await self._state.client.wait_for(  # type: ignore
            "item_customization_notification",
            check=lambda n: n.item_id[0] == self.id and n.request == ItemCustomizationNotification.CasketContents,
            timeout=30,
        )
        return [item for item in self._state.casket_items if item.casket_id == self.id]

    async def inspect(
        self,
        owner: SteamID,
        d: str,
    ):
        ...


class Backpack(BaseInventory[BackpackItem]):
    """A class to represent the client's backpack."""

    __slots__ = ()

    def __init__(self, inventory: Inventory):  # noqa
        utils.update_class(inventory, self)
        self.items = [BackpackItem(item, _state=self._state) for item in inventory.items]  # type: ignore

    async def update(self) -> None:
        await super().update()
        self.items = [BackpackItem(item, _state=self._state) for item in self.items]  # type: ignore
