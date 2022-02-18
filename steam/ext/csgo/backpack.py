from __future__ import annotations

import asyncio
from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from typing_extensions import Self, TypeAlias

from ... import utils
from ...protobufs import GCMsg, GCMsgProto
from ...trade import BaseInventory, Item
from .enums import (
    ItemCustomizationNotification as ItemCustomizationNotificationEnum,
    ItemFlags,
    ItemOrigin,
    ItemQuality,
    Language,
)
from .models import Sticker
from .protobufs.base import Item as ProtoItem, ItemAttribute, ItemEquipped
from .protobufs.econ import ItemCustomizationNotification as ItemCustomizationNotificationProto

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "Paint",
    "BaseItem",
    "CasketItem",
    "BaseInspectedItem",
    "InspectedItem",
    "BackpackItem",
    "Casket",
    "Backpack",
)


class Paint:
    index: float
    seed: float
    wear: float

    def __init__(
        self,
        index: float = 0.0,
        seed: float = 0.0,
        wear: float = 0.0,
    ) -> None:
        self.index = index
        self.seed = seed
        self.wear = wear

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} index={self.index} seed={self.seed} wear={self.wear}>"


class BaseItem(metaclass=ABCMeta):
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
    quality: ItemQuality
    flags: ItemFlags
    origin: ItemOrigin
    custom_name: str
    custom_description: str
    attribute: list[ItemAttribute]
    interior_item: ProtoItem
    in_use: bool
    style: int
    original_id: int
    equipped_state: list[ItemEquipped]
    rarity: int

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} position={self.position}>"


class CasketItem(BaseItem):
    __slots__ = ("casket_id",)
    casket_id: int

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} casket_id={self.casket_id}>"


@dataclass(repr=False)
class BaseInspectedItem:
    __slots__ = (
        "id",
        "def_index",
        "paint",
        "rarity",
        "quality",
        "kill_eater_score_type",
        "kill_eater_value",
        "custom_name",
        "stickers",
        "inventory",
        "origin",
        "quest_id",
        "drop_reason",
        "music_index",
        "ent_index",
    )

    id: int
    def_index: int
    paint: Paint
    rarity: int
    quality: ItemQuality
    kill_eater_score_type: int | None
    kill_eater_value: int | None
    custom_name: str
    stickers: list[Sticker]
    inventory: int
    origin: ItemOrigin
    quest_id: int
    drop_reason: int
    music_index: int
    ent_index: int

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


if TYPE_CHECKING:

    class InspectedItem(Item, BaseInspectedItem):
        __slots__ = ()


else:

    class InspectedItem(Item):
        __slots__ = BaseInspectedItem.__slots__


if TYPE_CHECKING:  # avoid mro issues but keep types

    class BaseBackpackItem(Item, BaseItem):
        __slots__ = ()


else:

    @BaseItem.register
    class BaseBackpackItem(Item):
        __slots__ = BaseItem.__slots__


def has_to_be_in_our_inventory(func):
    func.__doc__ += """
    Note
    ----
    For this method to work the item has to be in the client's backpack.
    """
    return func


class BackpackItem(BaseBackpackItem):
    """A class to represent an item which can interact with the GC."""

    __slots__ = ()
    _state: GCState

    REPR_ATTRS = (*Item.REPR_ATTRS, "position")

    @classmethod
    def from_item(cls, item: Item) -> Self:
        """A "type safe" way to cast ``item`` to a :class:`BackpackItem`."""
        return utils.update_class(item, cls())  # type: ignore

    @has_to_be_in_our_inventory
    async def rename_to(self, name: str, tag: BackpackItem) -> None:
        """Rename this item to ``name`` with ``tag``.

        Paramaters
        ----------
        name
            The desired name.
        tag
            The tag to consume for this request.
        """
        future = self._state.gc_wait_for(
            Language.ItemCustomizationNotification,
            check=lambda msg: (
                msg.body.request == ItemCustomizationNotificationEnum.NameItem and msg.body.item_id[0] == self.id
            ),
        )
        await self._state.ws.send_gc_message(GCMsg(Language.NameItem, name_tag_id=tag.id, item_id=self.id, name=name))
        await future

    @has_to_be_in_our_inventory
    async def delete(self) -> None:
        """Delete this item."""
        await self._state.ws.send_gc_message(GCMsg(Language.Delete, item_id=self.id))

    @property
    def inspect_url(self) -> str | None:
        """The inspect url of item if it's inspectable."""
        try:
            for action in self.actions:
                if "inspect" in action["name"].lower():
                    return (
                        action["link"]
                        .replace("%owner_steamid%", str(self.owner.id64))
                        .replace("%assetid%", str(self.id))
                    )

        except (ValueError, KeyError):
            return None

    async def inspect(self) -> InspectedItem:
        """Inspect this item.

        Note
        ----
        This mutates ``self`` in a way that attributes avaliable on the :class:`InspectedItem` are available on
        ``self``.
        """
        inspect_url = self.inspect_url
        if inspect_url is None:
            raise ValueError("Cannot inspect this item")
        basic = await self._state.client.inspect_item(url=inspect_url)
        return utils.update_class(self, basic)  # type: ignore


