#!/usr/bin/env python3
"""
Full Bot - MAXXPHARM Telegram Bot (Background Worker) - CLEAN VERSION
"""

import asyncio
import logging
import os
import signal
import sys
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# 🚀 МГНОВЕННАЯ ПРОВЕРКА ЗАПУСКА
print("🚀 MAXXPHARM BOT STARTING...")
print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
print(f"🐍 Python: {sys.version}")
print(f"📁 Working dir: {os.getcwd()}")
print(f"🌐 Environment: {os.getenv('RENDER', 'local')}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация из env переменных
BOT_TOKEN = os.getenv("BOT_TOKEN", "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))

print(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
print(f"👤 Admin ID: {ADMIN_ID}")

# Global flag to prevent multiple instances
BOT_RUNNING = False

print("✅ Imports loaded successfully")

# Role system - ОБНОВЛЕНО по ТЗ
class UserRole:
    DIRECTOR = "DIRECTOR"           # Директор - полный просмотр системы
    OPERATOR = "OPERATOR"           # Оператор - работа с заявками
    COLLECTOR = "COLLECTOR"         # Сборщик - сборка заказов
    INSPECTOR = "INSPECTOR"         # Проверщик - контроль качества
    COURIER = "COURIER"             # Курьер - доставка
    ADMIN = "ADMIN"                 # Администратор - полный доступ
    SUPER_ADMIN = "SUPER_ADMIN"       # Super Admin - полный доступ
    CLIENT = "CLIENT"               # Клиент - базовый доступ
    PHARMACY = "PHARMACY"           # Аптека - новый тип клиента

# Registration states for FSM
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    PHARMACY_NAME = State()
    PHONE = State()
    FULL_NAME = State()
    ADDRESS = State()

class ApplicationStates(StatesGroup):
    TEXT = State()
    PHOTO = State()
    VOICE = State()

# Registration data
REGISTRATION_DATA = {}  # {user_id: {"step": str, "data": dict}}

# Client applications
CLIENT_APPLICATIONS = []  # [{"id": int, "client_id": int, "type": str, "content": str, "timestamp": str, "status": str}]

# Generate unique registration link
def generate_registration_link(user_id: int) -> str:
    """Генерация уникальной ссылки для регистрации"""
    return f"https://t.me/solimfarm_bot?start=reg_{user_id}"

# Check if user is registering
def is_registering(user_id: int) -> bool:
    return user_id in REGISTRATION_DATA

# Order statuses - СТАТУСЫ ЗАЯВОК по ТЗ
class OrderStatus:
    NEW = "Новая"                  # Новая
    PROCESSING = "В обработке"      # В обработке
    COLLECTING = "Собирается"       # Собирается
    DELIVERING = "Доставляется"      # Доставляется
    COMPLETED = "Выполнена"         # Выполнена
    CANCELLED = "Отменена"          # Отменена

# Session management
SESSIONS = {}  # {user_id: {"role": str, "expires": datetime, "active": bool}}

# Activity logs
ACTIVITY_LOGS = []  # [{"user_id": int, "action": str, "timestamp": str, "details": str}]

# Order applications (заявки)
APPLICATIONS = []  # [{"id": int, "client_id": int, "status": str, "date": str, "total": float, "items": []}]

# Database
USERS = {}
PRODUCTS = [
    {"id": 1, "name": "Парацетамол", "price": 50, "category": "Обезболивающие", "stock": 100, "description": "Обезболивающее и жаропонижающее"},
    {"id": 2, "name": "Ибупрофен", "price": 80, "category": "Обезболивающие", "stock": 50, "description": "Противовоспалительное средство"},
    {"id": 3, "name": "Аспирин", "price": 30, "category": "Обезболивающие", "stock": 200, "description": "Ацетилсалициловая кислота"},
    {"id": 4, "name": "Витамин C", "price": 120, "category": "Витамины", "stock": 150, "description": "Аскорбиновая кислота 500мг"},
    {"id": 5, "name": "Витамин D", "price": 200, "category": "Витамины", "stock": 80, "description": "Витамин D3 1000 МЕ"},
    {"id": 6, "name": "Амоксициллин", "price": 150, "category": "Антибиотики", "stock": 40, "description": "Антибиотик широкого спектра"},
    {"id": 7, "name": "Арбидол", "price": 300, "category": "Противовирусные", "stock": 60, "description": "Противовирусный препарат"},
]

CATEGORIES = ["Обезболивающие", "Витамины", "Антибиотики", "Противовирусные"]
ORDERS = []

# User management - ОБНОВЛЕНО по ТЗ
def get_user_role(user_id):
    if user_id == ADMIN_ID:
        return UserRole.SUPER_ADMIN
    
    # Проверяем сессию
    if user_id in SESSIONS and SESSIONS[user_id].get("active", False):
        return SESSIONS[user_id].get("role", UserRole.CLIENT)
    
    return USERS.get(user_id, {}).get("role", UserRole.CLIENT)

def is_admin(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR]

def is_director(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.DIRECTOR]

def can_manage_orders(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR, UserRole.OPERATOR]

def can_collect_orders(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR, UserRole.COLLECTOR]

def can_inspect_orders(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR, UserRole.INSPECTOR]

def can_deliver_orders(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR, UserRole.COURIER]

def log_activity(user_id, action, details=""):
    """Логирование действий"""
    import datetime
    log_entry = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": details
    }
    ACTIVITY_LOGS.append(log_entry)
    print(f"📝 LOG: {action} by {user_id} - {details}")

def create_session(user_id, role):
    """Создание сессии"""
    import datetime
    expires = datetime.datetime.now() + datetime.timedelta(hours=24)
    SESSIONS[user_id] = {
        "role": role,
        "expires": expires.strftime("%Y-%m-%d %H:%M:%S"),
        "active": True
    }
    log_activity(user_id, "SESSION_CREATED", f"Role: {role}")

def check_session(user_id):
    """Проверка сессии"""
    if user_id not in SESSIONS:
        return False
    
    import datetime
    session = SESSIONS[user_id]
    expires = datetime.datetime.strptime(session["expires"], "%Y-%m-%d %H:%M:%S")
    
    if datetime.datetime.now() > expires:
        session["active"] = False
        return False
    
    return session["active"]

# Keyboards - ОБНОВЛЕНО по ТЗ
def get_main_menu(user_id):
    role = get_user_role(user_id)
    
    if role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR]:
        # Меню для руководства
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Все заявки")],
                [KeyboardButton(text="📈 Аналитика"), KeyboardButton(text="👥 Пользователи и роли")],
                [KeyboardButton(text="📜 История действий"), KeyboardButton(text="⚙ Настройки системы")],
                [KeyboardButton(text="🔗 Интеграция 1С"), KeyboardButton(text="📦 Управление статусами")],
                [KeyboardButton(text="📢 Рассылки"), KeyboardButton(text="🗄 Архив")],
                [KeyboardButton(text="🔐 Управление админами"), KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.OPERATOR:
        # Меню для оператора
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Все заявки")],
                [KeyboardButton(text="📈 Моя статистика"), KeyboardButton(text="📜 История действий")],
                [KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.COLLECTOR:
        # Меню для сборщика
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Мои сборки")],
                [KeyboardButton(text="📈 Моя статистика"), KeyboardButton(text="📜 История действий")],
                [KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.INSPECTOR:
        # Меню для проверщика
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Проверка качества")],
                [KeyboardButton(text="📈 Моя статистика"), KeyboardButton(text="📜 История действий")],
                [KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.COURIER:
        # Меню для курьера
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚚 Мои доставки")],
                [KeyboardButton(text="📈 Моя статистика"), KeyboardButton(text="📜 История действий")],
                [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.PHARMACY:
        # Меню для аптеки (клиента)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Создать заявку")],
                [KeyboardButton(text="📋 Мои заявки"), KeyboardButton(text="📊 Статус моей заявки")],
                [KeyboardButton(text="📞 Связаться с оператором")]
            ],
            resize_keyboard=True
        )
    else:  # CLIENT
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🛍 Каталог")],
                [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="🛒 Корзина")],
                [KeyboardButton(text="📦 Мои заказы"), KeyboardButton(text="📞 Поддержка")]
            ],
            resize_keyboard=True
        )
    
    return keyboard

def get_client_registration_menu():
    """Меню для создания заявки клиента"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать текстом")],
            [KeyboardButton(text="📷 Отправить фото")],
            [KeyboardButton(text="🎤 Отправить голосовое")],
            [KeyboardButton(text="❌ Отменить заявку")]
        ],
        resize_keyboard=True
    )

def get_admin_menu_keyboard():
    """Клавиатура для меню управления пользователями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_list_users")
        ],
        [
            InlineKeyboardButton(text="🔑 Изменить роли", callback_data="admin_change_roles"),
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data="admin_block_user")
        ],
        [
            InlineKeyboardButton(text="📊 Активность", callback_data="admin_activity"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")
        ]
    ])

