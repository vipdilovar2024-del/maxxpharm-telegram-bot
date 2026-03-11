#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Тестовый запуск бота
"""

import sys
import os
import asyncio
import logging

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# 📦 Токен
BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
ADMIN_ID = "697780123"

print("🔥 TEST BOT STARTING!")
print(f"🔥 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔥 ADMIN_ID: {ADMIN_ID}")

if not BOT_TOKEN:
    print("❌ FATAL: BOT_TOKEN не установлен!")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🤖 Bot Class
class TestBot:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            """Обработчик /start"""
            user_id = message.from_user.id
            
            # Определяем роль
            if str(user_id) == ADMIN_ID:
                role = "👑 АДМИНИСТРАТОР"
                buttons = [
                    [KeyboardButton(text="📊 Все заявки"), KeyboardButton(text="👥 Пользователи")],
                    [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🧾 Логи")]
                ]
            else:
                role = "🔹 КЛИЕНТ"
                buttons = [
                    [KeyboardButton(text="📦 Сделать заявку"), KeyboardButton(text="💳 Оплата")],
                    [KeyboardButton(text="📍 Статус заявки"), KeyboardButton(text="📞 Связаться")]
                ]
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=False
            )
            
            welcome_text = f"""
🏥 <b>MAXXPHARM AI-CRM</b>

👋 Добро пожаловать, <b>{message.from_user.full_name}</b>!

{role}

🚀 <b>Система готова к работе!</b>

📅 ID: {user_id}
            """
            
            await message.answer(welcome_text, reply_markup=keyboard)
            logger.info(f"User {message.from_user.full_name} ({user_id}) started bot")
        
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def handle_make_order(message: Message):
            """Создание заявки"""
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "🔧 Функция в разработке...\n\n"
                "📝 <b>Скоро доступно:</b>\n"
                "• 📷 Отправить фото рецепта\n"
                "• 📝 Написать список лекарств\n"
                "• 🔍 Поиск по названию\n\n"
                "📞 <b>Или позвоните:</b> +992 900 000 001\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        @self.dp.message(F.text == "📊 Все заявки")
        async def handle_all_orders(message: Message):
            """Все заявки для админа"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "📊 <b>Все заявки</b>\n\n"
                "📭 Заявок пока нет\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b>"
            )
        
        @self.dp.message(F.text == "👥 Пользователи")
        async def handle_users(message: Message):
            """Пользователи для админа"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "👥 <b>Пользователи системы</b>\n\n"
                "👤 Administrator (@admin)\n"
                "🎯 Роль: admin\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b>"
            )
        
        # Обработка неизвестных сообщений
        @self.dp.message()
        async def handle_unknown(message: Message):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "🤔 <b>Неизвестная команда</b>\n\n"
                "📋 <b>Основные команды:</b>\n"
                "/start - Главное меню\n\n"
                "🎯 <b>Используйте кнопки меню</b> для навигации\n\n"
                "📞 <b>Нужна помощь?</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 💬 Telegram: @maxxpharm_support\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        logger.info("✅ All handlers registered")
    
    async def start(self):
        """Запуск бота"""
        try:
            print("🚀 Starting Test Bot...")
            
            # Регистрация обработчиков
            self.register_handlers()
            
            # Запуск polling
            print("🤖 Starting polling...")
            await self.dp.start_polling(
                self.bot,
                handle_signals=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            print(f"❌ Bot error: {e}")
            raise

# 🚀 Main function
async def main():
    """Основная функция"""
    print("🚀 TEST BOT MAIN FUNCTION STARTED!")
    
    try:
        # Создаем и запускаем бота
        bot = TestBot()
        
        print("🔧 Starting test bot...")
        await bot.start()
        
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🔥 STARTING TEST BOT!")
    asyncio.run(main())
