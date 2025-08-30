from aiogram import F, Router, Bot
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
import asyncio

from bot.sql_interactions import get_cards, change_memory, get_memory
from bot.managing import manager
from bot.keyboards import custom_cd_end_section, show_cards_kb

r_router = Router()

EASY_AFFECTION = 5
GOOD_AFFECTION = 3
HARD_AFFECTION = 1
FAIL_AFFECTION = -5


@r_router.callback_query(F.data.startswith("review_deck_"))
async def how_many_cards(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    section_len = await callback.message.answer(
        "**how many cards do you want to review**",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="5",
                        callback_data=callback.data.replace(
                            "review_deck", f"review_{5}_"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="10",
                        callback_data=callback.data.replace(
                            "review_deck", f"review_{10}_"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="25",
                        callback_data=callback.data.replace(
                            "review_deck", f"review_{25}_"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="all",
                        callback_data=callback.data.replace(
                            "review_deck", f"review_{10000000}_"
                        ),
                    ),
                ]
            ]
        ),
    )
    manager.add_message(callback.message.chat.id, section_len.message_id)


@r_router.callback_query(F.data.startswith("review_"))
async def start_review(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await manager.delete_previous(bot, callback.message.chat.id)
    await manager.delete_user_msg(callback)
    loading_message = await callback.message.answer(
        f"⏰ **Review starting in 3 seconds...**"
    )
    manager.add_message(callback.message.chat.id, loading_message.message_id)
    for i in [2, 1, 0]:
        await asyncio.sleep(1)
        await loading_message.edit_text(f"⏰ **Review starting in {i} seconds...**")
    await manager.delete_previous(bot, callback.message.chat.id)
    length = callback.data.split("_")[1]
    cards = await get_cards(callback.data.replace("review_" + length + "__", ""))
    if not cards:
        new_cb = f"create_card_{callback.data.replace("review_" + length + "__", "")}"
        await callback.message.answer(
            "📝 **No cards in this deck!**\n\nCreate some cards first to start reviewing.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Create a new card", callback_data=new_cb
                        )
                    ]
                ]
            ),
        )
        return
    sorted_cards = sorted(cards, key=lambda x: x[2])
    await state.update_data(
        current_card_index=0,
        cards=sorted_cards,
        deck_id=callback.data.replace("review_" + length + "__", ""),
        cards_amount=callback.data.split("_")[1],
    )
    await show_next(callback, bot, state)


async def show_next(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    cards = data["cards"]
    current_card_index = data["current_card_index"]
    deck_id = data["deck_id"]
    length = data["cards_amount"]

    if current_card_index >= len(cards) or current_card_index >= int(length):
        editing_msg = manager.prev_direct(callback.message.chat.id)
        await editing_msg.edit_text(
            f"{cards[current_card_index - 1][0].replace("␟", " ")} -> {cards[current_card_index - 1][1].replace("␟", " ")}"
        )
        end_msg = await callback.message.answer(
            "🎉 **Review session completed!**\n\nGreat job! You've finished reviewing all the cards in this session.",
            reply_markup=await custom_cd_end_section(len(cards)),
        )
        manager.add_message(callback.message.chat.id, end_msg.message_id)
        return

    if current_card_index != 0:
        editing_msg = manager.prev_direct(callback.message.chat.id)
        await editing_msg.edit_text(
            f"{cards[current_card_index - 1][0].replace("␟", " ")} -> {cards[current_card_index - 1][1].replace("␟", " ")}"
        )
    front = cards[current_card_index][0].replace("␟", " ")
    rating = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Easy",
                    callback_data=f"rate_easy_{current_card_index}_{cards[current_card_index][3]}_{deck_id}",
                ),
                InlineKeyboardButton(
                    text="Good",
                    callback_data=f"rate_good_{current_card_index}_{cards[current_card_index][3]}_{deck_id}",
                ),
                InlineKeyboardButton(
                    text="Hard",
                    callback_data=f"rate_hard_{current_card_index}_{cards[current_card_index][3]}_{deck_id}",
                ),
                InlineKeyboardButton(
                    text="Fail",
                    callback_data=f"rate_fail_{current_card_index}_{cards[current_card_index][3]}_{deck_id}",
                ),
            ]
        ]
    )
    #print(current_card_index, cards[current_card_index][3], deck_id[:-2])
    msg = await callback.message.answer(text=front, reply_markup=rating)
    manager.add_direct_msg(callback.message.chat.id, msg)
    manager.add_message(callback.message.chat.id, msg.message_id)


# callback looks like rate_<easy>_<deckname_userid_rowid>_<how many cards you want to review>
@r_router.callback_query(F.data.startswith("rate_"))
async def insert_rating(callback: CallbackQuery, state: FSMContext, bot: Bot):
    rate = callback.data.split("_")[1]
    rowid = callback.data.split("_")[3]
    #print(rowid, callback.data.replace(f"rate_{rate}_", "")[4:-2] + "_" + rowid)
    memory = await get_memory(callback.data.replace(f"rate_{rate}_", "")[4:-2] + '_' + rowid, 0)
    if rate == "easy":
        await change_memory(
            callback.data.replace(f"rate_{rate}_", "")[4:],
            rowid,
            memory[0] + EASY_AFFECTION,
        )
    elif rate == "good":
        await change_memory(
            callback.data.replace(f"rate_{rate}_", "")[4:],
            rowid,
            memory[0] + GOOD_AFFECTION,
        )
    elif rate == "hard":
        await change_memory(
            callback.data.replace(f"rate_{rate}_", "")[4:],
            rowid,
            memory[0] + HARD_AFFECTION,
        )
    elif rate == "fail":
        await change_memory(
            callback.data.replace(f"rate_{rate}_", "")[4:],
            rowid,
            max(memory[0] + FAIL_AFFECTION, 0),
        )
    await state.update_data(current_card_index=int(callback.data.split("_")[2]) + 1)
    await show_next(callback, bot, state)


@r_router.callback_query(F.data.startswith("cancel_section"))
async def cancel_section(callback: CallbackQuery, bot: Bot):
    length = callback.data.split("_")[2]
    for _ in range(int(length) + 1):
        await manager.delete_previous(bot, callback.message.chat.id)
    await callback.message.answer(
        "**you are returned to the main menu**", reply_markup=show_cards_kb
    )
    manager.add_message(bot, callback.message.chat.id)
