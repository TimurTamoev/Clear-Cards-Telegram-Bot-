import pytest
import aiosqlite


@pytest.mark.asyncio
async def test_show_decks(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    user_id = "000000000"
    deck_name = "DeckName"
    from bot.managing import manager
    from bot import core
    from bot import create_deck
    from bot.sql_interactions import DB_PATH
    from bot.show_decks import show_decks_msg
    from bot.keyboards import generate_inline_decks

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
    state_mock.get_data = mocker.AsyncMock(return_value={"deck_name": str(deck_name)})
    state_mock.clear = mocker.AsyncMock()

    await create_deck.insert_deck_name(message_mock, state_mock, bot_mock)

    callback_mock = mocker.AsyncMock()
    callback_mock.message.chat.id = user_id
    callback_mock.data = "show_decks"
    callback_mock.message.answer = answer_mock
    await show_decks_msg(callback_mock, bot_mock)

    call = answer_mock.call_args

    assert (
        call.args[0]
        == "📚 **Here are your decks:**\n\nSelect a deck to manage or review your cards."
    )
    kb_to_test = await generate_inline_decks(user_id)
    assert call.kwargs["reply_markup"] == kb_to_test

    assert add_msg_mock.call_count == 2
    assert delete_prev_mock.await_count == 3

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()
