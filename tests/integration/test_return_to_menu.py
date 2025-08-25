from types import SimpleNamespace

import aiosqlite
import pytest


@pytest.mark.asyncio
async def test_return_to_menu(monkeypatch, mocker):
    from bot import cancel
    from bot import core
    from bot.keyboards import show_cards_kb
    from bot.managing import manager
    from bot.sql_interactions import DB_PATH

    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    user_id = "123456789"
    delete_prev_mock = mocker.AsyncMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    answer_mock = mocker.AsyncMock()
    message = SimpleNamespace(
        chat=SimpleNamespace(id=user_id),
        answer=answer_mock,
    )
    state_mock = mocker.AsyncMock()
    bot_mock = mocker.MagicMock()
    await core.init_work(message, bot_mock)
    await cancel.return_to_menu(message, state_mock, bot_mock)
    assert delete_prev_mock.await_count == 2
    call = answer_mock.await_args
    assert call.kwargs.get("reply_markup") is show_cards_kb
    assert (
        call.args[0]
        == "🏠 **Welcome back to the main menu!**\n\nWhat would you like to do next?"
    )
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()
