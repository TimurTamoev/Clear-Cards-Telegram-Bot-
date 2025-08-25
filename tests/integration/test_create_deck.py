import aiosqlite
import pytest

from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "databases" / "testing_app.db"


@pytest.mark.asyncio
async def test_create_deck_msg_callback(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    from bot import create_deck
    from bot.managing import manager

    user_id = "123456789"
    delete_prev_mock = mocker.AsyncMock()
    delete_user_msg_mock = mocker.AsyncMock()
    add_message_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "delete_user_msg", delete_user_msg_mock)
    mocker.patch.object(manager, "add_message", add_message_mock)

    answer_mock = mocker.AsyncMock()
    message_mock = mocker.MagicMock()
    message_mock.chat.id = user_id
    message_mock.answer = answer_mock
    callback_mock = mocker.MagicMock()
    callback_mock.message = message_mock
    callback_mock.data = "create_a_new_deck"
    state_mock = mocker.AsyncMock()
    bot_mock = mocker.MagicMock()

    await create_deck.create_deck_msg(callback_mock, state_mock, bot_mock)

    delete_prev_mock.assert_awaited_once_with(bot_mock, user_id)

    delete_user_msg_mock.assert_awaited_once_with(message_mock)

    answer_mock.assert_awaited_once_with(
        "📚 **What would you like to name your new deck?**\n\nType a name for your flashcard deck (e.g., 'Spanish Vocabulary', 'Math Formulas', etc.)"
    )

    add_message_mock.assert_called_once()

    state_mock.set_state.assert_awaited_once_with(create_deck.Deck.deck_name)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()


@pytest.mark.asyncio
async def test_insert_deck_name_success(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")

    from bot import core
    from bot import create_deck
    from bot.managing import manager
    from bot.keyboards import show_cards_kb
    from bot.sql_interactions import create_deck as sql_create_deck

    user_id = "123456789"
    deck_name = "Test Deck"
    delete_prev_mock = mocker.AsyncMock()
    delete_user_msg_mock = mocker.AsyncMock()
    add_message_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "delete_user_msg", delete_user_msg_mock)
    mocker.patch.object(manager, "add_message", add_message_mock)
    mocker.patch("bot.create_deck.create_deck", sql_create_deck)

    answer_mock = mocker.AsyncMock()
    message_mock = mocker.MagicMock()
    message_mock.chat.id = user_id
    message_mock.text = deck_name
    message_mock.answer = answer_mock

    state_mock = mocker.AsyncMock()
    state_mock.update_data = mocker.AsyncMock()
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": deck_name})
    state_mock.clear = mocker.AsyncMock()

    bot_mock = mocker.MagicMock()

    await core.init_work(message_mock, bot_mock)

    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)
    state_mock.update_data.assert_awaited_once_with(deck_name=deck_name)

    assert delete_prev_mock.await_count == 2
    delete_user_msg_mock.assert_awaited_once_with(message_mock)

    assert (
        answer_mock.await_count == 2
    )  # cus idk I used init_work so it also has its answer
    call = answer_mock.call_args
    assert call.kwargs["reply_markup"] == show_cards_kb
    assert (
        call.args[0]
        == "✅ **Deck created successfully!**\n\nYour new flashcard deck is ready. You can now start adding cards to it!"
    )
    add_message_mock.assert_called_once()
    state_mock.clear.assert_awaited_once()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()
