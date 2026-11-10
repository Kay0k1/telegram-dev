"""Fixture for the GitHub Action job: one retired parameter (a warning), no errors."""
from aiogram import Bot


async def notify(bot: Bot, chat_id: int) -> None:
    await bot.send_message(chat_id=chat_id, text="Hello", reply_to_message_id=1)
