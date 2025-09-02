from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.sql_interactions import (
    create_deck,
)

from bot.keyboards import show_cards_kb

from bot.managing import manager


class Deck(StatesGroup):
    deck_name = State()


cd_router = Router()


@cd_router.callback_query(F.data == "create_a_new_deck")
async def create_deck_msg(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await manager.delete_previous(bot, callback.message.chat.id)
    await manager.delete_user_msg(callback.message)
    decks_name_msg = await callback.message.answer(
        "📚 **What would you like to name your new deck?**\n\nType a name for your flashcard deck (e.g., 'Spanish Vocabulary', 'Math Formulas', etc.)"
    )
    manager.add_message(callback.message.chat.id, decks_name_msg.message_id)
    await state.set_state(Deck.deck_name)


@cd_router.message(Deck.deck_name)
async def insert_deck_name(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(deck_name=message.text)
    await manager.delete_previous(bot, message.chat.id)
    await manager.delete_user_msg(message)
    deck = await state.get_data()
    await create_deck(message.chat.id, deck["deck_name"].replace(" ", "␟").replace("_", "ø"))
    various_msg = await message.answer(
        "✅ **Deck created successfully!**\n\nYour new flashcard deck is ready. You can now start adding cards to it!",
        reply_markup=show_cards_kb,
    )
    manager.add_message(message.chat.id, various_msg.message_id)
    await state.clear()
