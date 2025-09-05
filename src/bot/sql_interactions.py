import aiosqlite

from typing import Optional, List, Tuple

from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "databases" / "app.db"


async def init_user(id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, rowid_index INTEGER) "
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS decks (deckname_txt TEXT, user_property TEXT, rowid_index INTEGER)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS cards (deck_and_user TEXT, front TEXT, back TEXT, memory INTEGER)"
        )
        await db.execute("INSERT OR IGNORE INTO users VALUES (?, 0) ", (id, ))
        rowid_to_set = await  db.execute("SELECT rowid FROM users WHERE user_id = ?", (id, ))
        rowid_to_set = await rowid_to_set.fetchone()
        await db.execute("UPDATE 'users' SET rowid_index = ? WHERE user_id = ?", (rowid_to_set[0], id))
        await db.commit()


async def get_decks(id: str) -> Optional[List[Tuple]]:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS decks (deckname_txt TEXT, user_property TEXT, rowid_index INTEGER)"
        )
        user_row = await db.execute("SELECT rowid_index FROM users WHERE user_id = ?", (id,))
        user_row = await user_row.fetchone()
        decks = await db.execute(
            "SELECT deckname_txt, rowid_index FROM 'decks' WHERE user_property = ?",
            (user_row[0],),
        )
        decks = await decks.fetchall()
        new_decks = []
        for deck in decks:
            new_deck = []
            if "␟" in deck[0]:
                new_deck.append(deck[0].replace("␟", " "))
                new_deck.append(f"{deck[0].replace("␟", " ")[:8]}_{id}_{deck[1]}")
                new_deck.append(new_deck[1])
            if "ø" in deck[0]:
                new_deck.append(deck[0].replace("ø", "_"))
                new_deck.append(f"{deck[0][:8]}_{id}_{deck[1]}")
                new_deck.append(deck[1])
            else:
                new_deck.append(deck[0])
                new_deck.append(f"{deck[0][:8]}_{id}_{deck[1]}")
                new_deck.append(deck[1])
            new_decks.append(new_deck)
        await db.commit()
        return new_decks


async def create_deck(id: str, deck_name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT rowid_index FROM 'users' WHERE user_id = ?", (id,))
        user_rowid: Tuple[str] = await cursor.fetchone()
        if "_" in deck_name:
            deck_name = deck_name.replace("_", "ø")
        await db.execute(
            "CREATE TABLE IF NOT EXISTS decks (deckname_txt TEXT, user_property TEXT rowid_index INTEGER)"
        )
        await db.execute(
            "INSERT INTO 'decks' VALUES (?, ?, 0)", (deck_name, user_rowid[0])
        )
        tmp = await db.execute("SELECT rowid from decks WHERE deckname_txt = ? AND rowid_index= ?", (deck_name, 0))
        tmp = await tmp.fetchone()
        await db.execute("UPDATE 'decks' SET rowid_index = ? WHERE rowid = ?", (tmp[0], tmp[0]))
        await db.commit()

async def delete_deck(deck_name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        deck_rowid = deck_name.split("_")[-1]
        user_id = deck_name.split("_")[1]
        user_row = await db.execute("SELECT rowid_index FROM users WHERE user_id = ?", (user_id,))
        user_row = await user_row.fetchone()
        await db.execute("DELETE FROM 'decks' WHERE rowid_index = ? AND user_property = ?", (deck_rowid, user_row[0]))
        await db.execute("DELETE FROM 'cards' WHERE deck_and_user = ?", (f"{deck_rowid}_{user_row[0]}",))
        await db.commit()


async def get_cards(deck_name: str) -> Optional[List[Tuple]]:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS cards (deck_and_user TEXT, front TEXT, back TEXT, memory INTEGER)"
        )
        user_rowid = await db.execute(
            "SELECT rowid_index FROM 'users' WHERE user_id = ?", (deck_name.split("_")[1],)
        )
        user_rowid = await user_rowid.fetchone()
        deck_sql_row = deck_name.split("_")[-1]
        cards = await db.execute(
            "SELECT front, back, memory, rowid FROM 'cards' WHERE deck_and_user = ?",
            (f"{deck_sql_row[0]}_{user_rowid[0]}",),
        )

        cards = await cards.fetchall()
        new_cards = []
        for card in cards:
            new_card = list(card)
            if " " in card[0]:
                new_card[0] = new_card[0].replace("␟", " ")
            if " " in card[1]:
                new_card[1] = new_card[1].replace("␟", " ")
            new_cards.append(new_card)
        await db.commit()
        return new_cards


async def insert_card(deck_id: str, front: str, back: str, memory: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        user_sql_row = await db.execute("SELECT user_property FROM 'decks' WHERE rowid_index = ?", (deck_id,))
        user_sql_row = await user_sql_row.fetchone()
        await db.execute("INSERT INTO cards VALUES (?, ?, ?, ?)",(f"{deck_id}_{user_sql_row[0]}", front, back, memory))
        await db.commit()


# This function if created in order to be able to delete a card by just clicking on it.
# This function would receive callback data just like this: <userid_deckname_rowid>_cardrowid_front_back
# This function is not sql-injectable because it only uses the previous data without letting a user to type something.
# This function contains a lot of string editing so I will create some variables not to get messy.
async def delete_card(relevant_info: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        deck_name = (
            relevant_info.split("_")[0]
            + "_"
            + relevant_info.split("_")[1]
            + "_"
            + relevant_info.split("_")[2]
        )
        deck_rowid = relevant_info.split("_")[2]
        card_rowid = relevant_info.split("_")[-1]
        user_sql_row = await db.execute(
            "SELECT rowid_index FROM 'users' WHERE user_id = ?", (deck_name.split("_")[1],)
        )
        user_sql_row = await user_sql_row.fetchone()
        deck_row = await db.execute(
            "SELECT rowid from 'decks' WHERE rowid_index = ? AND user_property = ?",
            (deck_rowid, user_sql_row[0]),
        )
        deck_row = await deck_row.fetchone()
        await db.execute(
            "DELETE FROM 'cards' WHERE deck_and_user = ? AND rowid = ?",
            (f"{deck_row[0]}_{user_sql_row[0]}", card_rowid),
        )
        await db.commit()


# This would receive information <deckname_userid_rowid>
async def change_memory(info: str, card_rowid: int, new_memory: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        user_sql_row = await db.execute(
            "SELECT rowid_index FROM 'users' WHERE user_id = ?", (info.split("_")[1],)
        )
        user_sql_row = await user_sql_row.fetchone()
        deck_sql_row = info.split("_")[-1]
        await db.execute(
            "UPDATE 'cards' SET memory = ? WHERE deck_and_user = ? AND rowid = ?",
            (
                new_memory,
                f"{deck_sql_row[0]}_{user_sql_row[0]}",
                card_rowid,
            ),
        )
        await db.commit()


# <deckname_id_rowid>_card_rowid
async def get_memory(info: str, card_rowid: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        memory = await db.execute(
            "SELECT memory FROM 'cards' WHERE rowid = ?", (info.split("_")[-1],)
        )
        memory = await memory.fetchall()
        await db.commit()
        return memory[0]


async def get_card_data(deckname: str, rowid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        card = await db.execute("SELECT * FROM 'cards' WHERE rowid = ?", (rowid,))
        await db.commit()
        return await card.fetchone()


async def get_deck_name_txt_from_its_rowid(rowid: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        deckanme_txt = await db.execute("SELECT deckname_txt FROM decks WHERE rowid_index = ?", (rowid,))
        deckanme_txt = await deckanme_txt.fetchone()
        return deckanme_txt[0]
