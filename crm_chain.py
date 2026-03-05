#!/usr/bin/env python3
"""
🚀 Complete CRM Chain - Полная цепочка заказа от клиента до доставки
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crm_chain.log')
    ]
)

logger = logging.getLogger("crm_chain")

# 🎭 Статусы заказа
class OrderStatus(Enum):
    CREATED = "created"
    WAITING_PAYMENT = "waiting_payment"
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    READY = "ready"
    CHECKING = "checking"
    WAITING_COURIER = "waiting_courier"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# 👤 Роли пользователей
class UserRole(Enum):
    CLIENT = "client"
    OPERATOR = "picker"
    PICKER = "picker"
    CHECKER = "checker"
    COURIER = "courier"
    ADMIN = "admin"
    DIRECTOR = "director"

# 📦 Модели данных
@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    client_name: str
    text: str
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
    metadata: Dict[str, Any] = None

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
    created_at: datetime = None

class CRMChain:
    """Основная CRM цепочка"""
    
    def __init__(self):
        self.orders = {}  # In-memory storage (в реальном проекте - БД)
        self.users = {}   # In-memory storage (в реальном проекте - БД)
        self.order_counter = 0
        self.user_counter = 0
        self.logger = logging.getLogger("crm_chain")
        
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
                role=role,
                created_at=datetime.now()
            )
            self.users[telegram_id] = user
        
        logger.info(f"✅ Created {len(test_users)} test users")
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        return self.users.get(telegram_id)
    
    async def create_order(self, client_id: int, text: str, items: List[Dict[str, Any]] = None) -> Order:
        """Создание заказа клиентом"""
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
            text=text,
            items=items or [],
            amount=amount,
            status=OrderStatus.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.orders[order.id] = order
        
        logger.info(f"📦 Order #{order.id} created by client {client_id}")
        return order
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus, updated_by: int, notes: Optional[str] = None) -> bool:
        """Обновление статуса заказа"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.now()
        if notes:
            order.notes = notes
        
        # Автоматическое назначение следующих исполнителей
        await self._auto_assign_next_role(order, new_status, updated_by)
        
        logger.info(f"📊 Order #{order_id} status: {old_status.value} → {new_status.value} by {updated_by}")
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
        
        # Находим работника с минимальным количеством активных заказов
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
        """Получение статистики для дашборда"""
        today = datetime.now().date()
        
        # Фильтруем заказы за сегодня
        today_orders = [
            order for order in self.orders.values()
            if order.created_at.date() == today
        ]
        
        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = len([
                order for order in today_orders if order.status == status
            ])
        
        return {
            "date": today.strftime("%d.%m.%Y"),
            "total_orders": len(today_orders),
            "delivered": status_counts.get("delivered", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "in_progress": len(today_orders) - status_counts.get("delivered", 0) - status_counts.get("cancelled", 0),
            "status_breakdown": status_counts
        }
    
    def complete_order(self, order_id: int):
        """Завершение заказа - освобождение исполнителей"""
        order = self.orders.get(order_id)
        if not order:
            return
        
        # Освобождаем нагрузку исполнителей
        if order.assigned_picker:
            picker = self.users.get(order.assigned_picker)
            if picker:
                picker.active_orders = max(0, picker.active_orders - 1)
        
        if order.assigned_checker:
            checker = self.users.get(order.assigned_checker)
            if checker:
                checker.active_orders = max(0, checker.active_orders - 1)
        
        if order.assigned_courier:
            courier = self.users.get(order.assigned_courier)
            if courier:
                courier.active_orders = max(0, courier.active_orders - 1)
        
        logger.info(f"✅ Order #{order_id} completed, workers released")

# 🎨 Форматирование сообщений
class MessageFormatter:
    """Форматирование сообщений для разных ролей"""
    
    @staticmethod
    def format_order_card(order: Order) -> str:
        """Форматирование карточки заказа"""
        status_emoji = {
            OrderStatus.CREATED: "📝",
            OrderStatus.WAITING_PAYMENT: "💳",
            OrderStatus.ACCEPTED: "✅",
            OrderStatus.PROCESSING: "🔄",
            OrderStatus.READY: "📦",
            OrderStatus.CHECKING: "🔍",
            OrderStatus.WAITING_COURIER: "🚚",
            OrderStatus.ON_WAY: "📍",
            OrderStatus.DELIVERED: "✅",
            OrderStatus.CANCELLED: "❌"
        }
        
        emoji = status_emoji.get(order.status, "📋")
        
        items_text = ""
        if order.items:
            items_text = "\n📋 <b>Состав:</b>\n"
            for item in order.items:
                items_text += f"• {item.get('product', 'Товар')} × {item.get('quantity', 1)}\n"
        
        return f"""
📦 <b>Заявка #{order.id}</b>

{emoji} <b>Статус:</b> {order.status.value.replace('_', ' ').title()}

👤 <b>Клиент:</b> {order.client_name}
💰 <b>Сумма:</b> ${order.amount:.2f}
📅 <b>Создана:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}

📝 <b>Описание:</b>
{order.text[:100]}...
{items_text}
"""
    
    @staticmethod
    def format_client_welcome(user: User) -> str:
        """Приветствие клиента"""
        return f"""
👋 <b>Здравствуйте, {user.name}!</b>

Добро пожаловать в систему заказов фармпрепаратов 🏥

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
        """Форматирование дашборда директора"""
        return f"""
📊 <b>Дашборд MAXXPHARM</b>
📅 {stats['date']}

📈 <b>Сегодня:</b>
📦 Заказов: {stats['total_orders']}
✅ Доставлено: {stats['delivered']}
❌ Отказ: {stats['cancelled']}
🔄 В работе: {stats['in_progress']}

📊 <b>По статусам:</b>
"""
        
        for status, count in stats['status_breakdown'].items():
            if count > 0:
                status_emoji = {
                    "created": "📝",
                    "waiting_payment": "💳",
                    "accepted": "✅",
                    "processing": "🔄",
                    "ready": "📦",
                    "checking": "🔍",
                    "waiting_courier": "🚚",
                    "on_way": "📍",
                    "delivered": "✅",
                    "cancelled": "❌"
                }
                emoji = status_emoji.get(status, "📋")
                stats['status_breakdown'][status] = count
                stats_text += f"{emoji} {status.replace('_', ' ').title()}: {count}\n"
        
        return stats_text

# 🎯 Глобальные функции
crm_chain = CRMChain()
formatter = MessageFormatter()

async def create_client_order(telegram_id: int, text: str, items: List[Dict[str, Any]] = None) -> Order:
    """Создание заказа клиентом"""
    user = crm_chain.get_user_by_telegram_id(telegram_id)
    if not user or user.role != UserRole.CLIENT:
        raise ValueError("User not found or not a client")
    
    return await crm_chain.create_order(user.id, text, items)

async def update_order_status(order_id: int, new_status: OrderStatus, updated_by: int, notes: Optional[str] = None) -> bool:
    """Обновление статуса заказа"""
    return await crm_chain.update_order_status(order_id, new_status, updated_by, notes)

def get_user_orders(telegram_id: int) -> List[Order]:
    """Получение заказов пользователя"""
    user = crm_chain.get_user_by_telegram_id(telegram_id)
    if not user:
        return []
    
    if user.role == UserRole.CLIENT:
        return crm_chain.get_orders_by_client(user.id)
    else:
        return crm_chain.get_orders_by_assignee(user.id, user.role)

def get_orders_by_status(status: OrderStatus) -> List[Order]:
    """Получение заказов по статусу"""
    return crm_chain.get_orders_by_status(status)

def get_dashboard_stats() -> Dict[str, Any]:
    """Получение статистики дашборда"""
    return crm_chain.get_dashboard_stats()

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Получение пользователя"""
    return crm_chain.get_user_by_telegram_id(telegram_id)

# 🎯 Тестовые функции
async def test_complete_chain():
    """Тест полной цепочки заказа"""
    print("🧪 Testing complete CRM chain...")
    
    # 1. Клиент создает заказ
    client = get_user_by_telegram_id(697780128)  # Клиент Ахмад
    order = await create_client_order(
        client.telegram_id,
        "Нужны лекарства: Парацетамол и Амоксиклав",
        [
            {"product": "Парацетамол 500мг", "quantity": 2, "price": 5.50},
            {"product": "Амоксиклав 1000мг", "quantity": 1, "price": 12.00}
        ]
    )
    print(f"📦 Order #{order.id} created by {client.name}")
    
    # 2. Оператор принимает заказ
    await update_order_status(order.id, OrderStatus.ACCEPTED, 697780124, "Принято в обработку")
    print(f"✅ Order #{order.id} accepted by operator")
    
    # 3. Сборщик начинает сборку
    await update_order_status(order.id, OrderStatus.PROCESSING, 697780125, "Начал сборку")
    print(f"🔄 Order #{order.id} processing by picker")
    
    # 4. Сборщик завершает сборку
    await update_order_status(order.id, OrderStatus.READY, 697780125, "Сборка завершена")
    print(f"📦 Order #{order.id} ready by picker")
    
    # 5. Проверщик проверяет заказ
    await update_order_status(order.id, OrderStatus.CHECKING, 697780126, "Начал проверку")
    print(f"🔍 Order #{order.id} checking by checker")
    
    # 6. Проверщик завершает проверку
    await update_order_status(order.id, OrderStatus.WAITING_COURIER, 697780126, "Проверка пройдена")
    print(f"✅ Order #{order.id} checked by checker")
    
    # 7. Курьер забирает заказ
    await update_order_status(order.id, OrderStatus.ON_WAY, 697780127, "Забрал заказ")
    print(f"🚚 Order #{order.id} on way by courier")
    
    # 8. Курьер доставляет заказ
    await update_order_status(order.id, OrderStatus.DELIVERED, 697780127, "Доставлено")
    print(f"✅ Order #{order.id} delivered by courier")
    
    # 9. Завершаем заказ (освобождаем исполнителей)
    crm_chain.complete_order(order.id)
    print(f"🎉 Order #{order.id} chain completed!")
    
    return order

if __name__ == "__main__":
    # Тест полной цепочки
    asyncio.run(test_complete_chain())
