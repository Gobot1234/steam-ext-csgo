# -*- coding: utf-8 -*-

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Optional, TYPE_CHECKING, TypeVar

from steam import Item, Inventory
from steam.enums import _is_descriptor

from .models import Sticker
from .protobufs.base_gcmessages import CsoEconItem

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "BackPackItem",
    "BackPack",
)

BPI = TypeVar("BPI", bound="BackPackItem")


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

    position: int
    casket_id: int
    paint_index: float
    paint_seed: float
    paint_wear: float
    tradable_after: datetime
    stickers: list[Sticker]
    casket_contained_item_count: int

    def __init__(self, item: Item, state: Optional[GCState] = None):  # noqa
        for name, attr in inspect.getmembers(item, predicate=lambda attr: not _is_descriptor(attr)):
            if not (name.startswith("__") and name.endswith("__")):
                try:
                    setattr(self, name, attr)
                except (AttributeError, TypeError):
                    pass

    def __repr__(self) -> str:
        item_repr = super().__repr__()[6:-1]
        resolved = [item_repr]
        attrs = ("position",)
        resolved.extend(f"{attr}={getattr(self, attr, None)!r}" for attr in attrs)
        return f"<BackPackItem {' '.join(resolved)}>"


if TYPE_CHECKING:

    class BackPackItem(BackPackItem, CsoEconItem):
        # We don't want the extra bloat of betterproto.Message at runtime but we do want its fields
        ...


class BackPack(Inventory[BPI]):
    """A class to represent the client's backpack."""

    items: list[BPI]

    def __init__(self, inventory: Inventory):  # noqa
        for name, attr in inspect.getmembers(inventory, lambda attr: not _is_descriptor(attr)):
            if not (name.startswith("__") and name.endswith("__")):
                try:
                    setattr(self, name, attr)
                except (AttributeError, TypeError):
                    pass
        self.items = [BackPackItem(item, self._state) for item in inventory.items]
