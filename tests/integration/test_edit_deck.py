from pathlib import Path

import aiosqlite
import pytest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

DB_PATH = Path(__file__).parent.parent.parent / "databases" / "testing_app.db"


@pytest.mark.asyncio
async def test_edit_deck_with_no_cards(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")

    from bot import create_deck
    from bot import core
    from bot.deck_interaction import edit_deck
    from bot.managing import manager

    user_id = "000000000"
    deck_name = "DeckName"
    delete_prev_mock = mocker.AsyncMock()
    add_msg_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "add_message", add_msg_mock)

    message_mock = mocker.AsyncMock()
    message_mock.chat.id = user_id
    message_mock.text = deck_name
    bot_mock = mocker.MagicMock()
    answer_mock = mocker.AsyncMock()
    message_mock.answer = answer_mock
    await core.init_work(message_mock, bot_mock)

    state_mock = mocker.AsyncMock()
    state_mock.update_data = mocker.AsyncMock()
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": deck_name})
    state_mock.clear = mocker.AsyncMock()
    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)

    callback_mock = mocker.AsyncMock()
    callback_mock.data = "edit_deck_DeckName_000000000_1"
    answer_mock_2 = mocker.AsyncMock()
    callback_mock.message.answer = answer_mock_2
    callback_mock.message.chat.id = user_id
    await edit_deck(callback_mock, bot_mock)

    assert delete_prev_mock.await_count == 3
    assert add_msg_mock.call_count == 2

    call = answer_mock_2.call_args

    no_decks_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Create card",
                    callback_data=f"create_card_{deck_name}_000000000_1",
                )
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
        ]
    )

    assert call.kwargs["reply_markup"] == no_decks_kb
    assert (
        call.args[0]
        == "📝 **No cards in this deck yet!**\n\nCreate your first card to start building your knowledge."
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.commit()


@pytest.mark.asyncio
async def test_edit_deck_with_cards(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")

    from bot import create_deck
    from bot import core
    from bot.deck_interaction import edit_deck
    from bot.sql_interactions import insert_card
    from bot.managing import manager
    from bot.keyboards import generate_inline_cards

    user_id = "000000000"
    deck_name = "DeckName"
    delete_prev_mock = mocker.AsyncMock()
    add_msg_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "add_message", add_msg_mock)

    message_mock = mocker.AsyncMock()
    message_mock.chat.id = user_id
    message_mock.text = deck_name
    bot_mock = mocker.MagicMock()
    answer_mock = mocker.AsyncMock()
    message_mock.answer = answer_mock
    await core.init_work(message_mock, bot_mock)

    state_mock = mocker.AsyncMock()
    state_mock.update_data = mocker.AsyncMock()
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": deck_name})
    state_mock.clear = mocker.AsyncMock()
    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)
    await insert_card("1", "front", "back", 0)

    callback_mock = mocker.AsyncMock()
    callback_mock.data = "edit_deck_DeckName_000000000_1"
    answer_mock_2 = mocker.AsyncMock()
    callback_mock.message.answer = answer_mock_2
    callback_mock.message.chat.id = user_id
    await edit_deck(callback_mock, bot_mock)

    assert delete_prev_mock.await_count == 3
    assert add_msg_mock.call_count == 2

    call = answer_mock_2.call_args

    assert_kb = await generate_inline_cards("DeckName_000000000_1")

    assert call.kwargs["reply_markup"] == assert_kb
    assert (
        call.args[0]
        == "📚 **Here are your cards:**\n\nSelect a card to edit or delete it."
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.commit()
