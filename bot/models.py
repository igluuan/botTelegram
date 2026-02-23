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
    video_id: str | None = None
    marca: str | None = None
    modelo: str | None = None
    tipo: str | None = None
    nivel: str | None = None
    youtube_url: str | None = None
    subcategoria: str | None = None

    @staticmethod
    def from_row(row: aiosqlite.Row) -> "Item":
        # verifica se a coluna subcategoria existe na row (migração)
        sub = None
        if "subcategoria" in row.keys():
            sub = row["subcategoria"]

        return Item(
            id=int(row["id"]),
            category_id=int(row["category_id"]),
            title=str(row["title"]),
            type=str(row["type"]),
            telegram_message_id=row["telegram_message_id"],
            url=row["url"],
            description=row["description"],
            video_id=row["video_id"],
            marca=row["marca"],
            modelo=row["modelo"],
            tipo=row["tipo"],
            nivel=row["nivel"],
            youtube_url=row["youtube_url"],
            subcategoria=sub,
        )

