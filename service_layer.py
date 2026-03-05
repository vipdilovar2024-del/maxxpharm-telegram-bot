#!/usr/bin/env python3
"""
🔧 Service Layer - Бизнес-логика Enterprise системы
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Импортируем CRM Core
from crm_core import Order, OrderStatus, OrderPriority, UserRole, Payment
from crm_core import RoleManager, UserManager, OrderManager, StatusManager

# 🎯 Статусы платежей
class PaymentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    REFUNDED = "refunded"

# 🚚 Статусы доставки
class DeliveryStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    FAILED = "failed"

# 📊 Модели сервисов
@dataclass
class PaymentConfirmation:
    """Модель подтверждения платежа"""
    payment_id: int
    order_id: int
    amount: float
    confirmed_by: int
    confirmation_method: str  # photo, voice, text
    confirmation_data: str
    confirmed_at: datetime

@dataclass
class DeliveryAssignment:
    """Модель назначения доставки"""
    delivery_id: int
    order_id: int
    courier_id: int
    assigned_by: int
    assigned_at: datetime
    estimated_delivery: datetime
    delivery_address: str
    contact_phone: str

@dataclass
class NotificationMessage:
    """Модель уведомления"""
    id: str
    recipient_id: int
    recipient_type: str  # user, role, all
    message_type: str  # order_status, payment, delivery, system
    title: str
    body: str
    data: Dict[str, Any]
    created_at: datetime
    sent_at: Optional[datetime]
    delivery_status: str

class OrderService:
    """Сервис управления заказами"""
    
    def __init__(self, order_manager: OrderManager, status_manager: StatusManager):
        self.order_manager = order_manager
        self.status_manager = status_manager
        self.logger = logging.getLogger("order_service")
    
    async def create_order(self, client_id: int, order_data: Dict[str, Any]) -> Order:
        """Создание заказа с бизнес-логикой"""
        
        # Валидация данных
        if not order_data.get('text'):
            raise ValueError("Order text is required")
        
        # Определение приоритета
        priority = OrderPriority.NORMAL
        if order_data.get('urgent', False):
            priority = OrderPriority.HIGH
        
        # Создание заказа
        order = await self.order_manager.create_order(
            client_id=client_id,
            text=order_data['text'],
            voice_url=order_data.get('voice_url'),
            photo_url=order_data.get('photo_url'),
            items=order_data.get('items', []),
            priority=priority
        )
        
        # Бизнес-логика: автоматическое назначение оператора
        await self._auto_assign_operator(order)
        
        self.logger.info(f"Order #{order.id} created with business logic")
        return order
    
    async def _auto_assign_operator(self, order: Order):
        """Автоматическое назначение оператора"""
        # Здесь должна быть логика выбора свободного оператора
        # Для примера используем первого доступного
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        operators = await role_manager.get_users_by_role(UserRole.OPERATOR)
        if operators:
            await self.order_manager.assign_order(order.id, UserRole.OPERATOR, operators[0])
            self.logger.info(f"Auto-assigned operator {operators[0]} to order #{order.id}")
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus, changed_by: int, notes: Optional[str] = None) -> bool:
        """Обновление статуса с бизнес-логикой"""
        
        order = await self.order_manager.get_order(order_id)
        if not order:
            return False
        
        # Проверка прав
        user_role = await self._get_user_role(changed_by)
        if not await self.status_manager.can_change_status(user_role, order.status, new_status):
            self.logger.warning(f"User {changed_by} cannot change order #{order_id} status to {new_status.value}")
            return False
        
        # Обновление статуса
        success = await self.order_manager.update_order_status(order_id, new_status, changed_by, notes)
        
        if success:
            # Бизнес-логика: автоматические действия при смене статуса
            await self._handle_status_change(order, new_status, changed_by)
        
        return success
    
    async def _handle_status_change(self, order: Order, new_status: OrderStatus, changed_by: int):
        """Обработка бизнес-логики при смене статуса"""
        
        if new_status == OrderStatus.ACCEPTED:
            # Автоматическое назначение сборщика
            await self._auto_assign_picker(order)
        
        elif new_status == OrderStatus.READY:
            # Автоматическое назначение проверщика
            await self._auto_assign_checker(order)
        
        elif new_status == OrderStatus.WAITING_COURIER:
            # Автоматическое назначение курьера
            await self._auto_assign_courier(order)
        
        elif new_status == OrderStatus.DELIVERED:
            # Расчет бонусов и статистики
            await self._calculate_order_completion(order)
    
    async def _auto_assign_picker(self, order: Order):
        """Автоматическое назначение сборщика"""
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        pickers = await role_manager.get_users_by_role(UserRole.PICKER)
        if pickers:
            await self.order_manager.assign_order(order.id, UserRole.PICKER, pickers[0])
            self.logger.info(f"Auto-assigned picker {pickers[0]} to order #{order.id}")
    
    async def _auto_assign_checker(self, order: Order):
        """Автоматическое назначение проверщика"""
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        checkers = await role_manager.get_users_by_role(UserRole.CHECKER)
        if checkers:
            await self.order_manager.assign_order(order.id, UserRole.CHECKER, checkers[0])
            self.logger.info(f"Auto-assigned checker {checkers[0]} to order #{order.id}")
    
    async def _auto_assign_courier(self, order: Order):
        """Автоматическое назначение курьера"""
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        couriers = await role_manager.get_users_by_role(UserRole.COURIER)
        if couriers:
            await self.order_manager.assign_order(order.id, UserRole.COURIER, couriers[0])
            self.logger.info(f"Auto-assigned courier {couriers[0]} to order #{order.id}")
    
    async def _calculate_order_completion(self, order: Order):
        """Расчет завершения заказа"""
        # Здесь должна быть логика расчета бонусов, статистики и т.д.
        self.logger.info(f"Order #{order.id} completed. Calculating bonuses...")
    
    async def _get_user_role(self, user_id: int) -> UserRole:
        """Получение роли пользователя"""
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        return await role_manager.get_user_role(user_id)
    
    async def get_orders_for_user(self, user_id: int, user_role: UserRole) -> List[Order]:
        """Получение заказов для пользователя"""
        if user_role == UserRole.CLIENT:
            return await self.order_manager.get_orders_by_client(user_id)
        else:
            return await self.order_manager.get_orders_by_assignee(user_id, user_role)
    
    async def get_order_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики заказов"""
        return await self.order_manager.get_orders_statistics(days)

