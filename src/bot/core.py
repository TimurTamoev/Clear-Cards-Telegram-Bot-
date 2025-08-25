import os
from dotenv import load_dotenv
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.sql_interactions import init_user
from bot.keyboards import show_cards_kb
from bot.managing import manager

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("api")
if not API_KEY:
    raise ValueError("There is no 'api' variable in .env file.")

bot = Bot(token=API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()


@dp.message(CommandStart())
async def init_work(message: Message, bot: Bot):
    await init_user(message.chat.id)
    # Trying to delete a previous message in case that user types /start
    # In the middle of the conversation
    await manager.delete_previous(bot, message.chat.id)
    registration_msg = await message.answer(
        "🎉 **Welcome! You are now registered.**\n\nYou can start creating decks and cards to begin your learning journey!",
        reply_markup=show_cards_kb,
    )
