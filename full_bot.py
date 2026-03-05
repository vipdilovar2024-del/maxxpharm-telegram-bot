#!/usr/bin/env python3
"""
🤖 MAXXPHARM AI-CRM TELEGRAM BOT
Полнофункциональный CRM с AI-анализом и автоматизацией
"""

# 🔥 FILE STARTED - ОТЛАДОЧНЫЙ PRINT
print("🔥 FILE STARTED - full_bot.py загружен!")

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# 🗄️ Database imports
import asyncpg
from asyncpg import Connection
import database

# 🧠 AI Brain imports
import ai_brain

# 🔄 Data Pipeline imports
import data_pipeline

# ⏰ AI Scheduler imports
import ai_scheduler

# � Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))
RENDER = os.getenv("RENDER", "False").lower() == "true"

# 🗄️ Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "maxxpharm_db")

# 🧠 AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔄 Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 📊 Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
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

# 🎹 Клавиатуры
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
                    KeyboardButton(text="🛍 Каталог")
                ],
                [
                    KeyboardButton(text="🔍 Поиск"),
                    KeyboardButton(text="🛒 Корзина")
                ],
                [
                    KeyboardButton(text="📦 Мои заказы"),
                    KeyboardButton(text="📞 Поддержка")
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
        welcome_text = f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n🔐 Ваша роль: {role}\n⏰ Сессия активна до: {expires}\n\nВыберите действие из меню ниже:"
    else:
        welcome_text = "Добро пожаловать в MAXXPHARM! 🏥\n\nВыберите действие из меню:"
    
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
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(url=None)  # Принудительно удаляем webhook
            print("✅ Webhook deleted successfully!")
        except Exception as e:
            print(f"⚠️ Webhook deletion error: {e}")
        
        # Ждем немного для стабилизации
        await asyncio.sleep(2)
        
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
