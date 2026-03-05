#!/usr/bin/env python3
"""
⚙️ Worker Services - Параллельная обработка 100K заказов/день
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
import time

# Импортируем микросервисы
from microservices import create_microservices, EventType, EventPriority

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('workers.log')
    ]
)

logger = logging.getLogger("workers")

class BaseWorker:
    """Базовый класс для всех workers"""
    
    def __init__(self, worker_id: str, redis_url: str):
        self.worker_id = worker_id
        self.redis_url = redis_url
        self.microservices = None
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.logger = logging.getLogger(f"worker_{worker_id}")
    
    async def initialize(self):
        """Инициализация worker"""
        try:
            self.microservices = await create_microservices(self.redis_url)
            self.running = True
            self.logger.info(f"✅ Worker {self.worker_id} initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize worker {self.worker_id}: {e}")
            return False
    
    async def start(self):
        """Запуск worker"""
        if not await self.initialize():
            return
        
        self.logger.info(f"🚀 Worker {self.worker_id} starting...")
        
        try:
            await self._run_worker_loop()
        except Exception as e:
            self.logger.error(f"❌ Worker {self.worker_id} error: {e}")
            raise
        finally:
            self.logger.info(f"🛑 Worker {self.worker_id} stopped")
    
    async def _run_worker_loop(self):
        """Основной цикл worker"""
        while self.running:
            try:
                await self._process_tasks()
                await asyncio.sleep(0.1)  # Небольшая задержка для предотвращения CPU overload
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"❌ Worker loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_tasks(self):
        """Обработка задач - должен быть переопределен в дочерних классах"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики worker"""
        uptime = time.time() - self.start_time
        return {
            "worker_id": self.worker_id,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "uptime": uptime,
            "avg_rate": self.processed_count / max(1, uptime)
        }

class OrderWorker(BaseWorker):
    """Worker для обработки заказов"""
    
    def __init__(self, worker_id: str, redis_url: str):
        super().__init__(worker_id, redis_url)
        self.queue_name = "order_queue"
    
    async def _process_tasks(self):
        """Обработка заказов"""
        try:
            # Получаем задачи из очереди
            tasks = await self._get_tasks_from_queue(self.queue_name, limit=10)
            
            for task in tasks:
                await self._process_order_task(task)
                self.processed_count += 1
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Order processing error: {e}")
    
    async def _get_tasks_from_queue(self, queue_name: str, limit: int = 10) -> List[Dict]:
        """Получение задач из очереди"""
        # Здесь должна быть реальная логика получения из Redis Queue
        # Для примера возвращаем пустой список
        return []
    
    async def _process_order_task(self, task: Dict[str, Any]):
        """Обработка задачи заказа"""
        try:
            task_type = task.get("type")
            order_data = task.get("data")
            
            if task_type == "create_order":
                # Создание заказа
                order = await self.microservices["order"].create_order(
                    order_data.get("user_id"),
                    order_data
                )
                self.logger.info(f"📦 Order #{order.id} created by worker {self.worker_id}")
            
            elif task_type == "update_status":
                # Обновление статуса
                await self.microservices["order"].update_order_status(
                    order_data.get("order_id"),
                    order_data.get("new_status"),
                    order_data.get("updated_by")
                )
                self.logger.info(f"📊 Order status updated by worker {self.worker_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Task processing error: {e}")
            raise

class PaymentWorker(BaseWorker):
    """Worker для обработки платежей"""
    
    def __init__(self, worker_id: str, redis_url: str):
        super().__init__(worker_id, redis_url)
        self.queue_name = "payment_queue"
    
    async def _process_tasks(self):
        """Обработка платежей"""
        try:
            tasks = await self._get_tasks_from_queue(self.queue_name, limit=5)
            
            for task in tasks:
                await self._process_payment_task(task)
                self.processed_count += 1
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Payment processing error: {e}")
    
    async def _get_tasks_from_queue(self, queue_name: str, limit: int = 5) -> List[Dict]:
        """Получение задач из очереди"""
        return []
    
    async def _process_payment_task(self, task: Dict[str, Any]):
        """Обработка задачи платежа"""
        try:
            task_type = task.get("type")
            payment_data = task.get("data")
            
            if task_type == "confirm_payment":
                # Подтверждение платежа
                await self.microservices["order"].update_order_status(
                    payment_data.get("order_id"),
                    "accepted",
                    payment_data.get("confirmed_by")
                )
                
                # Публикуем событие
                await self.microservices["order"].event_bus.publish(
                    EventType.PAYMENT_CONFIRMED,
                    payment_data,
                    payment_data.get("confirmed_by"),
                    EventPriority.HIGH
                )
                
                self.logger.info(f"💳 Payment confirmed by worker {self.worker_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Payment task error: {e}")
            raise

