# This file contains a managing messages class which is designed to delete messages.
# It would keep the chat history clean.
# Idk wether its really needed but for me it looks better to keep my bot clearn so thats it.

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from typing import List, Dict, Union, Optional


class ManagingMessages:
    def __init__(self):
        self.messages_: Dict[int : List[int]] = {}
        self.type_msg_: Dict[int : List[Message]] = {}

    def add_message(self, id: int, msg_id: int) -> None:
        if id not in self.messages_:
            self.messages_[id] = []
        self.messages_[id].append(msg_id)

    async def delete_msg(self, bot: Bot, id: int, msg_id: int) -> None:
        await bot.delete_message(chat_id=id, message_id=msg_id)

    async def delete_previous(
        self,
        bot: Bot,
        id: int,
    ) -> None:
        # I need to ensure that even if the user had cleaned the chat histoty,
        # The bot will not sent a bad telegram request (Deleting the message that do not exist).
        if id not in self.messages_:
            self.messages_[id] = []
            return
        if not self.messages_[id]:
            return
        try:
            await bot.delete_message(chat_id=id, message_id=self.messages_[id].pop())
        except Exception:
            pass

    async def delete_user_msg(self, union: Union[Message, CallbackQuery]):
        # Alas, I need just to try to delete a previous message without handling an exception.
        # Even if it is a bad practice.
        # In addition, I also need to send variative variable as I do not know wether
        # It is a message or a callback
        try:
            await union.delete()
        except:
            pass
        try:
            await union.message.delete()
        except:
            pass

    def add_direct_msg(self, id: int, msg: Message) -> None:
        if not id in self.type_msg_:
            self.type_msg_[id] = []
        self.type_msg_[id].append(msg)

    def prev_direct(self, id: int) -> Optional[Message]:
        if not id in self.type_msg_:
            self.type_msg_[id] = []
        if not self.type_msg_[id]:
            return None
        return self.type_msg_[id].pop()


manager = ManagingMessages()
