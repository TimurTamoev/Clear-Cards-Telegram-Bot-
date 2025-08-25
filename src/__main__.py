# Main file which is runned when I need to execute the bot. It does not contain any essential
# Things, but main file is crucial as it runs the bot.

import asyncio

from bot.core import bot, dp
from bot.create_deck import cd_router
from bot.show_decks import sd_router
from bot.cancel import c_router
from bot.deck_interaction import di_router
from bot.card_interaction import ci_router
from bot.review import r_router


async def main():
    dp.include_routers(cd_router, sd_router, c_router, di_router, ci_router, r_router)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
