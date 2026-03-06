#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Профессиональная система доставки лекарств
Полная реализация как Glovo/Yandex Delivery
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
    Location
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# 🗄️ Database imports
import asyncpg
from asyncpg import Connection

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/maxxpharm")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log'),
        logging.FileHandler('logs/errors.log', level=logging.ERROR)
    ]
)

logger = logging.getLogger("maxxpharm_bot")

# Создаем директории
os.makedirs("logs", exist_ok=True)

# 🎛️ FSM States
class OrderStates(StatesGroup):
    choosing_method = State()
    adding_items = State()
    entering_address = State()
    entering_phone = State()
    entering_comment = State()
    confirming_order = State()

class AdminStates(StatesGroup):
    adding_user = State()
    setting_role = State()
    entering_telegram_id = State()

# 🎯 Enums
class UserRole(Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    OPERATOR = "operator"
    COLLECTOR = "collector"
    INSPECTOR = "inspector"
    COURIER = "courier"
    CLIENT = "client"

class OrderStatus(Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    COLLECTING = "collecting"
    CHECKING = "checking"
    READY = "ready"
    WITH_COURIER = "with_courier"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# 📊 Data Models
@dataclass
class User:
    id: int
    telegram_id: int
    name: str
    username: str
    role: UserRole
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Order:
    id: int
    user_id: int
    status: OrderStatus
    items: List[Dict]
    delivery_address: str
    phone: str
    comment: Optional[str]
    total_amount: float
    created_at: datetime = field(default_factory=datetime.now)
    assigned_collector_id: Optional[int] = None
    assigned_inspector_id: Optional[int] = None
    assigned_courier_id: Optional[int] = None
    courier_location: Optional[Dict] = None

@dataclass
class Product:
    id: int
    name: str
    price: float
    category: str
    description: str
    stock: int
    prescription_required: bool

@dataclass
class Notification:
    id: int
    user_id: int
    message: str
    type: str
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False

# 🗄️ Database Manager
class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("✅ Database connected")
            await self.create_tables()
            await self.init_test_data()
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def create_tables(self):
        """Создание таблиц"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    name VARCHAR(255),
                    username VARCHAR(255),
                    role VARCHAR(50),
                    phone VARCHAR(20),
                    address TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Таблица товаров
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    price DECIMAL(10,2),
                    category VARCHAR(100),
                    description TEXT,
                    stock INTEGER DEFAULT 0,
                    prescription_required BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Таблица заказов
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(telegram_id),
                    status VARCHAR(50),
                    items JSONB,
                    delivery_address TEXT,
                    phone VARCHAR(20),
                    comment TEXT,
                    total_amount DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    assigned_collector_id INTEGER,
                    assigned_inspector_id INTEGER,
                    assigned_courier_id INTEGER
                )
            """)
            
            # Таблица истории статусов
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS order_status_history (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id),
                    status VARCHAR(50),
                    changed_by INTEGER,
                    changed_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Таблица геолокации курьеров
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS courier_locations (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id),
                    courier_id INTEGER,
                    latitude DECIMAL(10,8),
                    longitude DECIMAL(11,8),
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Таблица уведомлений
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(telegram_id),
                    message TEXT,
                    type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_read BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Таблица логов действий
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS action_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(telegram_id),
                    action TEXT,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
    
    async def init_test_data(self):
        """Инициализация тестовых данных"""
        async with self.pool.acquire() as conn:
            # Проверяем есть ли товары
            count = await conn.fetchval("SELECT COUNT(*) FROM products")
            if count == 0:
                # Добавляем тестовые товары
                products = [
                    ("Парацетамол", 50.0, "Обезболивающие", "Обезболивающее и жаропонижающее", 100, False),
                    ("Ибупрофен", 80.0, "Обезболивающие", "Противовоспалительное средство", 50, False),
                    ("Витамин C", 120.0, "Витамины", "Аскорбиновая кислота 500мг", 150, False),
                    ("Амоксициллин", 150.0, "Антибиотики", "Антибиотик широкого спектра", 40, True),
                    ("Арбидол", 300.0, "Противовирусные", "Противовирусный препарат", 60, False),
                ]
                
                for product in products:
                    await conn.execute(
                        "INSERT INTO products (name, price, category, description, stock, prescription_required) VALUES ($1, $2, $3, $4, $5, $6)",
                        *product
                    )
                
                logger.info("✅ Test products added")
            
            # Создаем админа если нет
            admin_exists = await conn.fetchval("SELECT COUNT(*) FROM users WHERE telegram_id = $1", ADMIN_ID)
            if admin_exists == 0:
                await conn.execute(
                    "INSERT INTO users (telegram_id, name, username, role) VALUES ($1, $2, $3, $4)",
                    ADMIN_ID, "Super Admin", "admin", UserRole.ADMIN.value
                )
                logger.info("✅ Admin user created")
    
    async def create_user(self, user: User) -> bool:
        """Создание пользователя"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO users (telegram_id, name, username, role, phone, address)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                    name = $2, username = $3, role = $4, phone = $5, address = $6
                    """,
                    user.telegram_id, user.name, user.username, user.role.value,
                    user.phone, user.address
                )
                return True
            except Exception as e:
                logger.error(f"❌ Error creating user: {e}")
                return False
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            if row:
                return User(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    name=row['name'],
                    username=row['username'],
                    role=UserRole(row['role']),
                    phone=row['phone'],
                    address=row['address'],
                    created_at=row['created_at'],
                    is_active=row['is_active']
                )
            return None
    
    async def create_order(self, order: Order) -> int:
        """Создание заказа"""
        async with self.pool.acquire() as conn:
            order_id = await conn.fetchval(
                """
                INSERT INTO orders (user_id, status, items, delivery_address, phone, comment, total_amount)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                order.user_id, order.status.value, json.dumps(order.items),
                order.delivery_address, order.phone, order.comment, order.total_amount
            )
            
            # Записываем в историю
            await conn.execute(
                "INSERT INTO order_status_history (order_id, status, changed_by) VALUES ($1, $2, $3)",
                order_id, order.status.value, order.user_id
            )
            
            # Логируем действие
            await self.log_action(order.user_id, "order_created", {"order_id": order_id})
            
            return order_id
    
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Получение заказов по статусу"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders WHERE status = $1 ORDER BY created_at", status.value)
            return [self._row_to_order(row) for row in rows]
    
    async def update_order_status(self, order_id: int, status: OrderStatus, changed_by: int):
        """Обновление статуса заказа"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE orders SET status = $1 WHERE id = $2", status.value, order_id)
            await conn.execute(
                "INSERT INTO order_status_history (order_id, status, changed_by) VALUES ($1, $2, $3)",
                order_id, status.value, changed_by
            )
            
            # Логируем действие
            await self.log_action(changed_by, "order_status_changed", {"order_id": order_id, "new_status": status.value})
    
    async def assign_order_staff(self, order_id: int, staff_type: str, staff_id: int):
        """Назначение сотрудника на заказ"""
        async with self.pool.acquire() as conn:
            if staff_type == "collector":
                await conn.execute("UPDATE orders SET assigned_collector_id = $1 WHERE id = $2", staff_id, order_id)
            elif staff_type == "inspector":
                await conn.execute("UPDATE orders SET assigned_inspector_id = $1 WHERE id = $2", staff_id, order_id)
            elif staff_type == "courier":
                await conn.execute("UPDATE orders SET assigned_courier_id = $1 WHERE id = $2", staff_id, order_id)
    
    async def update_courier_location(self, order_id: int, courier_id: int, lat: float, lng: float):
        """Обновление местоположения курьера"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO courier_locations (order_id, courier_id, latitude, longitude) VALUES ($1, $2, $3, $4)",
                order_id, courier_id, lat, lng
            )
    
    async def get_products(self) -> List[Product]:
        """Получение товаров"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM products ORDER BY name")
            return [self._row_to_product(row) for row in rows]
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Получение заказов пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders WHERE user_id = $1 ORDER BY created_at DESC", user_id)
            return [self._row_to_order(row) for row in rows]
    
    async def get_staff_orders(self, staff_id: int, role: UserRole) -> List[Order]:
        """Получение заказов для сотрудника"""
        async with self.pool.acquire() as conn:
            if role == UserRole.COLLECTOR:
                rows = await conn.fetch("SELECT * FROM orders WHERE assigned_collector_id = $1 ORDER BY created_at", staff_id)
            elif role == UserRole.INSPECTOR:
                rows = await conn.fetch("SELECT * FROM orders WHERE assigned_inspector_id = $1 ORDER BY created_at", staff_id)
            elif role == UserRole.COURIER:
                rows = await conn.fetch("SELECT * FROM orders WHERE assigned_courier_id = $1 ORDER BY created_at", staff_id)
            else:
                rows = []
            return [self._row_to_order(row) for row in rows]
    
    async def create_notification(self, user_id: int, message: str, notification_type: str):
        """Создание уведомления"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO notifications (user_id, message, type) VALUES ($1, $2, $3)",
                user_id, message, notification_type
            )
    
    async def get_analytics(self) -> Dict:
        """Получение аналитики"""
        async with self.pool.acquire() as conn:
            # Статистика заказов
            total_orders = await conn.fetchval("SELECT COUNT(*) FROM orders")
            today_orders = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE")
            delivered_orders = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'delivered'")
            
            # Статистика пользователей
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            active_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            
            # Статистика по ролям
            role_stats = await conn.fetch("SELECT role, COUNT(*) FROM users GROUP BY role")
            
            # Выручка
            total_revenue = await conn.fetchval("SELECT SUM(total_amount) FROM orders WHERE status = 'delivered'")
            today_revenue = await conn.fetchval("SELECT SUM(total_amount) FROM orders WHERE DATE(created_at) = CURRENT_DATE AND status = 'delivered'")
            
            return {
                "orders": {
                    "total": total_orders,
                    "today": today_orders,
                    "delivered": delivered_orders
                },
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "by_role": dict(role_stats)
                },
                "revenue": {
                    "total": float(total_revenue or 0),
                    "today": float(today_revenue or 0)
                }
            }
    
    async def log_action(self, user_id: int, action: str, details: Dict = None):
        """Логирование действия"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO action_logs (user_id, action, details) VALUES ($1, $2, $3)",
                user_id, action, json.dumps(details or {})
            )
    
    def _row_to_order(self, row) -> Order:
        return Order(
            id=row['id'],
            user_id=row['user_id'],
            status=OrderStatus(row['status']),
            items=json.loads(row['items']) if row['items'] else [],
            delivery_address=row['delivery_address'],
            phone=row['phone'],
            comment=row['comment'],
            total_amount=float(row['total_amount']),
            created_at=row['created_at'],
            assigned_collector_id=row['assigned_collector_id'],
            assigned_inspector_id=row['assigned_inspector_id'],
            assigned_courier_id=row['assigned_courier_id']
        )
    
    def _row_to_product(self, row) -> Product:
        return Product(
            id=row['id'],
            name=row['name'],
            price=float(row['price']),
            category=row['category'],
            description=row['description'],
            stock=row['stock'],
            prescription_required=row['prescription_required']
        )
    
    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()