class PaymentService:
    """Сервис управления платежами"""
    
    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager
        self.logger = logging.getLogger("payment_service")
        self._payments_cache = {}
        self._payment_counter = 0
    
    async def create_payment(self, order_id: int, amount: float, method: str = "cash") -> Payment:
        """Создание платежа"""
        self._payment_counter += 1
        
        payment = Payment(
            id=self._payment_counter,
            order_id=order_id,
            amount=amount,
            method=method,
            confirmed=False
        )
        
        self._payments_cache[payment.id] = payment
        
        self.logger.info(f"Payment #{payment.id} created for order #{order_id}")
        return payment
    
    async def confirm_payment(self, payment_id: int, confirmed_by: int, confirmation_method: str, confirmation_data: str) -> bool:
        """Подтверждение платежа"""
        
        payment = self._payments_cache.get(payment_id)
        if not payment:
            return False
        
        if payment.confirmed:
            self.logger.warning(f"Payment #{payment_id} already confirmed")
            return False
        
        # Подтверждаем платеж
        payment.confirmed = True
        payment.confirmed_by = confirmed_by
        payment.confirmed_at = datetime.now()
        
        # Обновляем статус заказа
        await self.order_manager.update_order_status(payment.order_id, OrderStatus.ACCEPTED, confirmed_by)
        
        self.logger.info(f"Payment #{payment_id} confirmed by {confirmed_by}")
        return True
    
    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Получение платежа"""
        return self._payments_cache.get(payment_id)
    
    async def get_payments_by_order(self, order_id: int) -> List[Payment]:
        """Получение платежей заказа"""
        return [payment for payment in self._payments_cache.values() if payment.order_id == order_id]
    
    async def get_payment_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики платежей"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_payments = [
            payment for payment in self._payments_cache.values()
            if payment.created_at > cutoff_date
        ]
        
        confirmed_payments = [p for p in recent_payments if p.confirmed]
        total_amount = sum(p.amount for p in confirmed_payments)
        
        return {
            'total_payments': len(recent_payments),
            'confirmed_payments': len(confirmed_payments),
            'confirmation_rate': (len(confirmed_payments) / len(recent_payments) * 100) if recent_payments else 0,
            'total_amount': total_amount,
            'average_amount': total_amount / len(confirmed_payments) if confirmed_payments else 0
        }

class DeliveryService:
    """Сервис управления доставкой"""
    
    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager
        self.logger = logging.getLogger("delivery_service")
        self._deliveries_cache = {}
        self._delivery_counter = 0
    
    async def create_delivery_assignment(self, order_id: int, courier_id: int, delivery_address: str, contact_phone: str, assigned_by: int) -> DeliveryAssignment:
        """Создание назначения доставки"""
        self._delivery_counter += 1
        
        delivery = DeliveryAssignment(
            delivery_id=self._delivery_counter,
            order_id=order_id,
            courier_id=courier_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(),
            estimated_delivery=datetime.now() + timedelta(hours=2),
            delivery_address=delivery_address,
            contact_phone=contact_phone
        )
        
        self._deliveries_cache[delivery.delivery_id] = delivery
        
        # Обновляем статус заказа
        await self.order_manager.update_order_status(order_id, OrderStatus.ON_WAY, assigned_by)
        
        self.logger.info(f"Delivery #{delivery.delivery_id} assigned to courier {courier_id}")
        return delivery
    
    async def complete_delivery(self, delivery_id: int, completed_by: int) -> bool:
        """Завершение доставки"""
        
        delivery = self._deliveries_cache.get(delivery_id)
        if not delivery:
            return False
        
        # Обновляем статус заказа
        await self.order_manager.update_order_status(delivery.order_id, OrderStatus.DELIVERED, completed_by)
        
        self.logger.info(f"Delivery #{delivery_id} completed by {completed_by}")
        return True
    
    async def get_delivery(self, delivery_id: int) -> Optional[DeliveryAssignment]:
        """Получение доставки"""
        return self._deliveries_cache.get(delivery_id)
    
    async def get_deliveries_by_courier(self, courier_id: int) -> List[DeliveryAssignment]:
        """Получение доставок курьера"""
        return [delivery for delivery in self._deliveries_cache.values() if delivery.courier_id == courier_id]
    
    async def get_delivery_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики доставок"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_deliveries = [
            delivery for delivery in self._deliveries_cache.values()
            if delivery.assigned_at > cutoff_date
        ]
        
        # Получаем соответствующие заказы
        delivered_orders = []
        for delivery in recent_deliveries:
            order = await self.order_manager.get_order(delivery.order_id)
            if order and order.status == OrderStatus.DELIVERED:
                delivered_orders.append(order)
        
        total_amount = sum(order.amount for order in delivered_orders)
        
        return {
            'total_deliveries': len(recent_deliveries),
            'completed_deliveries': len(delivered_orders),
            'completion_rate': (len(delivered_orders) / len(recent_deliveries) * 100) if recent_deliveries else 0,
            'total_amount': total_amount,
            'average_amount': total_amount / len(delivered_orders) if delivered_orders else 0
        }

class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("notification_service")
        self._notifications_cache = {}
        self._notification_counter = 0
    
    async def send_notification(self, recipient_id: int, message_type: str, title: str, body: str, data: Dict[str, Any] = None) -> str:
        """Отправка уведомления"""
        
        notification_id = str(uuid4())
        notification = NotificationMessage(
            id=notification_id,
            recipient_id=recipient_id,
            recipient_type="user",
            message_type=message_type,
            title=title,
            body=body,
            data=data or {},
            created_at=datetime.now(),
            sent_at=None,
            delivery_status="pending"
        )
        
        try:
            # Отправляем сообщение
            await self.bot.send_message(recipient_id, f"📢 <b>{title}</b>\n\n{body}")
            
            notification.sent_at = datetime.now()
            notification.delivery_status = "delivered"
            
            self._notifications_cache[notification_id] = notification
            
            self.logger.info(f"Notification {notification_id} sent to {recipient_id}")
            return notification_id
            
        except Exception as e:
            notification.delivery_status = "failed"
            self._notifications_cache[notification_id] = notification
            self.logger.error(f"Failed to send notification {notification_id}: {e}")
            return notification_id
    
    async def send_role_notification(self, role: UserRole, message_type: str, title: str, body: str, data: Dict[str, Any] = None) -> List[str]:
        """Отправка уведомления всем пользователям роли"""
        
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        user_ids = await role_manager.get_users_by_role(role)
        notification_ids = []
        
        for user_id in user_ids:
            notification_id = await self.send_notification(user_id, message_type, title, body, data)
            notification_ids.append(notification_id)
        
        return notification_ids
    
    async def send_order_status_notification(self, order_id: int, status: OrderStatus, changed_by: int):
        """Отправка уведомления об изменении статуса заказа"""
        
        order = await self._get_order(order_id)
        if not order:
            return
        
        status_emoji = {
            OrderStatus.CREATED: "📝",
            OrderStatus.WAITING_PAYMENT: "💳",
            OrderStatus.ACCEPTED: "✅",
            OrderStatus.PROCESSING: "🔄",
            OrderStatus.READY: "📦",
            OrderStatus.CHECKING: "🔍",
            OrderStatus.ON_WAY: "🚚",
            OrderStatus.DELIVERED: "✅",
            OrderStatus.REJECTED: "❌",
            OrderStatus.CANCELLED: "❌"
        }
        
        emoji = status_emoji.get(status, "📋")
        
        # Уведомление клиенту
        await self.send_notification(
            recipient_id=order.client_id,
            message_type="order_status",
            title=f"{emoji} Статус заказа",
            body=f"Ваш заказ #{order.id} теперь: {status.value.title()}",
            data={"order_id": order.id, "status": status.value}
        )
        
        # Уведомление исполнителям
        if status == OrderStatus.ACCEPTED:
            await self.send_role_notification(
                role=UserRole.PICKER,
                message_type="new_order",
                title="📦 Новый заказ",
                body=f"Заказ #{order.id} готов к сборке",
                data={"order_id": order.id}
            )
        
        elif status == OrderStatus.READY:
            await self.send_role_notification(
                role=UserRole.CHECKER,
                message_type="order_ready",
                title="🔍 Заказ на проверку",
                body=f"Заказ #{order.id} готов к проверке",
                data={"order_id": order.id}
            )
        
        elif status == OrderStatus.WAITING_COURIER:
            await self.send_role_notification(
                role=UserRole.COURIER,
                message_type="order_ready_delivery",
                title="🚚 Заказ к доставке",
                body=f"Заказ #{order.id} готов к доставке",
                data={"order_id": order.id}
            )
    
    async def _get_order(self, order_id: int):
        """Получение заказа (заглушка)"""
        # Здесь должна быть реальная логика получения заказа
        return None

class AssignmentService:
    """Сервис распределения задач"""
    
    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager
        self.logger = logging.getLogger("assignment_service")
        self._worker_load = {}  # Нагрузка работников
    
    async def auto_assign_order(self, order_id: int, role: UserRole) -> Optional[int]:
        """Автоматическое назначение заказа"""
        
        # Получаем работников роли
        from bot_gateway import RoleManager
        role_manager = RoleManager()
        
        worker_ids = await role_manager.get_users_by_role(role)
        if not worker_ids:
            return None
        
        # Выбираем работника с наименьшей нагрузкой
        best_worker = min(worker_ids, key=lambda wid: self._worker_load.get(wid, 0))
        
        # Назначаем заказ
        success = await self.order_manager.assign_order(order_id, role, best_worker)
        
        if success:
            # Увеличиваем нагрузку
            self._worker_load[best_worker] = self._worker_load.get(best_worker, 0) + 1
            
            self.logger.info(f"Auto-assigned order #{order_id} to {role.value} {best_worker}")
            return best_worker
        
        return None
    
    async def release_worker_load(self, worker_id: int, role: UserRole):
        """Освобождение нагрузки работника"""
        current_load = self._worker_load.get(worker_id, 0)
        if current_load > 0:
            self._worker_load[worker_id] = current_load - 1
    
    async def get_worker_statistics(self) -> Dict[str, Any]:
        """Получение статистики работников"""
        return {
            'worker_load': self._worker_load.copy(),
            'total_workers': len(self._worker_load),
            'average_load': sum(self._worker_load.values()) / len(self._worker_load) if self._worker_load else 0
        }

# 🎯 Service Factory
class ServiceFactory:
    """Фабрика сервисов"""
    
    def __init__(self, crm_core, bot):
        self.crm_core = crm_core
        self.bot = bot
        self.logger = logging.getLogger("service_factory")
    
    async def create_services(self):
        """Создание всех сервисов"""
        self.order_service = OrderService(self.crm_core.order_manager, self.crm_core.status_manager)
        self.payment_service = PaymentService(self.crm_core.order_manager)
        self.delivery_service = DeliveryService(self.crm_core.order_manager)
        self.notification_service = NotificationService(self.bot)
        self.assignment_service = AssignmentService(self.crm_core.order_manager)
        
        self.logger.info("✅ All services created successfully")
        
        return {
            'order_service': self.order_service,
            'payment_service': self.payment_service,
            'delivery_service': self.delivery_service,
            'notification_service': self.notification_service,
            'assignment_service': self.assignment_service
        }

# 🎯 Enterprise функции
async def create_service_layer(crm_core, bot) -> Dict[str, Any]:
    """Создание слоя сервисов"""
    factory = ServiceFactory(crm_core, bot)
    return await factory.create_services()
