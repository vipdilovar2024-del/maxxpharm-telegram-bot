#!/usr/bin/env python3
"""
📱 Uber-like UX Interface - Идеальный интерфейс Telegram CRM как приложение
Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Импортируем aiogram
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('uber_ux.log')
    ]
)

logger = logging.getLogger("uber_ux")

# 🎭 Статусы заказа с эмодзи
class OrderStatus(Enum):
    CREATED = ("created", "📝", "Создана")
    WAITING_PAYMENT = ("waiting_payment", "💳", "Ожидает оплату")
    ACCEPTED = ("accepted", "✅", "Принята")
    PROCESSING = ("processing", "🔄", "В сборке")
    READY = ("ready", "📦", "Собрана")
    CHECKING = ("checking", "🔍", "На проверке")
    WAITING_COURIER = ("waiting_courier", "🚚", "Ожидает курьера")
    ON_WAY = ("on_way", "📍", "В пути")
    DELIVERED = ("delivered", "✅", "Доставлена")
    CANCELLED = ("cancelled", "❌", "Отменена")
    
    def __init__(self, value, emoji, title):
        self.value = value
        self.emoji = emoji
        self.title = title

# 👤 Роли пользователей
class UserRole(Enum):
    CLIENT = "client"
    OPERATOR = "operator"
    PICKER = "picker"
    CHECKER = "checker"
    COURIER = "courier"
    DIRECTOR = "director"

# 📦 Модели данных
@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    client_name: str
    client_phone: str
    client_address: str
    items: List[Dict[str, Any]]
    amount: float
    status: OrderStatus
    assigned_operator: Optional[int] = None
    assigned_picker: Optional[int] = None
    assigned_checker: Optional[int] = None
    assigned_courier: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None
    notes: Optional[str] = None

@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: int
    name: str
    role: UserRole
    phone: Optional[str] = None
    is_active: bool = True
    active_orders: int = 0

class UberLikeUX:
    """Uber-like UX интерфейс"""
    
    def __init__(self):
        self.orders = {}  # In-memory storage
        self.users = {}   # In-memory storage
        self.order_counter = 0
        self.user_counter = 0
        self.logger = logging.getLogger("uber_ux")
        
        # Создаем тестовых пользователей
        self._create_test_users()
    
    def _create_test_users(self):
        """Создание тестовых пользователей"""
        test_users = [
            (697780123, "Мухаммадмуссо", UserRole.DIRECTOR),
            (697780124, "Оператор Али", UserRole.OPERATOR),
            (697780125, "Сборщик Рустам", UserRole.PICKER),
            (697780126, "Проверщик Камол", UserRole.CHECKER),
            (697780127, "Курьер Бекзод", UserRole.COURIER),
            (697780128, "Клиент Ахмад", UserRole.CLIENT),
            (697780129, "Клиент Фарход", UserRole.CLIENT),
        ]
        
        for telegram_id, name, role in test_users:
            self.user_counter += 1
            user = User(
                id=self.user_counter,
                telegram_id=telegram_id,
                name=name,
                role=role
            )
            self.users[telegram_id] = user
        
        logger.info(f"✅ Created {len(test_users)} test users")
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        return self.users.get(telegram_id)
    
    async def create_order(self, client_id: int, text: str, items: List[Dict[str, Any]] = None) -> Order:
        """Создание заказа"""
        self.order_counter += 1
        
        # Рассчитываем сумму
        amount = 0.0
        if items:
            for item in items:
                amount += item.get('price', 0) * item.get('quantity', 1)
        
        order = Order(
            id=self.order_counter,
            client_id=client_id,
            client_name=self.users[client_id].name,
            client_phone="+992900000000",
            client_address="г. Душанбе, ул. Айни 45",
            text=text,
            items=items or [],
            amount=amount,
            status=OrderStatus.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.orders[order.id] = order
        
        logger.info(f"📦 Order #{order.id} created")
        return order
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus, updated_by: int) -> bool:
        """Обновление статуса заказа"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.now()
        
        # Автоматическое назначение следующих исполнителей
        await self._auto_assign_next_role(order, new_status, updated_by)
        
        logger.info(f"📊 Order #{order_id} status: {old_status.title} → {new_status.title}")
        return True
    
    async def _auto_assign_next_role(self, order: Order, status: OrderStatus, updated_by: int):
        """Автоматическое назначение следующего исполнителя"""
        if status == OrderStatus.ACCEPTED:
            # Назначаем сборщика
            picker = await self._get_least_loaded_worker(UserRole.PICKER)
            if picker:
                order.assigned_picker = picker.id
                picker.active_orders += 1
                logger.info(f"📦 Picker {picker.name} assigned to order #{order.id}")
        
        elif status == OrderStatus.READY:
            # Назначаем проверщика
            checker = await self._get_least_loaded_worker(UserRole.CHECKER)
            if checker:
                order.assigned_checker = checker.id
                checker.active_orders += 1
                logger.info(f"🔍 Checker {checker.name} assigned to order #{order.id}")
        
        elif status == OrderStatus.WAITING_COURIER:
            # Назначаем курьера
            courier = await self._get_least_loaded_worker(UserRole.COURIER)
            if courier:
                order.assigned_courier = courier.id
                courier.active_orders += 1
                logger.info(f"🚚 Courier {courier.name} assigned to order #{order.id}")
    
    async def _get_least_loaded_worker(self, role: UserRole) -> Optional[User]:
        """Получение работника с минимальной нагрузкой"""
        workers = [user for user in self.users.values() if user.role == role and user.is_active]
        
        if not workers:
            return None
        
        return min(workers, key=lambda u: u.active_orders)
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Получение заказов по статусу"""
        return [order for order in self.orders.values() if order.status == status]
    
    def get_orders_by_assignee(self, user_id: int, role: UserRole) -> List[Order]:
        """Получение заказов исполнителя"""
        orders = []
        
        for order in self.orders.values():
            if role == UserRole.OPERATOR and order.assigned_operator == user_id:
                orders.append(order)
            elif role == UserRole.PICKER and order.assigned_picker == user_id:
                orders.append(order)
            elif role == UserRole.CHECKER and order.assigned_checker == user_id:
                orders.append(order)
            elif role == UserRole.COURIER and order.assigned_courier == user_id:
                orders.append(order)
        
        return orders
    
    def get_orders_by_client(self, client_id: int) -> List[Order]:
        """Получение заказов клиента"""
        return [order for order in self.orders.values() if order.client_id == client_id]
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Статистика для дашборда"""
        today = datetime.now().date()
        
        today_orders = [
            order for order in self.orders.values()
            if order.created_at.date() == today
        ]
        
        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = len([
                order for order in today_orders if order.status == status
            ])
        
        total_revenue = sum(order.amount for order in today_orders if order.status == OrderStatus.DELIVERED)
        
        return {
            "date": today.strftime("%d.%m.%Y"),
            "total_orders": len(today_orders),
            "delivered": status_counts.get("delivered", 0),
            "in_progress": len(today_orders) - status_counts.get("delivered", 0) - status_counts.get("cancelled", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "revenue": total_revenue
        }

class UXFormatter:
    """Форматирование UX сообщений"""
    
    @staticmethod
    def format_order_card(order: Order, show_actions: bool = True) -> str:
        """Универсальная карточка заказа"""
        # Формируем товары
        items_text = ""
        if order.items:
            items_text = "\n💊 <b>Товары:</b>\n"
            for item in order.items:
                items_text += f"• {item.get('product', 'Товар')} × {item.get('quantity', 1)}\n"
        
        return f"""
📦 <b>Заказ #{order.id}</b>

👤 <b>Клиент:</b> {order.client_name}
📞 <b>Телефон:</b> {order.client_phone}
📍 <b>Адрес:</b> {order.client_address}

{items_text}
💰 <b>Сумма:</b> {order.amount:.0f} сомони

📊 <b>Статус:</b> {order.status.emoji} {order.status.title}
"""
    
    @staticmethod
    def format_client_welcome(user: User) -> str:
        """Приветствие клиента"""
        return f"""
👋 <b>Здравствуйте, {user.name}!</b>

Добро пожаловать в MAXXPHARM 🏥

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_operator_welcome(user: User) -> str:
        """Приветствие оператора"""
        return f"""
👨‍💻 <b>Панель оператора</b>

👤 <b>Оператор:</b> {user.name}
📊 <b>Активных заказов:</b> {user.active_orders}

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_picker_welcome(user: User) -> str:
        """Приветствие сборщика"""
        return f"""
📦 <b>Панель сборщика</b>

👤 <b>Сборщик:</b> {user.name}
📊 <b>Активных заказов:</b> {user.active_orders}

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_checker_welcome(user: User) -> str:
        """Приветствие проверщика"""
        return f"""
🔍 <b>Панель проверщика</b>

👤 <b>Проверщик:</b> {user.name}
📊 <b>Активных заказов:</b> {user.active_orders}

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_courier_welcome(user: User) -> str:
        """Приветствие курьера"""
        return f"""
🚚 <b>Панель курьера</b>

👤 <b>Курьер:</b> {user.name}
📊 <b>Активных заказов:</b> {user.active_orders}

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_director_welcome(user: User) -> str:
        """Приветствие директора"""
        return f"""
👑 <b>Панель директора</b>

👤 <b>Директор:</b> {user.name}

Выберите действие из меню ниже 👇
"""
    
    @staticmethod
    def format_dashboard(stats: Dict[str, Any]) -> str:
        """Дашборд директора"""
        return f"""
📊 <b>Сегодня</b>

📦 <b>Заказы:</b> {stats['total_orders']}
✅ <b>Доставлено:</b> {stats['delivered']}
🔄 <b>В работе:</b> {stats['in_progress']}
❌ <b>Отказ:</b> {stats['cancelled']}

💰 <b>Выручка:</b> {stats['revenue']:.0f} сомони
"""
    
    @staticmethod
    def format_new_orders_list(orders: List[Order]) -> str:
        """Список новых заявок"""
        if not orders:
            return "📭 <b>Новых заявок нет</b>"
        
        text = f"📥 <b>Новые заявки ({len(orders)})</b>\n\n"
        
        for order in orders[:5]:  # Показываем первые 5
            text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
            text += f"💰 {order.amount:.0f} сомони • 🕐 {order.created_at.strftime('%H:%M')}\n\n"
        
        return text
    
    @staticmethod
    def format_picker_orders_list(orders: List[Order]) -> str:
        """Список заказов сборщика"""
        if not orders:
            return "📭 <b>Нет заказов для сборки</b>"
        
        text = f"📦 <b>Заказы на сборку ({len(orders)})</b>\n\n"
        
        for order in orders:
            text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
            text += f"📝 {order.text[:30]}...\n\n"
        
        return text
    
    @staticmethod
    def format_checker_orders_list(orders: List[Order]) -> str:
        """Список заказов проверщика"""
        if not orders:
            return "📭 <b>Нет заказов на проверке</b>"
        
        text = f"🔍 <b>Заказы на проверке ({len(orders)})</b>\n\n"
        
        for order in orders:
            text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
            text += f"📦 Собрано: {order.updated_at.strftime('%H:%M')}\n\n"
        
        return text
    
    @staticmethod
    def format_courier_orders_list(orders: List[Order]) -> str:
        """Список заказов курьера"""
        if not orders:
            return "📭 <b>Нет заказов для доставки</b>"
        
        text = f"🚚 <b>Заказы к доставке ({len(orders)})</b>\n\n"
        
        for order in orders:
            text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
            text += f"📍 {order.client_address}\n\n"
        
        return text
    
    @staticmethod
    def format_client_orders_list(orders: List[Order]) -> str:
        """Список заказов клиента"""
        if not orders:
            return "📭 <b>У вас нет заказов</b>"
        
        text = f"📍 <b>Мои заказы ({len(orders)})</b>\n\n"
        
        for order in orders:
            text += f"{order.status.emoji} <b>#{order.id}</b> {order.status.title}\n"
            text += f"💰 {order.amount:.0f} сомони • 🕐 {order.created_at.strftime('%d.%m')}\n\n"
        
        return text

class UXKeyboardBuilder:
    """Построитель UX клавиатур"""
    
    @staticmethod
    def get_client_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню клиента"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Сделать заявку")],
                [KeyboardButton(text="📍 Мои заказы"), KeyboardButton(text="💳 Оплата")],
                [KeyboardButton(text="📞 Менеджер"), KeyboardButton(text="ℹ️ Информация")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_operator_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню оператора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📥 Новые заявки")],
                [KeyboardButton(text="💳 Подтверждение оплаты"), KeyboardButton(text="📦 Все заказы")],
                [KeyboardButton(text="🔎 Найти заказ")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_picker_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню сборщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Заказы на сборку")],
                [KeyboardButton(text="🔄 В сборке")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_checker_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню проверщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Заказы на проверке")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_courier_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню курьера"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚚 Заказы к доставке")],
                [KeyboardButton(text="📍 В пути")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_director_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню директора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Дашборд")],
                [KeyboardButton(text="📈 Продажи"), KeyboardButton(text="👥 Сотрудники")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_order_action_keyboard(order_id: int, user_role: UserRole) -> InlineKeyboardMarkup:
        """Клавиатура действий с заказом"""
        if user_role == UserRole.OPERATOR:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_order_{order_id}"),
                        InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_order_{order_id}")
                    ],
                    [
                        InlineKeyboardButton(text="📞 Позвонить клиенту", callback_data=f"call_client_{order_id}")
                    ]
                ]
            )
        elif user_role == UserRole.PICKER:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="▶ Начать сборку", callback_data=f"start_picking_{order_id}"),
                        InlineKeyboardButton(text="📦 Готово", callback_data=f"finish_picking_{order_id}")
                    ]
                ]
            )
        elif user_role == UserRole.CHECKER:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="❌ Ошибка", callback_data=f"check_error_{order_id}"),
                        InlineKeyboardButton(text="✅ Проверено", callback_data=f"check_passed_{order_id}")
                    ]
                ]
            )
        elif user_role == UserRole.COURIER:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🚚 Взять заказ", callback_data=f"take_delivery_{order_id}"),
                        InlineKeyboardButton(text="📍 Я в пути", callback_data=f"on_way_{order_id}")
                    ],
                    [
                        InlineKeyboardButton(text="✅ Доставлено", callback_data=f"delivered_{order_id}")
                    ]
                ]
            )
        else:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Детали", callback_data=f"order_details_{order_id}")]
                ]
            )
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура отмены"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )

# 🎯 Глобальные экземпляры
uber_ux = UberLikeUX()
formatter = UXFormatter()
keyboard_builder = UXKeyboardBuilder()

# 🎯 Удобные функции
async def create_order_from_text(telegram_id: int, text: str) -> Order:
    """Создание заказа из текста"""
    user = uber_ux.get_user_by_telegram_id(telegram_id)
    if not user or user.role != UserRole.CLIENT:
        raise ValueError("User not found or not a client")
    
    # Создаем тестовые товары
    items = [
        {"product": "Препарат из сообщения", "quantity": 1, "price": 50.0}
    ]
    
    return await uber_ux.create_order(user.id, text, items)

async def update_order_status_callback(order_id: int, new_status: OrderStatus, updated_by: int) -> bool:
    """Обновление статуса заказа"""
    return await uber_ux.update_order_status(order_id, new_status, updated_by)

def get_user_orders(telegram_id: int) -> List[Order]:
    """Получение заказов пользователя"""
    user = uber_ux.get_user_by_telegram_id(telegram_id)
    if not user:
        return []
    
    if user.role == UserRole.CLIENT:
        return uber_ux.get_orders_by_client(user.id)
    else:
        return uber_ux.get_orders_by_assignee(user.id, user.role)

def get_orders_by_status(status: OrderStatus) -> List[Order]:
    """Получение заказов по статусу"""
    return uber_ux.get_orders_by_status(status)

def get_dashboard_stats() -> Dict[str, Any]:
    """Получение статистики дашборда"""
    return uber_ux.get_dashboard_stats()

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Получение пользователя"""
    return uber_ux.get_user_by_telegram_id(telegram_id)

# 🧪 Тестовая функция
async def test_uber_ux():
    """Тест Uber-like UX"""
    print("🧱 Testing Uber-like UX...")
    
    # Клиент создает заказ
    client = get_user_by_telegram_id(697780128)
    order = await create_order_from_text(
        client.telegram_id,
        "Нужны лекарства: Парацетамол и Амоксиклав"
    )
    print(f"📦 Order #{order.id} created by {client.name}")
    
    # Оператор принимает
    await update_order_status_callback(order.id, OrderStatus.ACCEPTED, 697780124)
    print(f"✅ Order #{order.id} accepted")
    
    # Сборщик собирает
    await update_order_status_callback(order.id, OrderStatus.PROCESSING, 697780125)
    print(f"🔄 Order #{order.id} processing")
    
    await update_order_status_callback(order.id, OrderStatus.READY, 697780125)
    print(f"📦 Order #{order.id} ready")
    
    # Проверщик проверяет
    await update_order_status_callback(order.id, OrderStatus.CHECKING, 697780126)
    print(f"🔍 Order #{order.id} checking")
    
    await update_order_status_callback(order.id, OrderStatus.WAITING_COURIER, 697780126)
    print(f"🚚 Order #{order.id} waiting courier")
    
    # Курьер доставляет
    await update_order_status_callback(order.id, OrderStatus.ON_WAY, 697780127)
    print(f"📍 Order #{order.id} on way")
    
    await update_order_status_callback(order.id, OrderStatus.DELIVERED, 697780127)
    print(f"✅ Order #{order.id} delivered")
    
    return order

if __name__ == "__main__":
    asyncio.run(test_uber_ux())
