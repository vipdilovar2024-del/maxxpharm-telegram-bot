#!/usr/bin/env python3
"""
CLEAN TELEGRAM BOT - новый бот с нуля
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден!")
    exit(1)

# Создаем роутер
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    telegram_id = str(message.from_user.id)
    logger.info(f"CLEAN BOT: Получен /start от {telegram_id}")
    
    # ПРЯМАЯ ПРОВЕРКА ID
    if telegram_id == "697780123":
        logger.info(f"CLEAN BOT: Доступ разрешен для {telegram_id}")
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users")],
            [InlineKeyboardButton(text="📦 Управление заказами", callback_data="orders")],
            [InlineKeyboardButton(text="📊 Отчеты", callback_data="reports")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main")]
        ])
        
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

@router.callback_query(F.data)
async def handle_callbacks(callback: F.CallbackQuery):
    """Обработчик кнопок"""
    logger.info(f"CLEAN BOT: Нажата кнопка: {callback.data}")
    await callback.answer(f"Выбрано: {callback.data}")
    await callback.message.answer(f"Вы выбрали: {callback.data}")

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("CLEAN TELEGRAM BOT ЗАПУСКАЕТСЯ...")
    logger.info("=" * 50)
    
    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Инициализация диспетчера
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # Установка команд
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Запустить бота"),
    ]
    await bot.set_my_commands(commands)
    
    logger.info("CLEAN BOT: Бот успешно запущен")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("CLEAN BOT: Бот остановлен")
    except Exception as e:
        logger.error(f"CLEAN BOT: Ошибка бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("CLEAN BOT: Бот остановлен")
    except Exception as e:
        print(f"CLEAN BOT: Ошибка запуска: {e}")