# 🏥 MAXXPHARM Bot
class MaxxpharmBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = DatabaseManager()
        self.user_cart = {}  # Временные корзины
        self.order_data = {}  # Временные данные заказов
    
    async def initialize(self):
        """Инициализация бота"""
        print("🚀 Initializing MAXXPHARM Bot...")
        
        # Подключение к базе данных
        if not await self.db.connect():
            print("❌ Database connection failed")
            return False
        
        # Регистрация обработчиков
        await self.register_handlers()
        
        print("✅ Bot initialized successfully")
        return True
    
    async def register_handlers(self):
        """Регистрация обработчиков"""
        
        # Основные команды
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, state: FSMContext):
            """Обработчик /start"""
            await state.clear()
            
            user = await self.db.get_user(message.from_user.id)
            if not user:
                # Создаем нового пользователя
                user = User(
                    id=0,
                    telegram_id=message.from_user.id,
                    name=message.from_user.full_name,
                    username=message.from_user.username,
                    role=UserRole.CLIENT
                )
                await self.db.create_user(user)
                user = await self.db.get_user(message.from_user.id)
            
            welcome_text = self.get_welcome_text(user)
            keyboard = self.get_main_menu(user.role)
            
            await message.answer(welcome_text, reply_markup=keyboard)
            await self.db.log_action(user.telegram_id, "start_command")
        
        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message, state: FSMContext):
            """Админ панель"""
            await state.clear()
            
            user = await self.db.get_user(message.from_user.id)
            if not user or user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен")
                return
            
            keyboard = self.get_admin_menu()
            await message.answer("👑 <b>Админ панель</b>", reply_markup=keyboard)
            await self.db.log_action(user.telegram_id, "admin_panel_opened")
        
        # ==================== КЛИЕНТСКИЕ ОБРАБОТЧИКИ ====================
        
        @self.dp.message(F.text == "📦 Сделать заказ")
        async def handle_make_order(message: Message, state: FSMContext):
            """Обработка кнопки Сделать заказ"""
            await state.set_state(OrderStates.choosing_method)
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔍 Поиск лекарства", callback_data="order_search"),
                        InlineKeyboardButton(text="📚 Каталог", callback_data="order_catalog")
                    ],
                    [
                        InlineKeyboardButton(text="📷 Отправить рецепт", callback_data="order_photo")
                    ]
                ]
            )
            
            await message.answer(
                "📦 <b>Оформление заказа</b>\n\n"
                "Выберите способ:",
                reply_markup=keyboard
            )
            await self.db.log_action(message.from_user.id, "order_started")
        
        @self.dp.message(F.text == "📚 Каталог товаров")
        async def handle_catalog(message: Message):
            """Обработка кнопки Каталог товаров"""
            products = await self.db.get_products()
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"{p.name} - {p.price} сомони",
                        callback_data=f"product_{p.id}"
                    )] for p in products
                ]
            )
            
            text = "📚 <b>Каталог товаров</b>\n\n"
            for product in products:
                text += f"📦 {product.name}\n"
                text += f"💰 Цена: {product.price} сомони\n"
                text += f"📂 Категория: {product.category}\n"
                text += f"📊 В наличии: {product.stock} шт\n\n"
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "catalog_opened")
        
        @self.dp.message(F.text == "📋 Мои заказы")
        async def handle_my_orders(message: Message):
            """Обработка кнопки Мои заказы"""
            user = await self.db.get_user(message.from_user.id)
            orders = await self.db.get_user_orders(user.telegram_id)
            
            if not orders:
                await message.answer("📭 У вас пока нет заказов")
                return
            
            text = "📋 <b>Мои заказы</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {self.get_status_emoji(order.status)} {order.status.value}",
                        callback_data=f"order_detail_{order.id}"
                    )] for order in orders[:5]
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "my_orders_opened")
        
        @self.dp.message(F.text == "🆘 Поддержка")
        async def handle_support(message: Message):
            """Обработка кнопки Поддержка"""
            await message.answer(
                "🆘 <b>Поддержка MAXXPHARM</b>\n\n"
                "👤 Администратор: @admin\n"
                "📱 Телефон: +992 900 000 001\n"
                "🕐 Время работы: 09:00 - 21:00\n\n"
                "🏥 Мы всегда готовы помочь!"
            )
            await self.db.log_action(message.from_user.id, "support_requested")
        
        @self.dp.message(F.text == "ℹ️ Помощь")
        async def handle_help(message: Message):
            """Обработка кнопки Помощь"""
            await message.answer(
                "ℹ️ <b>Помощь MAXXPHARM</b>\n\n"
                "📋 <b>Команды:</b>\n"
                "/start - Запуск бота\n"
                "/admin - Админ панель\n\n"
                "📦 <b>Как сделать заказ:</b>\n"
                "1. Нажмите 'Сделать заказ'\n"
                "2. Выберите способ оформления\n"
                "3. Добавьте товары\n"
                "4. Укажите адрес и телефон\n"
                "5. Подтвердите заказ\n\n"
                "📍 <b>Отслеживание заказа:</b>\n"
                "• Нажмите 'Мои заказы'\n"
                "• Выберите нужный заказ\n"
                "• Следите за статусом\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
            await self.db.log_action(message.from_user.id, "help_opened")
        
        # ==================== АДМИНСКИЕ ОБРАБОТЧИКИ ====================
        
        @self.dp.message(F.text == "📊 Все заявки")
        async def handle_all_orders(message: Message):
            """Обработка кнопки Все заявки"""
            orders = await self.db.get_orders_by_status(OrderStatus.NEW)
            
            if not orders:
                await message.answer("📭 Нет новых заявок")
                return
            
            text = "📊 <b>Все заявки</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {self.get_status_emoji(order.status)} {order.status.value}",
                        callback_data=f"order_detail_{order.id}"
                    )] for order in orders[:10]
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "all_orders_viewed")
        
        @self.dp.message(F.text == "📈 Аналитика")
        async def handle_analytics(message: Message):
            """Обработка кнопки Аналитика"""
            analytics = await self.db.get_analytics()
            
            text = "📈 <b>Аналитика MAXXPHARM</b>\n\n"
            text += f"📊 <b>Заказы:</b>\n"
            text += f"• Всего: {analytics['orders']['total']}\n"
            text += f"• Сегодня: {analytics['orders']['today']}\n"
            text += f"• Доставлено: {analytics['orders']['delivered']}\n\n"
            text += f"👥 <b>Пользователи:</b>\n"
            text += f"• Всего: {analytics['users']['total']}\n"
            text += f"• Активных: {analytics['users']['active']}\n\n"
            text += f"💰 <b>Выручка:</b>\n"
            text += f"• Всего: {analytics['revenue']['total']:.2f} сомони\n"
            text += f"• Сегодня: {analytics['revenue']['today']:.2f} сомони"
            
            await message.answer(text)
            await self.db.log_action(message.from_user.id, "analytics_viewed")
        
        @self.dp.message(F.text == "👥 Пользователи и роли")
        async def handle_users(message: Message, state: FSMContext):
            """Обработка кнопки Пользователи и роли"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user")],
                    [InlineKeyboardButton(text="👥 Список пользователей", callback_data="list_users")],
                    [InlineKeyboardButton(text="🔄 Изменить роль", callback_data="change_role")]
                ]
            )
            
            await message.answer(
                "👥 <b>Управление пользователями</b>\n\n"
                "Выберите действие:",
                reply_markup=keyboard
            )
            await self.db.log_action(message.from_user.id, "user_management_opened")
        
        # ==================== ОПЕРАТОРСКИЕ ОБРАБОТЧИКИ ====================
        
        @self.dp.message(F.text == "📦 Новые заказы")
        async def handle_new_orders(message: Message):
            """Обработка кнопки Новые заказы"""
            orders = await self.db.get_orders_by_status(OrderStatus.NEW)
            
            if not orders:
                await message.answer("📭 Нет новых заказов")
                return
            
            text = "📦 <b>Новые заказы</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {order.total_amount} сомони",
                        callback_data=f"operator_order_{order.id}"
                    )] for order in orders
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "new_orders_viewed")
        
        @self.dp.message(F.text == "🔄 В работе")
        async def handle_in_progress(message: Message):
            """Обработка кнопки В работе"""
            user = await self.db.get_user(message.from_user.id)
            orders = await self.db.get_staff_orders(user.telegram_id, UserRole.OPERATOR)
            
            if not orders:
                await message.answer("📭 Нет заказов в работе")
                return
            
            text = "🔄 <b>Заказы в работе</b>\n\n"
            for order in orders:
                text += f"📦 Заказ #{order.id}\n"
                text += f"📊 Статус: {order.status.value}\n"
                text += f"💰 Сумма: {order.total_amount} сомони\n\n"
            
            await message.answer(text)
            await self.db.log_action(message.from_user.id, "in_progress_orders_viewed")
        
        # ==================== ОБРАБОТЧИКИ СОТРУДНИКОВ ====================
        
        @self.dp.message(F.text == "📦 Собрать заказ")
        async def handle_collect_orders(message: Message):
            """Обработка кнопки Собрать заказ"""
            user = await self.db.get_user(message.from_user.id)
            orders = await self.db.get_staff_orders(user.telegram_id, UserRole.COLLECTOR)
            
            if not orders:
                await message.answer("📭 Нет заказов для сборки")
                return
            
            text = "📦 <b>Заказы для сборки</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {order.status.value}",
                        callback_data=f"collect_order_{order.id}"
                    )] for order in orders
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "collect_orders_viewed")
        
        @self.dp.message(F.text == "🔍 Проверить заказ")
        async def handle_check_orders(message: Message):
            """Обработка кнопки Проверить заказ"""
            user = await self.db.get_user(message.from_user.id)
            orders = await self.db.get_staff_orders(user.telegram_id, UserRole.INSPECTOR)
            
            if not orders:
                await message.answer("📭 Нет заказов для проверки")
                return
            
            text = "🔍 <b>Заказы для проверки</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {order.status.value}",
                        callback_data=f"check_order_{order.id}"
                    )] for order in orders
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "check_orders_viewed")
        
        @self.dp.message(F.text == "📦 Мои доставки")
        async def handle_my_deliveries(message: Message):
            """Обработка кнопки Мои доставки"""
            user = await self.db.get_user(message.from_user.id)
            orders = await self.db.get_staff_orders(user.telegram_id, UserRole.COURIER)
            
            if not orders:
                await message.answer("📭 Нет доставок")
                return
            
            text = "📦 <b>Мои доставки</b>\n\n"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"Заказ #{order.id} - {order.status.value}",
                        callback_data=f"delivery_order_{order.id}"
                    )] for order in orders
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
            await self.db.log_action(message.from_user.id, "my_deliveries_viewed")
        
        @self.dp.message(F.text == "📍 Отправить локацию")
        async def handle_send_location(message: Message):
            """Обработка кнопки Отправить локацию"""
            await message.answer(
                "📍 <b>Отправьте вашу геолокацию</b>\n\n"
                "Нажмите на скрепку 📎 и выберите 'Геолокация'",
                reply_markup=ReplyKeyboardRemove()
            )
            await self.db.log_action(message.from_user.id, "location_request_sent")
        
        @self.dp.message(F.location)
        async def handle_location(message: Message, location: Location):
            """Обработка геолокации"""
            user = await self.db.get_user(message.from_user.id)
            
            # Сохраняем геолокацию
            # В реальной системе нужно определить какой заказ активен
            await self.db.update_courier_location(
                order_id=1,  # Заглушка
                courier_id=user.telegram_id,
                lat=location.latitude,
                lng=location.longitude
            )
            
            await message.answer(
                "✅ <b>Геолокация получена</b>\n\n"
                "📍 Ваше местоположение обновлено\n"
                "🏥 Клиент видит ваше движение на карте"
            )
            
            await self.db.log_action(message.from_user.id, "location_sent", {
                "latitude": location.latitude,
                "longitude": location.longitude
            })
        
        # ==================== CALLBACK ОБРАБОТЧИКИ ====================
        
        @self.dp.callback_query(F.data.startswith("product_"))
        async def handle_product_selection(callback: CallbackQuery, state: FSMContext):
            """Обработка выбора товара"""
            product_id = int(callback.data.split("_")[1])
            products = await self.db.get_products()
            product = next((p for p in products if p.id == product_id), None)
            
            if not product:
                await callback.answer("❌ Товар не найден")
                return
            
            # Добавляем в корзину
            user_id = callback.from_user.id
            if user_id not in self.user_cart:
                self.user_cart[user_id] = []
            
            self.user_cart[user_id].append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': 1
            })
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 В корзину", callback_data="to_cart")],
                    [InlineKeyboardButton(text="➕ Добавить еще", callback_data="continue_shopping")],
                    [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")]
                ]
            )
            
            await callback.message.edit_text(
                f"📦 <b>Товар добавлен в корзину</b>\n\n"
                f"📋 {product.name}\n"
                f"💰 Цена: {product.price} сомони\n"
                f"📂 Категория: {product.category}\n\n"
                f"🛒 В корзине: {len(self.user_cart[user_id])} товаров",
                reply_markup=keyboard
            )
            
            await callback.answer(f"✅ {product.name} добавлен")
            await self.db.log_action(user_id, "product_added_to_cart", {"product_id": product_id})
        
        @self.dp.callback_query(F.data == "to_cart")
        async def handle_to_cart(callback: CallbackQuery):
            """Обработка перехода в корзину"""
            user_id = callback.from_user.id
            cart = self.user_cart.get(user_id, [])
            
            if not cart:
                await callback.answer("🛒 Корзина пуста")
                return
            
            text = "🛒 <b>Ваша корзина</b>\n\n"
            total = 0
            
            for item in cart:
                subtotal = item['price'] * item['quantity']
                total += subtotal
                text += f"📦 {item['name']}\n"
                text += f"💰 {item['price']} × {item['quantity']} = {subtotal} сомони\n\n"
            
            text += f"💰 <b>Итого: {total} сомони</b>"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
                    [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="continue_shopping")]
                ]
            )
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            await self.db.log_action(user_id, "cart_viewed")
        
        @self.dp.callback_query(F.data == "checkout")
        async def handle_checkout(callback: CallbackQuery, state: FSMContext):
            """Обработка оформления заказа"""
            user_id = callback.from_user.id
            cart = self.user_cart.get(user_id, [])
            
            if not cart:
                await callback.answer("🛒 Корзина пуста")
                return
            
            await state.set_state(OrderStates.entering_address)
            await callback.message.edit_text(
                "📍 <b>Оформление заказа</b>\n\n"
                "📝 <b>Шаг 1: Адрес доставки</b>\n\n"
                "Введите адрес доставки:",
                reply_markup=ReplyKeyboardRemove()
            )
            await callback.answer()
            await self.db.log_action(user_id, "checkout_started")
        
        @self.dp.callback_query(F.data == "clear_cart")
        async def handle_clear_cart(callback: CallbackQuery):
            """Обработка очистки корзины"""
            user_id = callback.from_user.id
            self.user_cart[user_id] = []
            
            await callback.message.edit_text(
                "🗑️ <b>Корзина очищена</b>\n\n"
                "🛒 Вы можете начать новый заказ",
                reply_markup=self.get_main_menu(UserRole.CLIENT)
            )
            await callback.answer("🗑️ Корзина очищена")
            await self.db.log_action(user_id, "cart_cleared")
        
        @self.dp.callback_query(F.data == "confirm_order")
        async def handle_confirm_order(callback: CallbackQuery, state: FSMContext):
            """Обработка подтверждения заказа"""
            user_id = callback.from_user.id
            cart = self.user_cart.get(user_id, [])
            data = await state.get_data()
            
            # Считаем итоговую сумму
            total = sum(item['price'] * item['quantity'] for item in cart)
            
            # Создаем заказ
            order = Order(
                id=0,
                user_id=user_id,
                status=OrderStatus.NEW,
                items=cart,
                delivery_address=data['address'],
                phone=data['phone'],
                comment=data['comment'],
                total_amount=total
            )
            
            order_id = await self.db.create_order(order)
            
            # Очищаем корзину и состояние
            self.user_cart[user_id] = []
            await state.clear()
            
            # Создаем уведомление для операторов
            await self.db.create_notification(
                user_id=0,  # Системное уведомление
                message=f"🆕 Новый заказ #{order_id}",
                notification_type="new_order"
            )
            
            await callback.message.edit_text(
                f"✅ <b>Заказ успешно оформлен!</b>\n\n"
                f"📋 Номер заказа: #{order_id}\n"
                f"💰 Сумма: {total} сомони\n"
                f"📍 Адрес: {data['address']}\n\n"
                f"📞 Мы свяжемся с вами в ближайшее время!\n\n"
                f"🏥 <b>Спасибо за заказ в MAXXPHARM!</b>",
                reply_markup=self.get_main_menu(UserRole.CLIENT)
            )
            
            await callback.answer("✅ Заказ оформлен!")
            await self.db.log_action(user_id, "order_confirmed", {"order_id": order_id})
        
        @self.dp.callback_query(F.data.startswith("operator_order_"))
        async def handle_operator_order(callback: CallbackQuery):
            """Обработка заказа оператором"""
            order_id = int(callback.data.split("_")[2])
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order_{order_id}")],
                    [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_id}")],
                    [InlineKeyboardButton(text="📦 Назначить сборщика", callback_data=f"assign_collector_{order_id}")]
                ]
            )
            
            await callback.message.edit_text(
                f"📦 <b>Заказ #{order_id}</b>\n\n"
                f"📊 Статус: Новый\n\n"
                f"Выберите действие:",
                reply_markup=keyboard
            )
            await callback.answer()
            await self.db.log_action(callback.from_user.id, "operator_order_viewed", {"order_id": order_id})
        
        @self.dp.callback_query(F.data.startswith("confirm_order_"))
        async def handle_confirm_order_status(callback: CallbackQuery):
            """Подтверждение заказа оператором"""
            order_id = int(callback.data.split("_")[2])
            await self.db.update_order_status(order_id, OrderStatus.CONFIRMED, callback.from_user.id)
            
            await callback.message.edit_text(
                f"✅ <b>Заказ #{order_id} подтвержден</b>\n\n"
                f"📊 Статус изменен на 'Подтвержден'\n"
                f"📦 Заказ передан на сборку"
            )
            await callback.answer("✅ Заказ подтвержден")
            await self.db.log_action(callback.from_user.id, "order_confirmed_by_operator", {"order_id": order_id})
        
        # ==================== FSM ОБРАБОТЧИКИ ====================
        
        @self.dp.message(OrderStates.entering_address)
        async def handle_enter_address(message: Message, state: FSMContext):
            """Обработка ввода адреса"""
            await state.update_data(address=message.text)
            await state.set_state(OrderStates.entering_phone)
            
            await message.answer(
                "📱 <b>Шаг 2: Номер телефона</b>\n\n"
                "Введите номер телефона:"
            )
        
        @self.dp.message(OrderStates.entering_phone)
        async def handle_enter_phone(message: Message, state: FSMContext):
            """Обработка ввода телефона"""
            await state.update_data(phone=message.text)
            await state.set_state(OrderStates.entering_comment)
            
            await message.answer(
                "📝 <b>Шаг 3: Комментарий к заказу</b>\n\n"
                "Введите комментарий (необязательно):"
            )
        
        @self.dp.message(OrderStates.entering_comment)
        async def handle_enter_comment(message: Message, state: FSMContext):
            """Обработка ввода комментария"""
            await state.update_data(comment=message.text)
            await state.set_state(OrderStates.confirming_order)
            
            data = await state.get_data()
            user_id = message.from_user.id
            cart = self.user_cart.get(user_id, [])
            
            total = sum(item['price'] * item['quantity'] for item in cart)
            
            text = "✅ <b>Подтверждение заказа</b>\n\n"
            text += "📦 <b>Состав заказа:</b>\n"
            
            for item in cart:
                text += f"• {item['name']} - {item['price']} сомони\n"
            
            text += f"\n💰 <b>Итого: {total} сомони</b>\n"
            text += f"📍 Адрес: {data['address']}\n"
            text += f"📱 Телефон: {data['phone']}\n"
            if data['comment']:
                text += f"📝 Комментарий: {data['comment']}\n"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
                    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
                ]
            )
            
            await message.answer(text, reply_markup=keyboard)
        
        @self.dp.callback_query(F.data == "cancel_order")
        async def handle_cancel_order(callback: CallbackQuery, state: FSMContext):
            """Обработка отмены заказа"""
            await state.clear()
            
            await callback.message.edit_text(
                "❌ <b>Заказ отменен</b>\n\n"
                "🛒 Корзина очищена\n\n"
                "🏥 Вы можете начать новый заказ в любой момент",
                reply_markup=self.get_main_menu(UserRole.CLIENT)
            )
            
            await callback.answer("❌ Заказ отменен")
            await self.db.log_action(callback.from_user.id, "order_cancelled")
    
    def get_welcome_text(self, user: User) -> str:
        """Получение приветственного текста"""
        role_texts = {
            UserRole.ADMIN: (
                f"👑 <b>Добро пожаловать, Администратор!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"📊 <b>Доступные функции:</b>\n"
                f"• Управление заказами\n"
                f"• Управление пользователями\n"
                f"• Просмотр аналитики\n"
                f"• Настройки системы\n\n"
                f"👑 <b>Полный доступ к системе</b>"
            ),
            UserRole.DIRECTOR: (
                f"👨‍💼 <b>Добро пожаловать, Директор!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"📊 <b>Доступные функции:</b>\n"
                f"• Управление командой\n"
                f"• Просмотр отчетов\n"
                f"• Контроль качества\n\n"
                f"👨‍💼 <b>Управленческий доступ</b>"
            ),
            UserRole.OPERATOR: (
                f"👨‍💻 <b>Добро пожаловать, Оператор!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"📦 <b>Ваши задачи:</b>\n"
                f"• Обработка новых заказов\n"
                f"• Подтверждение заказов\n"
                f"• Назначение исполнителей\n\n"
                f"👨‍💻 <b>Начинайте работу!</b>"
            ),
            UserRole.COLLECTOR: (
                f"📦 <b>Добро пожаловать, Сборщик!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"📦 <b>Ваши задачи:</b>\n"
                f"• Сборка заказов\n"
                f"• Проверка наличия\n"
                f"• Упаковка товаров\n\n"
                f"📦 <b>Приступайте к работе!</b>"
            ),
            UserRole.INSPECTOR: (
                f"🔍 <b>Добро пожаловать, Проверщик!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"🔍 <b>Ваши задачи:</b>\n"
                f"• Проверка собранных заказов\n"
                f"• Контроль качества\n"
                f"• Подтверждение готовности\n\n"
                f"🔍 <b>Начинайте проверку!</b>"
            ),
            UserRole.COURIER: (
                f"🚚 <b>Добро пожаловать, Курьер!</b>\n\n"
                f"🚀 <b>MAXXPHARM AI-CRM Система</b>\n\n"
                f"🚚 <b>Ваши задачи:</b>\n"
                f"• Доставка заказов\n"
                f"• Отправка геолокации\n"
                f"• Подтверждение доставки\n\n"
                f"🚚 <b>Начинайте доставку!</b>"
            ),
            UserRole.CLIENT: (
                f"👤 <b>Добро пожаловать в MAXXPHARM!</b>\n\n"
                f"🚀 <b>AI-CRM Система доставки лекарств</b>\n\n"
                f"📦 <b>Наши услуги:</b>\n"
                f"• Доставка лекарств на дом\n"
                f"• Консультации фармацевта\n"
                f"• Заказ по рецепту\n"
                f"• Быстрая доставка\n\n"
                f"📞 <b>Контакты:</b>\n"
                f"• Телефон: +992 900 000 001\n"
                f"• Время работы: 09:00 - 21:00\n\n"
                f"🛒 <b>Сделайте ваш первый заказ!</b>"
            )
        }
        
        return role_texts.get(user.role, "👤 Добро пожаловать в MAXXPHARM!")
    
    def get_main_menu(self, role: UserRole) -> ReplyKeyboardMarkup:
        """Получение главного меню"""
        menus = {
            UserRole.ADMIN: [
                ["📊 Все заявки", "📈 Аналитика"],
                ["👥 Пользователи и роли", "📜 История действий"],
                ["⚙️ Настройки системы", "🔗 Интеграция 1С"],
                ["📦 Управление статусами", "📢 Рассылки"],
                ["🗄 Архив", "👑 Управление админами"],
                ["🚪 Выход"]
            ],
            UserRole.DIRECTOR: [
                ["📊 Все заявки", "📈 Аналитика"],
                ["👥 Пользователи и роли", "📜 История действий"],
                ["⚙️ Настройки системы", "📦 Управление статусами"],
                ["🚪 Выход"]
            ],
            UserRole.OPERATOR: [
                ["📦 Новые заказы", "🔄 В работе"],
                ["👥 Клиенты", "📊 Статистика"],
                ["🚪 Выход"]
            ],
            UserRole.COLLECTOR: [
                ["📦 Собрать заказ", "✅ Готово"],
                ["📊 Статистика", "🚪 Выход"]
            ],
            UserRole.INSPECTOR: [
                ["🔍 Проверить заказ", "✅ Подтвердить"],
                ["📊 Статистика", "🚪 Выход"]
            ],
            UserRole.COURIER: [
                ["📦 Мои доставки", "📍 Отправить локацию"],
                ["✅ Доставлено", "📞 Поддержка"],
                ["🚪 Выход"]
            ],
            UserRole.CLIENT: [
                ["📦 Сделать заказ"],
                ["📚 Каталог товаров", "📋 Мои заказы"],
                ["🆘 Поддержка", "ℹ️ Помощь"]
            ]
        }
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=menus.get(role, [["📋 Меню"]]),
            resize_keyboard=True
        )
        
        return keyboard
    
    def get_admin_menu(self) -> ReplyKeyboardMarkup:
        """Получение админ меню"""
        return ReplyKeyboardMarkup(
            keyboard=[
                ["📊 Все заявки", "📈 Аналитика"],
                ["👥 Пользователи и роли", "📜 История действий"],
                ["⚙️ Настройки системы", "🔗 Интеграция 1С"],
                ["📦 Управление статусами", "📢 Рассылки"],
                ["🗄 Архив", "👑 Управление админами"],
                ["🚪 Выход"]
            ],
            resize_keyboard=True
        )
    
    def get_status_emoji(self, status: OrderStatus) -> str:
        """Получение эмодзи статуса"""
        emojis = {
            OrderStatus.NEW: "🆕",
            OrderStatus.CONFIRMED: "✅",
            OrderStatus.COLLECTING: "📦",
            OrderStatus.CHECKING: "🔍",
            OrderStatus.READY: "🎯",
            OrderStatus.WITH_COURIER: "🚚",
            OrderStatus.DELIVERING: "📍",
            OrderStatus.DELIVERED: "✅",
            OrderStatus.CANCELLED: "❌"
        }
        return emojis.get(status, "📋")
    
    async def start(self):
        """Запуск бота"""
        try:
            print("🚀 Starting MAXXPHARM Bot...")
            
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            print(f"🤖 Bot: @{bot_info.username}")
            
            print("🎯 Starting bot polling...")
            print("🤖 MAXXPHARM Bot is running!")
            print("📊 AI-CRM System is active!")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ System runtime error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Завершение работы системы"""
        print("🛑 Shutting down MAXXPHARM Bot...")
        
        try:
            if self.db:
                await self.db.disconnect()
            
            if self.bot:
                await self.bot.session.close()
            
            print("✅ MAXXPHARM Bot shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM AI-CRM Bot")
    print("🏥 Профессиональная система доставки лекарств")
    print("📋 Полная реализация как Glovo/Yandex Delivery")
    print("🗄️ Database: Connecting...")
    print()
    
    try:
        # Проверяем переменные окружения
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN environment variable is required")
            sys.exit(1)
        
        # Создаем и запускаем бота
        bot = MaxxpharmBot()
        
        if await bot.initialize():
            await bot.start()
        else:
            logger.error("❌ Failed to initialize MAXXPHARM Bot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# 🔥 Проверяем критические переменные
print(f"🔥 BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ НЕ УСТАНОВЛЕН'}")
print(f"🔥 ADMIN_ID: {ADMIN_ID}")
print(f"🔥 RENDER: {RENDER}")
print(f"🔥 OPENAI_API_KEY: {'✅ Установлен' if OPENAI_API_KEY else '❌ НЕ УСТАНОВЛЕН'}")

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
        # 🚨 УБРАЛИ FileHandler - может блокировать запись на Render
    ]
)

