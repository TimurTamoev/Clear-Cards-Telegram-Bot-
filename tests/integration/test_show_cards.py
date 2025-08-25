import pytest
import aiosqlite


@pytest.mark.asyncio
async def test_show_card(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    user_id = "000000000"
    deck_name = "DeckName"
    from bot.managing import manager
    from bot import core
    from bot import create_deck
    from bot.sql_interactions import DB_PATH
    from bot.card_interaction import set_back_add_card
    from bot.keyboards import generate_inline_cards
    from bot.deck_interaction import edit_deck

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

    message_mock.answer = answer_mock

    await set_back_add_card(message_mock, state_mock, bot_mock)

    callback_mocker = mocker.AsyncMock()
    callback_mocker.message.chat.id = user_id
    callback_mocker.data = f"edit_deck_DeckName_{user_id}_1"
    callback_mocker.message.answer = answer_mock

    await edit_deck(callback_mocker, bot_mock)

    test_kb = await generate_inline_cards(f"{deck_name}_000000000_1")

    call = answer_mock.call_args

    assert add_msg_mock.call_count == 3
    assert delete_prev_mock.await_count == 4

    assert call.kwargs["reply_markup"] == test_kb
    assert (
        call.args[0]
        == "📚 **Here are your cards:**\n\nSelect a card to edit or delete it."
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.commit()
