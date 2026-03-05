"""
🏗️ Database Models - Модели данных для CRM
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

class OrderStatus(Enum):
    """Статусы заказа"""
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

class UserRole(Enum):
    """Роли пользователей"""
    CLIENT = "client"
    OPERATOR = "operator"
    PICKER = "picker"
    CHECKER = "checker"
    COURIER = "courier"
    ADMIN = "admin"
    DIRECTOR = "director"

@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    operator_id: Optional[int]
    picker_id: Optional[int]
    checker_id: Optional[int]
    courier_id: Optional[int]
    comment: str
    amount: float
    status: OrderStatus
    message_type: str
    photo_file_id: Optional[str]
    voice_file_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int]
    rejection_reason: Optional[str] = None
    payment_confirmed_at: Optional[datetime] = None
    payment_confirmed_by: Optional[int] = None

@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: int
    name: str
    phone: Optional[str]
    address: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_order_id: Optional[int] = None
    active_orders_count: int = 0

@dataclass
class OrderItem:
    """Модель товара в заказе"""
    id: int
    order_id: int
    product: str
    quantity: int
    price: float
    created_at: datetime

@dataclass
class OrderStatusHistory:
    """Модель истории статусов заказа"""
    id: int
    order_id: int
    old_status: Optional[str]
    new_status: str
    changed_by: int
    changed_by_name: str
    changed_at: datetime
    comment: Optional[str] = None

@dataclass
class Notification:
    """Модель уведомления"""
    id: int
    user_id: int
    order_id: Optional[int]
    type: str
    message: str
    is_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime
