import asyncio
import logging
import os
import sqlite3
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from sol import (
    get_searches,
)
from utils import to_wav

dp = Dispatcher()


DB_PATH = "metrics.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=OFF;")
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,        -- 'request' or 'feedback'
        video_id TEXT,
        actor_name TEXT,
        hit INTEGER,                     -- 1 like, 0 dislike, NULL for requests
        event_rank INTEGER,              -- позиция (1-5) или NULL
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}!\n"
        "This app finds the celebrity whose voice matches yours."
    )
    await message.answer("Send a voice message to try it.")


@dp.message(F.content_type == ContentType.VOICE)
async def handle_voice(message: Message) -> None:
    os.makedirs("downloads", exist_ok=True)
    file = await message.bot.get_file(message.voice.file_id)
    ogg = f"downloads/{message.voice.file_unique_id}.oga"
    await message.bot.download_file(file.file_path, destination=ogg)
    wav = to_wav(ogg, message.voice.file_unique_id)

    results = get_searches(wav)  # dict preserves order

    for tmp in (ogg, wav):
        try:
            os.remove(tmp)
        except:
            pass

    for rank, (actor, info) in enumerate(results.items(), start=1):
        cursor.execute(
            "INSERT INTO metrics (event_type, video_id, actor_name, event_rank) VALUES (?, ?, ?, ?)",
            ("request", info["path"], actor, rank),
        )
    conn.commit()

    for rank, (actor, info) in enumerate(results.items(), start=1):
        path = os.path.join("wav", info["id"], info["path"], f"{info['num']}.wav")
        if os.path.exists(path):
            url = f"https://youtu.be/{info['path']}"
            caption = f'{actor} — score {info["score"]:.3f}\n<a href="{url}">Watch</a>'
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👍 Like", callback_data=f"fb|{info['path']}|{actor}|1"
                        ),
                        InlineKeyboardButton(
                            text="👎 Dislike",
                            callback_data=f"fb|{info['path']}|{actor}|0",
                        ),
                    ]
                ]
            )
            audio = FSInputFile(path=path, filename=f"{actor}.wav")
            await message.answer_audio(
                audio=audio, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb
            )
        else:
            await message.answer(f"File not found for {actor}")


@dp.callback_query(F.data.startswith("fb"))
async def handle_feedback(q: CallbackQuery) -> None:
    _, vid, actor, hit_str = q.data.split("|")
    hit = int(hit_str)
    cursor.execute(
        "INSERT INTO metrics (event_type, video_id, actor_name, hit) VALUES (?, ?, ?, ?)",
        ("feedback", vid, actor, hit),
    )
    conn.commit()
    await q.answer("Thanks!")


@dp.message(Command("metrics"))
async def show_metrics(message: Message) -> None:
    cursor.execute(
        """
        SELECT
          COUNT(CASE WHEN event_type='request' THEN 1 END) as impressions,
          COUNT(CASE WHEN event_type='feedback' THEN 1 END) as feedbacks,
          SUM(CASE WHEN event_type='feedback' AND hit=1 THEN 1 ELSE 0 END) as likes,
          SUM(CASE WHEN event_type='feedback' AND hit=0 THEN 1 ELSE 0 END) as dislikes,
          AVG(CASE WHEN event_type='request' THEN event_rank END) as avg_rank
        FROM metrics
        """
    )
    row = cursor.fetchone()
    impressions, feedbacks, likes, dislikes, avg_rank = row
    ctr = likes / (likes + dislikes) if (likes + dislikes) else 0
    bounce = (impressions - feedbacks) / impressions if impressions else 0
    text = (
        f"Total Impressions: {impressions}\n"
        f"Feedbacks: {feedbacks}\n"
        f"CTR: {ctr:.1%}\n"
        f"Likes/Dislikes: {likes}/{dislikes}\n"
        f"Bounce Rate: {bounce:.1%}\n"
        f"Average Rank: {avg_rank:.2f}"
    )
    await message.answer(text)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

