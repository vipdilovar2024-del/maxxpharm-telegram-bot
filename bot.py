#!/usr/bin/env python3
"""
CLEAN TELEGRAM BOT - новый бот с нуля (aiogram 2.25.1)
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден!")
    exit(1)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    telegram_id = str(message.from_user.id)
    logger.info(f"CLEAN BOT: Получен /start от {telegram_id}")
    
    # ПРЯМАЯ ПРОВЕРКА ID
    if telegram_id == "697780123":
        logger.info(f"CLEAN BOT: Доступ разрешен для {telegram_id}")
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users"))
        keyboard.add(InlineKeyboardButton(text="📦 Управление заказами", callback_data="orders"))
        keyboard.add(InlineKeyboardButton(text="📊 Отчеты", callback_data="reports"))
        keyboard.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
        keyboard.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main"))
        
        await message.answer(
            "👋 Добро пожаловать, VIP Dilovar!\n\n"
            "🔐 Роль: АДМИНИСТРАТОР\n"
            "🟢 Доступ: РАЗРЕШЕН\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
        logger.info(f"CLEAN BOT: Меню отправлено {telegram_id}")
        return
    
    # Если не тот ID
    logger.info(f"CLEAN BOT: Доступ запрещен для {telegram_id}")
    await message.answer(
        "❌ Доступ запрещен. Ваш Telegram ID не найден в системе.\n"
        f"Ваш ID: {telegram_id}\n"
        "Свяжитесь с администратором для получения доступа."
    )

@dp.callback_query_handler(lambda call: True)
async def handle_callbacks(call: types.CallbackQuery):
    """Обработчик кнопок"""
    logger.info(f"CLEAN BOT: Нажата кнопка: {call.data}")
    await bot.answer_callback_query(call.id, text=f"Выбрано: {call.data}")
    await bot.send_message(call.message.chat.id, f"Вы выбрали: {call.data}")

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("CLEAN TELEGRAM BOT ЗАПУСКАЕТСЯ...")
    logger.info("=" * 50)
    
    # Установка команд
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
    ])
    
    logger.info("CLEAN BOT: Бот успешно запущен")

if __name__ == "__main__":
    try:
        main()
        executor.start_polling(dp, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("CLEAN BOT: Бот остановлен")
    except Exception as e:
        logger.error(f"CLEAN BOT: Ошибка бота: {e}")
