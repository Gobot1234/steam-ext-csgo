from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ... import utils
from ...trade import BaseInventory, Item
from .models import Sticker
from .protobufs.base_gcmessages import CsoEconItem, CsoEconItemAttribute, CsoEconItemEquipped

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "BackPackItem",
    "BackPack",
)


class BackPackItem(Item):
    """A class to represent an item from the client's backpack."""

    __slots__ = (
        "position",
        "casket_id",
        "paint_index",
        "paint_seed",
        "paint_wear",
        "tradable_after",
        "stickers",
        "casket_contained_item_count",
    ) + tuple(CsoEconItem.__annotations__)

    REPR_ATTRS = (*Item.REPR_ATTRS, "position")

    position: int
    casket_id: int
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
    attribute: list[CsoEconItemAttribute]
    interior_item: CsoEconItem
    in_use: bool
    style: int
    original_id: int
    equipped_state: list[CsoEconItemEquipped]
    rarity: int

    def __init__(self, item: Item, *, _state: GCState | None = None):  # noqa
        utils.update_class(item, self)
        self._state = _state


class BackPack(BaseInventory[BackPackItem]):
    """A class to represent the client's backpack."""

    def __init__(self, inventory: Inventory):  # noqa
        utils.update_class(inventory, self)
        self.items = [BackPackItem(item, _state=self._state) for item in inventory.items]  # type: ignore

    async def update(self) -> None:
        await super().update()
        self.items = [BackPackItem(item, _state=self._state) for item in self.items]  # type: ignore
