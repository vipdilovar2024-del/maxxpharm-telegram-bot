#!/usr/bin/env python3
"""
🏢 CRM Core Layer - Сердце Enterprise системы
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

# 🎭 Роли пользователей
class UserRole(Enum):
    CLIENT = "client"
    OPERATOR = "operator"
    PICKER = "picker"
    CHECKER = "checker"
    COURIER = "courier"
    ADMIN = "admin"
    DIRECTOR = "director"

# 📊 Статусы заказов
class OrderStatus(Enum):
    CREATED = "created"
    WAITING_PAYMENT = "waiting_payment"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    READY = "ready"
    CHECKING = "checking"
    WAITING_COURIER = "waiting_courier"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# 🎯 Приоритеты заказов
class OrderPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

# 📦 Модели данных
@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: int
    name: str
    username: Optional[str]
    phone: Optional[str]
    role: UserRole
    email: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    text: str
    voice_url: Optional[str]
    photo_url: Optional[str]
    status: OrderStatus
    priority: OrderPriority
    amount: float
    items: List[Dict[str, Any]] = field(default_factory=list)
    assigned_operator: Optional[int] = None
    assigned_picker: Optional[int] = None
    assigned_checker: Optional[int] = None
    assigned_courier: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OrderItem:
    """Модель элемента заказа"""
    id: int
    order_id: int
    product_name: str
    quantity: int
    price: float
    total_price: float
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Payment:
    """Модель платежа"""
    id: int
    order_id: int
    amount: float
    method: str
    photo_url: Optional[str]
    voice_url: Optional[str]
    confirmed: bool
    confirmed_by: Optional[int]
    confirmed_at: Optional[datetime]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class StatusHistory:
    """Модель истории статусов"""
    id: int
    order_id: int
    old_status: Optional[OrderStatus]
    new_status: OrderStatus
    changed_by: int
    changed_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

@dataclass
class ActivityLog:
    """Модель лога активности"""
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime = field(default_factory=datetime.now)

class RoleManager:
    """Менеджер ролей пользователей"""
    
    def __init__(self):
        self.logger = logging.getLogger("role_manager")
        self._roles_cache = {}  # Кеш ролей
    
    async def get_user_role(self, telegram_id: int) -> Optional[UserRole]:
        """Получение роли пользователя"""
        # Проверяем кеш
        if telegram_id in self._roles_cache:
            return self._roles_cache[telegram_id]
        
        # Здесь должна быть логика получения роли из БД
        # Для примера используем мок-данные
        mock_roles = {
            697780123: UserRole.DIRECTOR,
            697780124: UserRole.OPERATOR,
            697780125: UserRole.PICKER,
            697780126: UserRole.CHECKER,
            697780127: UserRole.COURIER,
            697780128: UserRole.CLIENT,
            697780129: UserRole.CLIENT,
            697780130: UserRole.ADMIN,
        }
        
        role = mock_roles.get(telegram_id, UserRole.CLIENT)
        
        # Сохраняем в кеш
        self._roles_cache[telegram_id] = role
        
        return role
    
    async def create_user(self, telegram_id: int, name: str, username: Optional[str], role: UserRole) -> bool:
        """Создание пользователя с ролью"""
        try:
            # Здесь должна быть логика создания пользователя в БД
            self._roles_cache[telegram_id] = role
            self.logger.info(f"Created user {telegram_id} with role {role.value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False
    
    async def update_user_role(self, telegram_id: int, new_role: UserRole) -> bool:
        """Обновление роли пользователя"""
        try:
            self._roles_cache[telegram_id] = new_role
            self.logger.info(f"Updated user {telegram_id} role to {new_role.value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update user role: {e}")
            return False
    
    async def get_users_by_role(self, role: UserRole) -> List[int]:
        """Получение пользователей по роли"""
        return [tid for tid, r in self._roles_cache.items() if r == role]

class UserManager:
    """Менеджер пользователей"""
    
    def __init__(self):
        self.logger = logging.getLogger("user_manager")
        self._users_cache = {}  # Кеш пользователей
    
    async def get_or_create_user(self, telegram_id: int, name: str, username: Optional[str], role: UserRole) -> User:
        """Получение или создание пользователя"""
        # Проверяем кеш
        if telegram_id in self._users_cache:
            user = self._users_cache[telegram_id]
            # Обновляем данные при необходимости
            if user.name != name or user.username != username:
                user.name = name
                user.username = username
                user.updated_at = datetime.now()
            return user
        
        # Создаем нового пользователя
        user = User(
            id=len(self._users_cache) + 1,
            telegram_id=telegram_id,
            name=name,
            username=username,
            role=role
        )
        
        # Сохраняем в кеш
        self._users_cache[telegram_id] = user
        
        self.logger.info(f"Created user: {name} ({role.value})")
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        for user in self._users_cache.values():
            if user.id == user_id:
                return user
        return None
    
    async def update_user(self, user_id: int, **kwargs) -> bool:
        """Обновление данных пользователя"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        return True
    
    async def get_active_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Получение активных пользователей"""
        users = [user for user in self._users_cache.values() if user.is_active]
        
        if role:
            users = [user for user in users if user.role == role]
        
        return users

class OrderManager:
    """Менеджер заказов"""
    
    def __init__(self):
        self.logger = logging.getLogger("order_manager")
        self._orders_cache = {}  # Кеш заказов
        self._order_counter = 0
    
    async def create_order(self, client_id: int, text: str, voice_url: Optional[str] = None, 
                          photo_url: Optional[str] = None, items: List[Dict] = None, 
                          priority: OrderPriority = OrderPriority.NORMAL) -> Order:
        """Создание заказа"""
        self._order_counter += 1
        
        # Рассчитываем сумму
        amount = 0.0
        if items:
            for item in items:
                amount += item.get('price', 0) * item.get('quantity', 1)
        
        order = Order(
            id=self._order_counter,
            client_id=client_id,
            text=text,
            voice_url=voice_url,
            photo_url=photo_url,
            status=OrderStatus.CREATED,
            priority=priority,
            amount=amount,
            items=items or []
        )
        
        # Сохраняем в кеш
        self._orders_cache[order.id] = order
        
        self.logger.info(f"Created order #{order.id} for client {client_id}")
        return order
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Получение заказа по ID"""
        return self._orders_cache.get(order_id)
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus, changed_by: int, notes: Optional[str] = None) -> bool:
        """Обновление статуса заказа"""
        order = await self.get_order(order_id)
        if not order:
            return False
        
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.now()
        
        # Здесь должна быть логика сохранения истории статусов
        self.logger.info(f"Order #{order_id} status changed: {old_status.value} -> {new_status.value} by {changed_by}")
        
        return True
    
    async def assign_order(self, order_id: int, role: UserRole, assignee_id: int) -> bool:
        """Назначение исполнителя заказа"""
        order = await self.get_order(order_id)
        if not order:
            return False
        
        if role == UserRole.OPERATOR:
            order.assigned_operator = assignee_id
        elif role == UserRole.PICKER:
            order.assigned_picker = assignee_id
        elif role == UserRole.CHECKER:
            order.assigned_checker = assignee_id
        elif role == UserRole.COURIER:
            order.assigned_courier = assignee_id
        
        order.updated_at = datetime.now()
        
        self.logger.info(f"Order #{order_id} assigned to {role.value} {assignee_id}")
        return True
    
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Получение заказов по статусу"""
        return [order for order in self._orders_cache.values() if order.status == status]
    
    async def get_orders_by_client(self, client_id: int) -> List[Order]:
        """Получение заказов клиента"""
        return [order for order in self._orders_cache.values() if order.client_id == client_id]
    
    async def get_orders_by_assignee(self, assignee_id: int, role: UserRole) -> List[Order]:
        """Получение заказов исполнителя"""
        orders = []
        
        for order in self._orders_cache.values():
            if role == UserRole.OPERATOR and order.assigned_operator == assignee_id:
                orders.append(order)
            elif role == UserRole.PICKER and order.assigned_picker == assignee_id:
                orders.append(order)
            elif role == UserRole.CHECKER and order.assigned_checker == assignee_id:
                orders.append(order)
            elif role == UserRole.COURIER and order.assigned_courier == assignee_id:
                orders.append(order)
        
        return orders
    
    async def get_orders_by_priority(self, priority: OrderPriority) -> List[Order]:
        """Получение заказов по приоритету"""
        return [order for order in self._orders_cache.values() if order.priority == priority]
    
    async def get_orders_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики заказов"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_orders = [
            order for order in self._orders_cache.values()
            if order.created_at > cutoff_date
        ]
        
        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = len([
                order for order in recent_orders if order.status == status
            ])
        
        total_amount = sum(order.amount for order in recent_orders)
        delivered_orders = [order for order in recent_orders if order.status == OrderStatus.DELIVERED]
        
        return {
            'total_orders': len(recent_orders),
            'delivered_orders': len(delivered_orders),
            'conversion_rate': (len(delivered_orders) / len(recent_orders) * 100) if recent_orders else 0,
            'total_amount': total_amount,
            'average_amount': total_amount / len(recent_orders) if recent_orders else 0,
            'status_counts': status_counts
        }

class StatusManager:
    """Менеджер статусов"""
    
    def __init__(self):
        self.logger = logging.getLogger("status_manager")
        
        # Права доступа к статусам
        self.status_permissions = {
            OrderStatus.CREATED: [UserRole.CLIENT],
            OrderStatus.WAITING_PAYMENT: [UserRole.CLIENT],
            OrderStatus.REJECTED: [UserRole.OPERATOR],
            OrderStatus.ACCEPTED: [UserRole.OPERATOR],
            OrderStatus.PROCESSING: [UserRole.PICKER],
            OrderStatus.READY: [UserRole.PICKER],
            OrderStatus.CHECKING: [UserRole.CHECKER],
            OrderStatus.WAITING_COURIER: [UserRole.CHECKER],
            OrderStatus.ON_WAY: [UserRole.COURIER],
            OrderStatus.DELIVERED: [UserRole.COURIER],
            OrderStatus.CANCELLED: [UserRole.CLIENT, UserRole.OPERATOR]
        }
        
        # Возможные переходы статусов
        self.status_transitions = {
            OrderStatus.CREATED: [OrderStatus.WAITING_PAYMENT, OrderStatus.CANCELLED],
            OrderStatus.WAITING_PAYMENT: [OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.CHECKING, OrderStatus.CANCELLED],
            OrderStatus.CHECKING: [OrderStatus.WAITING_COURIER, OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.WAITING_COURIER: [OrderStatus.ON_WAY, OrderStatus.CANCELLED],
            OrderStatus.ON_WAY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],
            OrderStatus.REJECTED: [],
            OrderStatus.CANCELLED: []
        }
    
    async def can_change_status(self, user_role: UserRole, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Проверка прав на изменение статуса"""
        # Проверяем права доступа
        if user_role not in self.status_permissions.get(new_status, []):
            return False
        
        # Проверяем возможные переходы
        allowed_transitions = self.status_transitions.get(current_status, [])
        if new_status not in allowed_transitions:
            return False
        
        return True
    
    async def get_next_statuses(self, current_status: OrderStatus, user_role: UserRole) -> List[OrderStatus]:
        """Получение следующих возможных статусов"""
        allowed_transitions = self.status_transitions.get(current_status, [])
        
        # Фильтруем по правам доступа
        next_statuses = []
        for status in allowed_transitions:
            if user_role in self.status_permissions.get(status, []):
                next_statuses.append(status)
        
        return next_statuses
    
    async def get_status_history(self, order_id: int) -> List[StatusHistory]:
        """Получение истории статусов заказа"""
        # Здесь должна быть логика получения истории из БД
        # Для примера возвращаем пустой список
        return []

# 🏢 CRM Core Factory
class CRMCore:
    """Фабрика CRM Core"""
    
    def __init__(self):
        self.logger = logging.getLogger("crm_core")
        self.role_manager = RoleManager()
        self.user_manager = UserManager()
        self.order_manager = OrderManager()
        self.status_manager = StatusManager()
    
    async def initialize(self):
        """Инициализация CRM Core"""
        self.logger.info("🏢 CRM Core initializing...")
        
        # Здесь должна быть инициализация подключения к БД
        # Загрузка данных и т.д.
        
        self.logger.info("✅ CRM Core initialized successfully")
    
    async def shutdown(self):
        """Завершение работы CRM Core"""
        self.logger.info("🏢 CRM Core shutting down...")
        
        # Здесь должна быть очистка ресурсов
        
        self.logger.info("✅ CRM Core shutdown complete")

# 🎯 Enterprise функции
async def create_crm_core() -> CRMCore:
    """Создание CRM Core"""
    crm = CRMCore()
    await crm.initialize()
    return crm
