from __future__ import annotations

from dataclasses import dataclass

from bot.ui.formatters import build_item_body, item_line, items_overview, truncate_text


@dataclass
class DummyItem:
    type: str
    title: str
    description: str | None = None


def test_truncate_text_short() -> None:
    assert truncate_text("abc", limit=60) == "abc"


def test_truncate_text_long() -> None:
    text = "a" * 100
    result = truncate_text(text, limit=60)
    assert result.endswith("…")
    assert len(result) <= 60


def test_truncate_text_normalizes_spaces() -> None:
    assert truncate_text("  a   b  c ", limit=60) == "a b c"


def test_item_line_file() -> None:
    item = DummyItem(type="file", title="Manual", description=None)
    assert item_line(item).startswith("📎 ")


def test_item_line_link() -> None:
    item = DummyItem(type="link", title="Site", description=None)
    assert item_line(item).startswith("🔗 ")


def test_item_line_with_description() -> None:
    item = DummyItem(type="link", title="Site", description="   desc   longa   ")
    line = item_line(item)
    assert "—" in line
    assert "desc longa" in line


def test_item_line_no_description() -> None:
    item = DummyItem(type="link", title="Site", description="  ")
    assert item_line(item) == "🔗 Site"


def test_build_item_body_link() -> None:
    item = DummyItem(type="link", title="Site", description="Desc")
    body = build_item_body(item)
    assert "<b>Site</b>" in body
    assert "Desc" in body


def test_build_item_body_no_description() -> None:
    item = DummyItem(type="file", title="Manual", description=None)
    body = build_item_body(item)
    assert "<b>Manual</b>" in body
    assert "\n\n" not in body


def test_items_overview_empty() -> None:
    assert items_overview([]) == []