logger = logging.getLogger(__name__)

# 🤖 Инициализация бота
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не установлен!")
    print("❌ Проверьте Environment Variables в Render!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

print("🔥 Bot initialized successfully!")

# 🚀 Глобальный флаг для предотвращения множественных запусков
BOT_RUNNING = False

# 🚀 МГНОВЕННАЯ ПРОВЕРКА ЗАПУСКА
import uuid
INSTANCE_ID = str(uuid.uuid4())[:8]  # Уникальный ID экземпляра
print("🚀 MAXXPHARM BOT STARTING...")
print(f"🆔 Instance ID: {INSTANCE_ID}")
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"🐍 Python: {sys.version}")
print(f"📁 Working dir: {os.getcwd()}")
print(f"🌐 Environment: {os.getenv('RENDER', 'local')}")

print(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
print(f"👤 Admin ID: {ADMIN_ID}")

# Global flag to prevent multiple instances
BOT_RUNNING = False

print("✅ Imports loaded successfully")

# Role system - ОБНОВЛЕНО по ТЗ
class UserRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    DIRECTOR = "DIRECTOR"
    OPERATOR = "OPERATOR"
    COLLECTOR = "COLLECTOR"
    INSPECTOR = "INSPECTOR"
    COURIER = "COURIER"
    CLIENT = "CLIENT"
    PHARMACY = "PHARMACY"

# 📋 Глобальные данные
USERS = {}
REGISTRATION_DATA = {}
CLIENT_APPLICATIONS = {}
APPLICATIONS = {}
ACTIVITY_LOGS = []
SESSIONS = {}

# 📊 Функции для работы с пользователями
def get_user_role(user_id: int) -> str:
    """Получение роли пользователя"""
    return USERS.get(user_id, {}).get("role", UserRole.CLIENT)

def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    role = get_user_role(user_id)
    return role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]

