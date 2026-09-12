import os
import asyncio
import aiohttp
from datetime import datetime, timezone

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = os.environ["BOT_TOKEN"]
DB_PATH = "/data/schedule.db"

PIXEL_ID = "2521755591678075"
CAPI_TOKEN = os.environ["CAPI_TOKEN"]  # токен Conversions API из Events Manager

session = AiohttpSession(timeout=300)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# ---------- META PIXEL (Conversions API) ----------

async def send_pixel_event(telegram_user_id: int, event_name: str = "Lead"):
    url = f"https://graph.facebook.com/v21.0/{PIXEL_ID}/events"
    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(datetime.now(timezone.utc).timestamp()),
            "action_source": "other",
            "user_data": {
                "external_id": str(telegram_user_id)
            },
        }],
        "access_token": CAPI_TOKEN,
    }
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(url, json=payload) as resp:
                print("Pixel:", await resp.text())
    except Exception as e:
        print("Pixel error:", e)

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

    # Сразу: текущий APK с подписью
    await message.answer_document(
        document=FSInputFile("MaxfiyTanishuvlar.apk"),
        caption="🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥"
    )

    # Событие в Meta Pixel
    asyncio.create_task(send_pixel_event(message.from_user.id, "Lead"))

    promo_caption = (
        "🇺🇿 Yangi profil ✨\n"
        "Dilnoza, 28 yosh\n"
        "«Ba'zida qaysidir odam bilan suhbat birinchi jumlada o'ziyoq yo'li topadi. "
        "Umid qilamanki, bizda ham shunday bo'ladi» 😉\n"
        "📲 Ilovani yuklab ol — birinchi xabarni yuborgan odam aynan senga aylanishing mumkin!"
    )

    # Через 15 минут: первая интрига
    await schedule_text(chat_id, "Kutimmi? 👀", 15 * 60)

    # Через 60 минут: фото с текстом + ShaxsiySahifa.apk
    await schedule_promo(chat_id, promo_caption, 60 * 60)

# ---------- ЗАПУСК ----------

async def main():
    await init_db()
    await asyncio.gather(
        dp.start_polling(bot),
        sender_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