def get_role_selection_keyboard_tz(user_id: int, action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора роли по ТЗ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏥 Клиент (Аптека)", 
                callback_data=f"role_{action}_{user_id}_{UserRole.PHARMACY}"
            ),
            InlineKeyboardButton(
                text="📞 Оператор", 
                callback_data=f"role_{action}_{user_id}_{UserRole.OPERATOR}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Сборщик", 
                callback_data=f"role_{action}_{user_id}_{UserRole.COLLECTOR}"
            ),
            InlineKeyboardButton(
                text="🔍 Проверщик", 
                callback_data=f"role_{action}_{user_id}_{UserRole.INSPECTOR}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚚 Курьер", 
                callback_data=f"role_{action}_{user_id}_{UserRole.COURIER}"
            ),
            InlineKeyboardButton(
                text="👑 Администратор", 
                callback_data=f"role_{action}_{user_id}_{UserRole.ADMIN}"
            )
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
        ]
    ])
    return keyboard

def get_applications_keyboard():
    """Клавиатура для управления заявками"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Создать заявку", callback_data="app_create"),
            InlineKeyboardButton(text="🔍 Найти заявку", callback_data="app_search")
        ],
        [
            InlineKeyboardButton(text="📊 Фильтры", callback_data="app_filters"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")
        ]
    ])

def get_analytics_keyboard():
    """Клавиатура для аналитики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 За день", callback_data="analytics_day"),
            InlineKeyboardButton(text="📊 За неделю", callback_data="analytics_week")
        ],
        [
            InlineKeyboardButton(text="📊 За месяц", callback_data="analytics_month"),
            InlineKeyboardButton(text="📊 За все время", callback_data="analytics_all")
        ],
        [
            InlineKeyboardButton(text="🏆 Топ операторы", callback_data="analytics_top"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")
        ]
    ])

def get_categories_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for category in CATEGORIES:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=category, callback_data=f"category_{category}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    ])
    return keyboard

def get_products_keyboard(category=None):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if category:
        products = [p for p in PRODUCTS if p["category"] == category]
    else:
        products = PRODUCTS
    
    for product in products:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']}₽ ({product['stock']} шт)",
                callback_data=f"product_{product['id']}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_categories")
    ])
    return keyboard

def get_product_actions_keyboard(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_{product_id}"),
            InlineKeyboardButton(text="ℹ️ Информация", callback_data=f"product_info_{product_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")
        ]
    ])
    return keyboard

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 🎯 ПРОВЕРКА РЕГИСТРАЦИИ HANDLERS
print("🔧 Registering handlers...")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"🎯 START HANDLER CALLED by {message.from_user.full_name} (ID: {message.from_user.id})")
    user_id = message.from_user.id
    args = message.text.split()
    
    # Проверяем, это регистрация по ссылке
    if len(args) > 1 and args[1].startswith("reg_"):
        admin_id = int(args[1].split("_")[1])
        await handle_registration_start(message, admin_id)
        return
    
    role = get_user_role(user_id)
    print(f"👤 User role: {role}")
    
    # Initialize user if not exists
    if user_id not in USERS:
        USERS[user_id] = {
            "id": user_id,
            "full_name": message.from_user.full_name,
            "role": role,
            "cart": [],
            "orders": [],
            "phone": None,
            "address": None,
            "blocked": False
        }
        print(f"✅ User {user_id} initialized")
    
    # Check if user is registering
    if is_registering(user_id):
        await continue_registration(message)
        return
    
    # Create session for admin users
    if role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRECTOR]:
        create_session(user_id, role)
        session_info = SESSIONS.get(user_id, {})
        expires = session_info.get("expires", "Неизвестно")
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: {role}\n"
            f"⏰ Сессия активна до: {expires}\n\n"
            f"Выберите действие из меню ниже:"
        )
    elif role == UserRole.OPERATOR:
        create_session(user_id, role)
        session_info = SESSIONS.get(user_id, {})
        expires = session_info.get("expires", "Неизвестно")
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: ОПЕРАТОР\n"
            f"⏰ Сессия активна до: {expires}\n\n"
            f"Выберите действие из меню ниже:"
        )
    elif role == UserRole.PHARMACY:
        welcome_text = (
            f"🏥 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: АПТЕКА\n"
            f"📋 Вы можете создавать заявки и отслеживать их статус\n\n"
            f"Выберите действие из меню ниже:"
        )
    elif role == UserRole.COLLECTOR:
        create_session(user_id, role)
        session_info = SESSIONS.get(user_id, {})
        expires = session_info.get("expires", "Неизвестно")
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: СБОРЩИК\n"
            f"⏰ Сессия активна до: {expires}\n\n"
            f"Выберите действие из меню ниже:"
        )
    elif role == UserRole.INSPECTOR:
        create_session(user_id, role)
        session_info = SESSIONS.get(user_id, {})
        expires = session_info.get("expires", "Неизвестно")
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: ПРОВЕРЩИК\n"
            f"⏰ Сессия активна до: {expires}\n\n"
            f"Выберите действие из меню ниже:"
        )
    elif role == UserRole.COURIER:
        create_session(user_id, role)
        session_info = SESSIONS.get(user_id, {})
        expires = session_info.get("expires", "Неизвестно")
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            f"🔐 Ваша роль: КУРЬЕР\n"
            f"⏰ Сессия активна до: {expires}\n\n"
            f"Выберите действие из меню ниже:"
        )
    else:  # CLIENT
        welcome_text = (
            f"🚀 <b>Добро пожаловать в MAXXPHARM!</b>\n\n"
            f"👤 {message.from_user.full_name}\n\n"
            "🛍 Ваш надежный партнер в мире фармацевтики\n"
            "📦 Быстрая доставка качественных товаров\n"
            "💊 Только сертифицированная продукция\n\n"
            "Выберите действие в меню:"
        )
    
    # Get menu and check
    menu = get_main_menu(user_id)
    print(f"📱 Menu generated for role {role}")
    
    await message.answer(welcome_text, reply_markup=menu)
    log_activity(user_id, "START", f"Role: {role}")
    logger.info(f"User {user_id} ({role}) started bot")
    print(f"✅ Start message sent with menu to {message.from_user.full_name}")

