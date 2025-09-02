from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.sql_interactions import get_decks, get_cards

# This keyboard returns a user to their main menu
cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]
)


create_deck_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Create new deck", callback_data="create_a_new_deck"
            )
        ],
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
    ],
    resize_keyboard=True,
)


# This is a builder which is a dynamic keyboard that conatins all of the decks and has
# Callback data: call_deck_<deckname_userid_rowid>
# I do not check wether there are no decks as this exception is already handled
# In my show_decks funcion.
async def generate_inline_decks(id: str) -> InlineKeyboardMarkup:
    inline_template = InlineKeyboardBuilder()
    loaded_decks = await get_decks(id)
    for deck in loaded_decks:
        deck[1] = deck[1].split("_")
        deck[1][0] = 't'
        deck[1] = "_".join(deck[1])
        deck[2] = str(deck[2]).replace(deck[0][:8], "t")
        print(deck[1], deck[2], sep = '\n')
        if len(deck[0]) > 8:
            inline_template.button(
                text=f"{deck[0][:8]}...", callback_data=f"call_deck_{deck[1]}_{deck[2]}"
            )
        else:
            inline_template.button(
                text=f"{deck[0]}", callback_data=f"call_deck_{deck[1]}_{deck[2]}"
            )
    inline_template.button(text="Create new deck", callback_data="create_a_new_deck")
    inline_template.button(text="Cancel", callback_data="cancel")
    inline_template.adjust(1)
#    deck[1] = deck[1].replace(deck[0][:8], "t")
#    deck[2] = deck[2].replace(deck[0][:8], "t")
#    print(deck[0], deck[1], deck[2], sep='\n')
    return inline_template.as_markup(is_persistent=False)


# This keyboard is similar to the previous one but it is created in order to create an inline keyboard which includes cards.
# This function would recieve data like: <deckname_userid_rowid>
# The click on a card on this keyboard would send callback data like edit_card_<deckname_userid_rowid>_<card's rowid_front_back>
async def generate_inline_cards(deckname: str) -> InlineKeyboardMarkup:
    inline_template = InlineKeyboardBuilder()
    loaded_cards = await get_cards(deckname.replace("edit_card_", ""))
    for card in loaded_cards:
        if len(card[0]) >= 8 and len(card[1]) >= 8:
            inline_template.button(
                text=f"{card[0][:8]}... -> {card[1][:8]}...",
                callback_data=f"edit_card_{deckname}_{card[3]}",
            )
        elif len(card[1]) >= 8:
            inline_template.button(
                text=f"{card[0][:8]} -> {card[1][:8]}...",
                callback_data=f"edit_card_{deckname}_{card[3]}",
            )
        elif len(card[0]) >= 8:
            inline_template.button(
                text=f"{card[0][:8]}... -> {card[1][:8]}",
                callback_data=f"edit_card_{deckname}_{card[3]}",
            )
        else:
            inline_template.button(
                text=f"{card[0][:8]} -> {card[1][:8]}",
                callback_data=f"edit_card_{deckname}_{card[3]}",
            )
    inline_template.button(text="Cancel", callback_data="cancel")
    inline_template.adjust(1)
    return inline_template.as_markup(is_persistent=True)


async def custom_cd_end_section(len: int):
    inline_template = InlineKeyboardBuilder()
    inline_template.button(text="Back to menu", callback_data=f"cancel_section_{len}")
    inline_template.adjust(1)
    return inline_template.as_markup()


show_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Show decks", callback_data="show_decks")]
    ]
)