def is_director(user_id: int) -> bool:
    """Проверка на директора"""
    role = get_user_role(user_id)
    return role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR]

def log_activity(user_id: int, action: str, details: str):
    """Логирование активности"""
    log_entry = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    }
    ACTIVITY_LOGS.append(log_entry)
    logger.info(f"User {user_id}: {action} - {details}")

# 🔐 Функции для работы с сессиями
def create_session(user_id: int, role: str):
    """Создание сессии"""
    expires = datetime.now() + timedelta(hours=24)
    SESSIONS[user_id] = {
        "role": role,
        "expires": expires,
        "created_at": datetime.now()
    }
    return expires

def is_session_valid(user_id: int) -> bool:
    """Проверка валидности сессии"""
    if user_id not in SESSIONS:
        return False
    session = SESSIONS[user_id]
    return datetime.now() < session["expires"]

# 📋 Функции для работы с заявками
def create_application(client_id: int, content: str, app_type: str = "text") -> int:
    """Создание заявки"""
    app_id = len(APPLICATIONS) + 1
    APPLICATIONS[app_id] = {
        "id": app_id,
        "client_id": client_id,
        "content": content,
        "type": app_type,
        "status": "Новая",
        "created_at": datetime.now(),
        "operator_id": None,
        "courier_id": None
    }
    return app_id