class Casket(BackpackItem):
    __slots__ = ("contained_item_count",)
    REPR_ATTRS = (*BackpackItem.REPR_ATTRS, "contained_item_count")

    contained_item_count: int
    """The number of items contained in the casket."""

    async def add(self, item: BackpackItem) -> None:
        """Add an item to this casket.

        Parameters
        ----------
        item
            The item to add.
        """
        future = self._state.gc_wait_for(
            Language.ItemCustomizationNotification,
            lambda msg: msg.body.request == ItemCustomizationNotificationEnum.CasketAdded
            and msg.body.item_id[0] == self.id,
        )
        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemAdd, casket_item_id=self.id, item_item_id=item.id)
        )
        await future

    async def remove(self, item: CasketItem) -> BackpackItem:
        """Remove an item from this casket.

        Parameters
        ----------
        item
            The item to remove.

        Returns
        -------
        The item as a :class:`BackpackItem` in your inventory.
        """
        if item.casket_id != self.id:
            raise ValueError("item is not in this casket")

        future = self._state.gc_wait_for(
            Language.ItemCustomizationNotification,
            lambda msg: msg.body.request == ItemCustomizationNotificationEnum.CasketRemoved
            and msg.body.item_id[0] == self.id,
        )
        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemExtract, casket_item_id=self.id, item_item_id=item.id)
        )
        await future

        backpack_item = utils.get(self._state.backpack, asset_id=item.id)
        while backpack_item is None:
            backpack_item = utils.get(self._state.backpack, asset_id=item.id)
            await asyncio.sleep(0)

        return backpack_item

    async def contents(self) -> list[CasketItem]:
        """This casket's contents"""
        if not self.contained_item_count:
            return []

        contained_items = [item for item in self._state.casket_items.values() if item.casket_id == self.id]
        if len(contained_items) == self.contained_item_count:
            return contained_items

        future = self._state.gc_wait_for(
            Language.ItemCustomizationNotification,
            check=lambda msg: (
                msg.body.request == ItemCustomizationNotificationEnum.CasketContents and msg.body.item_id[0] == self.id
            ),
        )
        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemLoadContents, casket_item_id=self.id, item_item_id=self.id)
        )

        notification: GCMsgProto[ItemCustomizationNotificationProto] = await future  # type: ignore

        items = []
        for casket_item_id in notification.body.item_id[1:]:
            while True:
                try:
                    casket_item = self._state.casket_items[casket_item_id]
                except KeyError:
                    await asyncio.sleep(0)
                else:
                    items.append(casket_item)
                    break

        return items

    async def rename_to(self, name: str) -> None:
        """Rename this casket to ``name``.

        Parameters
        ----------
        name
            The name to rename the casket to.

        Note
        ----
        Caskets require names to work so if you've purchased one and forgot to activate it, use this method activate it.
        """
        # TODO consider this might need a lock to make sure that we can actually update the correct item
        item = _FakeNameTag()
        item.owner = self._state.client.user
        await super().rename_to(name, item)


class _FakeNameTag(BackpackItem):
    id = 0

    def __init__(self, *_, **__):
        pass


Backpack: TypeAlias = BaseInventory[BackpackItem]
"""A class to represent the client's backpack."""
