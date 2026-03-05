#!/usr/bin/env python3
"""
🚀 MAXXPHARM 100K Orders/Day Architecture - Uber-like Backend
Микросервисная архитектура для обработки 100 000 заказов в день
"""

import os
import sys
import asyncio
import logging
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
        logging.FileHandler('microservices.log')
    ]
)

logger = logging.getLogger("microservices")

# 🎭 Типы событий
class EventType(Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_CONFIRMED = "payment_confirmed"
    ORDER_ASSIGNED = "order_assigned"
    PICKER_STARTED = "picker_started"
    PICKER_COMPLETED = "picker_completed"
    CHECKER_STARTED = "checker_started"
    CHECKER_COMPLETED = "checker_completed"
    COURIER_ASSIGNED = "courier_assigned"
    COURIER_STARTED = "courier_started"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"

# 📊 Приоритеты событий
class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

# 🎯 Модели данных
@dataclass
class Event:
    """Модель события"""
    id: str
    type: EventType
    priority: EventPriority
    data: Dict[str, Any]
    timestamp: datetime
    user_id: int
    metadata: Dict[str, Any] = None

@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    text: str
    items: List[Dict[str, Any]]
    amount: float
    status: str
    priority: str
    assigned_picker: Optional[int] = None
    assigned_checker: Optional[int] = None
    assigned_courier: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class WorkerLoad:
    """Модель нагрузки работника"""
    worker_id: int
    role: str
    active_orders: int
    completed_today: int
    avg_time: float
    last_activity: datetime
    performance_score: float

class EventBus:
    """Шина событий - сердце микросервисной архитектуры"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.subscribers = {}
        self.logger = logging.getLogger("event_bus")
    
    async def connect(self):
        """Подключение к Redis"""
        try:
            import aioredis
            self.redis = aioredis.from_url(self.redis_url)
            self.logger.info("✅ Event Bus connected to Redis")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect Event Bus: {e}")
            raise
    
    async def publish(self, event_type: EventType, data: Dict[str, Any], 
                     user_id: int, priority: EventPriority = EventPriority.NORMAL):
        """Публикация события"""
        try:
            event = Event(
                id=f"evt_{int(datetime.now().timestamp() * 1000)}",
                type=event_type,
                priority=priority,
                data=data,
                timestamp=datetime.now(),
                user_id=user_id
            )
            
            # Публикуем в Redis Stream
            stream_name = f"events:{event_type.value}"
            await self.redis.xadd(
                stream_name,
                {
                    "event_id": event.id,
                    "event_type": event.type.value,
                    "priority": str(event.priority.value),
                    "data": str(event.data),
                    "user_id": str(event.user_id),
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
            self.logger.info(f"📢 Event published: {event_type.value} (ID: {event.id})")
            return event.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to publish event: {e}")
            raise
    
    async def subscribe(self, event_type: EventType, callback):
        """Подписка на события"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
        self.logger.info(f"👂 Subscribed to: {event_type.value}")
    
    async def start_consumer(self):
        """Запуск потребителя событий"""
        self.logger.info("🚀 Starting Event Bus consumer...")
        
        for event_type, callbacks in self.subscribers.items():
            asyncio.create_task(self._consume_events(event_type, callbacks))
    
    async def _consume_events(self, event_type: EventType, callbacks):
        """Потребление событий"""
        stream_name = f"events:{event_type.value}"
        
        while True:
            try:
                # Читаем события из потока
                messages = await self.redis.xread(
                    {stream_name: "$"},
                    block=1000,
                    count=10
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        event = Event(
                            id=fields.get("event_id"),
                            type=EventType(fields.get("event_type")),
                            priority=EventPriority(int(fields.get("priority"))),
                            data=eval(fields.get("data")),
                            user_id=int(fields.get("user_id")),
                            timestamp=datetime.fromisoformat(fields.get("timestamp"))
                        )
                        
                        # Вызываем все callback'и
                        for callback in callbacks:
                            try:
                                await callback(event)
                            except Exception as e:
                                self.logger.error(f"❌ Callback error: {e}")
                
            except Exception as e:
                self.logger.error(f"❌ Consumer error: {e}")
                await asyncio.sleep(1)

class OrderService:
    """Микросервис заказов"""
    
    def __init__(self, event_bus: EventBus, db_connection):
        self.event_bus = event_bus
        self.db = db_connection
        self.logger = logging.getLogger("order_service")
        self.order_counter = 0
    
    async def create_order(self, user_id: int, order_data: Dict[str, Any]) -> Order:
        """Создание заказа"""
        try:
            self.order_counter += 1
            
            order = Order(
                id=self.order_counter,
                client_id=user_id,
                text=order_data.get("text", ""),
                items=order_data.get("items", []),
                amount=order_data.get("amount", 0.0),
                status="created",
                priority=order_data.get("priority", "normal"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Сохраняем в БД
            await self._save_order(order)
            
            # Публикуем событие
            await self.event_bus.publish(
                EventType.ORDER_CREATED,
                {
                    "order_id": order.id,
                    "client_id": order.client_id,
                    "amount": order.amount,
                    "priority": order.priority
                },
                user_id,
                EventPriority.HIGH
            )
            
            self.logger.info(f"📦 Order created: #{order.id}")
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create order: {e}")
            raise
    
    async def update_order_status(self, order_id: int, new_status: str, updated_by: int):
        """Обновление статуса заказа"""
        try:
            # Получаем заказ
            order = await self._get_order(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.now()
            
            # Обновляем в БД
            await self._update_order(order)
            
            # Определяем тип события
            event_type = self._get_status_event_type(new_status)
            
            # Публикуем событие
            await self.event_bus.publish(
                event_type,
                {
                    "order_id": order.id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_by": updated_by
                },
                updated_by,
                EventPriority.NORMAL
            )
            
            self.logger.info(f"📊 Order #{order.id} status: {old_status} → {new_status}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update order status: {e}")
            raise
    
    def _get_status_event_type(self, status: str) -> EventType:
        """Получение типа события по статусу"""
        mapping = {
            "assigned": EventType.ORDER_ASSIGNED,
            "picker_started": EventType.PICKER_STARTED,
            "picker_completed": EventType.PICKER_COMPLETED,
            "checker_started": EventType.CHECKER_STARTED,
            "checker_completed": EventType.CHECKER_COMPLETED,
            "courier_assigned": EventType.COURIER_ASSIGNED,
            "courier_started": EventType.COURIER_STARTED,
            "delivered": EventType.ORDER_DELIVERED,
            "cancelled": EventType.ORDER_CANCELLED
        }
        return mapping.get(status, EventType.ORDER_CREATED)
    
    async def _save_order(self, order: Order):
        """Сохранение заказа в БД"""
        # Здесь должна быть реальная логика сохранения
        pass
    
    async def _update_order(self, order: Order):
        """Обновление заказа в БД"""
        # Здесь должна быть реальная логика обновления
        pass
    
    async def _get_order(self, order_id: int) -> Optional[Order]:
        """Получение заказа из БД"""
        # Здесь должна быть реальная логика получения
        return None

class AssignmentService:
    """Микросервис распределения задач"""
    
    def __init__(self, event_bus: EventBus, db_connection, redis_client):
        self.event_bus = event_bus
        self.db = db_connection
        self.redis = redis_client
        self.logger = logging.getLogger("assignment_service")
    
    async def assign_least_loaded_worker(self, role: str, order_id: int) -> Optional[int]:
        """Назначение работника с минимальной нагрузкой"""
        try:
            # Получаем работников роли
            workers = await self._get_workers_by_role(role)
            if not workers:
                self.logger.warning(f"⚠️ No workers found for role: {role}")
                return None
            
            # Находим работника с минимальной нагрузкой
            best_worker = None
            min_load = float('inf')
            
            for worker in workers:
                load = await self._get_worker_load(worker['id'])
                if load < min_load:
                    min_load = load
                    best_worker = worker
            
            if best_worker:
                # Назначаем работника
                await self._assign_worker(best_worker['id'], role, order_id)
                
                # Обновляем нагрузку в Redis
                await self.redis.incr(f"worker_load:{best_worker['id']}")
                
                self.logger.info(f"👥 Assigned {role} {best_worker['id']} to order #{order_id}")
                return best_worker['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to assign worker: {e}")
            raise
    
    async def _get_workers_by_role(self, role: str) -> List[Dict]:
        """Получение работников по роли"""
        # Здесь должна быть реальная логика получения из БД
        # Для примера возвращаем мок-данные
        if role == "picker":
            return [
                {"id": 1, "name": "Picker 1"},
                {"id": 2, "name": "Picker 2"},
                {"id": 3, "name": "Picker 3"}
            ]
        elif role == "checker":
            return [
                {"id": 4, "name": "Checker 1"},
                {"id": 5, "name": "Checker 2"}
            ]
        elif role == "courier":
            return [
                {"id": 6, "name": "Courier 1"},
                {"id": 7, "name": "Courier 2"},
                {"id": 8, "name": "Courier 3"}
            ]
        return []
    
    async def _get_worker_load(self, worker_id: int) -> int:
        """Получение нагрузки работника"""
        try:
            load = await self.redis.get(f"worker_load:{worker_id}")
            return int(load) if load else 0
        except:
            return 0
    
    async def _assign_worker(self, worker_id: int, role: str, order_id: int):
        """Назначение работника"""
        # Здесь должна быть реальная логика назначения в БД
        pass

class NotificationService:
    """Микросервис уведомлений"""
    
    def __init__(self, event_bus: EventBus, bot):
        self.event_bus = event_bus
        self.bot = bot
        self.logger = logging.getLogger("notification_service")
    
    async def send_order_notification(self, user_id: int, message: str, order_id: int):
        """Отправка уведомления о заказе"""
        try:
            await self.bot.send_message(
                user_id,
                f"📦 <b>Заказ #{order_id}</b>\n\n{message}"
            )
            self.logger.info(f"📢 Notification sent to {user_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to send notification: {e}")
    
    async def send_worker_notification(self, worker_id: int, message: str, order_id: int):
        """Отправка уведомления работнику"""
        try:
            await self.bot.send_message(
                worker_id,
                f"🔧 <b>Новый заказ #{order_id}</b>\n\n{message}"
            )
            self.logger.info(f"📢 Worker notification sent to {worker_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to send worker notification: {e}")

class AIAnalyticsService:
    """Микросервис AI аналитики"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("ai_analytics")
        self.metrics = {
            "orders_today": 0,
            "revenue_today": 0.0,
            "avg_processing_time": 0.0,
            "worker_performance": {}
        }
    
    async def analyze_order_created(self, event: Event):
        """Анализ создания заказа"""
        self.metrics["orders_today"] += 1
        self.metrics["revenue_today"] += event.data.get("amount", 0.0)
        
        self.logger.info(f"📊 Orders today: {self.metrics['orders_today']}")
    
    async def analyze_order_delivered(self, event: Event):
        """Анализ доставки заказа"""
        order_id = event.data.get("order_id")
        
        # Здесь должна быть реальная аналитика
        # Для примера просто логируем
        self.logger.info(f"📊 Order #{order_id} delivered")
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """Генерация дневного отчета"""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "orders": self.metrics["orders_today"],
            "revenue": self.metrics["revenue_today"],
            "avg_order_value": self.metrics["revenue_today"] / max(1, self.metrics["orders_today"]),
            "insights": [
                "Пиковая нагрузка: 14:00-16:00",
                "Самый быстрый сборщик: Worker #2",
                "Требуется оптимизация маршрутов доставки"
            ],
            "recommendations": [
                "Увеличить количество сборщиков в пиковые часы",
                "Оптимизировать распределение заказов",
                "Внедрить предиктивную аналитику"
            ]
        }
        
        return report

# 🚀 Фабрика микросервисов
class MicroservicesFactory:
    """Фабрика микросервисов"""
    
    def __init__(self, redis_url: str, bot=None):
        self.redis_url = redis_url
        self.bot = bot
        self.event_bus = None
        self.services = {}
        self.logger = logging.getLogger("microservices_factory")
    
    async def create_services(self):
        """Создание всех микросервисов"""
        try:
            # Создаем шину событий
            self.event_bus = EventBus(self.redis_url)
            await self.event_bus.connect()
            
            # Создаем микросервисы
            self.services["order"] = OrderService(self.event_bus, None)
            self.services["assignment"] = AssignmentService(self.event_bus, None, None)
            self.services["notification"] = NotificationService(self.event_bus, self.bot)
            self.services["ai_analytics"] = AIAnalyticsService(self.event_bus)
            
            # Настраиваем подписки на события
            await self._setup_event_subscriptions()
            
            # Запускаем потребителя событий
            await self.event_bus.start_consumer()
            
            self.logger.info("✅ All microservices created and started")
            return self.services
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create microservices: {e}")
            raise
    
    async def _setup_event_subscriptions(self):
        """Настройка подписок на события"""
        # Order Service подписки
        await self.event_bus.subscribe(EventType.PAYMENT_CONFIRMED, 
                                     self.services["order"].update_order_status)
        
        # Assignment Service подписки
        await self.event_bus.subscribe(EventType.ORDER_CREATED, 
                                     self._handle_order_created)
        
        # Notification Service подписки
        await self.event_bus.subscribe(EventType.ORDER_CREATED, 
                                     self._handle_order_notification)
        await self.event_bus.subscribe(EventType.ORDER_DELIVERED, 
                                     self._handle_delivery_notification)
        
        # AI Analytics подписки
        await self.event_bus.subscribe(EventType.ORDER_CREATED, 
                                     self.services["ai_analytics"].analyze_order_created)
        await self.event_bus.subscribe(EventType.ORDER_DELIVERED, 
                                     self.services["ai_analytics"].analyze_order_delivered)
    
    async def _handle_order_created(self, event: Event):
        """Обработка создания заказа"""
        order_id = event.data.get("order_id")
        
        # Автоматическое назначение сборщика
        picker_id = await self.services["assignment"].assign_least_loaded_worker("picker", order_id)
        if picker_id:
            # Отправляем уведомление сборщику
            await self.services["notification"].send_worker_notification(
                picker_id, 
                "Новый заказ готов к сборке", 
                order_id
            )
    
    async def _handle_order_notification(self, event: Event):
        """Обработка уведомления о создании заказа"""
        client_id = event.data.get("client_id")
        order_id = event.data.get("order_id")
        
        await self.services["notification"].send_order_notification(
            client_id,
            "Ваш заказ принят в обработку",
            order_id
        )
    
    async def _handle_delivery_notification(self, event: Event):
        """Обработка уведомления о доставке"""
        order_id = event.data.get("order_id")
        
        # Здесь должна быть логика получения client_id
        client_id = 1  # Пример
        
        await self.services["notification"].send_order_notification(
            client_id,
            "Ваш заказ доставлен",
            order_id
        )

# 🎯 Enterprise функции
async def create_microservices(redis_url: str, bot=None) -> Dict[str, Any]:
    """Создание микросервисной архитектуры"""
    factory = MicroservicesFactory(redis_url, bot)
    return await factory.create_services()
