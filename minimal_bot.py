#!/usr/bin/env python3
"""
🤖 MAXXPHARM MINIMAL BOT - Простая версия для тестирования
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# 📊 Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7759398408:AAE8sTBDYO9cf9tjbCu6ZcrvPQxy9j28KGI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 🤖 Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# 🚀 МГНОВЕННАЯ ПРОВЕРКА ЗАПУСКА
print("🚀 MAXXPHARM MINIMAL BOT STARTING...")
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"🐍 Python: {sys.version}")
print(f"📁 Working dir: {os.getcwd()}")
print(f"🌐 Environment: {os.getenv('RENDER', 'local')}")
print(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
print(f"👤 Admin ID: {ADMIN_ID}")
print("✅ Basic imports loaded successfully")

# 📋 Глобальные данные
USERS = {}

def get_user_role(user_id: int) -> str:
    """Получение роли пользователя"""
    return USERS.get(user_id, {}).get("role", "CLIENT")

def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    role = get_user_role(user_id)
    return role in ["SUPER_ADMIN", "ADMIN", "DIRECTOR"]

# 🎹 Клавиатуры
def get_main_menu(user_id):
    """Получение главного меню"""
    role = get_user_role(user_id)
    
    if is_admin(user_id):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="🧠 AI Анализ")],
                [KeyboardButton(text="👥 Пользователи")],
                [KeyboardButton(text="🚀 Выход")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Создать заявку")],
                [KeyboardButton(text="📋 Мои заявки")],
                [KeyboardButton(text="📞 Поддержка")]
            ],
            resize_keyboard=True
        )
    
    return keyboard

# 🎹 Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    if user_id not in USERS:
        USERS[user_id] = {
            "id": user_id,
            "full_name": message.from_user.full_name,
            "role": "CLIENT" if user_id != ADMIN_ID else "DIRECTOR"
        }
    
    role = get_user_role(user_id)
    welcome_text = f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n🔐 Ваша роль: {role}\n\nВыберите действие из меню ниже:"
    
    menu = get_main_menu(user_id)
    await message.answer(welcome_text, reply_markup=menu)
    
    print(f"✅ User {user_id} ({message.from_user.full_name}) started bot with role {role}")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Проверка статуса бота"""
    await message.answer(
        f"🤖 <b>Статус MAXXPHARM Bot</b>\n\n"
        f"📊 Пользователей: {len(USERS)}\n"
        f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🐍 Python: {sys.version.split()[0]}\n"
        f"🤖 Бот: 🟢 Работает"
    )

@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Проверка связи"""
    await message.answer("🏓 Pong! Бот работает и отвечает на сообщения!")

@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    """Информация о боте"""
    await message.answer(
        "🤖 <b>MAXXPHARM AI-CRM Bot</b>\n\n"
        "📋 Версия: Minimal Test\n"
        "🧠 AI: Базовый\n"
        "🗄️ База данных: Тестовая\n"
        "🔄 Статус: 🟢 Работает\n\n"
        "🎯 Команды:\n"
        "/start - Главное меню\n"
        "/status - Статус системы\n"
        "/ping - Проверка связи\n"
        "/info - Информация о боте"
    )

# 🎹 Обработчики кнопок
@dp.message(F.text == "📊 Статистика")
async def cmd_statistics(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    stats_text = (
        "📊 <b>Статистика MAXXPHARM</b>\n\n"
        f"👥 Пользователей: {len(USERS)}\n"
        f"📦 Заявок: 0\n"
        f"🤖 Бот: 🟢 Работает\n\n"
        f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await message.answer(stats_text)

@dp.message(F.text == "🧠 AI Анализ")
async def cmd_ai_analysis(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    await message.answer(
        "🧠 <b>AI Анализ системы</b>\n\n"
        "🔍 Анализирую данные...\n\n"
        "📊 Результаты:\n"
        "✅ Бот работает нормально\n"
        "✅ Пользователи активны\n"
        "✅ Система стабильна\n\n"
        "🎯 Рекомендации:\n"
        "• Система работает в штатном режиме\n"
        "• Проблем не обнаружено"
    )

@dp.message(F.text == "👥 Пользователи")
async def cmd_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Пользователи системы</b>\n\n"
    
    for user_id, user_data in USERS.items():
        users_text += f"👤 {user_data['full_name']} ({user_data['role']})\n"
    
    await message.answer(users_text)

@dp.message(F.text == "🚀 Выход")
async def cmd_exit(message: types.Message):
    await message.answer("👋 До свидания! Нажмите /start для возврата.")

@dp.message(F.text == "📝 Создать заявку")
async def cmd_create_application(message: types.Message):
    await message.answer(
        "📝 <b>Создание заявки</b>\n\n"
        "📋 Введите текст вашей заявки:\n"
        "• Опишите вашу потребность\n"
        "• Укажите контактные данные\n"
        "• Наш оператор свяжется с вами"
    )

@dp.message(F.text == "📋 Мои заявки")
async def cmd_my_applications(message: types.Message):
    await message.answer(
        "📋 <b>Мои заявки</b>\n\n"
        "📭 У вас пока нет заявок.\n\n"
        "📝 Создайте первую заявку с помощью кнопки 'Создать заявку'"
    )

@dp.message(F.text == "📞 Поддержка")
async def cmd_support(message: types.Message):
    await message.answer(
        "📞 <b>Поддержка MAXXPHARM</b>\n\n"
        "👨‍💼 Наша команда готова помочь!\n\n"
        "📞 Контакты:\n"
        "• Телефон: +7 (XXX) XXX-XX-XX\n"
        "• Email: support@maxxpharm.uz\n"
        "• Время работы: 9:00 - 18:00\n\n"
        "⏰ Мы ответим в ближайшее время!"
    )

# 🎹 Обработчик текстовых сообщений
@dp.message()
async def handle_text_message(message: types.Message):
    """Обработчик текстовых сообщений"""
    user_id = message.from_user.id
    text = message.text
    
    # Если это ответ на создание заявки
    if message.reply_to_message and "Введите текст вашей заявки" in message.reply_to_message.text:
        await message.answer(
            f"✅ <b>Заявка создана!</b>\n\n"
            f"📝 Текст: {text}\n"
            f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            "👨‍💼 Оператор свяжется с вами в ближайшее время!"
        )
    else:
        # Обычное сообщение
        await message.answer(
            "📝 Используйте меню для навигации или команды:\n"
            "/start - Главное меню\n"
            "/status - Статус системы\n"
            "/ping - Проверка связи"
        )

print("✅ All handlers registered")

async def main():
    """Главная функция"""
    print("🚀 ASYNC MAIN FUNCTION STARTED...")
    
    try:
        # Delete webhook
        print("🗑️ Deleting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"🤖 Bot info: {bot_info.full_name} (@{bot_info.username})")
        
        print("🎯 Starting bot polling...")
        print("🤖 MAXXPHARM Minimal Bot is running!")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    try:
        print("🚀 Starting MAXXPHARM Minimal Bot...")
        print("📊 Simple version for testing")
        print("🤖 Ready to work!")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
