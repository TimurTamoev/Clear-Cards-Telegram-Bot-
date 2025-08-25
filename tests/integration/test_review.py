from types import SimpleNamespace

import asyncio
import pytest


class FakeState:
    def __init__(self):
        self._data = {}

    async def get_data(self):
        return dict(self._data)

    async def update_data(self, **kwargs):
        self._data.update(kwargs)


@pytest.mark.asyncio
async def test_how_many_cards_keyboard(mocker):
    from bot import review

    delete_prev = mocker.AsyncMock()
    add_msg = mocker.MagicMock()
    mocker.patch.object(review.manager, "delete_previous", delete_prev)
    mocker.patch.object(review.manager, "add_message", add_msg)

    answer_mock = mocker.AsyncMock()
    answer_mock.return_value = SimpleNamespace(message_id=111)
    message = SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock)
    cb = SimpleNamespace(data="review_deck_deck_1_1", message=message)
    bot = mocker.MagicMock()

    await review.how_many_cards(cb, bot)

    delete_prev.assert_awaited_once_with(bot, "u1")
    answer_mock.assert_awaited_once()
    args, kwargs = answer_mock.await_args
    assert "how many cards" in args[0]
    kb = kwargs.get("reply_markup")
    texts = [b.text for b in kb.inline_keyboard[0]]
    assert texts == ["5", "10", "25", "all"]
    datas = [b.callback_data for b in kb.inline_keyboard[0]]
    assert all(d.startswith("review_") for d in datas)
    add_msg.assert_called_once_with("u1", 111)


@pytest.mark.asyncio
async def test_start_review_no_cards(mocker):
    from bot import review

    mocker.patch("bot.review.asyncio.sleep", mocker.AsyncMock())

    mocker.patch("bot.review.get_cards", mocker.AsyncMock(return_value=[]))
    mocker.patch.object(review.manager, "delete_previous", mocker.AsyncMock())
    mocker.patch.object(review.manager, "delete_user_msg", mocker.AsyncMock())
    mocker.patch.object(review.manager, "add_message", mocker.MagicMock())

    loading_msg = SimpleNamespace(message_id=22, edit_text=mocker.AsyncMock())
    answer_mock = mocker.AsyncMock(side_effect=[loading_msg, None])
    message = SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock)
    cb = SimpleNamespace(data="review_5__deck_1_1", message=message)
    bot = mocker.MagicMock()
    state = FakeState()

    await review.start_review(cb, bot, state)

    assert answer_mock.await_count == 2
    _, kwargs2 = answer_mock.await_args_list[1]
    kb = kwargs2.get("reply_markup")
    assert kb.inline_keyboard[0][0].text == "Create a new card"


@pytest.mark.asyncio
async def test_start_review_with_cards_shows_first(mocker):
    from bot import review

    mocker.patch("bot.review.asyncio.sleep", mocker.AsyncMock())

    cards = [["Front B", "Back B", 3, 7], ["Front A", "Back A", 1, 5]]
    mocker.patch("bot.review.get_cards", mocker.AsyncMock(return_value=cards))

    mocker.patch.object(review.manager, "delete_previous", mocker.AsyncMock())
    mocker.patch.object(review.manager, "delete_user_msg", mocker.AsyncMock())
    mocker.patch.object(review.manager, "add_message", mocker.MagicMock())
    mocker.patch.object(review.manager, "add_direct_msg", mocker.MagicMock())

    loading_msg = SimpleNamespace(message_id=33, edit_text=mocker.AsyncMock())
    card_msg = SimpleNamespace(message_id=34)
    answer_mock = mocker.AsyncMock(side_effect=[loading_msg, card_msg])
    message = SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock)
    cb = SimpleNamespace(data="review_10__deck_1_1", message=message)
    bot = mocker.MagicMock()
    state = FakeState()

    await review.start_review(cb, bot, state)

    _, kwargs2 = answer_mock.await_args_list[1]
    kb = kwargs2.get("reply_markup")
    assert kwargs2.get("text") == "Front A"
    labels = [b.text for b in kb.inline_keyboard[0]]
    assert labels == ["Easy", "Good", "Hard", "Fail"]


@pytest.mark.asyncio
async def test_insert_rating_updates_memory_and_moves_next(mocker):
    from bot import review

    get_memory_mock = mocker.AsyncMock(return_value=(10,))
    change_memory_mock = mocker.AsyncMock()
    mocker.patch("bot.review.get_memory", get_memory_mock)
    mocker.patch("bot.review.change_memory", change_memory_mock)

    show_next_mock = mocker.AsyncMock()
    mocker.patch("bot.review.show_next", show_next_mock)

    state = FakeState()
    bot = mocker.MagicMock()

    cases = {
        "easy": 5,
        "good": 3,
        "hard": 1,
        "fail": -5,
    }
    for rate, delta in cases.items():
        change_memory_mock.reset_mock()
        get_memory_mock.reset_mock(return_value=True)
        get_memory_mock.return_value = (1,) if rate == "fail" else (10,)

        cb_data = f"rate_{rate}_0_5_deck_1_1"
        cb = SimpleNamespace(data=cb_data)

        await review.insert_rating(cb, state, bot)

        base = 1 if rate == "fail" else 10
        expected = max(base + delta, 0)
        assert change_memory_mock.await_args.args[2] == expected
        show_next_mock.assert_awaited()


@pytest.mark.asyncio
async def test_show_next_completion_flow(mocker):
    from bot import review

    state = FakeState()
    await state.update_data(
        cards=[["F1", "B1", 0, 1]],
        current_card_index=1,
        deck_id="deck_1_1",
        cards_amount="5",
    )

    edit_msg = SimpleNamespace(edit_text=mocker.AsyncMock())
    mocker.patch.object(
        review.manager, "prev_direct", mocker.MagicMock(return_value=edit_msg)
    )
    add_message = mocker.MagicMock()
    mocker.patch.object(review.manager, "add_message", add_message)
    custom_end = mocker.AsyncMock(return_value="kb")
    mocker.patch("bot.review.custom_cd_end_section", custom_end)

    answer_mock = mocker.AsyncMock(return_value=SimpleNamespace(message_id=99))
    message = SimpleNamespace(chat=SimpleNamespace(id="u1"), answer=answer_mock)
    cb = SimpleNamespace(message=message)
    bot = mocker.MagicMock()

    await review.show_next(cb, bot, state)

    edit_msg.edit_text.assert_awaited()
    custom_end.assert_awaited_once_with(1)
    add_message.assert_called_once_with("u1", 99)
