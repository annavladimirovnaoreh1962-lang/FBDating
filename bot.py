import os
import asyncio
import random
from datetime import datetime, timezone

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession

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

async def schedule_promo(chat_id: int, caption: str, delay: int):
    await _insert(chat_id, "promo", caption, delay)

async def _insert(chat_id: int, kind: str, text: str, delay: int):
    send_at = datetime.now(timezone.utc).timestamp() + delay
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, kind, text, send_at) VALUES (?, ?, ?, ?)",
            (chat_id, kind, text, send_at),
        )
        await db.commit()

# ---------- ОТПРАВКА ----------

async def send_promo(chat_id: int, caption: str):
    # 1. Фото с текстом
    await bot.send_photo(chat_id, photo=FSInputFile("photo.jpg"), caption=caption)
    # 2. Сразу под ним — сам APK
    await bot.send_document(chat_id, document=FSInputFile("ShaxsiySahifa.apk"))

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
                    if row["kind"] == "promo":
                        await send_promo(row["chat_id"], row["text"])
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

    await message.answer_document(
        document=FSInputFile("MaxfiyTanishuvlar.apk"),
        caption="🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥"
    )

    promo_caption = (
        "🇺🇿 Yangi profil ✨\n"
        "Dilnoza, 28 yosh\n"
        "«Ba'zida qaysidir odam bilan suhbat birinchi jumlada o'ziyoq yo'li topadi. "
        "Umid qilamanki, bizda ham shunday bo'ladi» 😉\n"
        "📲 Ilovani yuklab ol — birinchi xabarni yuborgan odam aynan senga aylanishing mumkin!"
    )

    # ТЕСТ: 30 и 90 секунд
    await schedule_text(chat_id, "Kutimmi? 👀", 30)
    await schedule_promo(chat_id, promo_caption, 90)
    # БОЕВОЙ ВАРИАНТ после теста:
    # await schedule_text(chat_id, "Kutimmi? 👀", random.randint(15 * 60, 20 * 60))
    # await schedule_promo(chat_id, promo_caption, random.randint(3 * 60 * 60, 4 * 60 * 60))

# ---------- ЗАПУСК ----------

async def main():
    await init_db()
    await asyncio.gather(
        dp.start_polling(bot),
        sender_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
