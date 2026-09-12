import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart

TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer_document(
        document=FSInputFile("app.apk"),
        caption="🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
