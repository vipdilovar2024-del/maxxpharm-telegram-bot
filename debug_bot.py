#!/usr/bin/env python3
"""
🔍 DEBUG BOT - Простая проверка работы Telegram бота
"""

import os
import asyncio
import logging
from aiogram import Bot

# 📊 Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7759398408:AAE8sTBDYO9cf9tjbCu6ZcrvPQxy9j28KGI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot():
    """Тестирование работы бота"""
    print("🔍 DEBUG: Testing bot connection...")
    print(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
    print(f"👤 Admin ID: {ADMIN_ID}")
    
    try:
        # Инициализация бота
        bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
        
        # Проверка соединения
        bot_info = await bot.get_me()
        print(f"✅ Bot info: {bot_info.full_name} (@{bot_info.username})")
        
        # Тестовое сообщение админу
        await bot.send_message(
            ADMIN_ID,
            "🔍 <b>DEBUG TEST</b>\n\n"
            "🤖 Бот успешно запущен!\n"
            f"📅 Время: {asyncio.get_event_loop().time()}\n"
            "✅ Соединение с Telegram API работает!"
        )
        print("✅ Test message sent successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Bot test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting debug bot test...")
    
    try:
        result = asyncio.run(test_bot())
        if result:
            print("✅ Bot test PASSED!")
        else:
            print("❌ Bot test FAILED!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
