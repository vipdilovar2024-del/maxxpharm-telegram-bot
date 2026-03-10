#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Новый чистый бот
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

# 📦 Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv не установлен, используем системные переменные")

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI")
ADMIN_ID = os.getenv("ADMIN_ID", "697780123")

print("🔥 MAXXPHARM BOT STARTING!")
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
class MaxxpharmBot:
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
            
            # Определяем роль и создаем меню
            if str(user_id) == ADMIN_ID:
                user.role = UserRole.ADMIN
                role_emoji = "👑"
                welcome_text = f"""
{role_emoji} <b>MAXXPHARM AI-CRM</b> 🏥

👋 Добро пожаловать, <b>{user.name}</b>!

🎯 Ваша роль: <b>АДМИНИСТРАТОР</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Система готова к работе!</b>

🛠️ <b>Доступные функции:</b>
• Управление пользователями
• Статистика и аналитика
• Настройки системы
                """
                buttons = [
                    [KeyboardButton(text="👑 Управление"), KeyboardButton(text="📊 Аналитика")],
                    [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="⚙️ Настройки")]
                ]
                
            else:  # CLIENT
                role_emoji = "👤"
                welcome_text = f"""
{role_emoji} <b>MAXXPHARM AI-CRM</b> 🏥

👋 Добро пожаловать, <b>{user.name}</b>!

🎯 Ваша роль: <b>КЛИЕНТ</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Система готова к работе!</b>

📦 <b>Наши услуги:</b>
• Быстрая доставка лекарств
• Консультация фармацевта
• Отслеживание заказа 24/7
• Рецептурные препараты
                """
                buttons = [
                    [KeyboardButton(text="📦 Сделать заказ"), KeyboardButton(text="📚 Каталог")],
                    [KeyboardButton(text="📋 Мои заказы"), KeyboardButton(text="📍 Доставка")],
                    [KeyboardButton(text="📞 Поддержка"), KeyboardButton(text="ℹ️ О нас")]
                ]
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=False
            )
            
            await message.answer(welcome_text, reply_markup=keyboard)
            logger.info(f"User {user.name} ({user_id}) with role {user.role} started bot")
        
        @self.dp.message(F.text == "📦 Сделать заказ")
        async def handle_make_order(message: Message):
            """Обработка кнопки Сделать заказ"""
            await message.answer(
                "📦 <b>Создание заказа</b>\n\n"
                "🔧 Выберите способ заказа:\n\n"
                "📝 <b>Варианты:</b>\n"
                "• 📷 Отправить фото рецепта\n"
                "• 📝 Написать список лекарств\n"
                "• 🔍 Поиск по названию\n\n"
                "📞 <b>Или позвоните:</b> +992 900 000 001\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        @self.dp.message(F.text == "📚 Каталог")
        async def handle_catalog(message: Message):
            """Обработка кнопки Каталог"""
            catalog_text = """
📚 <b>Каталог товаров MAXXPHARM</b>

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
                "📭 У вас пока нет активных заказов\n\n"
                "📦 <b>Хотите сделать заказ?</b>\n"
                "Нажмите 'Сделать заказ' в меню\n\n"
                "📞 <b>Нужна помощь?</b>\n"
                "• Поддержка: @maxxpharm_support\n"
                "• Телефон: +992 900 000 001"
            )
        
        @self.dp.message(F.text == "📞 Поддержка")
        async def handle_support(message: Message):
            """Обработка кнопки Поддержка"""
            await message.answer(
                "📞 <b>Поддержка MAXXPHARM</b>\n\n"
                "📱 <b>Телефон:</b> +992 900 000 001\n"
                "💬 <b>Telegram:</b> @maxxpharm_support\n"
                "📧 <b>Email:</b> support@maxxpharm.tj\n"
                "🕐 <b>Время работы:</b> 09:00 - 21:00\n\n"
                "🏥 <b>MAXXPHARM - всегда на связи!</b>"
            )
        
        @self.dp.message(F.text == "ℹ️ О нас")
        async def handle_about(message: Message):
            """Обработка кнопки О нас"""
            await message.answer(
                "ℹ️ <b>О MAXXPHARM</b>\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b> - современная система доставки лекарств\n\n"
                "👥 <b>Наши преимущества:</b>\n"
                "• ⚡ Быстрая доставка по городу\n"
                "• 💊 Качественные лекарства\n"
                "• 📞 Круглосуточная поддержка\n"
                "• 📱 Удобное мобильное приложение\n\n"
                "📍 <b>Наши контакты:</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n"
                "• 📍 Адрес: г. Душанбе, ул. Рудаки 15\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        # Обработка неизвестных сообщений
        @self.dp.message()
        async def handle_unknown(message: Message):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "🤔 <b>Неизвестная команда</b>\n\n"
                "📋 <b>Доступные команды:</b>\n"
                "/start - Начать работу\n"
                "/admin - Админ панель\n\n"
                "🎯 <b>Используйте кнопки меню</b> для навигации\n\n"
                "📞 <b>Нужна помощь?</b> @maxxpharm_support\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        logger.info("✅ All handlers registered")
    
    async def start(self):
        """Запуск бота"""
        try:
            print("🚀 Starting MAXXPHARM Bot...")
            
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
    print("🚀 BOT MAIN FUNCTION STARTED!")
    
    try:
        # Создаем и запускаем бота
        bot = MaxxpharmBot()
        
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
    print("🔥 STARTING BOT!")
    asyncio.run(main())

print("🔥 BOT FINISHED!")
