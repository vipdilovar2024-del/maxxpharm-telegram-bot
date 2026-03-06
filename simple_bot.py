#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Простая рабочая версия
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🌐 Web imports для health check
from aiohttp import web

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "697780123")  # Строка!

print("🔥 SIMPLE BOT STARTING!")
print(f"🔥 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔥 ADMIN_ID: {ADMIN_ID}")

if not BOT_TOKEN:
    print("❌ FATAL: BOT_TOKEN не установлен!")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🌍 Глобальные переменные
bot_instance = None

# 🎛️ Enums
class UserRole:
    ADMIN = "admin"
    CLIENT = "client"

# 📊 Data Models
class User:
    def __init__(self, telegram_id: int, name: str, username: str, role: str = "client"):
        self.telegram_id = telegram_id
        self.name = name
        self.username = username
        self.role = role
        self.created_at = datetime.now()

# In-memory storage
users_db = {}

# 🤖 Bot Class
class SimpleMaxxpharmBot:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        self.app = web.Application()
        self.setup_web_routes()
    
    def setup_web_routes(self):
        """Настройка web маршрутов для health check"""
        async def health_check(request):
            return web.Response(text="OK", status=200)
        
        self.app.router.add_get('/health', health_check)
    
    async def start_web_server(self):
        """Запуск web сервера для health check"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 10000)
        await site.start()
        print("🌐 Web server started on port 10000")
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, state: FSMContext):
            """Обработчик /start"""
            await state.clear()
            
            user_id = message.from_user.id
            
            # Создаем или получаем пользователя
            if user_id not in users_db:
                users_db[user_id] = User(
                    telegram_id=user_id,
                    name=message.from_user.full_name,
                    username=message.from_user.username or "unknown",
                    role="client"
                )
            
            user = users_db[user_id]
            
            # Определяем роль
            if str(user_id) == ADMIN_ID:
                user.role = UserRole.ADMIN
                role_emoji = "👑"
                welcome_text = f"""
{role_emoji} <b>MAXXPHARM AI-CRM</b> 🏥

👋 Добро пожаловать, <b>{user.name}</b>!

🎯 Ваша роль: <b>АДМИНИСТРАТОР</b>
📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}

🚀 <b>Система готова к работе!</b>

🛠️ <b>Доступные команды:</b>
/start - Перезапуск бота
/admin - Админ панель
                """
                buttons = [
                    [KeyboardButton(text="👑 Админ панель")],
                    [KeyboardButton(text="📊 Статистика")],
                    [KeyboardButton(text="👥 Пользователи")]
                ]
            else:
                role_emoji = "👤"
                welcome_text = f"""
{role_emoji} <b>MAXXPHARM AI-CRM</b> 🏥

👋 Добро пожаловать, <b>{user.name}</b>!

🎯 Ваша роль: <b>КЛИЕНТ</b>
📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}

🚀 <b>Система готова к работе!</b>

📦 <b>Что вы можете делать:</b>
• Создавать заказы
• Просматривать каталог
• Отслеживать deliveries
                """
                buttons = [
                    [KeyboardButton(text="📦 Сделать заказ")],
                    [KeyboardButton(text="📚 Каталог товаров")],
                    [KeyboardButton(text="📋 Мои заказы")]
                ]
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=False
            )
            
            await message.answer(welcome_text, reply_markup=keyboard)
            logger.info(f"User {user.name} ({user_id}) started bot")
        
        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message):
            """Админ панель"""
            user_id = message.from_user.id
            
            if str(user_id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="👊 Управление")],
                    [KeyboardButton(text="📊 Статистика")],
                    [KeyboardButton(text="👥 Пользователи")],
                    [KeyboardButton(text="🔙 Назад")]
                ],
                resize_keyboard=True
            )
            
            await message.answer(
                "👑 <b>Админ панель MAXXPHARM</b>\n\n"
                "Выберите действие:",
                reply_markup=keyboard
            )
        
        @self.dp.message(F.text == "📦 Сделать заказ")
        async def handle_make_order(message: Message):
            """Обработка кнопки Сделать заказ"""
            await message.answer(
                "📦 <b>Создание заказа</b>\n\n"
                "🔧 Функция в разработке...\n"
                "Скоро вы сможете:\n"
                "• Выбрать лекарства\n"
                "• Указать адрес\n"
                "• Оплатить заказ\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        @self.dp.message(F.text == "📚 Каталог товаров")
        async def handle_catalog(message: Message):
            """Обработка кнопки Каталог"""
            catalog_text = """
📚 <b>Каталог товаров MAXXPHARM</b>

📦 <b>Популярные лекарства:</b>

🌡️ <b>Против температуры:</b>
• Парацетамол - 50 сомони
• Ибупрофен - 80 сомони
• Аспирин - 45 сомони

🦠 <b>Противовирусные:</b>
• Арбидол - 300 сомони
• Кагоцел - 250 сомони
• Ремантадин - 180 сомони

💪 <b>Витамины:</b>
• Витамин C - 120 сомони
• Витамин D - 200 сомони
• Комплекс витаминов - 350 сомони

🏥 <b>MAXXPHARM - Все лекарства всегда в наличии!</b>
            """
            
            await message.answer(catalog_text)
        
        @self.dp.message(F.text == "📋 Мои заказы")
        async def handle_my_orders(message: Message):
            """Обработка кнопки Мои заказы"""
            await message.answer(
                "📋 <b>Мои заказы</b>\n\n"
                "📭 У вас пока нет заказов\n\n"
                "📦 Хотите сделать заказ?\n"
                "Нажмите 'Сделать заказ' в меню"
            )
        
        @self.dp.message(F.text == "👑 Админ панель")
        async def handle_admin_panel(message: Message):
            """Обработка кнопки Админ панель"""
            user_id = message.from_user.id
            
            if str(user_id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            stats_text = f"""
👑 <b>Админ панель MAXXPHARM</b>

📊 <b>Статистика системы:</b>
👥 Пользователей: {len(users_db)}
🤖 Бот онлайн: ✅
🕐 Время работы: {datetime.now().strftime('%H:%M:%S')}

🛠️ <b>Функции администратора:</b>
• Управление пользователями
• Просмотр статистики
• Настройки бота

🏥 <b>MAXXPHARM AI-CRM работает отлично!</b>
            """
            
            await message.answer(stats_text)
        
        # Обработка неизвестных сообщений
        @self.dp.message()
        async def handle_unknown(message: Message):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "🤔 <b>Неизвестная команда</b>\n\n"
                "Используйте кнопки меню или команды:\n"
                "/start - Начать работу\n"
                "/admin - Админ панель\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        logger.info("✅ All handlers registered")
    
    async def start(self):
        """Запуск бота"""
        try:
            print("🚀 Starting Simple MAXXPHARM Bot...")
            
            # Регистрация обработчиков
            self.register_handlers()
            
            # Запуск web сервера
            await self.start_web_server()
            
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
    print("🚀 SIMPLE BOT MAIN FUNCTION STARTED!")
    
    try:
        # Создаем и запускаем бота
        bot = SimpleMaxxpharmBot()
        
        print("🔧 Starting bot...")
        await bot.start()
        
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🔥 STARTING SIMPLE BOT!")
    asyncio.run(main())

# 🚀 Запускаем напрямую для Render
print("🔥 DIRECT START FOR RENDER!")
asyncio.run(main())

print("🔥 BOT FINISHED!")
