from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING
 
from ... import utils
from ...utils import make_id64
from ...protobufs import GCMsgProto
from ...trade import BaseInventory, Inventory, Item
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

    async def rename_to(self, name: str, tag: BackpackItem):
        ...

    async def delete(self):
        ...

    async def add_to(self, casket: BackpackItem):
        ...

    async def remove_from(self, casket: BackpackItem):
        ...

    async def contents(self) -> list[ProtoItem]:
        if not self.casket_contained_item_count:
            return []

        contained_items = [item for item in self._state.casket_items.values() if item.casket_id == self.id]
        if len(contained_items) == self.casket_contained_item_count:
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
        return contained_items

    @property
    def inspect_url(self) -> str | None:
        """
        Get inspect url of item if it `inspectable`
        :return: Inspect url or None
        """
        try:
            for action in self.actions:
                if "inspect" in action["name"].lower():
                    return (action["link"]
                            .replace('%owner_steamid%', str(make_id64(self.account_id)))
                            .replace('%assetid%', str(self.id)))

        except (ValueError, KeyError):
            return None


class Backpack(BaseInventory[BackpackItem]):
    """A class to represent the client's backpack."""

    __slots__ = ()

    def __init__(self, inventory: Inventory):  # noqa
        utils.update_class(inventory, self)
        self.items = [BackpackItem(item, _state=self._state) for item in inventory.items]  # type: ignore

    async def update(self) -> None:
        await super().update()
        self.items = [BackpackItem(item, _state=self._state) for item in self.items]  # type: ignore
