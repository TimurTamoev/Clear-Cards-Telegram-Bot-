from pathlib import Path

import aiosqlite
import pytest


@pytest.mark.asyncio
async def test_delete_deck(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    from bot import core
    from bot.keyboards import show_cards_kb
    from bot import deck_interaction
    from bot.sql_interactions import delete_deck, DB_PATH
    from bot.managing import manager
    from bot import create_deck

    user_id = "000000000"
    deck_name = "Deck to delete"

    delete_prev_mock = mocker.AsyncMock()
    add_message_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "add_message", add_message_mock)
    mocker.patch("bot.deck_interaction.delete_deck", delete_deck)

    message_mock = mocker.AsyncMock()
    message_mock.chat.id = user_id

    bot_mock = mocker.MagicMock()

    await core.init_work(message_mock, bot_mock)
    callback_mock = mocker.AsyncMock()
    callback_mock.data = f"delete_deck_Deck␟to␟delete_000000000_1"
    callback_mock.message.chat.id = user_id
    answer_mock = mocker.AsyncMock()
    callback_mock.message.answer = answer_mock

    state_mock = mocker.AsyncMock()
    state_mock.update_data = mocker.AsyncMock()
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": deck_name})
    state_mock.clear = mocker.AsyncMock()
    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)

    await deck_interaction.impl_delete_deck(callback_mock, bot_mock)

    assert delete_prev_mock.await_count == 3
    assert add_message_mock.call_count == 2

    call = answer_mock.call_args

    assert call.kwargs["reply_markup"] == show_cards_kb
    assert (
        call.args[0]
        == "🗑️ **Deck deleted successfully!**\n\nThe deck and all its cards have been removed."
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.commit()
