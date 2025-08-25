from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.sql_interactions import (
    delete_deck,
    get_cards,
    get_deck_name_txt_from_its_rowid
)

from bot.keyboards import generate_inline_cards, show_cards_kb
from bot.managing import manager

di_router = Router()



@di_router.callback_query(F.data.startswith("call_deck_"))
async def click_on_deck(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    await manager.delete_user_msg(callback)
    deck_inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Review",
                    callback_data=f"review_deck_{callback.data.replace("call_deck_", "")}",
                )  # callback: review_deck_<deckname_userid_rowid>
            ],
            [
                InlineKeyboardButton(
                    text="Create card",
                    callback_data=f"create_card_{callback.data.replace("call_deck_", "")}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Edit",
                    callback_data=f"edit_deck_{callback.data.replace("call_deck_", "")}",
                ),  # edit_deck_<deckname_userid_rowid>
                InlineKeyboardButton(
                    text="Delete",
                    callback_data=f"delete_deck_{callback.data.replace("call_deck_", "")}",
                ),  # delete_deck_<deckname_userid_rowid>
            ],
            [
                InlineKeyboardButton(text="Cancel", callback_data="cancel")
            ],  # this callback is already handled
        ]
    )
    deckanme = await get_deck_name_txt_from_its_rowid(int(callback.data.split("_")[4]))
    #deck_inline_msg = await callback.message.answer(
    #    f"{callback.data.split("_")[2].replace("␟", " ")}:", reply_markup=deck_inline
    #)
    deck_inline_msg = await callback.message.answer(text=f"{deckanme.replace("␟", " ").replace("ø", "_")}:", reply_markup=deck_inline)
    manager.add_message(callback.message.chat.id, deck_inline_msg.message_id)


@di_router.callback_query(F.data.startswith("delete_deck_"))
async def impl_delete_deck(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    await delete_deck(callback.data.replace("delete_deck_", ""))
    deleting_msg = await callback.message.answer(
        "🗑️ **Deck deleted successfully!**\n\nThe deck and all its cards have been removed.",
        reply_markup=show_cards_kb,
    )
    manager.add_message(callback.message.chat.id, deleting_msg.message_id)


@di_router.callback_query(F.data.startswith("edit_deck_"))
async def edit_deck(callback: CallbackQuery, bot: Bot):
    await manager.delete_previous(bot, callback.message.chat.id)
    cards = await get_cards(callback.data.replace("edit_deck_", ""))
    if not cards:
        special_card_create_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Create card",
                        callback_data=f"create_card_{callback.data.replace("edit_deck_", "")}",
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
            ]
        )
        no_cards_msg = await callback.message.answer(
            "📝 **No cards in this deck yet!**\n\nCreate your first card to start building your knowledge.",
            reply_markup=special_card_create_kb,
        )
        manager.add_message(callback.message.chat.id, no_cards_msg.message_id)
    else:
        cards_inline = await generate_inline_cards(
            callback.data.replace("edit_deck_", "")
        )
        cards_msg = await callback.message.answer(
            "📚 **Here are your cards:**\n\nSelect a card to edit or delete it.",
            reply_markup=cards_inline,
        )
        manager.add_message(callback.message.chat.id, cards_msg.message_id)
