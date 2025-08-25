from pathlib import Path

import pytest
import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent / "databases" / "testing_app.db"


@pytest.mark.asyncio
async def test_card_creation(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    user_id = "000000000"
    deck_name = "DeckName"
    from bot.managing import manager
    from bot import core
    from bot import create_deck
    from bot import card_interaction
    from bot.keyboards import show_cards_kb

    bot_mock = mocker.MagicMock()
    message_mock = mocker.AsyncMock()
    answer_mock = mocker.AsyncMock()
    message_mock.answer = answer_mock
    message_mock.chat.id = user_id

    delete_prev_mock = mocker.AsyncMock()
    add_msg_mock = mocker.MagicMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    mocker.patch.object(manager, "add_message", add_msg_mock)

    await core.init_work(message_mock, bot_mock)

    state_mock = mocker.AsyncMock()
    state_mock.update_data = mocker.AsyncMock()
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": deck_name})
    state_mock.clear = mocker.AsyncMock()

    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)

    state_mock.get_data = mocker.AsyncMock(
        return_value={
            "deck_id": '1',
            "front": "front",
            "back": "back",
        }
    )

    await card_interaction.set_back_add_card(message_mock, state_mock, bot_mock)

    assert delete_prev_mock.await_count == 3
    assert add_msg_mock.call_count == 2

    call = answer_mock.call_args

    assert call.kwargs["reply_markup"] == show_cards_kb
    assert (
        call.args[0]
        == "✅ **Card created successfully!**\n\nYour new flashcard has been added to the deck."
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.commit()
