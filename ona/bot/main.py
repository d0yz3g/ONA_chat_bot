import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
import os
from ona.bot.config import TELEGRAM_TOKEN
from ona.bot.handlers import start, dialog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начать диалог")
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_routers(
        start.router,
        dialog.router,
    )

    await setup_bot_commands(bot)

    logger.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