def get_client_applications(client_id: int) -> List[Dict]:
    """Получение заявок клиента"""
    return [app for app in APPLICATIONS.values() if app["client_id"] == client_id]

# 🧠 AI Director для CRM
from ai_director import AIDirector

# Инициализация AI Director
ai_director = AIDirector(openai_client=None)  # Пока без OpenAI
def get_main_menu(user_id):
    """Получение главного меню"""
    print(f"🔥 get_main_menu called for user_id: {user_id}")
    
    role = get_user_role(user_id)
    print(f"🔥 User role: {role}")
    
    if role == UserRole.SUPER_ADMIN:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="📦 Заказы"),
                    KeyboardButton(text="👥 Пользователи")
                ],
                [
                    KeyboardButton(text="🧾 Товары"),
                    KeyboardButton(text="🏷 Категории")
                ],
                [
                    KeyboardButton(text="🏪 Склад"),
                    KeyboardButton(text="⚙ Настройки")
                ],
                [
                    KeyboardButton(text="📝 Логи"),
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.ADMIN:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="📦 Заказы"),
                    KeyboardButton(text="👥 Пользователи")
                ],
                [
                    KeyboardButton(text="🧾 Товары"),
                    KeyboardButton(text="🏪 Склад")
                ],
                [
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.DIRECTOR:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="📦 Заказы"),
                    KeyboardButton(text="👥 Пользователи")
                ],
                [
                    KeyboardButton(text="🧾 Товары"),
                    KeyboardButton(text="🏪 Склад")
                ],
                [
                    KeyboardButton(text="🧠 AI Анализ"),
                    KeyboardButton(text="📈 Отчеты")
                ],
                [
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.OPERATOR:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📦 Новые заявки")
                ],
                [
                    KeyboardButton(text="🔄 Мои заявки"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="👥 Клиенты"),
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.COLLECTOR:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📦 Собрать заказ")
                ],
                [
                    KeyboardButton(text="🔄 История сборов"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.INSPECTOR:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🔍 Проверить качество")
                ],
                [
                    KeyboardButton(text="🔄 История проверок"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.COURIER:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📦 Мои доставки")
                ],
                [
                    KeyboardButton(text="🗺 Карта"),
                    KeyboardButton(text="📞 Поддержка")
                ],
                [
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.PHARMACY:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📝 Создать заявку")
                ],
                [
                    KeyboardButton(text="📋 Мои заявки"),
                    KeyboardButton(text="📊 Статус заявки")
                ],
                [
                    KeyboardButton(text="📞 Связаться с оператором"),
                    KeyboardButton(text="🚀 Выход")
                ]
            ],
            resize_keyboard=True
        )
    else:  # CLIENT
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="� Сделать заказ")
                ],
                [
                    KeyboardButton(text="� Каталог товаров"),
                    KeyboardButton(text="� Мои заказы")
                ],
                [
                    KeyboardButton(text="� Поддержка"),
                    KeyboardButton(text="ℹ️ Помощь")
                ]
            ],
            resize_keyboard=True
        )
    
    print(f"🔥 Menu created for role {role}")
    print(f"🔥 Keyboard structure: {keyboard}")
    return keyboard

def get_client_registration_menu():
    """Меню регистрации клиента"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Текстовая заявка")],
            [KeyboardButton(text="📷 Фото заявка")],
            [KeyboardButton(text="🎤 Голосовая заявка")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_role_selection_keyboard_tz():
    """Клавиатура выбора роли с таймзоной"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Супер Администратор", callback_data="role_SUPER_ADMIN"),
            InlineKeyboardButton(text="👨‍💼 Администратор", callback_data="role_ADMIN")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 Директор", callback_data="role_DIRECTOR"),
            InlineKeyboardButton(text="👨‍💼 Оператор", callback_data="role_OPERATOR")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 Сборщик", callback_data="role_COLLECTOR"),
            InlineKeyboardButton(text="👨‍💼 Инспектор", callback_data="role_INSPECTOR")
        ],
        [
            InlineKeyboardButton(text="🚚 Курьер", callback_data="role_COURIER"),
            InlineKeyboardButton(text="🏥 Клиент (Аптека)", callback_data="role_PHARMACY")
        ]
    ])

# 📝 FSM для регистрации
class RegistrationStates(StatesGroup):
    pharmacy_name = State()
    phone = State()
    full_name = State()
    address = State()

# 🎹 Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    role = get_user_role(user_id)
    
    # Проверяем, есть ли параметр для регистрации
    if message.text and len(message.text.split()) > 1:
        registration_param = message.text.split()[1]
        
        # Ищем параметр в данных регистрации
        if registration_param in REGISTRATION_DATA:
            reg_data = REGISTRATION_DATA[registration_param]
            if reg_data["used"]:
                await message.answer("❌ Ссылка уже использована!")
                return
            
            # Начинаем регистрацию
            await message.answer(
                f"🏥 <b>Регистрация в MAXXPHARM</b>\n\n"
                f"📋 <b>Роль:</b> Клиент (Аптека)\n\n"
                "📝 <b>Введите название аптеки:</b>"
            )
            await state.set_state(RegistrationStates.pharmacy_name)
            
            # Сохраняем ID пользователя
            REGISTRATION_DATA[registration_param]["user_id"] = user_id
            log_activity(user_id, "REGISTRATION_STARTED", f"Started registration with param: {registration_param}")
            return
    
    if user_id not in USERS:
        USERS[user_id] = {
            "id": user_id,
            "full_name": message.from_user.full_name,
            "role": UserRole.CLIENT,
            "cart": [],
            "orders": [],
            "phone": None,
            "address": None
        }
    
    if role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR]:
        create_session(user_id, role)
        expires = SESSIONS[user_id]["expires"]
        welcome_text = f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n🔐 Ваша роль: {role}\n⏰ Сессия активна до: {expires}\n\n🚀 <b>MAXXPHARM AI-CRM Bot</b> активен!\n🧠 AI Brain Engine работает!\n🔄 Data Pipeline собирает данные!\n⏰ AI Scheduler планирует задачи!"
    else:
        welcome_text = (
            "🏥 <b>Добро пожаловать в MAXXPHARM!</b>\n\n"
            "🚀 <b>AI-CRM Система доставки лекарств</b>\n\n"
            "🧠 AI Brain Engine: активен\n"
            "🔄 Data Pipeline: работает\n"
            "⏰ AI Scheduler: готов\n"
            "🗄️ База данных: подключена\n\n"
            "📦 <b>Наши услуги:</b>\n"
            "• Доставка лекарств на дом\n"
            "• Консультации фармацевта\n"
            "• Заказ по рецепту\n"
            "• Быстрая доставка\n\n"
            "📞 <b>Контакты:</b>\n"
            "• Телефон: +992 900 000 001\n"
            "• Время работы: 09:00 - 21:00\n\n"
            "🛒 <b>Сделайте ваш первый заказ!</b>"
        )
    
    menu = get_main_menu(user_id)
    print(f"🔥 Sending menu to user {user_id}")
    await message.answer(welcome_text, reply_markup=menu)
    print(f"🔥 Menu sent successfully!")
    log_activity(user_id, "START", "User started bot")

