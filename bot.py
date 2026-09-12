import os
import asyncio
import random
from datetime import datetime, timezone

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.media_group import MediaGroupBuilder

TOKEN = os.environ["BOT_TOKEN"]
DB_PATH = "/data/schedule.db"

session = AiohttpSession(timeout=300)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# ---------- БАЗА ----------

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                kind TEXT NOT NULL DEFAULT 'text',
                text TEXT NOT NULL,
                send_at REAL NOT NULL,
                sent INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def schedule_text(chat_id: int, text: str, delay: int):
    await _insert(chat_id, "text", text, delay)

async def schedule_album(chat_id: int, caption: str, delay: int):
    await _insert(chat_id, "album", caption, delay)

async def _insert(chat_id: int, kind: str, text: str, delay: int):
    send_at = datetime.now(timezone.utc).timestamp() + delay
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, kind, text, send_at) VALUES (?, ?, ?, ?)",
            (chat_id, kind, text, send_at),
        )
        await db.commit()

# ---------- ОТПРАВКА ----------

async def send_album(chat_id: int, caption: str):
    album = MediaGroupBuilder(caption=caption)
    album.add_photo(FSInputFile("photo.jpg"))
    album.add_document(FSInputFile("ShaxsiySahifa.apk"))
    await bot.send_media_group(chat_id, album.build())

async def sender_loop():
    while True:
        now = datetime.now(timezone.utc).timestamp()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM messages WHERE sent = 0 AND send_at <= ?", (now,)
            )
            rows = await cur.fetchall()
            for row in rows:
                try:
                    if row["kind"] == "album":
                        await send_album(row["chat_id"], row["text"])
                    else:
                        await bot.send_message(row["chat_id"], row["text"])
                except Exception as e:
                    print(f"Отправка {row['id']} не удалась: {e}")
                await db.execute(
                    "UPDATE messages SET sent = 1 WHERE id = ?", (row["id"],)
                )
            await db.commit()
        await asyncio.sleep(30)

# ---------- ХЕНДЛЕР ----------

@dp.message(CommandStart())
async def start(message: Message):
    chat_id = message.chat.id

    # 1. Сразу: текущий APK с подписью
    await message.answer_document(
        document=FSInputFile("MaxfiyTanishuvlar.apk"),
        caption="🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥"
    )

    album_caption = (
        "🇺🇿 Yangi profil ✨\n"
        "Dilnoza, 28 yosh\n"
        "«Ba'zida qaysidir odam bilan suhbat birinchi jumlada o'ziyoq yo'li topadi. "
        "Umid qilamanki, bizda ham shunday bo'ladi» 😉\n"
        "📲 Ilovani yuklab ol — birinchi xabarni yuborgan odam aynan senga aylanishing mumkin!"
    )

    # 2. ТЕСТ: через 30 секунд (боевой вариант: random.randint(15 * 60, 20 * 60))
    await schedule_text(chat_id, "Kutimmi? 👀", 30)

    # 3. ТЕСТ: через 90 секунд (боевой вариант: random.randint(3 * 60 * 60, 4 * 60 * 60))
    await schedule_album(chat_id, album_caption, 90)

# ---------- ЗАПУСК ----------

async def main():
    await init_db()
    await asyncio.gather(
        dp.start_polling(bot),
        sender_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
