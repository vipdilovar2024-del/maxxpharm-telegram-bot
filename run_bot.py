#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Запуск бота локально
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🌐 Web imports для health check
from aiohttp import web

# 📦 Прямая установка токена
BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
ADMIN_ID = "697780123"

print("🔥 MAXXPHARM BOT STARTING!")
print(f"🔥 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔥 ADMIN_ID: {ADMIN_ID}")

if not BOT_TOKEN:
    print("❌ FATAL: BOT_TOKEN не установлен!")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 🎛 Enums
class OrderStatus(Enum):
    CREATED = "📝 Заявка создана"
    AWAITING_PAYMENT = "💳 Ожидает оплаты"
    PAID = "✅ Заявка принята"
    PROCESSING = "🔄 В обработке (сборка)"
    READY = "📦 Готово"
    CHECKING = "🔍 На проверке"
    DELIVERING = "🚚 В пути"
    DELIVERED = "✅ Доставлено"

class UserRole(Enum):
    CLIENT = "🔹 Клиент"
    OPERATOR = "🔹 Оператор"
    COLLECTOR = "🔹 Сборщик"
    CHECKER = "🔹 Проверщик"
    COURIER = "🔹 Курьер"
    ADMIN = "👑 Администратор"
    DIRECTOR = "📊 Директор"

# 📊 Data Models
class Order:
    def __init__(self, order_id: str, client_name: str, client_phone: str, 
                 items: List[str], total: float, status: OrderStatus, 
                 created_at: datetime = None):
        self.order_id = order_id
        self.client_name = client_name
        self.client_phone = client_phone
        self.items = items
        self.total = total
        self.status = status
        self.created_at = created_at or datetime.now()
        self.payment_confirmed = False
        self.collector_id = None
        self.checker_id = None
        self.courier_id = None

class User:
    def __init__(self, telegram_id: int, name: str, username: str, role: str):
        self.telegram_id = telegram_id
        self.name = name
        self.username = username
        self.role = role
        self.created_at = datetime.now()