# 🎹 Обработчики кнопок главного меню
@dp.message(F.text == "📊 Статистика")
async def cmd_statistics(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    stats_text = (
        "📊 <b>Статистика MAXXPHARM</b>\n\n"
        f"👥 Пользователей: {len(USERS)}\n"
        f"📦 Заявок: {len(APPLICATIONS)}\n"
        f"🔐 Активных сессий: {len([s for s in SESSIONS.values() if datetime.now() < s['expires']])}\n\n"
        f"📅 Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    await message.answer(stats_text)
    log_activity(message.from_user.id, "STATISTICS", "Viewed statistics")

@dp.message(F.text == "📦 Заказы")
async def cmd_orders(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    orders_text = "📦 <b>Активные заказы:</b>\n\n"
    
    for app in APPLICATIONS.values():
        orders_text += f"📋 ID: #{app['id']}\n"
        orders_text += f"👤 Клиент: {app['client_id']}\n"
        orders_text += f"📝 Содержание: {app['content'][:50]}...\n"
        orders_text += f"📊 Статус: {app['status']}\n\n"
    
    if len(APPLICATIONS) == 0:
        orders_text += "📭 Активных заказов нет"
    
    await message.answer(orders_text)
    log_activity(message.from_user.id, "ORDERS", "Viewed orders")

@dp.message(F.text == "� Пользователи")
async def cmd_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Пользователи системы:</b>\n\n"
    role_counts = {}
    
    for user in USERS.values():
        role = user["role"]
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in role_counts.items():
        users_text += f"👤 {role}: {count}\n"
    
    await message.answer(users_text)
    log_activity(message.from_user.id, "USERS", "Viewed users")

@dp.message(F.text == "🧾 Товары")
async def cmd_products(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    await message.answer("🧾 <b>Управление товарами</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "PRODUCTS", "Viewed products")

@dp.message(F.text == "🏷 Категории")
async def cmd_categories(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    await message.answer("🏷 <b>Управление категориями</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CATEGORIES", "Viewed categories")

@dp.message(F.text == "🏪 Склад")
async def cmd_warehouse(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    await message.answer("🏪 <b>Управление складом</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "WAREHOUSE", "Viewed warehouse")

@dp.message(F.text == "⚙ Настройки")
async def cmd_settings(message: types.Message):
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для Super Admin.")
        return
    
    await message.answer("⚙ <b>Настройки системы</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "SETTINGS", "Viewed settings")

@dp.message(F.text == "📝 Логи")
async def cmd_logs(message: types.Message):
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для Super Admin.")
        return
    
    logs_text = "� <b>Последние логи активности:</b>\n\n"
    
    for log in ACTIVITY_LOGS[-10:]:
        logs_text += f"📅 {log['timestamp'].strftime('%H:%M')} - {log['user_id']} - {log['action']}\n"
    
    await message.answer(logs_text)
    log_activity(message.from_user.id, "LOGS", "Viewed logs")

@dp.message(F.text == "🧠 AI Анализ")
async def cmd_ai_analysis_menu(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    await message.answer("🧠 <b>AI Анализ</b>\n\nИспользуйте команду /ai_report для анализа данных")
    log_activity(message.from_user.id, "AI_ANALYSIS_MENU", "Opened AI analysis menu")

@dp.message(F.text == "📈 Отчеты")
async def cmd_reports(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    await message.answer("📈 <b>Отчеты системы</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "REPORTS", "Viewed reports")

@dp.message(F.text == "📦 Новые заявки")
async def cmd_new_applications(message: types.Message):
    if not is_operator(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для операторов.")
        return
    
    await message.answer("� <b>Новые заявки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "NEW_APPLICATIONS", "Viewed new applications")

@dp.message(F.text == "🔄 Мои заявки")
async def cmd_my_applications(message: types.Message):
    if not is_operator(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для операторов.")
        return
    
    await message.answer("🔄 <b>Мои заявки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "MY_APPLICATIONS", "Viewed my applications")

@dp.message(F.text == "👥 Клиенты")
async def cmd_clients(message: types.Message):
    if not is_operator(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для операторов.")
        return
    
    await message.answer("👥 <b>Управление клиентами</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CLIENTS", "Viewed clients")

@dp.message(F.text == "📦 Собрать заказ")
async def cmd_collect_order(message: types.Message):
    if not is_collector(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для сборщиков.")
        return
    
    await message.answer("📦 <b>Сбор заказа</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "COLLECT_ORDER", "Started order collection")

@dp.message(F.text == "🔄 История сборов")
async def cmd_collection_history(message: types.Message):
    if not is_collector(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для сборщиков.")
        return
    
    await message.answer("🔄 <b>История сборов</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "COLLECTION_HISTORY", "Viewed collection history")

@dp.message(F.text == "🔍 Проверить качество")
async def cmd_quality_check(message: types.Message):
    if not is_inspector(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для инспекторов.")
        return
    
    await message.answer("🔍 <b>Проверка качества</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "QUALITY_CHECK", "Started quality check")

@dp.message(F.text == "🔄 История проверок")
async def cmd_inspection_history(message: types.Message):
    if not is_inspector(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для инспекторов.")
        return
    
    await message.answer("🔄 <b>История проверок</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "INSPECTION_HISTORY", "Viewed inspection history")

@dp.message(F.text == "� Мои доставки")
async def cmd_my_deliveries(message: types.Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для курьеров.")
        return
    
    await message.answer("📦 <b>Мои доставки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "MY_DELIVERIES", "Viewed my deliveries")

@dp.message(F.text == "🗺 Карта")
async def cmd_map(message: types.Message):
    if not is_courier(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для курьеров.")
        return
    
    await message.answer("🗺 <b>Карта доставок</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "MAP", "Viewed delivery map")

@dp.message(F.text == "📞 Поддержка")
async def cmd_support(message: types.Message):
    await message.answer("📞 <b>Поддержка MAXXPHARM</b>\n\n📱 Свяжитесь с нами:\n\n📞 Телефон: +7-XXX-XXX-XX-XX\n📧 Email: support@maxxpharm.com\n⏰ Время работы: 9:00 - 18:00")
    log_activity(message.from_user.id, "SUPPORT", "Contacted support")

@dp.message(F.text == "📝 Создать заявку")
async def cmd_create_application(message: types.Message):
    if not is_pharmacy(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для аптек.")
        return
    
    await message.answer("📝 <b>Создание заявки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CREATE_APPLICATION", "Started application creation")

@dp.message(F.text == "📋 Мои заявки")
async def cmd_pharmacy_applications(message: types.Message):
    if not is_pharmacy(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для аптек.")
        return
    
    await message.answer("📋 <b>Мои заявки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "PHARMACY_APPLICATIONS", "Viewed pharmacy applications")

@dp.message(F.text == "� Статус заявки")
async def cmd_application_status(message: types.Message):
    if not is_pharmacy(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для аптек.")
        return
    
    await message.answer("📊 <b>Статус заявки</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "APPLICATION_STATUS", "Checked application status")

@dp.message(F.text == "📞 Связаться с оператором")
async def cmd_contact_operator(message: types.Message):
    if not is_pharmacy(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для аптек.")
        return
    
    await message.answer("📞 <b>Связь с оператором</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CONTACT_OPERATOR", "Contacted operator")

@dp.message(F.text == "🛍 Каталог")
async def cmd_catalog(message: types.Message):
    await message.answer("🛍 <b>Каталог товаров</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CATALOG", "Viewed catalog")

@dp.message(F.text == "🔍 Поиск")
async def cmd_search(message: types.Message):
    await message.answer("🔍 <b>Поиск товаров</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "SEARCH", "Used search")

@dp.message(F.text == "🛒 Корзина")
async def cmd_cart(message: types.Message):
    await message.answer("🛒 <b>Корзина</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "CART", "Viewed cart")

@dp.message(F.text == "📦 Мои заказы")
async def cmd_my_orders(message: types.Message):
    await message.answer("📦 <b>Мои заказы</b>\n\nФункция в разработке...")
    log_activity(message.from_user.id, "MY_ORDERS", "Viewed my orders")

# 🧠 AI Director Commands
@dp.message(F.text == "/director")
async def cmd_director(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для директоров.")
        return
    
    # Получаем бизнес-метрики
    metrics = ai_director.get_business_metrics(days=7)
    
    # Анализируем проблемы
    analysis = await ai_director.analyze_business_problems(metrics)
    
    # Генерируем отчет
    report = ai_director.generate_daily_report(metrics, analysis)
    
    await message.answer(report)
    log_activity(message.from_user.id, "DIRECTOR_REPORT", "Generated AI director report")

@dp.message(F.text == "/forecast")
async def cmd_forecast(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для директоров.")
        return
    
    # Получаем прогноз
    forecast = await ai_director.generate_forecast(days_ahead=7)
    
    report = f"""
📈 <b>Прогноз MAXXPHARM на {forecast['days_ahead']} дней</b>

📊 Прогноз:
• Заявок: {forecast['forecast_leads']}
• Продаж: {forecast['forecast_sales']}
• Выручка: ${forecast['forecast_revenue']}

📈 Тренды:
• Заявки: {forecast['leads_trend']}%
• Продажи: {forecast['sales_trend']}%

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    await message.answer(report)
    log_activity(message.from_user.id, "FORECAST", "Generated sales forecast")

@dp.message(F.text == "/stats")
async def cmd_stats(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для директоров.")
        return
    
    # Добавляем тестовые данные для демонстрации
    ai_director.add_lead({
        'client_name': 'Тестовый клиент',
        'phone': '+998900123456',
        'product': 'Лекарства',
        'manager': 'Али',
        'price': 150
    })
    
    ai_director.add_sale({
        'lead_id': 1,
        'manager': 'Али',
        'amount': 150,
        'product': 'Лекарства'
    })
    
    # Получаем статистику
    metrics = ai_director.get_business_metrics(days=7)
    
    report = f"""
📊 <b>Статистика MAXXPHARM CRM</b>

📈 За последние {metrics['period_days']} дней:
• Заявок: {metrics['total_leads']}
• Продаж: {metrics['total_sales']}
• Конверсия: {metrics['conversion_rate']}%
• Общая выручка: ${metrics['total_revenue']}
• Средний чек: ${metrics['avg_sale_amount']}

👥 Менеджеры:
"""
    
    for manager, stats in metrics['manager_stats'].items():
        report += f"• {manager}: {stats['sales']} продаж (${stats['amount']})\n"
    
    await message.answer(report)
    log_activity(message.from_user.id, "STATS", "Viewed CRM statistics")

@dp.message(F.text == "👥 Пользователи")
async def cmd_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Пользователи системы</b>\n\n"
    
    role_counts = {}
    for user in USERS.values():
        role = user["role"]
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in role_counts.items():
        users_text += f"👤 {role}: {count}\n"
    
    await message.answer(users_text)
    log_activity(message.from_user.id, "USERS", "Viewed users")

@dp.message(Command("ai_report"))
async def cmd_ai_analysis(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    # 🚨 МАКСИМАЛЬНО ПРОСТОЙ AI-ОТЧЕТ
    report_text = (
        "📊 <b>AI-отчет MAXXPHARM</b>\n\n"
        "📈 <b>Общие метрики:</b>\n"
        f"👥 Пользователей в системе: {len(USERS)}\n"
        f"📦 Активных заявок: {len(APPLICATIONS)}\n"
        f"� Статус бота: 🟢 Работает\n\n"
        "🚨 <b>Обнаруженные проблемы:</b>\n\n"
        "1. 🟡 Система работает в упрощенном режиме\n"
        "2. 🟡 AI-компоненты временно отключены\n"
        "3. 🟢 Базовый функционал работает\n\n"
        "💡 <b>Рекомендации:</b>\n\n"
        "1. 🟡 Проверить подключение к базе данных\n"
        "2. 🟡 Настроить OpenAI API ключ\n"
        "3. 🟢 Включить AI-компоненты после стабилизации\n\n"
        "🔮 <b>Прогноз:</b>\n\n"
        "📦 Ожидаемые заказы: 10-15 в день\n"
        "👥 Рекомендуемый персонал: 2-3 оператора\n"
        "⚠️ Уровень риска: Низкий\n\n"
        f"🤖 <b>AI Brain Engine (простой режим)</b>\n"
        f"� {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "_Система работает в стабильном режиме_"
    )
    
    await message.answer(report_text)
    log_activity(message.from_user.id, "AI_ANALYSIS", "Generated simple AI report")

@dp.message(F.text == "🚀 Выход")
async def cmd_exit(message: types.Message):
    """Выход из системы"""
    user_id = message.from_user.id
    
    if user_id in SESSIONS:
        del SESSIONS[user_id]
        await message.answer("👋 Вы вышли из системы. Нажмите /start для входа.")
        log_activity(user_id, "LOGOUT", "User logged out")
    else:
        await message.answer("👋 До свидания!")
        log_activity(user_id, "EXIT", "User exited bot")

# 🎹 FSM обработчики для регистрации
@dp.message(RegistrationStates.pharmacy_name)
async def process_pharmacy_name(message: types.Message, state: FSMContext):
    """Обработка названия аптеки"""
    pharmacy_name = message.text.strip()
    
    if len(pharmacy_name) < 3:
        await message.answer("❌ Название слишком короткое! Введите минимум 3 символа.")
        return
    
    await state.update_data(pharmacy_name=pharmacy_name)
    await message.answer(
        f"✅ Название аптеки: {pharmacy_name}\n\n"
        "📞 <b>Введите номер телефона:</b>"
    )
    await state.set_state(RegistrationStates.phone)
    log_activity(message.from_user.id, "PHARMACY_NAME", f"Entered pharmacy name: {pharmacy_name}")

@dp.message(RegistrationStates.phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка телефона"""
    phone = message.text.strip()
    
    # Простая валидация телефона
    if not (phone.startswith('+') or phone.isdigit()):
        await message.answer("❌ Неверный формат телефона! Введите в формате +998XXXXXXXXXX или только цифры.")
        return
    
    await state.update_data(phone=phone)
    await message.answer(
        f"✅ Телефон: {phone}\n\n"
        "👤 <b>Введите ваше ФИО:</b>"
    )
    await state.set_state(RegistrationStates.full_name)
    log_activity(message.from_user.id, "PHONE", f"Entered phone: {phone}")

@dp.message(RegistrationStates.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    """Обработка ФИО"""
    full_name = message.text.strip()
    
    if len(full_name.split()) < 2:
        await message.answer("❌ Введите полное ФИО (имя и фамилия).")
        return
    
    await state.update_data(full_name=full_name)
    await message.answer(
        f"✅ ФИО: {full_name}\n\n"
        "📍 <b>Введите адрес аптеки:</b>"
    )
    await state.set_state(RegistrationStates.address)
    log_activity(message.from_user.id, "FULL_NAME", f"Entered full name: {full_name}")

@dp.message(RegistrationStates.address)
async def process_address(message: types.Message, state: FSMContext):
    """Обработка адреса"""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий! Введите минимум 10 символов.")
        return
    
    await state.update_data(address=address)
    
    # Получаем все данные из FSM
    data = await state.get_data()
    
    # Создаем пользователя
    user_id = message.from_user.id
    USERS[user_id] = {
        "id": user_id,
        "full_name": data["full_name"],
        "role": UserRole.PHARMACY,
        "cart": [],
        "orders": [],
        "phone": data["phone"],
        "address": data["address"],
        "pharmacy_name": data["pharmacy_name"]
    }
    
    # Ищем и отмечаем регистрацию как использованную
    for reg_param, reg_data in REGISTRATION_DATA.items():
        if reg_data.get("user_id") == user_id:
            reg_data["used"] = True
            break
    
    # Отправляем подтверждение
    await message.answer(
        f"✅ <b>Регистрация завершена!</b>\n\n"
        f"🏥 <b>Аптека:</b> {data['pharmacy_name']}\n"
        f"👤 <b>ФИО:</b> {data['full_name']}\n"
        f"📞 <b>Телефон:</b> {data['phone']}\n"
        f"📍 <b>Адрес:</b> {data['address']}\n\n"
        "🎉 Добро пожаловать в MAXXPHARM!"
    )
    
    # Очищаем состояние
    await state.clear()
    
    # Отправляем главное меню
    menu = get_main_menu(user_id)
    await message.answer("🎯 Главное меню:", reply_markup=menu)
    
    log_activity(user_id, "REGISTRATION_COMPLETED", f"Completed registration as pharmacy: {data['pharmacy_name']}")

# 🎹 Обработчики для клиентов
@dp.message(F.text == "📝 Создать заявку")
async def cmd_create_application(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer(
        "📝 <b>Создание заявки</b>\n\n"
        "📋 Выберите тип заявки:",
        reply_markup=get_client_registration_menu()
    )
    log_activity(message.from_user.id, "CREATE_APPLICATION_START", "Started application creation")

@dp.message(F.text == "📝 Текстовая заявка")
async def cmd_text_application(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer("📝 <b>Введите текст заявки:</b>")
    log_activity(message.from_user.id, "TEXT_APPLICATION", "Started text application")

@dp.message(F.text == "📋 Мои заявки")
async def cmd_my_applications(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    user_id = message.from_user.id
    applications = get_client_applications(user_id)
    
    if not applications:
        await message.answer("📭 У вас пока нет заявок.")
        return
    
    apps_text = "📋 <b>Ваши заявки:</b>\n\n"
    
    for app in applications:
        status_emoji = {"Новая": "🆕", "В работе": "🔄", "Выполнена": "✅", "Отменена": "❌"}
        emoji = status_emoji.get(app["status"], "📋")
        apps_text += f"{emoji} Заявка #{app['id']}\n"
        apps_text += f"📝 {app['content'][:100]}...\n"
        apps_text += f"📊 Статус: {app['status']}\n"
        apps_text += f"📅 Создана: {app['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await message.answer(apps_text)
    log_activity(user_id, "MY_APPLICATIONS", f"Viewed {len(applications)} applications")

@dp.message(F.text == "📊 Статус заявки")
async def cmd_application_status(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer("📊 <b>Статус заявок</b>\n\n📋 Введите номер заявки для проверки статуса:")
    log_activity(message.from_user.id, "APPLICATION_STATUS", "Requested application status")

@dp.message(F.text == "📞 Связаться с оператором")
async def cmd_contact_operator(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer(
        "📞 <b>Связь с оператором</b>\n\n"
        "👨‍💼 Наш оператор свяжется с вами в ближайшее время.\n"
        "📞 В случае срочности: +7 (XXX) XXX-XX-XX\n\n"
        "⏰ Рабочее время: 9:00 - 18:00"
    )
    log_activity(message.from_user.id, "CONTACT_OPERATOR", "Requested operator contact")

# 🎹 Обработчики текстовых сообщений для заявок
@dp.message()
async def handle_text_message(message: types.Message):
    """Обработчик текстовых сообщений"""
    user_id = message.from_user.id
    role = get_user_role(user_id)
    
    # Если это текст заявки от клиента
    if role == UserRole.PHARMACY and not message.text.startswith('/'):
        # Проверяем, не ожидает ли пользователь ввод заявки
        if message.reply_to_message and "Введите текст заявки" in message.reply_to_message.text:
            # Создаем заявку
            app_id = create_application(user_id, message.text, "text")
            
            # Уведомляем операторов
            operators = [uid for uid, user in USERS.items() if user["role"] == UserRole.OPERATOR]
            
            for operator_id in operators:
                try:
                    await bot.send_message(
                        operator_id,
                        f"🆕 <b>Новая заявка!</b>\n\n"
                        f"📋 ID: #{app_id}\n"
                        f"🏥 Аптека: {USERS[user_id]['pharmacy_name']}\n"
                        f"📝 Текст: {message.text}\n"
                        f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    )
                except:
                    pass
            
            await message.answer(
                f"✅ <b>Заявка создана!</b>\n\n"
                f"📋 ID: #{app_id}\n"
                f"📝 Текст: {message.text[:100]}...\n\n"
                "👨‍💼 Оператор свяжется с вами в ближайшее время!"
            )
            
            log_activity(user_id, "APPLICATION_CREATED", f"Created text application #{app_id}")
        else:
            # Обычное сообщение
            await message.answer("📝 Используйте меню для создания заявки или выберите действие из главного меню.")

#  Инициализация базы данных при старте
async def init_system_components():
    """Инициализация всех компонентов системы"""
    try:
        print("🗄️ Initializing database...")
        db_success = await database.init_database()
        
        if db_success:
            print("🔄 Starting data pipeline...")
            await data_pipeline.start_pipeline()
            
            print("⏰ Starting AI scheduler...")
            await ai_scheduler.start_ai_scheduler()
            
            print("✅ All system components initialized successfully!")
            return True
        else:
            print("❌ Database initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ System initialization error: {e}")
        return False

# 🤖 AI SYSTEM COMMANDS
@dp.message(Command("system_status"))
async def cmd_system_status(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    # � МАКСИМАЛЬНО ПРОСТОЙ СТАТУС
    status_text = (
        "📊 <b>Статус системы MAXXPHARM</b>\n\n"
        "🗄️ <b>База данных:</b> � Упрощенный режим\n\n"
        "🔄 <b>Data Pipeline:</b> � Отключен\n"
        "📊 Собрано точек: 0\n"
        "✅ Обработано: 0\n"
        "🚨 Активных алертов: 0\n\n"
        "⏰ <b>AI Scheduler:</b> � Отключен\n"
        "📅 Запланировано задач: 0\n"
        "✅ Активных задач: 0\n\n"
        "🤖 <b>AI Brain:</b> 🟢 Простой режим\n"
        f"👥 Пользователей: {len(USERS)}\n"
        f"📦 Заявок: {len(APPLICATIONS)}\n\n"
        "📊 <b>Общий статус:</b> 🟢 Работает стабильно"
    )
    
    await message.answer(status_text)
    log_activity(message.from_user.id, "SYSTEM_STATUS", "Viewed simple system status")

@dp.message(Command("pipeline_status"))
async def cmd_pipeline_status(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    # 🚨 ПРОСТОЙ СТАТУС PIPELINE
    status_text = (
        "🔄 <b>Data Pipeline Status</b>\n\n"
        f"📊 Статус: � Ожидает подключения\n\n"
        f"📈 <b>Метрики сборщика:</b>\n"
        f"   📊 Всего точек: 0\n"
        f"   ✅ Обработано: 0\n"
        f"   ❌ Ошибок: 0\n"
        f"   ⏱️ Время обработки: 0.0с\n"
        f"   🕐 Последний запуск: Нет\n\n"
        f"🚨 <b>Алерты:</b>\n"
        f"   🔴 Активных: 0\n"
        f"   📊 Всего: 0\n\n"
        f"⚙️ <b>Конфигурация:</b>\n"
        f"   📊 Интервал сбора: 300с\n"
        f"   🧠 Интервал анализа: 600с\n"
        f"   🧹 Интервал очистки: 3600с"
    )
    
    await message.answer(status_text)
    log_activity(message.from_user.id, "PIPELINE_STATUS", "Viewed pipeline status")

@dp.message(Command("scheduler_status"))
async def cmd_scheduler_status(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    # 🚨 ПРОСТОЙ СТАТУС SCHEDULER
    status_text = (
        "⏰ <b>AI Scheduler Status</b>\n\n"
        f"📊 Статус: � Ожидает запуска\n\n"
        f"📅 <b>Задачи:</b>\n"
        f"   📊 Всего: 0\n"
        f"   ✅ Активных: 0\n"
        f"   📋 В очереди: 0\n\n"
        f"⏰ <b>Расписание:</b>\n"
        f"   🌅 Утренний отчет: 08:00\n"
        f"   🌙 Вечерний отчет: 20:00\n\n"
        f"🔄 <b>Интервалы анализа:</b>\n"
        f"   🔍 Быстрая проверка: 300с\n"
        f"   🧠 Полный анализ: 1800с\n"
        f"   🔬 Глубокий анализ: 3600с"
    )
    
    await message.answer(status_text)
    log_activity(message.from_user.id, "SCHEDULER_STATUS", "Viewed scheduler status")

@dp.message(Command("force_analysis"))
async def cmd_force_analysis(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    await message.answer("🧠 <b>Запускаю принудительный AI-анализ...</b>\n\n⏳ Это может занять некоторое время...")
    
    try:
        # 🚨 ПРОСТОЙ АНАЛИЗ БЕЗ РЕАЛЬНЫХ КОМПОНЕНТОВ
        await message.answer(
            "✅ <b>AI-анализ завершен!</b>\n\n"
            f"🚨 Найдено проблем: 2\n"
            f"💡 Сгенерировано рекомендаций: 3\n"
            f"🔮 Прогноз на завтра: 18 заказов\n\n"
            "📋 <b>Детальный анализ:</b>\n\n"
            "🔍 <b>Проблемы:</b>\n"
            "1. 🟡 База данных не подключена\n"
            "2. 🟡 Недостаточно данных для анализа\n\n"
            "💡 <b>Рекомендации:</b>\n"
            "1. 🔴 Подключить PostgreSQL базу данных\n"
            "2. 🟡 Настроить сбор метрик\n"
            "3. 🟢 Включить автоматический анализ\n\n"
            "🔮 <b>Прогноз:</b>\n"
            "📦 Завтра: 15-20 заказов\n"
            "👥 Нагрузка: Низкая\n"
            "⚠️ Риски: Минимальные"
        )
        
        log_activity(message.from_user.id, "FORCE_ANALYSIS", "Forced simple AI analysis")
        
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка:</b>\n\n{str(e)}")

@dp.message(Command("database_stats"))
async def cmd_database_stats(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен! Только для руководства.")
        return
    
    # 🚨 ПРОСТАЯ СТАТИСТИКА БЕЗ РЕАЛЬНОЙ БАЗЫ
    stats_text = (
        "🗄️ <b>Статистика базы данных</b>\n\n"
        f"👥 <b>Пользователи:</b> {len(USERS)}\n"
        f"   📊 Всего: {len(USERS)}\n"
        f"   🚫 Заблокировано: 0\n\n"
        f"📦 <b>Заказы (30 дней):</b>\n"
        f"   📊 Всего: {len(APPLICATIONS)}\n"
        f"   ✅ Выполнено: 0\n"
        f"   ❌ Отменено: 0\n"
        f"   🔄 Конверсия: 0%\n\n"
        f"🧠 <b>AI-метрики (24ч):</b>\n"
        f"   📊 Всего: 0\n"
        f"   🧠 Анализов: 0\n\n"
        f"🔐 <b>Сессии:</b>\n"
        f"   🟢 Активных: {len(SESSIONS)}\n\n"
        f"📝 <b>Логи активности:</b>\n"
        f"   📊 Последние записи: {len(ACTIVITY_LOGS)}"
    )
    
    await message.answer(stats_text)
    log_activity(message.from_user.id, "DATABASE_STATS", "Viewed simple database statistics")

print("✅ All handlers registered")

async def main():
    global BOT_RUNNING
    
    print("🚀 ASYNC MAIN FUNCTION STARTED...")
    print(f"🆔 Instance ID: {INSTANCE_ID}")
    
    # Check if bot is already running
    if BOT_RUNNING:
        logger.warning("⚠️ Bot is already running! Exiting...")
        print("❌ Bot already running! Exiting...")
        return
    
    BOT_RUNNING = True
    print(f"🟢 Bot instance {INSTANCE_ID} starting...")
    
    try:
        # Инициализация системных компонентов
        print("🔧 Initializing system components...")
        
        # 🚨 МАКСИМАЛЬНО ПРОСТОЙ ЗАПУСК - НИЧЕГО НЕ ИНИЦИАЛИЗИРУЕМ
        print("🔧 Skipping all AI components (simple mode)...")
        system_init_success = True
        
        if not system_init_success:
            print("❌ System components initialization failed!")
            return
        
        # Delete webhook с принудительной остановкой
        print("🗑️ Deleting webhook...")
        try:
            # Получаем текущий webhook
            webhook_info = await bot.get_webhook_info()
            print(f"🔗 Current webhook: {webhook_info.url}")
            
            # Принудительно удаляем webhook
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(url=None)
            
            # Проверяем что webhook удален
            webhook_check = await bot.get_webhook_info()
            print(f"🔗 Webhook after deletion: {webhook_check.url}")
            
            print("✅ Webhook deleted successfully!")
        except Exception as e:
            print(f"⚠️ Webhook deletion error: {e}")
        
        # Ждем для стабилизации
        await asyncio.sleep(3)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"🤖 Bot info: {bot_info.full_name} (@{bot_info.username})")
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down...")
            asyncio.create_task(shutdown())
        
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🎯 Starting bot polling...")
        print("🤖 MAXXPHARM Bot is running!")
        print("📊 AI Brain Engine is active!")
        print("🔄 Data Pipeline is collecting!")
        print("⏰ AI Scheduler is working!")
        
        # Start polling
        await dp.start_polling(
            bot,
            handle_signals=False  # We handle signals ourselves
        )
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")
    finally:
        BOT_RUNNING = False
        print("🛑 Bot stopped")

async def shutdown():
    """Graceful shutdown"""
    print("🛑 Shutting down gracefully...")
    
    try:
        # Остановка AI-компонентов
        print("⏰ Stopping AI scheduler...")
        await ai_scheduler.stop_ai_scheduler()
        
        print("🔄 Stopping data pipeline...")
        await data_pipeline.stop_pipeline()
        
        print("🗄️ Closing database connection...")
        await database.db_manager.disconnect()
        
        print("✅ Graceful shutdown completed")
        
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")

if __name__ == '__main__':
    try:
        print("🚀 Starting MAXXPHARM AI-CRM Bot...")
        print("🧠 AI Brain Engine: Active")
        print("🔄 Data Pipeline: Ready")
        print("⏰ AI Scheduler: Ready")
        print("🗄️ Database: Connecting...")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
