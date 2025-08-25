import aiosqlite
import pytest

from bot.sql_interactions import (
    DB_PATH,
    init_user,
    create_deck,
    get_decks,
    get_cards,
    insert_card,
    delete_deck,
    change_memory,
    get_memory,
    get_card_data,
    get_deck_name_txt_from_its_rowid,
)


async def _cleanup_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()


@pytest.mark.asyncio
async def test_init_user_creates_user_record():
    await _cleanup_db()
    user_id = "1"
    await init_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        assert await cursor.fetchone() == (user_id,)
    await _cleanup_db()


@pytest.mark.asyncio
async def test_create_deck_basic():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT deckname_txt FROM decks WHERE user_property = (SELECT rowid FROM users WHERE user_id = ?)", (user_id,))
        result = await cursor.fetchone()
        assert result[0] == deck_name
    await _cleanup_db()


@pytest.mark.asyncio
async def test_create_deck_with_underscore():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My_Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT deckname_txt FROM decks WHERE user_property = (SELECT rowid FROM users WHERE user_id = ?)", (user_id,))
        result = await cursor.fetchone()
        assert result[0] == "MyøDeck"
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_decks_format():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    
    decks = await get_decks(user_id)
    assert len(decks) == 1
    
    display_name, callback_id, deck_rowid = decks[0]
    assert display_name == deck_name
    assert callback_id == f"{deck_name[:8]}_{user_id}_{deck_rowid}"
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_decks_with_special_characters():
    await _cleanup_db()
    user_id = "1"
    await init_user(user_id)
    await create_deck(user_id, "My Deck")
    await create_deck(user_id, "My_Deck")
    
    decks = await get_decks(user_id)
    assert len(decks) == 2
    display_name1, callback_id1, deck_rowid1 = decks[0]
    assert display_name1 == "My Deck"
    assert callback_id1 == f"My Deck_{user_id}_{deck_rowid1}"
    display_name2, callback_id2, deck_rowid2 = decks[1]
    assert display_name2 == "My_Deck"
    assert callback_id2 == f"MyøDeck_{user_id}_{deck_rowid2}"
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_insert_card_basic():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    
    # Get the deck rowid for insert_card
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]  # The actual rowid from the database
    
    # Insert card using deck_rowid (not the full callback string)
    await insert_card(str(deck_rowid), "front", "back", 0)
    
    # Verify card was inserted
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT front, back, memory FROM cards")
        result = await cursor.fetchone()
        assert result == ("front", "back", 0)
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_cards_basic():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]
    callback_id = decks[0][1]
    
    await insert_card(str(deck_rowid), "front", "back", 0)
    cards = await get_cards(callback_id)
    assert len(cards) == 1
    assert cards[0][:3] == ["front", "back", 0]  # front, back, memory
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_delete_deck():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    decks = await get_decks(user_id)
    callback_id = decks[0][1]
    deck_rowid = decks[0][2]
    await insert_card(str(deck_rowid), "front", "back", 0)
    assert len(await get_decks(user_id)) == 1
    cards = await get_cards(callback_id)
    assert len(cards) == 1
    await delete_deck(callback_id)
    assert len(await get_decks(user_id)) == 0
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_change_memory():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]
    callback_id = decks[0][1]
    await insert_card(str(deck_rowid), "front", "back", 0)
    await change_memory(callback_id, 1, 7)
    memory_value = await get_memory(callback_id, 1)
    assert memory_value == (7,)
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_memory():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]
    callback_id = decks[0][1]
    
    await insert_card(str(deck_rowid), "front", "back", 5)
    
    memory_value = await get_memory(callback_id, 1)
    assert memory_value == (5, )
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_card_data():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]
    await insert_card(str(deck_rowid), "front text", "back text", 0)
    card_data = await get_card_data("any_string", 1)  # deckname parameter is not used
    assert card_data[1:] == ("front text", "back text", 0)
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_get_deck_name_from_rowid():
    await _cleanup_db()
    user_id = "1"
    deck_name = "My Deck"
    await init_user(user_id)
    await create_deck(user_id, deck_name)
    decks = await get_decks(user_id)
    deck_rowid = decks[0][2]
    deck_name_text = await get_deck_name_txt_from_its_rowid(deck_rowid)
    assert deck_name_text == deck_name
    
    await _cleanup_db()


@pytest.mark.asyncio
async def test_multiple_decks_and_cards():
    await _cleanup_db()
    user_id = "1"
    await init_user(user_id)
    deck_names = ["Deck 1", "Deck 2", "Long Deck Name That Exceeds Eight Characters"]
    for name in deck_names:
        await create_deck(user_id, name)
    
    decks = await get_decks(user_id)
    assert len(decks) == 3
    for i, (display_name, callback_id, deck_rowid) in enumerate(decks):
        assert display_name == deck_names[i]
        expected_start = f"{deck_names[i][:8]}_{user_id}"
        assert callback_id.startswith(expected_start)
        assert callback_id.endswith(f"_{deck_rowid}")
    
    await _cleanup_db()


