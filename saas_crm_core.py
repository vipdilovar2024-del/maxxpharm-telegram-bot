#!/usr/bin/env python3
"""
🚀 MAXXPHARM SaaS CRM - Архитектура уровня Uber/Amazon/Glovo
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json

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

# 📦 Модель заказа
@dataclass
class Order:
    id: int
    client_id: int
    text: str
    voice: Optional[str]
    photo: Optional[str]
    status: OrderStatus
    amount: float
    created_at: datetime
    items: List[Dict]
    assigned_picker: Optional[int] = None
    assigned_checker: Optional[int] = None
    assigned_courier: Optional[int] = None

# 👤 Модель пользователя
@dataclass
class User:
    id: int
    telegram_id: int
    name: str
    phone: str
    role: UserRole
    created_at: datetime
    is_active: bool = True

# 💳 Модель платежа
@dataclass
class Payment:
    id: int
    order_id: int
    photo: Optional[str]
    voice: Optional[str]
    confirmed: bool
    confirmed_by: Optional[int]
    created_at: datetime

# 📊 Модель лога
@dataclass
class ActivityLog:
    id: int
    user_id: int
    action: str
    order_id: Optional[int]
    details: Dict
    created_at: datetime

class SaaSCRMCore:
    """Ядро SaaS CRM системы"""
    
    def __init__(self):
        self.logger = logging.getLogger("saas_crm")
        self.users: Dict[int, User] = {}
        self.orders: Dict[int, Order] = {}
        self.payments: Dict[int, Payment] = {}
        self.logs: List[ActivityLog] = []
        self.order_counter = 0
        self.payment_counter = 0
        self.log_counter = 0
        
        # 🎭 Права доступа к статусам
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
            OrderStatus.DELIVERED: [UserRole.COURIER]
        }
    
    def create_user(self, telegram_id: int, name: str, phone: str, role: UserRole) -> User:
        """Создание пользователя"""
        user = User(
            id=len(self.users) + 1,
            telegram_id=telegram_id,
            name=name,
            phone=phone,
            role=role,
            created_at=datetime.now()
        )
        self.users[user.id] = user
        self.log_activity(user.id, "user_created", None, {"role": role.value})
        return user
    
    def create_order(self, client_id: int, text: str, voice: Optional[str] = None, 
                    photo: Optional[str] = None, items: List[Dict] = None) -> Order:
        """Создание заказа"""
        self.order_counter += 1
        
        order = Order(
            id=self.order_counter,
            client_id=client_id,
            text=text,
            voice=voice,
            photo=photo,
            status=OrderStatus.CREATED,
            amount=0.0,  # Будет рассчитано позже
            created_at=datetime.now(),
            items=items or []
        )
        
        # Рассчитываем сумму
        order.amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in order.items)
        
        self.orders[order.id] = order
        self.log_activity(client_id, "order_created", order.id, {"amount": order.amount})
        
        return order
    
    def can_change_status(self, user_role: UserRole, status: OrderStatus) -> bool:
        """Проверка прав на изменение статуса"""
        return user_role in self.status_permissions.get(status, [])
    
    def change_order_status(self, order_id: int, new_status: OrderStatus, 
                          user_id: int, details: Dict = None) -> bool:
        """Изменение статуса заказа"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        user = self.users.get(user_id)
        
        if not user or not self.can_change_status(user.role, new_status):
            return False
        
        old_status = order.status
        order.status = new_status
        
        # Автоматическое назначение исполнителей
        if new_status == OrderStatus.ACCEPTED:
            order.assigned_picker = self.get_free_picker()
        elif new_status == OrderStatus.CHECKING:
            order.assigned_checker = self.get_free_checker()
        elif new_status == OrderStatus.ON_WAY:
            order.assigned_courier = self.get_free_courier()
        
        self.log_activity(user_id, "status_changed", order_id, {
            "old_status": old_status.value,
            "new_status": new_status.value,
            "details": details or {}
        })
        
        return True
    
    def create_payment(self, order_id: int, photo: Optional[str] = None, 
                      voice: Optional[str] = None) -> Payment:
        """Создание платежа"""
        self.payment_counter += 1
        
        payment = Payment(
            id=self.payment_counter,
            order_id=order_id,
            photo=photo,
            voice=voice,
            confirmed=False,
            confirmed_by=None,
            created_at=datetime.now()
        )
        
        self.payments[payment.id] = payment
        self.log_activity(None, "payment_created", order_id, {"payment_id": payment.id})
        
        return payment
    
    def confirm_payment(self, payment_id: int, confirmed_by: int) -> bool:
        """Подтверждение платежа"""
        if payment_id not in self.payments:
            return False
        
        payment = self.payments[payment_id]
        payment.confirmed = True
        payment.confirmed_by = confirmed_by
        
        # Меняем статус заказа
        self.change_order_status(payment.order_id, OrderStatus.ACCEPTED, confirmed_by)
        
        self.log_activity(confirmed_by, "payment_confirmed", payment.order_id, {"payment_id": payment_id})
        
        return True
    
    def get_free_picker(self) -> Optional[int]:
        """Получение свободного сборщика"""
        pickers = [user for user in self.users.values() if user.role == UserRole.PICKER and user.is_active]
        return pickers[0].id if pickers else None
    
    def get_free_checker(self) -> Optional[int]:
        """Получение свободного проверщика"""
        checkers = [user for user in self.users.values() if user.role == UserRole.CHECKER and user.is_active]
        return checkers[0].id if checkers else None
    
    def get_free_courier(self) -> Optional[int]:
        """Получение свободного курьера"""
        couriers = [user for user in self.users.values() if user.role == UserRole.COURIER and user.is_active]
        return couriers[0].id if couriers else None
    
    def get_user_orders(self, user_id: int) -> List[Order]:
        """Получение заказов пользователя"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        if user.role == UserRole.CLIENT:
            return [order for order in self.orders.values() if order.client_id == user_id]
        elif user.role == UserRole.PICKER:
            return [order for order in self.orders.values() if order.assigned_picker == user_id]
        elif user.role == UserRole.CHECKER:
            return [order for order in self.orders.values() if order.assigned_checker == user_id]
        elif user.role == UserRole.COURIER:
            return [order for order in self.orders.values() if order.assigned_courier == user_id]
        elif user.role in [UserRole.OPERATOR, UserRole.ADMIN, UserRole.DIRECTOR]:
            return list(self.orders.values())
        
        return []
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Получение данных для дашборда"""
        today = datetime.now().date()
        today_orders = [order for order in self.orders.values() if order.created_at.date() == today]
        
        delivered_today = [order for order in today_orders if order.status == OrderStatus.DELIVERED]
        rejected_today = [order for order in today_orders if order.status == OrderStatus.REJECTED]
        
        total_revenue = sum(order.amount for order in delivered_today)
        
        # Статистика по статусам
        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = len([order for order in self.orders.values() if order.status == status])
        
        return {
            "today_orders": len(today_orders),
            "delivered_today": len(delivered_today),
            "rejected_today": len(rejected_today),
            "total_revenue": total_revenue,
            "status_counts": status_counts,
            "total_users": len(self.users),
            "active_orders": len([order for order in self.orders.values() if order.status not in [OrderStatus.DELIVERED, OrderStatus.REJECTED]])
        }
    
    def log_activity(self, user_id: Optional[int], action: str, order_id: Optional[int], details: Dict):
        """Логирование активности"""
        self.log_counter += 1
        
        log = ActivityLog(
            id=self.log_counter,
            user_id=user_id,
            action=action,
            order_id=order_id,
            details=details,
            created_at=datetime.now()
        )
        
        self.logs.append(log)
        self.logger.info(f"📊 Activity: {action} by user {user_id} for order {order_id}")
    
    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Получение аналитики"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_orders = [order for order in self.orders.values() if order.created_at > cutoff_date]
        
        # Конверсия
        delivered = len([order for order in recent_orders if order.status == OrderStatus.DELIVERED])
        conversion_rate = (delivered / len(recent_orders) * 100) if recent_orders else 0
        
        # Выручка
        total_revenue = sum(order.amount for order in recent_orders if order.status == OrderStatus.DELIVERED)
        
        # Среднее время обработки
        processing_times = []
        for order in recent_orders:
            if order.status == OrderStatus.DELIVERED:
                processing_time = (order.created_at - order.created_at).total_seconds() / 3600
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "period_days": days,
            "total_orders": len(recent_orders),
            "delivered_orders": delivered,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": total_revenue,
            "avg_processing_time": round(avg_processing_time, 2),
            "revenue_per_day": round(total_revenue / days, 2)
        }
