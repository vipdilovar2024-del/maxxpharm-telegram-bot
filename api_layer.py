"""
🏗️ API Layer - API слой для Uber-архитектуры Telegram-CRM
Разделяет интерфейс от бизнес-логики
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from aiogram import Bot

logger = logging.getLogger("api_layer")

class APILayer:
    """API слой для разделения интерфейса от бизнес-логики"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = logging.getLogger("api_layer")
        
        # Импорты сервисов (отложенные для избежания циклических импортов)
        self._order_service = None
        self._notification_service = None
        self._assignment_service = None
        self._queue_service = None
    
    @property
    def order_service(self):
        """Ленивая загрузка order service"""
        if self._order_service is None:
            from services.order_service import OrderService
            self._order_service = OrderService()
        return self._order_service
    
    @property
    def notification_service(self):
        """Ленивая загрузка notification service"""
        if self._notification_service is None:
            from services.notification_service import NotificationService
            self._notification_service = NotificationService(self.bot)
        return self._notification_service
    
    @property
    def assignment_service(self):
        """Ленивая загрузка assignment service"""
        if self._assignment_service is None:
            from services.assignment_service import AssignmentService
            self._assignment_service = AssignmentService(self.bot)
        return self._assignment_service
    
    @property
    def queue_service(self):
        """Ленивая загрузка queue service"""
        if self._queue_service is None:
            from services.queue_service import QueueService
            self._queue_service = QueueService()
        return self._queue_service
    
    # 📦 Order API методы
    async def create_order(self, user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заказа через API"""
        try:
            # Создаем заказ
            order = await self.order_service.create_order(user_id, order_data)
            
            # Отправляем задачу в очередь
            await self.queue_service.enqueue_task(
                "process_new_order",
                {"order_id": order["id"]}
            )
            
            self.logger.info(f"📦 Order {order['id']} created and queued")
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Error creating order: {e}")
            raise
    
    async def get_order(self, order_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение заказа через API"""
        try:
            order = await self.order_service.get_order(order_id)
            
            # Проверяем права доступа
            if order and order["client_id"] == user_id:
                return order
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting order {order_id}: {e}")
            return None
    
    async def get_user_orders(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение заказов пользователя через API"""
        try:
            orders = await self.order_service.get_user_orders(user_id, limit)
            return orders
        except Exception as e:
            self.logger.error(f"❌ Error getting user orders: {e}")
            return []
    
    # 👨‍💻 Operator API методы
    async def get_new_orders(self, operator_id: int) -> List[Dict[str, Any]]:
        """Получение новых заказов для оператора"""
        try:
            orders = await self.order_service.get_orders_by_status("created", limit=50)
            return orders
        except Exception as e:
            self.logger.error(f"❌ Error getting new orders: {e}")
            return []
    
    async def accept_order(self, order_id: int, operator_id: int) -> bool:
        """Принятие заказа оператором"""
        try:
            # Обновляем статус
            success = await self.order_service.update_order_status(
                order_id, "accepted", operator_id
            )
            
            if success:
                # Отправляем задачу в очередь
                await self.queue_service.enqueue_task(
                    "process_accepted_order",
                    {"order_id": order_id, "operator_id": operator_id}
                )
                
                self.logger.info(f"✅ Order {order_id} accepted by operator {operator_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error accepting order {order_id}: {e}")
            return False
    
    async def reject_order(self, order_id: int, operator_id: int, reason: str = "") -> bool:
        """Отклонение заказа оператором"""
        try:
            success = await self.order_service.update_order_status(
                order_id, "cancelled", operator_id
            )
            
            if success:
                # Отправляем задачу в очередь
                await self.queue_service.enqueue_task(
                    "process_rejected_order",
                    {"order_id": order_id, "operator_id": operator_id, "reason": reason}
                )
                
                self.logger.info(f"❌ Order {order_id} rejected by operator {operator_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error rejecting order {order_id}: {e}")
            return False
    
    # 📦 Worker API методы
    async def get_worker_orders(self, worker_id: int, role: str) -> List[Dict[str, Any]]:
        """Получение заказов для работника"""
        try:
            orders = await self.order_service.get_worker_orders(worker_id, role)
            return orders
        except Exception as e:
            self.logger.error(f"❌ Error getting worker orders: {e}")
            return []
    
    async def update_order_status(self, order_id: int, new_status: str, worker_id: int) -> bool:
        """Обновление статуса заказа работником"""
        try:
            success = await self.order_service.update_order_status(
                order_id, new_status, worker_id
            )
            
            if success:
                # Отправляем задачу в очередь
                await self.queue_service.enqueue_task(
                    "process_status_update",
                    {"order_id": order_id, "new_status": new_status, "worker_id": worker_id}
                )
                
                self.logger.info(f"🔄 Order {order_id} status updated to {new_status} by {worker_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error updating order status {order_id}: {e}")
            return False
    
    # 📊 Analytics API методы
    async def get_dashboard_stats(self, user_id: int, role: str) -> Dict[str, Any]:
        """Получение статистики дашборда"""
        try:
            if role in ["admin", "director"]:
                stats = await self.order_service.get_comprehensive_stats()
                return stats
            else:
                stats = await self.order_service.get_worker_stats(user_id, role)
                return stats
        except Exception as e:
            self.logger.error(f"❌ Error getting dashboard stats: {e}")
            return {}
    
    async def get_performance_metrics(self, user_id: int, role: str) -> Dict[str, Any]:
        """Получение метрик производительности"""
        try:
            metrics = await self.order_service.get_performance_metrics(user_id, role)
            return metrics
        except Exception as e:
            self.logger.error(f"❌ Error getting performance metrics: {e}")
            return {}
    
    # 🔔 Notification API методы
    async def send_notification(self, user_id: int, message: str, order_id: Optional[int] = None):
        """Отправка уведомления через API"""
        try:
            await self.notification_service.send_notification(user_id, message, order_id)
        except Exception as e:
            self.logger.error(f"❌ Error sending notification to {user_id}: {e}")
    
    # 🧠 AI API методы
    async def get_ai_insights(self, user_id: int, role: str) -> Dict[str, Any]:
        """Получение AI инсайтов"""
        try:
            if role in ["admin", "director"]:
                from services.ai_service import AIService
                ai_service = AIService()
                insights = await ai_service.get_business_insights()
                return insights
            else:
                return {}
        except Exception as e:
            self.logger.error(f"❌ Error getting AI insights: {e}")
            return {}
    
    async def get_demand_forecast(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Получение прогноза спроса"""
        try:
            from services.ai_service import AIService
            ai_service = AIService()
            forecast = await ai_service.get_demand_forecast(hours_ahead)
            return forecast
        except Exception as e:
            self.logger.error(f"❌ Error getting demand forecast: {e}")
            return {}
    
    # 🏥 Health API методы
    async def get_system_health(self) -> Dict[str, Any]:
        """Получение здоровья системы"""
        try:
            from health_check_system import get_health_checker
            health_checker = get_health_checker(self.bot)
            health_report = await health_checker.comprehensive_health_check()
            return health_report
        except Exception as e:
            self.logger.error(f"❌ Error getting system health: {e}")
            return {}
    
    # 📊 Queue API методы
    async def get_queue_status(self) -> Dict[str, Any]:
        """Получение статуса очереди"""
        try:
            status = await self.queue_service.get_queue_status()
            return status
        except Exception as e:
            self.logger.error(f"❌ Error getting queue status: {e}")
            return {}
    
    async def enqueue_manual_task(self, task_name: str, task_data: Dict[str, Any]) -> bool:
        """Ручное добавление задачи в очередь"""
        try:
            success = await self.queue_service.enqueue_task(task_name, task_data)
            return success
        except Exception as e:
            self.logger.error(f"❌ Error enqueuing manual task: {e}")
            return False

# Глобальный экземпляр API слоя
api_layer: Optional[APILayer] = None

def get_api_layer(bot: Bot) -> APILayer:
    """Получение экземпляра API слоя"""
    global api_layer
    if api_layer is None:
        api_layer = APILayer(bot)
    return api_layer

# Удобные функции для использования в handlers
async def api_create_order(user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Создание заказа через API"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    api = get_api_layer(bot)
    return await api.create_order(user_id, order_data)

async def api_accept_order(order_id: int, operator_id: int) -> bool:
    """Принятие заказа через API"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    api = get_api_layer(bot)
    return await api.accept_order(order_id, operator_id)

async def api_get_user_orders(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Получение заказов пользователя через API"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    api = get_api_layer(bot)
    return await api.get_user_orders(user_id, limit)

async def api_update_order_status(order_id: int, new_status: str, worker_id: int) -> bool:
    """Обновление статуса заказа через API"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    api = get_api_layer(bot)
    return await api.update_order_status(order_id, new_status, worker_id)

async def api_get_dashboard_stats(user_id: int, role: str) -> Dict[str, Any]:
    """Получение статистики дашборда через API"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    api = get_api_layer(bot)
    return await api.get_dashboard_stats(user_id, role)
