"""
🏗️ Worker System - Система воркеров для обработки задач
Uber-архитектура: распределение нагрузки между серверами
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from services.queue_service import QueueService, Task, TaskStatus, get_queue_service

logger = logging.getLogger("worker_system")

class BaseWorker(ABC):
    """Базовый класс для всех воркеров"""
    
    def __init__(self, worker_id: str, queue_names: List[str]):
        self.worker_id = worker_id
        self.queue_names = queue_names
        self.queue_service: Optional[QueueService] = None
        self.running = False
        self.processed_tasks = 0
        self.failed_tasks = 0
        self.start_time = None
        self.logger = logging.getLogger(f"worker_{worker_id}")
    
    async def initialize(self):
        """Инициализация воркера"""
        self.queue_service = await get_queue_service()
        self.start_time = datetime.now()
        self.logger.info(f"🤖 Worker {self.worker_id} initialized")
    
    async def start(self):
        """Запуск воркера"""
        self.running = True
        self.logger.info(f"🚀 Worker {self.worker_id} starting...")
        
        try:
            while self.running:
                task_processed = False
                
                # Обрабатываем задачи из всех очередей
                for queue_name in self.queue_names:
                    if not self.running:
                        break
                    
                    task = await self.queue_service.dequeue_task(queue_name)
                    
                    if task:
                        await self._process_task(task)
                        task_processed = True
                        break
                
                # Если нет задач, ждем немного
                if not task_processed:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"❌ Worker {self.worker_id} error: {e}")
            raise
        finally:
            self.logger.info(f"🛑 Worker {self.worker_id} stopped")
    
    async def stop(self):
        """Остановка воркера"""
        self.running = False
        self.logger.info(f"🛑 Worker {self.worker_id} stopping...")
    
    async def _process_task(self, task: Task):
        """Обработка задачи"""
        try:
            self.logger.info(f"📋 Processing task {task.id}: {task.name}")
            
            # Вызываем конкретный обработчик
            result = await self.handle_task(task)
            
            # Завершаем задачу
            await self.queue_service.complete_task(task.id, result)
            self.processed_tasks += 1
            
            self.logger.info(f"✅ Task {task.id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Task {task.id} failed: {e}")
            
            # Завершаем задачу с ошибкой
            await self.queue_service.fail_task(task.id, str(e))
            self.failed_tasks += 1
    
    @abstractmethod
    async def handle_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Обработка конкретной задачи - должен быть реализован в наследниках"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики воркера"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "worker_id": self.worker_id,
            "processed_tasks": self.processed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.processed_tasks / max(1, self.processed_tasks + self.failed_tasks)) * 100,
            "uptime_seconds": uptime,
            "tasks_per_hour": (self.processed_tasks / max(1, uptime / 3600)),
            "running": self.running
        }

class OrderWorker(BaseWorker):
    """Воркер для обработки заказов"""
    
    def __init__(self, worker_id: str):
        super().__init__(worker_id, [
            "process_new_order",
            "process_accepted_order", 
            "process_status_update",
            "process_rejected_order"
        ])
    
    async def handle_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Обработка задач заказов"""
        
        if task.name == "process_new_order":
            return await self._process_new_order(task)
        elif task.name == "process_accepted_order":
            return await self._process_accepted_order(task)
        elif task.name == "process_status_update":
            return await self._process_status_update(task)
        elif task.name == "process_rejected_order":
            return await self._process_rejected_order(task)
        else:
            raise ValueError(f"Unknown task: {task.name}")
    
    async def _process_new_order(self, task: Task) -> Dict[str, Any]:
        """Обработка нового заказа"""
        order_id = task.data["order_id"]
        
        # Здесь логика обработки нового заказа
        # Например, уведомление операторов
        
        from services.notification_service import NotificationService
        from database.queries import get_users_by_role
        
        notification_service = NotificationService(None)  # Bot будет установлен позже
        
        # Получаем операторов
        operators = await get_users_by_role("operator")
        
        # Отправляем уведомления
        for operator in operators:
            await notification_service.send_notification(
                operator["telegram_id"],
                f"📥 Новый заказ #{order_id} создан",
                order_id
            )
        
        return {"status": "processed", "notified_operators": len(operators)}
    
    async def _process_accepted_order(self, task: Task) -> Dict[str, Any]:
        """Обработка принятого заказа"""
        order_id = task.data["order_id"]
        operator_id = task.data["operator_id"]
        
        # Автоматическое назначение сборщика
        from services.assignment_service import assign_picker
        
        picker = await assign_picker(order_id)
        
        if picker:
            return {"status": "picker_assigned", "picker_id": picker["id"]}
        else:
            return {"status": "no_picker_available"}
    
    async def _process_status_update(self, task: Task) -> Dict[str, Any]:
        """Обработка обновления статуса"""
        order_id = task.data["order_id"]
        new_status = task.data["new_status"]
        worker_id = task.data["worker_id"]
        
        # Здесь логика для разных статусов
        if new_status == "ready":
            # Назначаем проверщика
            from services.assignment_service import assign_checker
            checker = await assign_checker(order_id)
            return {"status": "checker_assigned", "checker_id": checker["id"] if checker else None}
        
        elif new_status == "checking":
            # Назначаем курьера
            from services.assignment_service import assign_courier
            courier = await assign_courier(order_id)
            return {"status": "courier_assigned", "courier_id": courier["id"] if courier else None}
        
        return {"status": "processed"}
    
    async def _process_rejected_order(self, task: Task) -> Dict[str, Any]:
        """Обработка отклоненного заказа"""
        order_id = task.data["order_id"]
        operator_id = task.data["operator_id"]
        reason = task.data.get("reason", "")
        
        # Уведомление клиента об отклонении
        from database.queries import get_order_by_id
        from services.notification_service import NotificationService
        
        order = await get_order_by_id(order_id)
        if order:
            notification_service = NotificationService(None)
            await notification_service.send_notification(
                order["client_id"],
                f"❌ Ваш заказ #{order_id} был отклонен. Причина: {reason}",
                order_id
            )
        
        return {"status": "processed", "client_notified": order is not None}

