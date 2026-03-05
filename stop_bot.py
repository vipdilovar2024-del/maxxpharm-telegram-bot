#!/usr/bin/env python3
"""
🚨 Скрипт для принудительной остановки всех экземпляров бота
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем только необходимые модули
from aiogram import Bot

async def force_stop_bot():
    """Принудительно останавливаем все экземпляры бота"""
    
    # Получаем токен
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        return False
    
    print(f"🚨 Принудительная остановка бота...")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Создаем экземпляр бота
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"🤖 Найден бот: {bot_info.full_name} (@{bot_info.username})")
        
        # Принудительно удаляем webhook
        print("🗑️ Принудительное удаление webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url=None)
        
        # Закрываем сессию
        await bot.session.close()
        
        print("✅ Бот принудительно остановлен!")
        print("🎯 Теперь можно запускать новый экземпляр")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка остановки: {e}")
        return False

if __name__ == "__main__":
    print("🚨 ЗАПУСК СКРИПТА ПРИНУДИТЕЛЬНОЙ ОСТАНОВКИ")
    asyncio.run(force_stop_bot())
