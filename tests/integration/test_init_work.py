from types import SimpleNamespace

import aiosqlite
import pytest


@pytest.mark.asyncio
async def test_init_work(monkeypatch, mocker):
    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    from bot import core
    from bot.keyboards import show_cards_kb
    from bot.managing import manager
    from bot.sql_interactions import DB_PATH

    user_id = "123456789"
    delete_prev_mock = mocker.AsyncMock()
    mocker.patch.object(manager, "delete_previous", delete_prev_mock)
    answer_mock = mocker.AsyncMock()
    message = SimpleNamespace(
        chat=SimpleNamespace(id=user_id),
        answer=answer_mock,
    )
    bot_mock = mocker.MagicMock()

    await core.init_work(message, bot_mock)
    delete_prev_mock.assert_awaited_once_with(bot_mock, user_id)
    answer_mock.assert_awaited_once()
    call = answer_mock.await_args
    assert (
        call.args[0]
        == "🎉 **Welcome! You are now registered.**\n\nYou can start creating decks and cards to begin your learning journey!"
    )
    assert call.kwargs.get("reply_markup") is show_cards_kb
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id=?", (user_id,)
        )
        assert await cursor.fetchone() == (user_id,)
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.commit()