async def handle_registration_start(message: types.Message, admin_id: int):
    """Обработка начала регистрации по ссылке"""
    user_id = message.from_user.id
    
    # Инициализируем данные регистрации
    REGISTRATION_DATA[user_id] = {
        "admin_id": admin_id,
        "step": "pharmacy_name",
        "data": {}
    }
    
    await message.answer(
        "🏥 <b>Регистрация аптеки</b>\n\n"
        "📝 Пожалуйста, введите название вашей аптеки:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить регистрацию")]],
            resize_keyboard=True
        )
    )
    
    log_activity(user_id, "REGISTRATION_STARTED", f"Admin: {admin_id}")

async def continue_registration(message: types.Message):
    """Продолжение процесса регистрации"""
    user_id = message.from_user.id
    reg_data = REGISTRATION_DATA.get(user_id)
    
    if not reg_data:
        return
    
    step = reg_data["step"]
    data = reg_data["data"]
    
    if step == "pharmacy_name":
        data["pharmacy_name"] = message.text
        reg_data["step"] = "phone"
        
        await message.answer(
            "📞 <b>Регистрация аптеки</b>\n\n"
            "📝 Пожалуйста, введите номер телефона:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить регистрацию")]],
                resize_keyboard=True
            )
        )
        
    elif step == "phone":
        data["phone"] = message.text
        reg_data["step"] = "full_name"
        
        await message.answer(
            "👤 <b>Регистрация аптеки</b>\n\n"
            "📝 Пожалуйста, введите ФИО ответственного лица:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить регистрацию")]],
                resize_keyboard=True
            )
        )
        
    elif step == "full_name":
        data["full_name"] = message.text
        reg_data["step"] = "address"
        
        await message.answer(
            "📍 <b>Регистрация аптеки</b>\n\n"
            "📝 Пожалуйста, введите адрес аптеки:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить регистрацию")]],
                resize_keyboard=True
            )
        )
        
    elif step == "address":
        data["address"] = message.text
        
        # Завершаем регистрацию
        await complete_registration(message, user_id, data)

async def complete_registration(message: types.Message, user_id: int, data: dict):
    """Завершение регистрации"""
    # Обновляем данные пользователя
    if user_id not in USERS:
        USERS[user_id] = {
            "id": user_id,
            "full_name": data["full_name"],
            "role": UserRole.PHARMACY,
            "cart": [],
            "orders": [],
            "phone": data["phone"],
            "address": data["address"],
            "pharmacy_name": data["pharmacy_name"],
            "blocked": False
        }
    else:
        USERS[user_id].update({
            "role": UserRole.PHARMACY,
            "phone": data["phone"],
            "address": data["address"],
            "pharmacy_name": data["pharmacy_name"]
        })
    
    # Удаляем данные регистрации
    del REGISTRATION_DATA[user_id]
    
    # Отправляем подтверждение
    await message.answer(
        "✅ <b>Регистрация завершена!</b>\n\n"
        f"🏥 Аптека: {data['pharmacy_name']}\n"
        f"👤 Ответственный: {data['full_name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "🎉 Теперь вы можете создавать заявки!",
        reply_markup=get_main_menu(user_id)
    )
    
    log_activity(user_id, "REGISTRATION_COMPLETED", f"Pharmacy: {data['pharmacy_name']}")

# 🏥 Меню для аптек (клиентов)
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
    log_activity(message.from_user.id, "CREATE_APPLICATION_START", "Started creating application")

@dp.message(F.text == "✍️ Написать текстом")
async def cmd_text_application(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer(
        "✍️ <b>Текстовая заявка</b>\n\n"
        "📝 Напишите текст вашей заявки:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить заявку")]],
            resize_keyboard=True
        )
    )

@dp.message(F.text == "❌ Отменить заявку")
async def cmd_cancel_application(message: types.Message):
    await message.answer(
        "❌ <b>Заявка отменена</b>\n\n"
        "📋 Вы вернулись в главное меню",
        reply_markup=get_main_menu(message.from_user.id)
    )

@dp.message(F.text == "📋 Мои заявки")
async def cmd_my_applications(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    user_id = message.from_user.id
    my_apps = [app for app in CLIENT_APPLICATIONS if app["client_id"] == user_id]
    
    if not my_apps:
        await message.answer(
            "📋 <b>Мои заявки</b>\n\n"
            "📝 У вас пока нет заявок",
            reply_markup=get_main_menu(user_id)
        )
        return
    
    apps_text = "📋 <b>Мои заявки:</b>\n\n"
    
    for app in my_apps:
        apps_text += f"🆔 ID: {app['id']}\n"
        apps_text += f"📊 Статус: {app['status']}\n"
        apps_text += f"📅 Дата: {app['timestamp']}\n"
        apps_text += f"📝 Тип: {app['type']}\n\n"
    
    await message.answer(apps_text, reply_markup=get_main_menu(user_id))

@dp.message(F.text == "📊 Статус моей заявки")
async def cmd_application_status(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    user_id = message.from_user.id
    my_apps = [app for app in CLIENT_APPLICATIONS if app["client_id"] == user_id]
    
    if not my_apps:
        await message.answer(
            "📊 <b>Статус заявки</b>\n\n"
            "📝 У вас пока нет заявок",
            reply_markup=get_main_menu(user_id)
        )
        return
    
    # Показываем последнюю заявку
    last_app = my_apps[-1]
    
    status_text = (
        f"📊 <b>Статус последней заявки</b>\n\n"
        f"🆔 ID: {last_app['id']}\n"
        f"📊 Статус: {last_app['status']}\n"
        f"📅 Дата: {last_app['timestamp']}\n"
        f"📝 Тип: {last_app['type']}\n\n"
        f"📄 Содержимое: {last_app['content'][:100]}..."
    )
    
    await message.answer(status_text, reply_markup=get_main_menu(user_id))

@dp.message(F.text == "📞 Связаться с оператором")
async def cmd_contact_operator(message: types.Message):
    if get_user_role(message.from_user.id) != UserRole.PHARMACY:
        await message.answer("❌ Эта функция доступна только для аптек!")
        return
    
    await message.answer(
        "📞 <b>Связь с оператором</b>\n\n"
        "📝 Напишите ваше сообщение оператору:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить")]],
            resize_keyboard=True
        )
    )

