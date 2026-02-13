from __future__ import annotations

import pytest

from bot import database


@pytest.mark.asyncio
async def test_init_and_category_crud(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_id = await database.create_category(name="Docs", emoji="📁", db_path=temp_db_path)
    cats = await database.list_categories(db_path=temp_db_path)
    assert [c.id for c in cats] == [cat_id]
    assert cats[0].name == "Docs"
    assert cats[0].emoji == "📁"
    removed = await database.delete_category(category_id=cat_id, db_path=temp_db_path)
    assert removed is True
    cats2 = await database.list_categories(db_path=temp_db_path)
    assert cats2 == []


@pytest.mark.asyncio
async def test_item_crud_and_search(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_id = await database.create_category(name="Links", emoji="🔗", db_path=temp_db_path)
    link_id = await database.create_link_item(
        category_id=cat_id,
        title="Site Oficial",
        url="https://example.com",
        description="desc",
        db_path=temp_db_path,
    )
    file_id = await database.create_file_item(
        category_id=cat_id,
        title="Manual",
        telegram_message_id=123,
        description=None,
        db_path=temp_db_path,
    )
    items = await database.list_items_by_category(category_id=cat_id, db_path=temp_db_path)
    assert {it.id for it in items} == {link_id, file_id}
    res = await database.search_items(term="Manual", db_path=temp_db_path)
    assert len(res) == 1
    assert res[0].id == file_id
    removed = await database.delete_item(item_id=link_id, db_path=temp_db_path)
    assert removed is True


@pytest.mark.asyncio
async def test_category_counts_and_paging(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_a = await database.create_category(name="Alpha", emoji="🅰️", db_path=temp_db_path)
    cat_b = await database.create_category(name="Beta", emoji="🅱️", db_path=temp_db_path)
    cat_c = await database.create_category(name="Gamma", emoji="🌀", db_path=temp_db_path)
    await database.create_link_item(
        category_id=cat_a,
        title="Alpha Link",
        url="https://a.example.com",
        description=None,
        db_path=temp_db_path,
    )
    await database.create_file_item(
        category_id=cat_b,
        title="Beta File",
        telegram_message_id=10,
        description=None,
        db_path=temp_db_path,
    )
    counts = await database.list_categories_with_counts(db_path=temp_db_path)
    counts_map = {c.id: count for c, count in counts}
    assert counts_map[cat_a] == 1
    assert counts_map[cat_b] == 1
    assert counts_map[cat_c] == 0
    paged_1 = await database.list_categories_with_counts_paged(
        page=1, limit=2, db_path=temp_db_path
    )
    paged_2 = await database.list_categories_with_counts_paged(
        page=2, limit=2, db_path=temp_db_path
    )
    assert len(paged_1) == 2
    assert len(paged_2) == 1


@pytest.mark.asyncio
async def test_search_pagination_and_category_search(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_docs = await database.create_category(name="Docs", emoji="📄", db_path=temp_db_path)
    cat_links = await database.create_category(name="Links", emoji="🔗", db_path=temp_db_path)
    ids_docs = []
    for i in range(3):
        ids_docs.append(
            await database.create_file_item(
                category_id=cat_docs,
                title=f"Doc {i}",
                telegram_message_id=100 + i,
                description=None,
                db_path=temp_db_path,
            )
        )
    ids_links = []
    for i in range(2):
        ids_links.append(
            await database.create_link_item(
                category_id=cat_links,
                title=f"Doc Link {i}",
                url=f"https://example.com/{i}",
                description=None,
                db_path=temp_db_path,
            )
        )
    total = await database.count_search_items(term="Doc", db_path=temp_db_path)
    assert total == 5
    page_1 = await database.search_items(term="Doc", page=1, limit=2, db_path=temp_db_path)
    page_3 = await database.search_items(term="Doc", page=3, limit=2, db_path=temp_db_path)
    assert len(page_1) == 2
    assert len(page_3) == 1
    by_cat_total = await database.count_search_items_by_category(
        category_id=cat_docs, term="Doc", db_path=temp_db_path
    )
    assert by_cat_total == 3
    by_cat = await database.search_items_by_category(
        category_id=cat_docs, term="Doc", page=1, limit=10, db_path=temp_db_path
    )
    assert {item.id for item in by_cat} == set(ids_docs)


@pytest.mark.asyncio
async def test_favorites_and_history(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_id = await database.create_category(name="Favoritos", emoji="⭐", db_path=temp_db_path)
    item_a = await database.create_link_item(
        category_id=cat_id,
        title="Item A",
        url="https://a.example.com",
        description=None,
        db_path=temp_db_path,
    )
    item_b = await database.create_link_item(
        category_id=cat_id,
        title="Item B",
        url="https://b.example.com",
        description=None,
        db_path=temp_db_path,
    )
    item_c = await database.create_link_item(
        category_id=cat_id,
        title="Item C",
        url="https://c.example.com",
        description=None,
        db_path=temp_db_path,
    )
    user_id = 10
    await database.add_favorite(user_id=user_id, item_id=item_a, db_path=temp_db_path)
    await database.add_favorite(user_id=user_id, item_id=item_b, db_path=temp_db_path)
    assert await database.is_favorite(
        user_id=user_id, item_id=item_a, db_path=temp_db_path
    )
    fav_count = await database.count_favorites(user_id=user_id, db_path=temp_db_path)
    assert fav_count == 2
    fav_page = await database.list_favorites(
        user_id=user_id, page=1, limit=1, db_path=temp_db_path
    )
    assert len(fav_page) == 1
    await database.remove_favorite(user_id=user_id, item_id=item_a, db_path=temp_db_path)
    fav_count_2 = await database.count_favorites(user_id=user_id, db_path=temp_db_path)
    assert fav_count_2 == 1
    await database.add_history_entry(
        user_id=user_id, item_id=item_a, limit=2, db_path=temp_db_path
    )
    await database.add_history_entry(
        user_id=user_id, item_id=item_b, limit=2, db_path=temp_db_path
    )
    await database.add_history_entry(
        user_id=user_id, item_id=item_c, limit=2, db_path=temp_db_path
    )
    history_count = await database.count_history(user_id=user_id, db_path=temp_db_path)
    assert history_count == 2
    history_items = await database.list_history(
        user_id=user_id, page=1, limit=10, db_path=temp_db_path
    )
    assert history_items[0].id == item_c

