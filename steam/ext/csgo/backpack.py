from __future__ import annotations

import asyncio
from abc import ABCMeta
from dataclasses import dataclass
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from typing_extensions import Literal, Self, TypeAlias

from ... import utils
from ..._const import DOCS_BUILDING
from ...protobufs import GCMsg, GCMsgProto
from ...trade import BaseInventory, Item
from .enums import (
    ItemCustomizationNotification as ItemCustomizationNotificationEnum,
    ItemFlags,
    ItemOrigin,
    ItemQuality,
    Language,
)
from .protobufs.base import Item as ProtoItem, ItemAttribute, ItemEquipped
from .protobufs.econ import ItemCustomizationNotification as ItemCustomizationNotificationProto

if TYPE_CHECKING:
    from .state import GCState

__all__ = (
    "Sticker",
    "Paint",
    "BaseItem",
    "CasketItem",
    "BaseInspectedItem",
    "InspectedItem",
    "BackpackItem",
    "Casket",
    "Backpack",
)


class Sticker:
    __slots__ = ("slot", "id", "wear", "scale", "rotation", "tint_id")

    def __init__(
        self,
        slot: Literal[0, 1, 2, 3, 4],
        id: int,
        wear: float | None = None,
        scale: float | None = None,
        rotation: float | None = None,
        tint_id: float | None = None,
    ):
        self.slot = slot
        """The sticker's slot."""
        self.id = id
        """The sticker's ID."""
        self.wear = wear
        """The sticker's wear."""
        self.scale = scale
        """The sticker's scale."""
        self.rotation = rotation
        """The sticker's rotation."""
        self.tint_id = tint_id
        """The sticker's tint_id."""

    _decodeable_attrs = (
        "wear",
        "scale",
        "rotation",
    )


class Paint:
    """Represents the pain on an item."""

    def __init__(
        self,
        index: float = 0.0,
        seed: float = 0.0,
        wear: float = 0.0,
    ) -> None:
        self.index = index
        """The paint's index."""
        self.seed = seed
        """The paint's seed."""
        self.wear = wear
        """The paint's wear."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} index={self.index} seed={self.seed} wear={self.wear}>"


class BaseItem(metaclass=ABCMeta):
    """Represents an item received from the Game Coordinator."""

    __slots__ = (
        "position",
        "paint",
        "tradable_after",
        "stickers",
    ) + tuple(ProtoItem.__annotations__)

    position: int
    """The item's position."""
    paint: Paint
    """The item's paint."""
    tradeable_after: datetime
    """The time the item's tradeable after."""
    stickers: list[Sticker]
    """The item's stickers."""
    id: int
    """The item's asset ID."""
    account_id: int
    """The item's owner's 32-bit account ID."""
    inventory: int
    """Flags that aren't useful."""
    def_index: int
    """The item's def-index useful for its SKU."""
    quantity: int
    """The item's quantity."""
    level: int
    """The item's level."""
    quality: ItemQuality
    """The item's quality."""
    flags: ItemFlags
    """The item's flags."""
    origin: ItemOrigin
    """The item's origin."""
    custom_name: str
    """The item's custom name."""
    custom_description: str
    """The item's custom description."""
    attribute: list[ItemAttribute]
    """The item's attribute."""
    interior_item: ProtoItem
    """The item's interior item."""
    in_use: bool
    """Whether the item's in use."""
    style: int
    """The item's style."""
    original_id: int
    """The item's original ID."""
    equipped_state: list[ItemEquipped]
    """The item's equipped state."""
    rarity: int
    """The item's rarity."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} position={self.position}>"


class CasketItem(BaseItem):
    """Represents an item in a :class:`Casket`."""

    __slots__ = ("casket_id",)
    casket_id: int
    """The asset ID of the casket this item is from."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} casket_id={self.casket_id}>"


@dataclass(repr=False)
class BaseInspectedItem(metaclass=ABCMeta):
    """Represents an item received after inspecting an item."""

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
    """The item's asset ID."""
    def_index: int
    """The item's asset ID."""
    paint: Paint
    """The item's paint."""
    rarity: int
    """The item's rarity."""
    quality: ItemQuality
    """The item's quality."""
    kill_eater_score_type: int | None
    """The item's kill eater score type."""
    kill_eater_value: int | None
    """The item's kill eater value."""
    custom_name: str
    """The item's custom name."""
    stickers: list[Sticker]
    """The item's stickers."""
    inventory: int
    """The item's inventory."""
    origin: ItemOrigin
    """The item's origin."""
    quest_id: int
    """The item's quest id."""
    drop_reason: int
    """The item's drop reason."""
    music_index: int
    """The item's music index."""
    ent_index: int
    """The item's ent index."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


if TYPE_CHECKING:  # avoid mro issues but keep types

    class InspectedItem(Item, BaseInspectedItem):
        __slots__ = ()

    class BaseBackpackItem(Item, BaseItem):
        __slots__ = ()


# elif DOCS_BUILDING:  # needed to keep docstrings

#     InspectedItem = type("InspectedItem", (Item,), BaseInspectedItem.__dict__ | {"__slots__": ("__dict__",)})
#     BaseBackpackItem = type("BaseBackpackItem", (Item,), BaseItem.__dict__ | {"__slots__": ("__dict__",)})

else:

    @BaseInspectedItem.register
    class InspectedItem(Item):
        __slots__ = BaseInspectedItem.__slots__

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

    async def rename_to(self, name: str, tag: BackpackItem) -> None:
        """Rename this item to ``name`` with ``tag``.

        Parameters
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
        This mutates ``self`` in a way that attributes available on the :class:`InspectedItem` are available on
        ``self``.
        """
        inspect_url = self.inspect_url
        if inspect_url is None:
            raise ValueError("Cannot inspect this item")
        basic = await self._state.client.inspect_item(url=inspect_url)
        return utils.update_class(self, basic)  # type: ignore


class Casket(BackpackItem):
    """Represents a casket/storage container."""

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
        self.contained_item_count += 1

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
        self.contained_item_count -= 1

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

        future: asyncio.Future[GCMsgProto[ItemCustomizationNotificationProto]] = self._state.gc_wait_for(
            Language.ItemCustomizationNotification,
            check=lambda msg: (
                msg.body.request == ItemCustomizationNotificationEnum.CasketContents and msg.body.item_id[0] == self.id
            ),
        )
        await self._state.ws.send_gc_message(
            GCMsgProto(Language.CasketItemLoadContents, casket_item_id=self.id, item_item_id=self.id)
        )

        notification = await future

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
        Caskets require names to work so if you've purchased one and forgot to activate it, use this method activate
        it.
        """
        # TODO consider this might need a lock to make sure that we can actually update the correct item
        item = _FakeNameTag()
        item.owner = self._state.client.user
        await super().rename_to(name, item)


class _FakeNameTag(BackpackItem):
    id = 0
    __slots__ = ()

    def __init__(self, *_, **__):
        pass


class Backpack(BaseInventory[BackpackItem]):
    """A class to represent the client's backpack."""

    @property
    def caskets(self) -> Sequence[Casket]:
        """The caskets in this backpack."""
        return [item for item in self if isinstance(item, Casket)]