# 📊 Все заявки - НОВЫЙ МОДУЛЬ
@dp.message(F.text == "📊 Все заявки")
async def cmd_applications(message: types.Message):
    if not can_manage_orders(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    if not APPLICATIONS:
        await message.answer(
            "📊 <b>Все заявки</b>\n\n"
            "📝 Заявок пока нет",
            reply_markup=get_applications_keyboard()
        )
        return
    
    apps_text = "📊 <b>Все заявки:</b>\n\n"
    
    for app in APPLICATIONS:
        user = USERS.get(app['client_id'], {})
        apps_text += f"🆔 ID: {app['id']}\n"
        apps_text += f"👤 Клиент: {user.get('full_name', 'Unknown')}\n"
        apps_text += f"📊 Статус: {app['status']}\n"
        apps_text += f"📅 Дата: {app['date']}\n"
        apps_text += f"💰 Сумма: {app['total']}₽\n\n"
    
    await message.answer(apps_text, reply_markup=get_applications_keyboard())
    log_activity(message.from_user.id, "VIEW_APPLICATIONS", "Viewed all applications")

# 📈 Аналитика - НОВЫЙ МОДУЛЬ
@dp.message(F.text == "📈 Аналитика")
async def cmd_analytics(message: types.Message):
    if not is_director(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    total_apps = len(APPLICATIONS)
    completed = len([a for a in APPLICATIONS if a['status'] == OrderStatus.COMPLETED])
    in_progress = len([a for a in APPLICATIONS if a['status'] in [OrderStatus.PROCESSING, OrderStatus.COLLECTING, OrderStatus.DELIVERING]])
    cancelled = len([a for a in APPLICATIONS if a['status'] == OrderStatus.CANCELLED])
    
    avg_check = sum([a['total'] for a in APPLICATIONS]) / len(APPLICATIONS) if APPLICATIONS else 0
    
    analytics_text = (
        f"📈 <b>Аналитика MAXXPHARM</b>\n\n"
        f"📊 Количество заявок: {total_apps}\n"
        f"✅ Выполнено: {completed}\n"
        f"⏳ В работе: {in_progress}\n"
        f"❌ Отменено: {cancelled}\n"
        f"💰 Средний чек: {avg_check:.2f}₽\n\n"
        f"📊 Выберите период:"
    )
    
    await message.answer(analytics_text, reply_markup=get_analytics_keyboard())
    log_activity(message.from_user.id, "VIEW_ANALYTICS", "Viewed analytics")

# 👥 Пользователи и роли - НОВЫЙ МОДУЛЬ
@dp.message(F.text == "👥 Пользователи и роли")
async def cmd_users_roles(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Управление пользователями и ролями</b>\n\n"
    users_text += f"📊 Всего пользователей: {len(USERS)}\n"
    users_text += f"🔐 Активных сессий: {len([s for s in SESSIONS.values() if s.get('active', False)])}\n\n"
    users_text += "Выберите действие:"
    
    await message.answer(users_text, reply_markup=get_admin_menu_keyboard())
    log_activity(message.from_user.id, "VIEW_USER_MANAGEMENT", "Viewed user management")

# 📜 История действий - НОВЫЙ МОДУЛЬ
@dp.message(F.text == "📜 История действий")
async def cmd_history(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    if not ACTIVITY_LOGS:
        await message.answer(
            "📜 <b>История действий</b>\n\n"
            "📝 История пуста",
            reply_markup=get_main_menu(message.from_user.id)
        )
        return
    
    history_text = "📜 <b>История действий:</b>\n\n"
    
    # Показываем последние 20 записей
    recent_logs = ACTIVITY_LOGS[-20:]
    for log in reversed(recent_logs):
        user = USERS.get(log['user_id'], {})
        history_text += f"👤 {user.get('full_name', 'Unknown')}\n"
        history_text += f"🔧 Действие: {log['action']}\n"
        history_text += f"📅 Время: {log['timestamp']}\n"
        history_text += f"📝 Детали: {log['details']}\n\n"
    
    await message.answer(history_text, reply_markup=get_main_menu(message.from_user.id))
    log_activity(message.from_user.id, "VIEW_HISTORY", "Viewed action history")

# 🚪 Выйти - НОВЫЙ МОДУЛЬ
@dp.message(F.text == "🚪 Выйти")
async def cmd_logout(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in SESSIONS:
        SESSIONS[user_id]["active"] = False
        del SESSIONS[user_id]
    
    # Меняем роль на CLIENT
    if user_id in USERS:
        USERS[user_id]["role"] = UserRole.CLIENT
    
    await message.answer(
        "🚪 <b>Выход выполнен</b>\n\n"
        "👤 Вы вернулись в обычный режим\n"
        "🔐 Сессия завершена",
        reply_markup=get_main_menu(user_id)
    )
    log_activity(user_id, "LOGOUT", "User logged out")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    role = get_user_role(message.from_user.id)
    
    if role == UserRole.SUPER_ADMIN:
        help_text = (
            "🆘 <b>Помощь MAXXPHARM Super Admin</b>\n\n"
            "📋 <b>Команды:</b>\n"
            "• /start - Главное меню\n"
            "• /help - Эта справка\n"
            "• /stats - Быстрая статистика\n"
            "• /admin - Админ-панель\n\n"
            "🔧 <b>Функции:</b>\n"
            "• 📊 Статистика - Полная статистика системы\n"
            "• 📦 Заказы - Управление всеми заказами\n"
            "• 👥 Пользователи - Управление ролями\n"
            "• 🧾 Товары - Управление каталогом\n"
            "• 🏷 Категории - Управление категориями\n"
            "• 🏪 Склад - Управление складом\n"
            "• ⚙ Настройки - Системные настройки\n"
            "• 📝 Логи - Просмотр логов\n\n"
            "✅ Полный контроль системой!"
        )
    else:  # CLIENT
        help_text = (
            "🆘 <b>Помощь MAXXPHARM</b>\n\n"
            "📋 <b>Основные команды:</b>\n"
            "• /start - Главное меню\n"
            "• /help - Эта справка\n"
            "• /cancel - Отменить действие\n\n"
            "🛍 <b>Как заказать:</b>\n"
            "1. 🛍 Выберите каталог\n"
            "2. 🏷 Выберите категорию\n"
            "3. 📦 Выберите товар\n"
            "4. ➕ Добавьте в корзину\n"
            "5. 🛒 Оформите заказ\n\n"
            "📞 <b>Поддержка:</b>\n"
            "• Меню → 📞 Поддержка\n\n"
            "✅ Всегда готовы помочь!"
        )
    
    await message.answer(help_text, reply_markup=get_main_menu(message.from_user.id))

# Client menu handlers
@dp.message(F.text == "🛍 Каталог")
async def cmd_catalog(message: types.Message):
    await message.answer(
        "🛍 <b>Каталог товаров</b>\n\n"
        "🏷 Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )

@dp.message(F.text == "🛒 Корзина")
async def cmd_cart(message: types.Message):
    user_id = message.from_user.id
    user_data = USERS.get(user_id, {})
    cart = user_data.get("cart", [])
    
    if not cart:
        await message.answer(
            "🛒 <b>Ваша корзина пуста</b>\n\n"
            "🛍 Перейдите в каталог для выбора товаров",
            reply_markup=get_main_menu(user_id)
        )
        return
    
    cart_text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart:
        product = next((p for p in PRODUCTS if p["id"] == item["id"]), None)
        if product:
            cart_text += f"📦 {product['name']}\n"
            cart_text += f"   Количество: {item['quantity']} шт\n"
            cart_text += f"   Цена: {product['price']}₽/шт\n"
            cart_text += f"   Сумма: {product['price'] * item['quantity']}₽\n\n"
            total += product['price'] * item['quantity']
    
    cart_text += f"💰 <b>Итого: {total}₽</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
            InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])
    
    await message.answer(cart_text, reply_markup=keyboard)

@dp.message(F.text == "📦 Мои заказы")
async def cmd_my_orders(message: types.Message):
    user_id = message.from_user.id
    user_data = USERS.get(user_id, {})
    user_orders = user_data.get("orders", [])
    
    if not user_orders:
        await message.answer(
            "📦 <b>У вас пока нет заказов</b>\n\n"
            "🛍 Сделайте первый заказ в каталоге",
            reply_markup=get_main_menu(user_id)
        )
        return
    
    orders_text = "📦 <b>Ваши заказы:</b>\n\n"
    
    for order in user_orders:
        orders_text += f"🆔 Заказ #{order['id']}\n"
        orders_text += f"📅 Дата: {order['date']}\n"
        orders_text += f"💰 Сумма: {order['total']}₽\n"
        orders_text += f"📊 Статус: {order['status']}\n\n"
    
    await message.answer(orders_text, reply_markup=get_main_menu(user_id))

@dp.message(F.text == "📞 Поддержка")
async def cmd_support(message: types.Message):
    support_text = (
        "📞 <b>Поддержка MAXXPHARM</b>\n\n"
        "👥 Наши специалисты готовы помочь!\n\n"
        "📞 <b>Телефон:</b> +7 (495) 123-45-67\n"
        "📧 <b>Email:</b> support@maxxpharm.ru\n"
        "⏰ <b>Время работы:</b> 9:00 - 18:00\n\n"
        "💬 <b>Напишите ваш вопрос:</b>\n"
        "Мы ответим в ближайшее время!\n\n"
        "✅ Всегда на связи!"
    )
    
    await message.answer(support_text, reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "🔍 Поиск")
async def cmd_search(message: types.Message):
    await message.answer(
        "🔍 <b>Поиск товаров</b>\n\n"
        "🔧 Функция поиска в разработке\n\n"
        "📝 Введите название товара для поиска\n\n"
        "✅ Скоро будет доступна!",
        reply_markup=get_main_menu(message.from_user.id)
    )

# Admin menu handlers
@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    stats_text = (
        "📊 <b>Статистика MAXXPHARM</b>\n\n"
        f"👥 Всего пользователей: {len(USERS)}\n"
        f"🛍 Клиентов: {len([u for u in USERS.values() if u['role'] == UserRole.CLIENT])}\n"
        f"👨‍💼 Админов: {len([u for u in USERS.values() if u['role'] in [UserRole.SUPER_ADMIN, UserRole.ADMIN]])}\n"
        f"👨‍💼 Менеджеров: {len([u for u in USERS.values() if u['role'] == UserRole.MANAGER])}\n"
        f"🚚 Курьеров: {len([u for u in USERS.values() if u['role'] == UserRole.COURIER])}\n\n"
        f"📦 Всего товаров: {len(PRODUCTS)}\n"
        f"🏷 Категорий: {len(CATEGORIES)}\n\n"
        f"🛒 Всего заказов: {len(ORDERS)}\n"
        f"✅ Выполнено: {len([o for o in ORDERS if o['status'] == 'COMPLETED'])}\n"
        f"⏳ В работе: {len([o for o in ORDERS if o['status'] in ['NEW', 'CONFIRMED', 'IN_PROGRESS']])}\n\n"
        "🤖 Статус бота: ✅ Работает\n"
        "🌐 Платформа: Render\n"
        "🐍 Python: 3.11.14"
    )
    
    await message.answer(stats_text, reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "📦 Заказы")
async def admin_orders(message: types.Message):
    if not is_manager(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    if not ORDERS:
        await message.answer(
            "📦 <b>Заказов пока нет</b>\n\n"
            "🛍 Ожидайте заказы от клиентов",
            reply_markup=get_main_menu(message.from_user.id)
        )
        return
    
    orders_text = "📦 <b>Все заказы:</b>\n\n"
    
    for order in ORDERS:
        user = USERS.get(order['user_id'], {})
        orders_text += f"🆔 Заказ #{order['id']}\n"
        orders_text += f"👤 Клиент: {user.get('full_name', 'Unknown')}\n"
        orders_text += f"💰 Сумма: {order['total']}₽\n"
        orders_text += f"📊 Статус: {order['status']}\n"
        orders_text += f"📅 Дата: {order['date']}\n\n"
    
    await message.answer(orders_text, reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "👥 Пользователи")
async def admin_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Все пользователи:</b>\n\n"
    
    for user_id, user_data in USERS.items():
        role_name = {
            UserRole.SUPER_ADMIN: "Super Admin",
            UserRole.ADMIN: "Admin", 
            UserRole.MANAGER: "Manager",
            UserRole.COURIER: "Courier",
            UserRole.CLIENT: "Client"
        }.get(user_data.get('role', UserRole.CLIENT), "Unknown")
        
        users_text += f"👤 {user_data['full_name']}\n"
        users_text += f"🆔 ID: {user_id}\n"
        users_text += f"🔑 Роль: {role_name}\n"
        users_text += f"📦 Заказов: {len(user_data.get('orders', []))}\n\n"
    
    # Добавляем кнопки управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user_start"),
            InlineKeyboardButton(text="🔧 Изменить роль", callback_data="change_role_start")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data="delete_user_start"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])
    
    await message.answer(users_text, reply_markup=keyboard)

@dp.message(F.text == "🧾 Товары")
async def admin_products(message: types.Message):
    if not is_manager(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    products_text = "🧾 <b>Все товары:</b>\n\n"
    
    for product in PRODUCTS:
        products_text += f"📦 {product['name']}\n"
        products_text += f"💰 Цена: {product['price']}₽\n"
        products_text += f"📊 Остаток: {product['stock']} шт\n"
        products_text += f"🏷 Категория: {product['category']}\n"
        products_text += f"📝 {product.get('description', 'Нет описания')}\n\n"
    
    await message.answer(products_text, reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "🚀 Выход")
async def admin_logout(message: types.Message):
    # Change role to CLIENT
    user_id = message.from_user.id
    if user_id in USERS:
        USERS[user_id]["role"] = UserRole.CLIENT
    
    await message.answer(
        "🚀 <b>Выход из админ-панели</b>\n\n"
        "👤 Вы вернулись в режим клиента",
        reply_markup=get_main_menu(user_id)
    )

# Other admin handlers
@dp.message(F.text.in_(["🏷 Категории", "🏪 Склад", "⚙ Настройки", "📝 Логи", "📦 Мои доставки", "🗺 Карта"]))
async def admin_other(message: types.Message):
    feature = message.text
    
    # Check permissions
    if feature in ["🏷 Категории", "🏪 Склад", "⚙ Настройки", "📝 Логи"]:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещен!")
            return
    elif feature in ["📦 Мои доставки", "🗺 Карта"]:
        if get_user_role(message.from_user.id) != UserRole.COURIER:
            await message.answer("❌ Доступ запрещен!")
            return
    
    await message.answer(
        f"⚠️ <b>{feature}</b>\n\n"
        "🔧 Функция в разработке\n\n"
        "✅ Скоро будет доступна!",
        reply_markup=get_main_menu(message.from_user.id)
    )

# Callback handlers
@dp.callback_query(F.data.startswith("category_"))
async def callback_category(callback: types.CallbackQuery):
    category = callback.data.replace("category_", "")
    
    await callback.message.edit_text(
        f"🏷 <b>Категория: {category}</b>\n\n"
        "📦 Доступные товары:",
        reply_markup=get_products_keyboard(category)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def callback_product(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("product_", ""))
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден!")
        return
    
    product_text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📊 Остаток: {product['stock']} шт\n"
        f"🏷 Категория: {product['category']}\n\n"
        f"📝 {product.get('description', 'Качественный фармацевтический продукт')}"
    )
    
    await callback.message.edit_text(
        product_text,
        reply_markup=get_product_actions_keyboard(product_id)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("add_to_cart_"))
async def callback_add_to_cart(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("add_to_cart_", ""))
    user_id = callback.from_user.id
    
    user_data = USERS.get(user_id, {})
    cart = user_data.get("cart", [])
    
    existing_item = next((item for item in cart if item["id"] == product_id), None)
    if existing_item:
        existing_item["quantity"] += 1
    else:
        cart.append({"id": product_id, "quantity": 1})
    
    user_data["cart"] = cart
    USERS[user_id] = user_data
    
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    
    await callback.answer(f"✅ {product['name']} добавлен в корзину!")

@dp.callback_query(F.data == "clear_cart")
async def callback_clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = USERS.get(user_id, {})
    user_data["cart"] = []
    USERS[user_id] = user_data
    
    await callback.message.edit_text(
        "🗑️ <b>Корзина очищена</b>\n\n"
        "🛍 Выберите товары в каталоге",
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()

@dp.callback_query(F.data == "checkout")
async def callback_checkout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = USERS.get(user_id, {})
    cart = user_data.get("cart", [])
    
    if not cart:
        await callback.answer("❌ Корзина пуста!")
        return
    
    total = 0
    
    for item in cart:
        product = next((p for p in PRODUCTS if p["id"] == item["id"]), None)
        if product:
            total += product['price'] * item['quantity']
    
    order_id = len(ORDERS) + 1
    order = {
        "id": order_id,
        "user_id": user_id,
        "items": cart.copy(),
        "total": total,
        "status": "NEW",
        "date": "Сегодня"
    }
    
    ORDERS.append(order)
    
    user_orders = user_data.get("orders", [])
    user_orders.append(order)
    user_data["orders"] = user_orders
    
    user_data["cart"] = []
    USERS[user_id] = user_data
    
    order_text = (
        f"✅ <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"💰 Сумма: {total}₽\n"
        f"📊 Статус: Новый\n"
        f"📅 Дата: {order['date']}\n\n"
        "📦 Мы свяжемся с вами в ближайшее время\n"
        "🚀 Спасибо за заказ!"
    )
    
    await callback.message.edit_text(
        order_text,
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "🚀 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_categories")
async def callback_back_to_categories(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛍 <b>Каталог товаров</b>\n\n"
        "🏷 Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_products")
async def callback_back_to_products(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📦 <b>Все товары</b>\n\n"
        "Выберите товар:",
        reply_markup=get_products_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("product_info_"))
async def callback_product_info(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("product_info_", ""))
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден!")
        return
    
    info_text = (
        f"ℹ️ <b>Информация о товаре</b>\n\n"
        f"📦 <b>{product['name']}</b>\n\n"
        f"💰 <b>Цена:</b> {product['price']}₽\n"
        f"📊 <b>Остаток:</b> {product['stock']} шт\n"
        f"🏷 <b>Категория:</b> {product['category']}\n\n"
        f"📝 <b>Описание:</b>\n"
        f"{product.get('description', 'Качественный фармацевтический продукт')}\n\n"
        f"✅ <b>Сертифицировано</b>\n"
        f"🏆 <b>Гарантия качества</b>\n"
        f"🚚 <b>Быстрая доставка</b>"
    )
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_product_actions_keyboard(product_id)
    )
    await callback.answer()

# 🎯 ОБРАБОТЧИКИ ДОБАВЛЕНИЯ ПОЛЬЗОВАТЕЛЕЙ по ТЗ
@dp.callback_query(F.data == "admin_add_user")
async def callback_admin_add_user(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!")
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление пользователя</b>\n\n"
        "🎯 Выберите роль для нового пользователя:",
        reply_markup=get_role_selection_keyboard_tz(callback.from_user.id, "add")
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("role_add_"))
async def callback_role_add(callback: types.CallbackQuery):
    """Обработка добавления пользователя с ролью"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!")
        return
    
    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        role = parts[3]
        
        if role == UserRole.PHARMACY:
            # Генерируем ссылку для регистрации аптеки
            registration_link = generate_registration_link(user_id)
            
            await callback.message.edit_text(
                f"🏥 <b>Добавление аптеки</b>\n\n"
                f"🔗 Ссылка для регистрации:\n"
                f"`{registration_link}`\n\n"
                f"📋 <b>Инструкция:</b>\n"
                f"1️⃣ Отправьте эту ссылку клиенту\n"
                f"2️⃣ Клиент переходит по ссылке\n"
                f"3️⃣ Нажимает /start\n"
                f"4️⃣ Проходит регистрацию\n\n"
                f"✅ После регистрации клиент сможет создавать заявки",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="� Назад", callback_data="admin_back_main")]
                ])
            )
        else:
            # Добавляем сотрудника напрямую
            USERS[user_id] = {
                "id": user_id,
                "full_name": f"User_{user_id}",
                "role": role,
                "cart": [],
                "orders": [],
                "phone": None,
                "address": None,
                "blocked": False
            }
            
            role_name = {
                UserRole.OPERATOR: "Оператор",
                UserRole.COLLECTOR: "Сборщик",
                UserRole.INSPECTOR: "Проверщик",
                UserRole.COURIER: "Курьер",
                UserRole.ADMIN: "Администратор",
                UserRole.DIRECTOR: "Директор"
            }.get(role, "Unknown")
            
            await callback.message.edit_text(
                f"✅ <b>Сотрудник добавлен!</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👤 Имя: User_{user_id}\n"
                f"🔑 Роль: {role_name}\n\n"
                f"� <b>Примечание:</b>\n"
                f"Имя обновится при первом входе в бота",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
                ])
            )
        
        log_activity(callback.from_user.id, "USER_ADDED", f"Role: {role}, ID: {user_id}")
        await callback.answer("✅ Готово!")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}")
        logger.error(f"Role add error: {e}")

@dp.callback_query(F.data == "admin_cancel")
async def callback_admin_cancel(callback: types.CallbackQuery):
    """Отмена действия"""
    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>\n\n"
        "📋 Вы вернулись в главное меню",
        reply_markup=get_main_menu(callback.from_user.id)
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_back_main")
async def callback_admin_back_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "👥 <b>Управление пользователями и ролями</b>\n\n"
        f"📊 Всего пользователей: {len(USERS)}\n"
        f"🔐 Активных сессий: {len([s for s in SESSIONS.values() if s.get('active', False)])}\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()

# 🎯 ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ ДЛЯ РЕГИСТРАЦИИ И ЗАЯВОК
@dp.message(F.text)
async def handle_text_messages(message: types.Message):
    user_id = message.from_user.id
    
    # Если пользователь в процессе регистрации
    if is_registering(user_id):
        await continue_registration(message)
        return
    
    # Если это текстовая заявка от аптеки
    if get_user_role(user_id) == UserRole.PHARMACY:
        # Проверяем, не это ли ответ на приглашение написать текст
        if "Напишите текст вашей заявки" in message.reply_to_message.text if message.reply_to_message else "":
            # Создаем текстовую заявку
            import datetime
            app_id = len(CLIENT_APPLICATIONS) + 1
            
            application = {
                "id": app_id,
                "client_id": user_id,
                "type": "text",
                "content": message.text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Новая"
            }
            
            CLIENT_APPLICATIONS.append(application)
            
            await message.answer(
                f"✅ <b>Заявка создана!</b>\n\n"
                f"🆔 ID: {app_id}\n"
                f"📝 Тип: Текстовая\n"
                f"📊 Статус: Новая\n\n"
                f"📞 Оператор свяжется с вами в ближайшее время",
                reply_markup=get_main_menu(user_id)
            )
            
            log_activity(user_id, "APPLICATION_CREATED", f"Text application #{app_id}")
            
            # Отправляем уведомление операторам (заглушка)
            await notify_operators(application)
        
        # Если это сообщение оператору
        elif "Напишите ваше сообщение оператору" in message.reply_to_message.text if message.reply_to_message else "":
            await message.answer(
                "✅ <b>Сообщение отправлено!</b>\n\n"
                "📞 Оператор ответит вам в ближайшее время",
                reply_markup=get_main_menu(user_id)
            )
            
            log_activity(user_id, "MESSAGE_TO_OPERATOR", message.text)

async def notify_operators(application: dict):
    """Уведомление операторов о новой заявке"""
    # Это заглушка - в реальной системе здесь будет отправка операторам
    print(f"🔔 НОВАЯ ЗАЯВКА #{application['id']} от клиента {application['client_id']}")
    print(f"📝 Тип: {application['type']}")
    print(f"📄 Содержимое: {application['content']}")

@dp.callback_query(F.data == "change_role_start")
async def callback_change_role_start(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!")
        return
    
    await callback.message.edit_text(
        "🔧 <b>Изменение роли пользователя</b>\n\n"
        "📤 Отправьте ID пользователя для изменения роли:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_users")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "delete_user_start")
async def callback_delete_user_start(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!")
        return
    
    await callback.message.edit_text(
        "🗑️ <b>Удаление пользователя</b>\n\n"
        "⚠️ <b>Внимание!</b>\n"
        "Это действие удалит все данные пользователя\n\n"
        "📤 Отправьте ID пользователя для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_users")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_users")
async def callback_back_to_users(callback: types.CallbackQuery):
    # Возвращаемся к списку пользователей
    users_text = "👥 <b>Все пользователи:</b>\n\n"
    
    for user_id, user_data in USERS.items():
        role_name = {
            UserRole.SUPER_ADMIN: "Super Admin",
            UserRole.ADMIN: "Admin", 
            UserRole.MANAGER: "Manager",
            UserRole.COURIER: "Courier",
            UserRole.CLIENT: "Client"
        }.get(user_data.get('role', UserRole.CLIENT), "Unknown")
        
        users_text += f"👤 {user_data['full_name']}\n"
        users_text += f"🆔 ID: {user_id}\n"
        users_text += f"🔑 Роль: {role_name}\n"
        users_text += f"📦 Заказов: {len(user_data.get('orders', []))}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user_start"),
            InlineKeyboardButton(text="🔧 Изменить роль", callback_data="change_role_start")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить пользователь", callback_data="delete_user_start"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])
    
    await callback.message.edit_text(users_text, reply_markup=keyboard)
    await callback.answer()

# 🎯 ОБРАБОТЧИКИ ID ПОЛЬЗОВАТЕЛЕЙ
@dp.message(F.text.regexp(r'^\d+$'))
async def handle_user_id(message: types.Message):
    """Обработка ID пользователя для управления"""
    user_id = int(message.text)
    admin_id = message.from_user.id
    
    if not is_admin(admin_id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    # Проверяем, есть ли такой пользователь в системе
    if user_id in USERS:
        # Пользователь существует - предлагаем изменить роль
        user_data = USERS[user_id]
        current_role = user_data.get('role', UserRole.CLIENT)
        
        role_name = {
            UserRole.SUPER_ADMIN: "Super Admin",
            UserRole.ADMIN: "Admin", 
            UserRole.MANAGER: "Manager",
            UserRole.COURIER: "Courier",
            UserRole.CLIENT: "Client"
        }.get(current_role, "Unknown")
        
        await message.answer(
            f"👤 <b>Пользователь найден:</b>\n\n"
            f"👤 {user_data['full_name']}\n"
            f"🆔 ID: {user_id}\n"
            f"🔑 Текущая роль: {role_name}\n\n"
            f"🔧 <b>Выберите новую роль:</b>",
            reply_markup=get_role_selection_keyboard(user_id, "change")
        )
    else:
        # Пользователя нет - предлагаем добавить
        await message.answer(
            f"👤 <b>Пользователь не найден:</b>\n\n"
            f"🆔 ID: {user_id}\n\n"
            f"➕ <b>Добавить пользователя?</b>\n"
            f"🔧 <b>Выберите роль для нового пользователя:</b>",
            reply_markup=get_role_selection_keyboard(user_id, "add")
        )

def get_role_selection_keyboard(user_id: int, action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора роли"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👑 Super Admin", 
                callback_data=f"role_{action}_{user_id}_{UserRole.SUPER_ADMIN}"
            ),
            InlineKeyboardButton(
                text="👨‍💼 Admin", 
                callback_data=f"role_{action}_{user_id}_{UserRole.ADMIN}"
            )
        ],
        [
            InlineKeyboardButton(
                text="👨‍💼 Manager", 
                callback_data=f"role_{action}_{user_id}_{UserRole.MANAGER}"
            ),
            InlineKeyboardButton(
                text="🚚 Courier", 
                callback_data=f"role_{action}_{user_id}_{UserRole.COURIER}"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Client", 
                callback_data=f"role_{action}_{user_id}_{UserRole.CLIENT}"
            )
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_users")
        ]
    ])
    return keyboard

@dp.callback_query(F.data.startswith("role_"))
async def callback_role_action(callback: types.CallbackQuery):
    """Обработка выбора роли"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!")
        return
    
    try:
        parts = callback.data.split("_")
        action = parts[1]  # add или change
        user_id = int(parts[2])
        role = parts[3]
        
        if action == "add":
            # Добавляем нового пользователя
            USERS[user_id] = {
                "id": user_id,
                "full_name": f"User_{user_id}",
                "role": role,
                "cart": [],
                "orders": [],
                "phone": None,
                "address": None
            }
            
            role_name = {
                UserRole.SUPER_ADMIN: "Super Admin",
                UserRole.ADMIN: "Admin", 
                UserRole.MANAGER: "Manager",
                UserRole.COURIER: "Courier",
                UserRole.CLIENT: "Client"
            }.get(role, "Unknown")
            
            await callback.message.edit_text(
                f"✅ <b>Пользователь добавлен!</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👤 Имя: User_{user_id}\n"
                f"🔑 Роль: {role_name}\n\n"
                f"💡 <b>Примечание:</b>\n"
                f"Имя обновится при первом входе в бота",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад к пользователям", callback_data="back_to_users")]
                ])
            )
            
        elif action == "change":
            # Изменяем роль существующего пользователя
            if user_id in USERS:
                USERS[user_id]["role"] = role
                
                role_name = {
                    UserRole.SUPER_ADMIN: "Super Admin",
                    UserRole.ADMIN: "Admin", 
                    UserRole.MANAGER: "Manager",
                    UserRole.COURIER: "Courier",
                    UserRole.CLIENT: "Client"
                }.get(role, "Unknown")
                
                await callback.message.edit_text(
                    f"✅ <b>Роль изменена!</b>\n\n"
                    f"👤 {USERS[user_id]['full_name']}\n"
                    f"🆔 ID: {user_id}\n"
                    f"🔑 Новая роль: {role_name}\n\n"
                    f"🔄 Изменения вступят в силу при следующем входе",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад к пользователям", callback_data="back_to_users")]
                    ])
                )
            else:
                await callback.message.edit_text(
                    "❌ <b>Ошибка!</b>\n\n"
                    "Пользователь не найден",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад к пользователям", callback_data="back_to_users")]
                    ])
                )
        
        await callback.answer("✅ Готово!")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}")
        logger.error(f"Role action error: {e}")