class NotificationWorker(BaseWorker):
    """Воркер для отправки уведомлений"""
    
    def __init__(self, worker_id: str):
        super().__init__(worker_id, ["send_notification"])
    
    async def handle_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Обработка уведомлений"""
        user_id = task.data["user_id"]
        message = task.data["message"]
        order_id = task.data.get("order_id")
        
        # Здесь логика отправки уведомлений
        # В реальном приложении здесь будет отправка через bot
        
        self.logger.info(f"📢 Notification sent to {user_id}: {message[:50]}...")
        
        return {"status": "sent", "user_id": user_id}

class AIWorker(BaseWorker):
    """Воркер для AI аналитики"""
    
    def __init__(self, worker_id: str):
        super().__init__(worker_id, ["ai_analysis", "daily_report"])
    
    async def handle_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Обработка AI задач"""
        
        if task.name == "ai_analysis":
            return await self._process_ai_analysis(task)
        elif task.name == "daily_report":
            return await self._process_daily_report(task)
        else:
            raise ValueError(f"Unknown task: {task.name}")
    
    async def _process_ai_analysis(self, task: Task) -> Dict[str, Any]:
        """Обработка AI анализа"""
        order_id = task.data.get("order_id")
        
        # Здесь логика AI анализа
        # Например, предсказание времени доставки
        
        prediction = {
            "estimated_delivery_time": "45 минут",
            "confidence": 0.85,
            "factors": ["пиковое время", "расстояние"]
        }
        
        return {"status": "analyzed", "prediction": prediction}
    
    async def _process_daily_report(self, task: Task) -> Dict[str, Any]:
        """Обработка дневного отчета"""
        # Генерация дневного отчета
        
        from database.queries import get_daily_stats
        
        stats = await get_daily_stats()
        
        report = {
            "date": stats.get("date", datetime.now().strftime("%d.%m.%Y")),
            "total_orders": stats.get("total_orders", 0),
            "delivered_orders": stats.get("delivered_orders", 0),
            "revenue": stats.get("total_revenue", 0)
        }
        
        # Здесь логика отправки отчета директору
        
        return {"status": "generated", "report": report}

class WorkerManager:
    """Менеджер воркеров"""
    
    def __init__(self):
        self.workers = {}
        self.logger = logging.getLogger("worker_manager")
    
    async def add_worker(self, worker: BaseWorker):
        """Добавление воркера"""
        await worker.initialize()
        self.workers[worker.worker_id] = worker
        self.logger.info(f"➕ Worker {worker.worker_id} added")
    
    async def start_all_workers(self):
        """Запуск всех воркеров"""
        self.logger.info(f"🚀 Starting {len(self.workers)} workers...")
        
        tasks = []
        for worker in self.workers.values():
            task = asyncio.create_task(worker.start())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def stop_all_workers(self):
        """Остановка всех воркеров"""
        self.logger.info("🛑 Stopping all workers...")
        
        for worker in self.workers.values():
            await worker.stop()
    
    def get_worker_stats(self) -> List[Dict[str, Any]]:
        """Получение статистики всех воркеров"""
        return [worker.get_stats() for worker in self.workers.values()]
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Получение общей статистики"""
        total_processed = sum(w.processed_tasks for w in self.workers.values())
        total_failed = sum(w.failed_tasks for w in self.workers.values())
        total_success_rate = (total_processed / max(1, total_processed + total_failed)) * 100
        
        return {
            "total_workers": len(self.workers),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "total_success_rate": total_success_rate,
            "workers": self.get_worker_stats()
        }

# Фабрика воркеров
class WorkerFactory:
    """Фабрика для создания воркеров"""
    
    @staticmethod
    def create_order_worker(worker_id: str) -> OrderWorker:
        """Создание воркера заказов"""
        return OrderWorker(worker_id)
    
    @staticmethod
    def create_notification_worker(worker_id: str) -> NotificationWorker:
        """Создание воркера уведомлений"""
        return NotificationWorker(worker_id)
    
    @staticmethod
    def create_ai_worker(worker_id: str) -> AIWorker:
        """Создание AI воркера"""
        return AIWorker(worker_id)
    
    @staticmethod
    def create_workers_by_type(worker_type: str, count: int) -> List[BaseWorker]:
        """Создание нескольких воркеров одного типа"""
        workers = []
        
        for i in range(count):
            worker_id = f"{worker_type}_{i+1}"
            
            if worker_type == "order":
                workers.append(WorkerFactory.create_order_worker(worker_id))
            elif worker_type == "notification":
                workers.append(WorkerFactory.create_notification_worker(worker_id))
            elif worker_type == "ai":
                workers.append(WorkerFactory.create_ai_worker(worker_id))
        
        return workers

# Удобные функции для использования
async def create_worker_pool() -> WorkerManager:
    """Создание пула воркеров"""
    manager = WorkerManager()
    
    # Создаем воркеров разных типов
    order_workers = WorkerFactory.create_workers_by_type("order", 3)
    notification_workers = WorkerFactory.create_workers_by_type("notification", 2)
    ai_workers = WorkerFactory.create_workers_by_type("ai", 1)
    
    # Добавляем все воркеры
    for worker in order_workers + notification_workers + ai_workers:
        await manager.add_worker(worker)
    
    return manager

async def start_worker_pool():
    """Запуск пула воркеров"""
    manager = await create_worker_pool()
    await manager.start_all_workers()
    return manager
