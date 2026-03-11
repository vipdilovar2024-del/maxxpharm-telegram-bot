#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Простой тестовый бот
"""

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 📦 Токен
BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

print("🔥 SIMPLE BOT STARTING!")
print(f"🔥 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик /start"""
    await message.answer(
        "🏥 <b>MAXXPHARM AI-CRM</b>\n\n"
        "👋 Добро пожаловать!\n\n"
        "🚀 Бот работает!\n\n"
        "📞 Телефон: +992 900 000 001\n"
        "🌐 Сайт: www.maxxpharm.tj\n\n"
        "🏥 MAXXPHARM - Ваша надежная аптека!"
    )

@dp.message()
async def echo_message(message: types.Message):
    """Эхо-обработчик"""
    await message.answer(
        f"🤔 Получил сообщение: {message.text}\n\n"
        "📋 Используйте /start для начала"
    )

async def main():
    print("🚀 Starting bot...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("🛑 Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
