from aiogram import Router, F, Bot
from aiogram.types import  CallbackQuery

from bot.sql_interactions import (
    get_decks,
)

from bot.keyboards import create_deck_keyboard, generate_inline_decks, show_cards_kb
from bot.managing import manager

sd_router = Router()


@sd_router.callback_query(F.data == "show_decks")
async def show_decks_msg(callback: CallbackQuery, bot: Bot):
    try:
        await manager.delete_previous(bot, callback.message.chat.id)
    except:
        pass
    await manager.delete_user_msg(callback)
    decks = await get_decks(callback.message.chat.id)
    if not decks:
        various_msg = await callback.message.answer(
            "📚 **No decks yet!**\n\nCreate your first deck to start building your flashcard collection.",
            reply_markup=create_deck_keyboard,
        )
    else:
        inline_decks = await generate_inline_decks(callback.message.chat.id)
        various_msg = await callback.message.answer(
            "📚 **Here are your decks:**\n\nSelect a deck to manage or review your cards.",
            reply_markup=inline_decks,
        )
    manager.add_message(callback.message.chat.id, various_msg.message_id)
