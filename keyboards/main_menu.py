"""
🧭 Main Menu - Главное меню с динамическими ролями для MAXXPHARM CRM
aiogram 3.4.1 compatible
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional

def get_main_menu(user_role: str) -> ReplyKeyboardMarkup:
    """Получение главного меню в зависимости от роли пользователя"""
    
    if user_role == "client":
        return client_menu()
    elif user_role == "operator":
        return operator_menu()
    elif user_role == "picker":
        return picker_menu()
    elif user_role == "checker":
        return checker_menu()
    elif user_role == "courier":
        return courier_menu()
    elif user_role in ["admin", "director"]:
        return director_menu()
    else:
        return default_menu()

def client_menu() -> ReplyKeyboardMarkup:
    """Меню клиента"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Сделать заявку")],
            [KeyboardButton(text="📍 Мои заказы"), KeyboardButton(text="💳 Оплата")],
            [KeyboardButton(text="📞 Менеджер"), KeyboardButton(text="ℹ️ Информация")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def operator_menu() -> ReplyKeyboardMarkup:
    """Меню оператора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Новые заявки")],
            [KeyboardButton(text="💳 Подтверждение оплаты"), KeyboardButton(text="📦 Все заказы")],
            [KeyboardButton(text="🔎 Найти заказ"), KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def picker_menu() -> ReplyKeyboardMarkup:
    """Меню сборщика"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Заказы на сборку")],
            [KeyboardButton(text="🔄 В сборке"), KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def checker_menu() -> ReplyKeyboardMarkup:
    """Меню проверщика"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Заказы на проверке")],
            [KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def courier_menu() -> ReplyKeyboardMarkup:
    """Меню курьера"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚚 Заказы к доставке")],
            [KeyboardButton(text="📍 В пути"), KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def director_menu() -> ReplyKeyboardMarkup:
    """Меню директора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Аналитика")],
            [KeyboardButton(text="📦 Все заказы"), KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📈 Продажи"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def admin_menu() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Аналитика")],
            [KeyboardButton(text="📦 Все заказы"), KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🔧 Управление")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def default_menu() -> ReplyKeyboardMarkup:
    """Меню по умолчанию"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажмите /start для начала"
    )

# Меню для специфических действий
def cancel_menu() -> ReplyKeyboardMarkup:
    """Меню отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def payment_menu() -> ReplyKeyboardMarkup:
    """Меню оплаты"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Оплатить картой")],
            [KeyboardButton(text="💵 Оплатить наличными")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def support_menu() -> ReplyKeyboardMarkup:
    """Меню поддержки"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Позвонить менеджеру")],
            [KeyboardButton(text="💬 Написать в чат")],
            [KeyboardButton(text="📧 Отправить email")],
            [KeyboardButton(text="❌ Назад")]
        ],
        resize_keyboard=True
    )

# Удобные функции для использования
def get_menu_by_role(user_role: str) -> ReplyKeyboardMarkup:
    """Получение меню по роли (alias для get_main_menu)"""
    return get_main_menu(user_role)