print("✅ All handlers registered")

async def main():
    global BOT_RUNNING
    
    print("🚀 ASYNC MAIN FUNCTION STARTED...")
    
    # Check if bot is already running
    if BOT_RUNNING:
        logger.warning("⚠️ Bot is already running! Exiting...")
        print("❌ Bot already running! Exiting...")
        return
    
    BOT_RUNNING = True
    logger.info("🚀 Starting MAXXPHARM Bot (Background Worker)")
    print("✅ Bot instance flag set to True")
    
    try:
        # Delete webhook with force
        print("📡 Deleting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted")
        print("✅ Webhook deleted successfully")
        
        # Get bot info
        print("🤖 Getting bot info...")
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: {bot_info.full_name} (@{bot_info.username})")
        print(f"✅ Bot connected: {bot_info.full_name} (@{bot_info.username})")
        
        # Add signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down...")
            print(f"🛑 Signal {signum} received, shutting down...")
            BOT_RUNNING = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        print("✅ Signal handlers configured")
        
        # Start polling with error handling
        print("🤖 Starting polling...")
        logger.info("🤖 Starting polling...")
        print("🎯 Background Worker is now running!")
        
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        logger.error(f"❌ Bot error: {e}")
        if "conflict" in str(e).lower():
            logger.error("🔄 Bot conflict detected! Another instance is running.")
            print("🔄 CONFLICT DETECTED! Another bot instance is running!")
        BOT_RUNNING = False
        raise
    finally:
        BOT_RUNNING = False
        logger.info("🛑 Bot stopped")
        print("🛑 Background Worker stopped")

if __name__ == "__main__":
    print("🎯 MAIN FUNCTION STARTING...")
    print("🌐 MAXXPHARM Background Worker")
    try:
        logger.info("🎯 RUNNING MAXXPHARM BOT WORKER")
        print("⚡ Starting asyncio.run(main())...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        logger.error(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
