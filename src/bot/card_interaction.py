from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.sql_interactions import insert_card, delete_card, get_card_data, get_deck_name_txt_from_its_rowid

from bot.keyboards import show_cards_kb
from bot.managing import manager

ci_router = Router()


class Card(StatesGroup):
    deckname = State()
    # It is <deckname_userid_rowid>
    front = State()
    back = State()


@ci_router.callback_query(F.data.startswith("create_card_"))
async def create_card(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await manager.delete_user_msg(callback)
    deck_id = callback.data.split("_")[-1]
    await state.update_data(deck_id = deck_id)
    await state.set_state(Card.front)
    front_msg = await callback.message.answer(
        "📝 **What is written on the front side?**\n\nType the question or prompt that will appear on the front of your card."
    )
    manager.add_message(callback.message.chat.id, front_msg.message_id)


@ci_router.message(Card.front)
async def set_front_get_back(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(front=message.text.replace("␟", " "))
    await manager.delete_previous(bot, message.chat.id)
    await manager.delete_user_msg(message)
    await state.set_state(Card.back)
    back_msg = await message.answer(
        "📝 **What is written on the back side?**\n\nType the answer or explanation that will appear on the back of your card."
    )
    manager.add_message(message.chat.id, back_msg.message_id)


@ci_router.message(Card.back)
async def set_back_add_card(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(back=message.text.replace("␟", " "))
    await manager.delete_previous(bot, message.chat.id)
    await manager.delete_user_msg(message)
    card_info = (
        await state.get_data()
    )  # Is it a dict {'deckname': , 'front': ,'back': }.
    await insert_card(card_info["deck_id"], card_info["front"], card_info["back"], 0)
    creation_msg = await message.answer(
        "✅ **Card created successfully!**\n\nYour new flashcard has been added to the deck.",
        reply_markup=show_cards_kb,
    )
    manager.add_message(message.chat.id, creation_msg.message_id)
    await state.clear()


@ci_router.callback_query(F.data.startswith("edit_card_"))
async def init_cards_kb(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    inline_template = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Delete",
                    callback_data=f"{callback.data.replace("edit_card_", "delete_card_")}",
                )
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
        ]
    )
    card_data = await get_card_data(
        callback.data.replace("edit_card_", "")[:-2], int(callback.data.split("_")[-1])
    )
    front = card_data[1]
    back = card_data[2]
    cards_inf_msg = await callback.message.answer(
        text=f"{front} -> {back}", reply_markup=inline_template
    )
    manager.add_message(callback.message.chat.id, cards_inf_msg.message_id)


# This function is created in order to be able to delete a card by clicking "delete" button
@ci_router.callback_query(F.data.startswith("delete_card_"))
async def delete_card_click(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    await delete_card(callback.data.replace("delete_card_", ""))
    deleting_msg = await callback.message.answer(
        "🗑️ **Card deleted successfully!**\n\nThe card has been removed from your deck.",
        reply_markup=show_cards_kb,
    )
    manager.add_message(callback.message.chat.id, deleting_msg.message_id)
