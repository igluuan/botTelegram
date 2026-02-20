from __future__ import annotations

from pathlib import Path

import pytest

from bot.db.connection import connect


@pytest.mark.asyncio
async def test_connect_creates_file(tmp_path: Path) -> None:
    db = tmp_path / "created.db"
    assert db.exists() is False
    async with connect(str(db)):
        pass
    assert db.exists() is True


@pytest.mark.asyncio
async def test_connect_foreign_keys_on(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    async with connect(db) as conn:
        cur = await conn.execute("PRAGMA foreign_keys")
        row = await cur.fetchone()
        assert row[0] == 1


@pytest.mark.asyncio
async def test_connect_row_factory(tmp_path: Path) -> None:
    db = str(tmp_path / "test.db")
    async with connect(db) as conn:
        cur = await conn.execute("SELECT 1 AS a")
        row = await cur.fetchone()
        assert row["a"] == 1
