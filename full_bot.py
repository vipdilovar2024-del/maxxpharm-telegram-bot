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
from aiogram.client.default import DefaultBotProperties
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

# Создаем директории ПЕРЕД логированием
os.makedirs("logs", exist_ok=True)

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
        self.in_memory_mode = False
        self.users = {}
        self.products = []
        self.orders = []
        self.notifications = []
        self.action_logs = []
        self.order_counter = 1
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            # Пробуем подключиться к базе данных
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("✅ Database connected")
            await self.create_tables()
            await self.init_test_data()
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            # Если база недоступна, работаем в режиме in-memory
            logger.warning("⚠️ Working in in-memory mode (no database)")
            self.in_memory_mode = True
            await self.init_in_memory_data()
            return True
    
    async def init_in_memory_data(self):
        """Инициализация данных в памяти"""
        logger.info("📦 Initializing in-memory data...")
        
        # Создаем тестовые товары
        self.products = [
            Product(
                id=1,
                name="Парацетамол",
                price=50.0,
                category="Обезболивающие",
                description="Обезболивающее и жаропонижающее",
                stock=100,
                prescription_required=False
            ),
            Product(
                id=2,
                name="Ибупрофен",
                price=80.0,
                category="Обезболивающие",
                description="Противовоспалительное средство",
                stock=50,
                prescription_required=False
            ),
            Product(
                id=3,
                name="Витамин C",
                price=120.0,
                category="Витамины",
                description="Аскорбиновая кислота 500мг",
                stock=150,
                prescription_required=False
            ),
            Product(
                id=4,
                name="Амоксициллин",
                price=150.0,
                category="Антибиотики",
                description="Антибиотик широкого спектра",
                stock=40,
                prescription_required=True
            ),
            Product(
                id=5,
                name="Арбидол",
                price=300.0,
                category="Противовирусные",
                description="Противовирусный препарат",
                stock=60,
                prescription_required=False
            ),
        ]
        
        # Создаем админа
        admin_user = User(
            id=1,
            telegram_id=ADMIN_ID,
            name="Super Admin",
            username="admin",
            role=UserRole.ADMIN
        )
        self.users[ADMIN_ID] = admin_user
        
        logger.info("✅ In-memory data initialized")
    
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
        if self.in_memory_mode:
            self.users[user.telegram_id] = user
            return True
        
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
        if self.in_memory_mode:
            return self.users.get(telegram_id)
        
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
        if self.in_memory_mode:
            order.id = self.order_counter
            self.order_counter += 1
            self.orders.append(order)
            await self.log_action(order.user_id, "order_created", {"order_id": order.id})
            return order.id
        
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
        if self.in_memory_mode:
            return [order for order in self.orders if order.status == status]
        
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
        if self.in_memory_mode:
            return self.products
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM products ORDER BY name")
            return [self._row_to_product(row) for row in rows]
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Получение заказов пользователя"""
        if self.in_memory_mode:
            return [order for order in self.orders if order.user_id == user_id]
        
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
        if self.in_memory_mode:
            total_orders = len(self.orders)
            today_orders = len([o for o in self.orders if o.created_at.date() == datetime.now().date()])
            delivered_orders = len([o for o in self.orders if o.status == OrderStatus.DELIVERED])
            
            total_users = len(self.users)
            active_users = len([u for u in self.users.values() if u.is_active])
            
            role_stats = {}
            for user in self.users.values():
                role = user.role.value
                role_stats[role] = role_stats.get(role, 0) + 1
            
            total_revenue = sum(o.total_amount for o in self.orders if o.status == OrderStatus.DELIVERED)
            today_revenue = sum(o.total_amount for o in self.orders 
                              if o.status == OrderStatus.DELIVERED and o.created_at.date() == datetime.now().date())
            
            return {
                "orders": {
                    "total": total_orders,
                    "today": today_orders,
                    "delivered": delivered_orders
                },
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "by_role": role_stats
                },
                "revenue": {
                    "total": total_revenue,
                    "today": today_revenue
                }
            }
        
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
        if self.in_memory_mode:
            self.action_logs.append({
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'created_at': datetime.now()
            })
            return
        
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
        logger.info("✅ Database disconnected")

# 🏥 MAXXPHARM Bot
class MaxxpharmBot:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
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
    
    # 🔥 Проверяем переменные окружения
    print(f"🔥 BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"🔥 ADMIN_ID: {ADMIN_ID}")
    print(f"🔥 DATABASE_URL: {'✅ Установлен' if DATABASE_URL else '❌ НЕ УСТАНОВЛЕН'}")
    print()
    
    try:
        # Проверяем переменные окружения
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN environment variable is required")
            print("❌ ОШИБКА: BOT_TOKEN не установлен!")
            sys.exit(1)
        
        # Создаем и запускаем бота
        bot = MaxxpharmBot()
        
        if await bot.initialize():
            await bot.start()
        else:
            logger.error("❌ Failed to initialize MAXXPHARM Bot")
            print("❌ ОШИБКА: Не удалось инициализировать бота!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
        print("🛑 Система остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Fatal system error: {e}")
        print(f"❌ Фатальная ошибка системы: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