# 🗄️ In-memory storage
users_db: Dict[int, User] = {}
orders_db: Dict[str, Order] = {}
order_counter = 1

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
        
        # Инициализация администратора
        if ADMIN_ID not in users_db:
            users_db[int(ADMIN_ID)] = User(
                telegram_id=int(ADMIN_ID),
                name="Administrator",
                username="admin",
                role="admin"
            )
    
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
    
    def get_user_role_keyboard(self, user_role: str) -> ReplyKeyboardMarkup:
        """Получить клавиатуру в зависимости от роли"""
        
        if user_role == "admin":
            buttons = [
                [KeyboardButton(text="📊 Все заявки"), KeyboardButton(text="📈 Аналитика")],
                [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🎛 Роли")],
                [KeyboardButton(text="🧾 Логи"), KeyboardButton(text="⚙️ Настройки")]
            ]
        elif user_role == "director":
            buttons = [
                [KeyboardButton(text="📊 Дашборд"), KeyboardButton(text="📈 Статистика")],
                [KeyboardButton(text="💰 Финансы"), KeyboardButton(text="📋 Отчеты")],
                [KeyboardButton(text="🔄 Эффективность"), KeyboardButton(text="⏰ Время работы")]
            ]
        elif user_role == "operator":
            buttons = [
                [KeyboardButton(text="📥 Новые заявки"), KeyboardButton(text="📦 В работе")],
                [KeyboardButton(text="💳 Оплата"), KeyboardButton(text="✅ Принять")],
                [KeyboardButton(text="❌ Отказать"), KeyboardButton(text="📊 Статистика")]
            ]
        elif user_role == "collector":
            buttons = [
                [KeyboardButton(text="📦 В сборке"), KeyboardButton(text="🔄 В обработке")],
                [KeyboardButton(text="✅ Готово"), KeyboardButton(text="❌ Проблема")],
                [KeyboardButton(text="📋 Список"), KeyboardButton(text="📊 Статистика")]
            ]
        elif user_role == "checker":
            buttons = [
                [KeyboardButton(text="🔍 На проверке"), KeyboardButton(text="✅ Подтвердить")],
                [KeyboardButton(text="❌ Вернуть"), KeyboardButton(text="📋 История")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🔄 В обработке")]
            ]
        elif user_role == "courier":
            buttons = [
                [KeyboardButton(text="🚚 В пути"), KeyboardButton(text="📍 Маршрут")],
                [KeyboardButton(text="✅ Доставлено"), KeyboardButton(text="📞 Связаться")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🗺️ Карта")]
            ]
        else:  # client
            buttons = [
                [KeyboardButton(text="📦 Сделать заявку"), KeyboardButton(text="💳 Оплата")],
                [KeyboardButton(text="📍 Статус заявки"), KeyboardButton(text="📞 Связаться")],
                [KeyboardButton(text="📚 Каталог"), KeyboardButton(text="ℹ️ О нас")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, state: FSMContext):
            """Обработчик /start"""
            await state.clear()
            
            user_id = message.from_user.id
            
            # Создаем пользователя если нет
            if user_id not in users_db:
                users_db[user_id] = User(
                    telegram_id=user_id,
                    name=message.from_user.full_name,
                    username=message.from_user.username or "unknown",
                    role="client"
                )
            
            user = users_db[user_id]
            
            # Определяем роль
            role_display = UserRole.CLIENT.value
            if str(user_id) == ADMIN_ID:
                user.role = "admin"
                role_display = UserRole.ADMIN.value
            
            welcome_text = f"""
🏥 <b>MAXXPHARM AI-CRM</b>

👋 Добро пожаловать, <b>{user.name}</b>!

{role_display}

📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Система готова к работе!</b>
            """
            
            keyboard = self.get_user_role_keyboard(user.role)
            
            await message.answer(welcome_text, reply_markup=keyboard)
            logger.info(f"User {user.name} ({user_id}) started bot")
        
        # 📝 Обработчики для клиентов
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def handle_create_order(message: Message, state: FSMContext):
            """Создание заявки"""
            await state.set_state("creating_order")
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📝 Текстом", callback_data="order_text"),
                        InlineKeyboardButton(text="📷 Фото рецепта", callback_data="order_photo"),
                        InlineKeyboardButton(text="🎤 Голосом", callback_data="order_voice")
                    ]
                ]
            )
            
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "📝 Выберите способ оформления заявки:",
                reply_markup=keyboard
            )
        
        @self.dp.message(F.text == "💳 Оплата")
        async def handle_payment(message: Message, state: FSMContext):
            """Оплата заявки"""
            await message.answer(
                "💳 <b>Оплата заявки</b>\n\n"
                "💰 <b>Реквизиты:</b>\n"
                "📱 Карта: 1234 5678 9012 3456\n"
                "🏦 Банк: Евросеть, получатель: ООО МАКСФАРМ\n\n"
                "📸 <b>После оплаты отправьте:</b>\n"
                "• Фото чека\n"
                "• Или номер операции\n\n"
                "🏥 <b>MAXXPHARM - Спасибо за доверие!</b>"
            )
        
        @self.dp.message(F.text == "📍 Статус заявки")
        async def handle_order_status(message: Message, state: FSMContext):
            """Проверка статуса заявки"""
            await message.answer(
                "📍 <b>Статус заявки</b>\n\n"
                "📭 У вас пока нет активных заявок\n\n"
                "📦 <b>Хотите создать заявку?</b>\n"
                "Нажмите 'Сделать заявку' в меню"
            )
        
        @self.dp.message(F.text == "📞 Связаться")
        async def handle_contact(message: Message, state: FSMContext):
            """Связь с менеджером"""
            await message.answer(
                "📞 <b>Связь с MAXXPHARM</b>\n\n"
                "👥 <b>Наши менеджеры:</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 📞 Телефон: +992 900 000 002\n"
                "• 💬 Telegram: @maxxpharm_support\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n"
                "• 🕐 Время работы: 09:00 - 21:00\n\n"
                "🏥 <b>MAXXPHARM - Всегда рады помочь!</b>"
            )
        
        @self.dp.message(F.text == "📚 Каталог")
        async def handle_catalog(message: Message, state: FSMContext):
            """Каталог товаров"""
            catalog_text = """
📚 <b>Каталог MAXXPHARM</b>

🌡️ <b>Против температуры и боли:</b>
• Парацетамол - 45 сомони
• Ибупрофен - 80 сомони
• Аспирин - 35 сомони
• Анальгин - 25 сомони

🦠 <b>Противовирусные:</b>
• Арбидол - 250 сомони
• Кагоцел - 200 сомони
• Ремантадин - 150 сомони
• Осельтамивир - 300 сомони

💊 <b>Сердечно-сосудистые:</b>
• Лозартан - 120 сомони
• Эналаприл - 90 сомони
• Амлодипин - 85 сомони

💪 <b>Витамины и БАДы:</b>
• Витамин D3 - 60 сомони
• Витамин C - 40 сомони
• Омега-3 - 150 сомони
• Кальций D3 - 80 сомони

🌿 <b>Травы и фитопрепараты:</b>
• Ромашка - 30 сомони
• Шалфей - 25 сомони
• Эхинацея - 45 сомони

🏥 <b>MAXXPHARM - Качественные лекарства по доступным ценам!</b>

📞 <b>Для заказа:</b>
• 📝 В этом чате
• 📞 Телефон: +992 900 000 001
• 🌐 Сайт: www.maxxpharm.tj
            """
            
            await message.answer(catalog_text)
        
        @self.dp.message(F.text == "ℹ️ О нас")
        async def handle_about(message: Message, state: FSMContext):
            """Информация о компании"""
            await message.answer(
                "ℹ️ <b>О MAXXPHARM</b>\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b> - современная система доставки лекарств\n\n"
                "👥 <b>Наши преимущества:</b>\n"
                "• ⚡ Быстрая доставка по Душанбе (до 60 минут)\n"
                "• 💊 Только сертифицированные лекарства\n"
                "• 📞 Круглосуточная поддержка\n"
                "• 💳 Удобная оплата (карта, перевод)\n"
                "• 📱 Отслеживание заявки в реальном времени\n"
                "• 🏥 Гарантия качества и сроков годности\n\n"
                "📍 <b>Наши контакты:</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n"
                "• 📍 Адрес: г. Душанбе, ул. Рудаки 15, офис 205\n"
                "• 🕐 Время работы: 09:00 - 21:00, без выходных\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        # 🔄 Callback обработчики
        @self.dp.callback_query(F.data.startswith("order_"))
        async def handle_order_callback(callback: types.CallbackQuery, state: FSMContext):
            """Обработка callback для создания заказа"""
            action = callback.data.split("_")[1]
            
            if action == "text":
                await callback.message.answer("📝 Напишите список лекарств и ваш контакт")
                await state.set_state("waiting_order_text")
                
            elif action == "photo":
                await callback.message.answer("📷 Отправьте фото рецепта и ваш контакт")
                await state.set_state("waiting_order_photo")
                
            elif action == "voice":
                await callback.message.answer("🎤 Отправьте голосовое сообщение с заказом")
                await state.set_state("waiting_order_voice")
            
            await callback.answer()
        
        # 🔄 Обработчики состояний
        @self.dp.message()
        async def handle_order_input(message: Message, state: FSMContext):
            """Обработка ввода заказа"""
            current_state = await state.get_state()
            
            if current_state == "waiting_order_text":
                # Создаем заявку из текста
                global order_counter
                order_id = f"ORD-{order_counter:06d}"
                order_counter += 1
                
                new_order = Order(
                    order_id=order_id,
                    client_name=message.from_user.full_name,
                    client_phone=message.text,  # В реальном боте здесь будет парсинг
                    items=["Заказ из текста"],
                    total=0.0,
                    status=OrderStatus.CREATED
                )
                
                orders_db[order_id] = new_order
                
                await message.answer(
                    f"✅ <b>Заявка создана!</b>\n\n"
                    f"📝 Номер: {order_id}\n"
                    f"👤 Клиент: {new_order.client_name}\n"
                    f"📞 Телефон: {new_order.client_phone}\n\n"
                    "🔄 Заявка передана оператору\n"
                    "💳 Ожидайте подтверждения оплаты"
                )
                
                await state.clear()
                await self.notify_operators(f"Новая заявка: {order_id}")
                
            elif current_state == "waiting_order_photo":
                # Обработка фото
                await message.answer("📷 Фото получено! Обрабатывается...")
                await state.clear()
                
            elif current_state == "waiting_order_voice":
                # Обработка голоса
                await message.answer("🎤 Голос получено! Обрабатывается...")
                await state.clear()
        
        # 📊 Обработчики для оператора
        @self.dp.message(F.text == "📥 Новые заявки")
        async def handle_new_orders(message: Message, state: FSMContext):
            """Новые заявки для оператора"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            new_orders = [order for order in orders_db.values() 
                          if order.status in [OrderStatus.CREATED, OrderStatus.AWAITING_PAYMENT]]
            
            if not new_orders:
                await message.answer("📭 Новых заявок нет")
                return
            
            text = "📥 <b>Новые заявки</b>\n\n"
            for order in new_orders[:5]:  # Показываем первые 5
                text += f"📝 {order.order_id}\n"
                text += f"👤 {order.client_name}\n"
                text += f"📞 {order.client_phone}\n"
                text += f"💰 {order.total} сомони\n"
                text += f"📅 {order.status.value}\n\n"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"✅ Принять {order.order_id}",
                            callback_data=f"accept_{order.order_id}"
                        )
                    ] for order in new_orders[:5]
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
        
        @self.dp.message(F.text == "📦 В работе")
        async def handle_orders_in_work(message: Message, state: FSMContext):
            """Заявки в работе"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            work_orders = [order for order in orders_db.values() 
                         if order.status in [OrderStatus.PAID, OrderStatus.PROCESSING]]
            
            if not work_orders:
                await message.answer("📭 Заявок в работе нет")
                return
            
            text = "📦 <b>Заявки в работе</b>\n\n"
            for order in work_orders[:5]:
                text += f"📝 {order.order_id}\n"
                text += f"👤 {order.client_name}\n"
                text += f"📊 {order.status.value}\n\n"
            
            await message.answer(text)
        
        # 📊 Обработчики для администратора
        @self.dp.message(F.text == "📊 Все заявки")
        async def handle_all_orders(message: Message, state: FSMContext):
            """Все заявки для админа"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            if not orders_db:
                await message.answer("📭 Заявок пока нет")
                return
            
            text = "📊 <b>Все заявки</b>\n\n"
            for order in list(orders_db.values())[-10:]:  # Последние 10
                text += f"📝 {order.order_id}\n"
                text += f"👤 {order.client_name}\n"
                text += f"📊 {order.status.value}\n"
                text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text)
        
        @self.dp.message(F.text == "👥 Пользователи")
        async def handle_users(message: Message, state: FSMContext):
            """Пользователи для админа"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            text = "👥 <b>Пользователи системы</b>\n\n"
            for user_id, user in list(users_db.items())[-10:]:
                text += f"👤 {user.name} (@{user.username})\n"
                text += f"🎯 Роль: {user.role}\n"
                text += f"📅 {user.created_at.strftime('%d.%m.%Y')}\n\n"
            
            await message.answer(text)
        
        @self.dp.message(F.text == "🎛 Роли")
        async def handle_roles(message: Message, state: FSMContext):
            """Управление ролями"""
            if str(message.from_user.id) != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔹 Сделать оператором", callback_data="make_operator")],
                    [InlineKeyboardButton(text="🔹 Сделать сборщиком", callback_data="make_collector")],
                    [InlineKeyboardButton(text="🔹 Сделать проверщиком", callback_data="make_checker")],
                    [InlineKeyboardButton(text="🔹 Сделать курьером", callback_data="make_courier")]
                ]
            )
            
            await message.answer("🎛 <b>Управление ролями</b>", reply_markup=keyboard)
        
        # 📞 Обработка неизвестных сообщений
        @self.dp.message()
        async def handle_unknown(message: Message, state: FSMContext):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "🤔 <b>Неизвестная команда</b>\n\n"
                "📋 <b>Основные команды:</b>\n"
                "/start - Главное меню\n\n"
                "🎯 <b>Используйте кнопки меню</b> для навигации\n\n"
                "📞 <b>Нужна помощь?</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 💬 Telegram: @maxxpharm_support\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        logger.info("✅ All handlers registered")
    
    async def notify_operators(self, message: str):
        """Уведомление операторов о новой заявке"""
        for user_id, user in users_db.items():
            if user.role == "operator":
                try:
                    await self.bot.send_message(
                        user_id,
                        f"🔔 <b>Новая заявка!</b>\n\n{message}"
                    )
                except:
                    pass  # Игнорируем ошибки отправки
    
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
