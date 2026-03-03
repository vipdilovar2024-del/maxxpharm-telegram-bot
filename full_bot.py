#!/usr/bin/env python3
"""
Full Bot - MAXXPHARM Telegram Bot (Background Worker)
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

# Role system
class UserRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    COURIER = "COURIER"
    CLIENT = "CLIENT"

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

# User management
def get_user_role(user_id):
    if user_id == ADMIN_ID:
        return UserRole.SUPER_ADMIN
    return USERS.get(user_id, {}).get("role", UserRole.CLIENT)

def is_admin(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN]

def is_manager(user_id):
    return get_user_role(user_id) in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER]

# Keyboards - ИСПРАВЛЕНО для aiogram 3.4.1
def get_main_menu(user_id):
    role = get_user_role(user_id)
    
    if role == UserRole.SUPER_ADMIN:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="👥 Пользователи")],
                [KeyboardButton(text="🧾 Товары"), KeyboardButton(text="🏷 Категории")],
                [KeyboardButton(text="🏪 Склад"), KeyboardButton(text="⚙ Настройки")],
                [KeyboardButton(text="📝 Логи"), KeyboardButton(text="🚀 Выход")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.ADMIN:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="👥 Пользователи")],
                [KeyboardButton(text="🧾 Товары"), KeyboardButton(text="🏪 Склад")],
                [KeyboardButton(text="🚀 Выход")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.MANAGER:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="🧾 Товары")],
                [KeyboardButton(text="🚀 Выход")]
            ],
            resize_keyboard=True
        )
    elif role == UserRole.COURIER:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Мои доставки")],
                [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="📞 Поддержка")],
                [KeyboardButton(text="🚀 Выход")]
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

# Keyboards - УДАЛЯЕМ ДУБЛИКАТ
# def get_main_menu(is_admin=False): - УДАЛЕНО

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

# User management
def is_admin(user_id):
    return user_id == ADMIN_ID

# Handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    admin = is_admin(user_id)
    
    USERS[user_id] = {
        "id": user_id,
        "full_name": message.from_user.full_name,
        "cart": [],
        "orders": []
    }
    
    if admin:
        await message.answer(
            f"👑 <b>Добро пожаловать, {message.from_user.full_name}!</b>\n\n"
            "🚀 <b>MAXXPHARM Admin Panel</b>\n\n"
            "📊 Вы вошли как Super Admin\n"
            "🔧 Полный доступ к системе\n\n"
            "Выберите действие в меню:",
            reply_markup=get_main_menu(is_admin=True)
        )
    else:
        await message.answer(
            f"🚀 <b>Добро пожаловать в MAXXPHARM!</b>\n\n"
            f"👤 {message.from_user.full_name}\n\n"
            "🛍 Ваш надежный партнер в мире фармацевтики\n"
            "📦 Быстрая доставка качественных товаров\n\n"
            "Выберите действие в меню:",
            reply_markup=get_main_menu(is_admin=False)
        )
    
    logger.info(f"User {user_id} started bot (admin: {admin})")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    admin = is_admin(message.from_user.id)
    
    if admin:
        help_text = (
            "🆘 <b>Помощь MAXXPHARM Admin</b>\n\n"
            "📋 <b>Админ команды:</b>\n"
            "• /start - Главное меню\n"
            "• /help - Эта справка\n"
            "• /stats - Быстрая статистика\n\n"
            "🔧 <b>Функции:</b>\n"
            "• 📊 Статистика - Просмотр данных\n"
            "• 📦 Заказы - Управление заказами\n"
            "• 👥 Пользователи - Управление клиентами\n"
            "• 🧾 Товары - Управление каталогом\n"
            "• 🏷 Категории - Управление категориями\n"
            "• 🏪 Склад - Управление складом\n"
            "• ⚙ Настройки - Системные настройки\n"
            "• 📝 Логи - Просмотр логов\n\n"
            "✅ Система работает стабильно!"
        )
    else:
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
    
    await message.answer(help_text, reply_markup=get_main_menu(admin))

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды!")
        return
    
    stats_text = (
        "📊 <b>Статистика MAXXPHARM</b>\n\n"
        f"👥 Пользователей: {len(USERS)}\n"
        f"📦 Товаров: {len(PRODUCTS)}\n"
        f"🏷 Категорий: {len(CATEGORIES)}\n"
        f"🛒 Заказов: {len(ORDERS)}\n\n"
        "🤖 Статус: ✅ Работает\n"
        "🌐 Платформа: Render\n"
        "🐍 Python: 3.11.14\n\n"
        "✅ Все системы в норме!"
    )
    
    await message.answer(stats_text, reply_markup=get_main_menu(is_admin=True))

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
            reply_markup=get_main_menu(is_admin=False)
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
            reply_markup=get_main_menu(is_admin=False)
        )
        return
    
    orders_text = "📦 <b>Ваши заказы:</b>\n\n"
    
    for order in user_orders:
        orders_text += f"🆔 Заказ #{order['id']}\n"
        orders_text += f"📅 Дата: {order['date']}\n"
        orders_text += f"💰 Сумма: {order['total']}₽\n"
        orders_text += f"📊 Статус: {order['status']}\n\n"
    
    await message.answer(orders_text, reply_markup=get_main_menu(is_admin=False))

@dp.message(F.text == "📞 Поддержка")
async def cmd_support(message: types.Message):
    support_text = (
        "📞 <b>Поддержка MAXXPHARM</b>\n\n"
        "👥 Наши специалисты готовы помочь!\n\n"
        "📞 <b>Телефон:</b> +7 (XXX) XXX-XX-XX\n"
        "📧 <b>Email:</b> support@maxxpharm.ru\n"
        "⏰ <b>Время работы:</b> 9:00 - 18:00\n\n"
        "💬 <b>Напишите ваш вопрос:</b>\n"
        "Мы ответим в ближайшее время!\n\n"
        "✅ Всегда на связи!"
    )
    
    await message.answer(support_text, reply_markup=get_main_menu(is_admin=False))

@dp.message(F.text == "🔍 Поиск")
async def cmd_search(message: types.Message):
    await message.answer(
        "🔍 <b>Поиск товаров</b>\n\n"
        "🔧 Функция поиска в разработке\n\n"
        "📝 Введите название товара для поиска\n\n"
        "✅ Скоро будет доступна!",
        reply_markup=get_main_menu(is_admin=False)
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
        f"🛍 Клиентов: {len([u for u in USERS.values() if not is_admin(u['id'])])}\n"
        f"👑 Админов: {len([u for u in USERS.values() if is_admin(u['id'])])}\n\n"
        f"📦 Всего товаров: {len(PRODUCTS)}\n"
        f"🏷 Категорий: {len(CATEGORIES)}\n\n"
        f"🛒 Всего заказов: {len(ORDERS)}\n"
        f"✅ Выполнено: {len([o for o in ORDERS if o['status'] == 'COMPLETED'])}\n"
        f"⏳ В работе: {len([o for o in ORDERS if o['status'] in ['NEW', 'CONFIRMED', 'IN_PROGRESS']])}\n\n"
        "🤖 Статус бота: ✅ Работает\n"
        "🌐 Платформа: Render\n"
        "🐍 Python: 3.11.14"
    )
    
    await message.answer(stats_text, reply_markup=get_main_menu(is_admin=True))

@dp.message(F.text == "📦 Заказы")
async def admin_orders(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    if not ORDERS:
        await message.answer(
            "📦 <b>Заказов пока нет</b>\n\n"
            "🛍 Ожидайте заказы от клиентов",
            reply_markup=get_main_menu(is_admin=True)
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
    
    await message.answer(orders_text, reply_markup=get_main_menu(is_admin=True))

@dp.message(F.text == "👥 Пользователи")
async def admin_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    users_text = "👥 <b>Все пользователи:</b>\n\n"
    
    for user_id, user_data in USERS.items():
        users_text += f"👤 {user_data['full_name']}\n"
        users_text += f"🆔 ID: {user_id}\n"
        users_text += f"🔑 Роль: {'Admin' if is_admin(user_id) else 'Client'}\n"
        users_text += f"📦 Заказов: {len(user_data.get('orders', []))}\n\n"
    
    await message.answer(users_text, reply_markup=get_main_menu(is_admin=True))

@dp.message(F.text == "🧾 Товары")
async def admin_products(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    products_text = "🧾 <b>Все товары:</b>\n\n"
    
    for product in PRODUCTS:
        products_text += f"📦 {product['name']}\n"
        products_text += f"💰 Цена: {product['price']}₽\n"
        products_text += f"📊 Остаток: {product['stock']} шт\n"
        products_text += f"🏷 Категория: {product['category']}\n\n"
    
    await message.answer(products_text, reply_markup=get_main_menu(is_admin=True))

@dp.message(F.text == "🚀 Выход")
async def admin_logout(message: types.Message):
    await message.answer(
        "🚀 <b>Выход из админ-панели</b>\n\n"
        "👤 Вы вернулись в режим клиента",
        reply_markup=get_main_menu(is_admin=False)
    )

# Other admin handlers
@dp.message(F.text.in_(["🏷 Категории", "🏪 Склад", "⚙ Настройки", "📝 Логи"]))
async def admin_other(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен!")
        return
    
    feature = message.text
    await message.answer(
        f"⚠️ <b>{feature}</b>\n\n"
        "🔧 Функция в разработке\n\n"
        "✅ Скоро будет доступна!",
        reply_markup=get_main_menu(is_admin=True)
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
        f"📝 Качественный фармацевтический продукт"
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
        reply_markup=get_main_menu(is_admin=False)
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
        reply_markup=get_main_menu(is_admin=False)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: types.CallbackQuery):
    is_admin_user = is_admin(callback.from_user.id)
    
    await callback.message.edit_text(
        "🚀 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(is_admin=is_admin_user)
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
        f"� <b>Описание:</b>\n"
        f"Качественный фармацевтический продукт\n"
        f"производства высшего качества.\n\n"
        f"✅ <b>Сертифицировано</b>\n"
        f"🏆 <b>Гарантия качества</b>"
    )
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_product_actions_keyboard(product_id)
    )
    await callback.answer()

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