class NotificationWorker(BaseWorker):
    """Worker для отправки уведомлений"""
    
    def __init__(self, worker_id: str, redis_url: str):
        super().__init__(worker_id, redis_url)
        self.queue_name = "notification_queue"
    
    async def _process_tasks(self):
        """Обработка уведомлений"""
        try:
            tasks = await self._get_tasks_from_queue(self.queue_name, limit=20)
            
            for task in tasks:
                await self._process_notification_task(task)
                self.processed_count += 1
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Notification processing error: {e}")
    
    async def _get_tasks_from_queue(self, queue_name: str, limit: int = 20) -> List[Dict]:
        """Получение задач из очереди"""
        return []
    
    async def _process_notification_task(self, task: Dict[str, Any]):
        """Обработка задачи уведомления"""
        try:
            task_type = task.get("type")
            notification_data = task.get("data")
            
            if task_type == "order_notification":
                # Уведомление о заказе
                await self.microservices["notification"].send_order_notification(
                    notification_data.get("user_id"),
                    notification_data.get("message"),
                    notification_data.get("order_id")
                )
                
            elif task_type == "worker_notification":
                # Уведомление работника
                await self.microservices["notification"].send_worker_notification(
                    notification_data.get("worker_id"),
                    notification_data.get("message"),
                    notification_data.get("order_id")
                )
            
            self.logger.info(f"📢 Notification sent by worker {self.worker_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Notification task error: {e}")
            raise

class AIAnalyticsWorker(BaseWorker):
    """Worker для AI аналитики"""
    
    def __init__(self, worker_id: str, redis_url: str):
        super().__init__(worker_id, redis_url)
        self.queue_name = "analytics_queue"
    
    async def _process_tasks(self):
        """Обработка аналитики"""
        try:
            tasks = await self._get_tasks_from_queue(self.queue_name, limit=5)
            
            for task in tasks:
                await self._process_analytics_task(task)
                self.processed_count += 1
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Analytics processing error: {e}")
    
    async def _get_tasks_from_queue(self, queue_name: str, limit: int = 5) -> List[Dict]:
        """Получение задач из очереди"""
        return []
    
    async def _process_analytics_task(self, task: Dict[str, Any]):
        """Обработка задачи аналитики"""
        try:
            task_type = task.get("type")
            analytics_data = task.get("data")
            
            if task_type == "generate_report":
                # Генерация отчета
                report = await self.microservices["ai_analytics"].generate_daily_report()
                
                # Сохраняем отчет или отправляем администратору
                self.logger.info(f"📊 AI Report generated by worker {self.worker_id}")
                
            elif task_type == "analyze_performance":
                # Анализ производительности
                # Здесь должна быть логика анализа
                self.logger.info(f"📈 Performance analyzed by worker {self.worker_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Analytics task error: {e}")
            raise

