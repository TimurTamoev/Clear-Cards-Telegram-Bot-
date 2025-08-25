from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import show_cards_kb
from bot.managing import manager

c_router = Router()


@c_router.message(F.text == "**cancel**")
async def return_to_menu(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await manager.delete_previous(bot, message.chat.id)
    await manager.delete_user_msg(message)
    return_msg = await message.answer(
        "🏠 **Welcome back to the main menu!**\n\nWhat would you like to do next?",
        reply_markup=show_cards_kb,
    )
    manager.add_message(message.chat.id, return_msg.message_id)


@c_router.callback_query(F.data == "cancel")
async def cancel_inline(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    await state.clear()
    success_msg = await callback.message.answer(
        "🏠 **Welcome back to the main menu!**\n\nWhat would you like to do next?",
        reply_markup=show_cards_kb,
    )
    manager.add_message(callback.message.chat.id, success_msg.message_id)
