import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from sol import get_searches
from utils import to_wav

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(F.content_type == ContentType.VOICE)
async def voice_handler(message: Message) -> None:
    os.makedirs("downloads", exist_ok=True)

    file = await message.bot.get_file(message.voice.file_id)

    path = f"downloads/{message.voice.file_unique_id}.ogg"

    await message.bot.download_file(file.file_path, destination=path)
    path_wav = to_wav(path, message.voice.file_unique_id)
    res = get_searches(path_wav)

    if os.path.exists(path_wav):
        os.remove(path_wav)
    res = str(res)
    await message.answer(res)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
