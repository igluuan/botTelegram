from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import aiosqlite


ItemType = Literal["file", "link"]


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str
    emoji: str

    @staticmethod
    def from_row(row: aiosqlite.Row) -> "Category":
        return Category(id=int(row["id"]), name=str(row["name"]), emoji=str(row["emoji"]))


@dataclass(frozen=True, slots=True)
class Item:
    id: int
    category_id: int
    title: str
    type: ItemType
    telegram_message_id: int | None
    url: str | None
    description: str | None

    @staticmethod
    def from_row(row: aiosqlite.Row) -> "Item":
        return Item(
            id=int(row["id"]),
            category_id=int(row["category_id"]),
            title=str(row["title"]),
            type=str(row["type"]),
            telegram_message_id=row["telegram_message_id"],
            url=row["url"],
            description=row["description"],
        )

