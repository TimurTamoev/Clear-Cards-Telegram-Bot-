from pkgutil import get_data

import pytest
from types import SimpleNamespace
import aiosqlite
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class FakeState:
    def __init__(self):
        self.data = {}

    async def get_data(self):
        return self.data

    async def update_data(self, **kwargs):
        self.data.update(kwargs)


@pytest.mark.asyncio
async def test_how_many_cards_kb(monkeypatch, mocker):

    from bot.review import manager
    from bot.review import how_many_cards
    from bot.sql_interactions import DB_PATH

    monkeypatch.setenv("api", "123456:AAABBBCCCDDDEEEFFFGGGHHHIIJJKKLLMMNN")
    user_id = "000000000"

    delete_prev = mocker.AsyncMock()
    add_msg = mocker.MagicMock()
    mocker.patch.object(manager, "add_message", add_msg)
    mocker.patch.object(manager, "delete_previous", delete_prev)

    answer_mock = mocker.AsyncMock()

    bot = mocker.AsyncMock()

    callback_mock = mocker.AsyncMock()
    callback_mock.message.answer = answer_mock
    callback_mock.message.chat.id = user_id
    callback_mock.data = "review_deck_000000000_1"

    await how_many_cards(callback_mock, bot)

    call = answer_mock.call_args

    assert call.kwargs["reply_markup"] == InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="5",
                    callback_data=callback_mock.data.replace(
                        "review_deck", f"review_{5}_"
                    ),
                ),
                InlineKeyboardButton(
                    text="10",
                    callback_data=callback_mock.data.replace(
                        "review_deck", f"review_{10}_"
                    ),
                ),
                InlineKeyboardButton(
                    text="25",
                    callback_data=callback_mock.data.replace(
                        "review_deck", f"review_{25}_"
                    ),
                ),
                InlineKeyboardButton(
                    text="all",
                    callback_data=callback_mock.data.replace(
                        "review_deck", f"review_{10000000}_"
                    ),
                ),
            ]
        ]
    )

    assert call.args[0] == "**how many cards do you want to review**"

    assert add_msg.call_count == 1
    assert delete_prev.await_count == 1

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS 'cards'")
        await db.execute("DROP TABLE IF EXISTS 'decks'")
        await db.execute("DROP TABLE IF EXISTS 'users'")
        await db.commit()


@pytest.mark.asyncio
async def test_start_review_no_cards(mocker):
    from bot import review

    mocker.patch(
        "bot.review.asyncio.sleep", mocker.AsyncMock()
    )  # Do not need to check as it is too easy
    mocker.patch(
        "bot.review.get_cards", mocker.AsyncMock(return_value=[])
    )  # I basically mock the return cvalue idk
    mocker.patch.object(review.manager, "delete_previous", mocker.AsyncMock())
    mocker.patch.object(
        review.manager, "add_message", mocker.MagicMock()
    )  # as it is not async
    mocker.patch.object(review.manager, "delete_user_msg", mocker.AsyncMock())

    answer_mock = mocker.AsyncMock()
    message = SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock)
    cb = SimpleNamespace(data="review_5__deck_1_1", message=message)
    bot = mocker.MagicMock()
    state = FakeState()

    await review.start_review(cb, bot, state)

    assert answer_mock.await_count == 2

    _, kwargs2 = answer_mock.call_args_list[1]

    kb = kwargs2.get("reply_markup")

    assert kb.inline_keyboard[0][0].text == "Create a new card"

    assert answer_mock.await_count


@pytest.mark.asyncio
async def test_insert_rating_move_to_next(mocker):
    from bot import managing
    from bot import review

    state = SimpleNamespace(
        get_data=mocker.AsyncMock(
            return_value={
                "deck_id": 1,
                "cards": [("front", "back", 0, 1)],
                "cards_amount": 1,
                "current_card_index": 0,
            }
        )
    )
    answer_mock = mocker.AsyncMock()
    cb = SimpleNamespace(
        message=SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock),
        data="review_5__deck_1_1",
    )
    delete_prev = mocker.AsyncMock()
    mocker.patch.object(managing.manager, "delete_previous", delete_prev)
    add_msg = mocker.MagicMock()
    mocker.patch.object(managing.manager, "add_message", add_msg)

    bot = mocker.MagicMock()

    mocker.patch.object(
        managing.manager, "prev_direct", mocker.AsyncMock(return_value=None)
    )

    await review.show_next(cb, bot, state)

    call = answer_mock.await_args

    assert call.kwargs["reply_markup"] == InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Easy",
                    callback_data=f"rate_easy_0_1_1",
                ),
                InlineKeyboardButton(
                    text="Good",
                    callback_data=f"rate_good_0_1_1",
                ),
                InlineKeyboardButton(
                    text="Hard",
                    callback_data=f"rate_hard_0_1_1",
                ),
                InlineKeyboardButton(
                    text="Fail",
                    callback_data=f"rate_fail_0_1_1",
                ),
            ]
        ]
    )
    assert call.kwargs["text"] is "front"


@pytest.mark.asyncio
async def rate_it(mocker):
    from bot import review
    from bot import managing

    rating_cds = {
        "rate_easy_0_1_1": 5,
        "rate_good_0_1_1": 3,
        "rate_hard_0_1_1": 1,
        "rate_fail_0_1_1": -5
    }

    add_msg = mocker.MagicMock()
    mocker.patch.object(managing.manager, "add_message", add_msg)
    delete_prev = mocker.AsyncMock()
    mocker.patch.object(managing.manager, "delete_previous", delete_prev)

    mocker.patch("bot.sql_interactions.get_memory", mocker.AsyncMock(return_value=999))
    state = SimpleNamespace(
        get_data=mocker.AsyncMock(
            return_value={
                "deck_id": 1,
                "cards": [("front", "back", 0, 1)],
                "cards_amount": 1,
                "current_card_index": 0,
            }
        ),
        update_data=mocker.AsyncMock(
            side_effect=lambda: get_data.return_value_update(
                {"current_card_index": state.get_data()["current_card_index"] + 1}
            )
        ),
    )

    def add_it():
        state.get_data["current_card_index"] += 1

    answer_mock = mocker.AsyncMock()
    cd = SimpleNamespace(
        message=SimpleNamespace(chat=SimpleNamespace(id="u2")),
        answer=answer_mock,
        data=None,
    )
    bot = mocker.MagicMock()
    for cd_rate in rating_cds.keys():
        cd.data = cd_rate
        await review.insert_rating(cd, state, bot)
        assert state.get_data["cards"][3] == max(1 + rating_cds[cd_rate], 0)