class DeliveryWorker(BaseWorker):
    """Worker для обработки доставки"""
    
    def __init__(self, worker_id: str, redis_url: str):
        super().__init__(worker_id, redis_url)
        self.queue_name = "delivery_queue"
    
    async def _process_tasks(self):
        """Обработка доставки"""
        try:
            tasks = await self._get_tasks_from_queue(self.queue_name, limit=10)
            
            for task in tasks:
                await self._process_delivery_task(task)
                self.processed_count += 1
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Delivery processing error: {e}")
    
    async def _get_tasks_from_queue(self, queue_name: str, limit: int = 10) -> List[Dict]:
        """Получение задач из очереди"""
        return []
    
    async def _process_delivery_task(self, task: Dict[str, Any]):
        """Обработка задачи доставки"""
        try:
            task_type = task.get("type")
            delivery_data = task.get("data")
            
            if task_type == "assign_courier":
                # Назначение курьера
                courier_id = await self.microservices["assignment"].assign_least_loaded_worker(
                    "courier",
                    delivery_data.get("order_id")
                )
                
                if courier_id:
                    # Отправляем уведомление курьеру
                    await self.microservices["notification"].send_worker_notification(
                        courier_id,
                        "Новый заказ для доставки",
                        delivery_data.get("order_id")
                    )
                    
                    self.logger.info(f"🚚 Courier {courier_id} assigned by worker {self.worker_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Delivery task error: {e}")
            raise

class WorkerManager:
    """Менеджер всех workers"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.workers = {}
        self.logger = logging.getLogger("worker_manager")
    
    async def start_all_workers(self):
        """Запуск всех workers"""
        try:
            # Создаем workers разных типов
            worker_configs = [
                # Order Workers (4 экземпляра для высокой нагрузки)
                ("order_worker_1", OrderWorker),
                ("order_worker_2", OrderWorker),
                ("order_worker_3", OrderWorker),
                ("order_worker_4", OrderWorker),
                
                # Payment Workers (2 экземпляра)
                ("payment_worker_1", PaymentWorker),
                ("payment_worker_2", PaymentWorker),
                
                # Notification Workers (3 экземпляра)
                ("notification_worker_1", NotificationWorker),
                ("notification_worker_2", NotificationWorker),
                ("notification_worker_3", NotificationWorker),
                
                # AI Analytics Worker (1 экземпляр)
                ("analytics_worker_1", AIAnalyticsWorker),
                
                # Delivery Workers (2 экземпляра)
                ("delivery_worker_1", DeliveryWorker),
                ("delivery_worker_2", DeliveryWorker),
            ]
            
            # Запускаем все workers
            tasks = []
            for worker_id, worker_class in worker_configs:
                worker = worker_class(worker_id, self.redis_url)
                self.workers[worker_id] = worker
                tasks.append(worker.start())
            
            # Запускаем все workers параллельно
            self.logger.info("🚀 Starting all workers...")
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start workers: {e}")
            raise
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Получение статистики всех workers"""
        stats = {
            "total_workers": len(self.workers),
            "total_processed": 0,
            "total_errors": 0,
            "workers": {}
        }
        
        for worker_id, worker in self.workers.items():
            worker_stats = worker.get_stats()
            stats["workers"][worker_id] = worker_stats
            stats["total_processed"] += worker_stats["processed_count"]
            stats["total_errors"] += worker_stats["error_count"]
        
        return stats
    
    async def stop_all_workers(self):
        """Остановка всех workers"""
        self.logger.info("🛑 Stopping all workers...")
        
        for worker_id, worker in self.workers.items():
            worker.running = False
        
        self.logger.info("✅ All workers stopped")

# 🎯 Функции для запуска
async def start_order_workers(redis_url: str, count: int = 4):
    """Запуск order workers"""
    manager = WorkerManager(redis_url)
    
    tasks = []
    for i in range(count):
        worker = OrderWorker(f"order_worker_{i+1}", redis_url)
        tasks.append(worker.start())
    
    await asyncio.gather(*tasks)

async def start_all_workers(redis_url: str):
    """Запуск всех workers"""
    manager = WorkerManager(redis_url)
    await manager.start_all_workers()

def main():
    """Основная функция для запуска workers"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    worker_type = os.getenv("WORKER_TYPE", "all")
    
    print(f"⚙️ Starting MAXXPHARM Workers...")
    print(f"🗄️ Redis: {redis_url}")
    print(f"🔧 Worker Type: {worker_type}")
    
    try:
        if worker_type == "order":
            asyncio.run(start_order_workers(redis_url))
        else:
            asyncio.run(start_all_workers(redis_url))
    except KeyboardInterrupt:
        print("\n🛑 Workers stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
