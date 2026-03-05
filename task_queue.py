#!/usr/bin/env python3
"""
⚙️ Task Queue System - Вынос тяжелых задач из основного потока
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Celery
from celery.exceptions import Retry

# Настройка логирования
logger = logging.getLogger("task_queue")

# Создаем Celery приложение
def create_celery_app(redis_url: str) -> Celery:
    """Создание Celery приложения"""
    celery_app = Celery(
        "maxxpharm_tasks",
        broker=redis_url,
        backend=redis_url,
        include=['tasks']
    )
    
    # Настройки
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 минут на задачу
        task_soft_time_limit=240,  # 4 минуты мягкий лимит
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        worker_disable_rate_limits=False,
    )
    
    return celery_app

# Создаем экземпляр Celery
REDIS_URL = "redis://localhost:6379/0"
celery_app = create_celery_app(REDIS_URL)

class TaskQueue:
    """Менеджер очереди задач"""
    
    def __init__(self):
        self.celery = celery_app
        self.logger = logging.getLogger("task_queue")
    
    async def send_ai_report(self, user_id: int, report_data: Dict[str, Any]) -> str:
        """Отправка AI отчета в очередь"""
        try:
            task = self.celery.send_task(
                'tasks.generate_ai_report',
                args=[user_id, report_data],
                kwargs={},
                queue='ai_queue'
            )
            
            self.logger.info(f"📊 AI report task queued: {task.id}")
            return task.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue AI report: {e}")
            raise
    
    async def send_notification(self, user_id: int, message: str, message_type: str = "info") -> str:
        """Отправка уведомления в очередь"""
        try:
            task = self.celery.send_task(
                'tasks.send_notification',
                args=[user_id, message, message_type],
                kwargs={},
                queue='notification_queue'
            )
            
            self.logger.info(f"📢 Notification task queued: {task.id}")
            return task.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue notification: {e}")
            raise
    
    async def process_order(self, order_id: int, order_data: Dict[str, Any]) -> str:
        """Обработка заказа в очереди"""
        try:
            task = self.celery.send_task(
                'tasks.process_order',
                args=[order_id, order_data],
                kwargs={},
                queue='order_queue'
            )
            
            self.logger.info(f"📦 Order processing task queued: {task.id}")
            return task.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue order processing: {e}")
            raise
    
    async def analyze_metrics(self, metrics_data: Dict[str, Any]) -> str:
        """Анализ метрик в очереди"""
        try:
            task = self.celery.send_task(
                'tasks.analyze_metrics',
                args=[metrics_data],
                kwargs={},
                queue='analytics_queue'
            )
            
            self.logger.info(f"📈 Metrics analysis task queued: {task.id}")
            return task.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue metrics analysis: {e}")
            raise
    
    async def cleanup_old_data(self, days: int = 30) -> str:
        """Очистка старых данных"""
        try:
            task = self.celery.send_task(
                'tasks.cleanup_old_data',
                args=[days],
                kwargs={},
                queue='maintenance_queue'
            )
            
            self.logger.info(f"🧹 Cleanup task queued: {task.id}")
            return task.id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue cleanup: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получение статуса задачи"""
        try:
            result = self.celery.AsyncResult(task_id)
            
            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'traceback': result.traceback if result.failed() else None,
                'date_done': result.date_done
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get task status: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Получение статистики очередей"""
        try:
            inspect = self.celery.control.inspect()
            
            # Получаем активные задачи
            active_tasks = inspect.active()
            
            # Получаем запланированные задачи
            scheduled_tasks = inspect.scheduled()
            
            # Получаем зарезервированные задачи
            reserved_tasks = inspect.reserved()
            
            return {
                'active_tasks': active_tasks,
                'scheduled_tasks': scheduled_tasks,
                'reserved_tasks': reserved_tasks,
                'total_active': sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
                'total_scheduled': sum(len(tasks) for tasks in scheduled_tasks.values()) if scheduled_tasks else 0,
                'total_reserved': sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get queue stats: {e}")
            return {
                'error': str(e),
                'total_active': 0,
                'total_scheduled': 0,
                'total_reserved': 0
            }

# Определения задач Celery
@celery_app.task(bind=True, max_retries=3)
def generate_ai_report(self, user_id: int, report_data: Dict[str, Any]):
    """Генерация AI отчета"""
    try:
        logger.info(f"📊 Generating AI report for user {user_id}")
        
        # Здесь должна быть реальная логика генерации отчета
        # Для примера имитируем работу
        import time
        time.sleep(2)  # Имитация долгой задачи
        
        result = {
            'user_id': user_id,
            'report': f"AI Report for {user_id}",
            'generated_at': datetime.now().isoformat(),
            'data': report_data
        }
        
        logger.info(f"✅ AI report generated for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to generate AI report: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_notification(self, user_id: int, message: str, message_type: str = "info"):
    """Отправка уведомления"""
    try:
        logger.info(f"📢 Sending notification to user {user_id}")
        
        # Здесь должна быть реальная отправка сообщения
        # Для примера имитируем
        import time
        time.sleep(1)
        
        result = {
            'user_id': user_id,
            'message': message,
            'type': message_type,
            'sent_at': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        logger.info(f"✅ Notification sent to user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to send notification: {e}")
        raise self.retry(exc=e, countdown=30)

@celery_app.task(bind=True, max_retries=3)
def process_order(self, order_id: int, order_data: Dict[str, Any]):
    """Обработка заказа"""
    try:
        logger.info(f"📦 Processing order {order_id}")
        
        # Здесь должна быть реальная обработка заказа
        # Для примера имитируем
        import time
        time.sleep(3)
        
        result = {
            'order_id': order_id,
            'status': 'processed',
            'processed_at': datetime.now().isoformat(),
            'data': order_data
        }
        
        logger.info(f"✅ Order {order_id} processed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process order {order_id}: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def analyze_metrics(self, metrics_data: Dict[str, Any]):
    """Анализ метрик"""
    try:
        logger.info("📈 Analyzing metrics")
        
        # Здесь должен быть реальный анализ
        # Для примера имитируем
        import time
        time.sleep(5)
        
        result = {
            'analysis': 'Metrics analysis completed',
            'analyzed_at': datetime.now().isoformat(),
            'data': metrics_data,
            'insights': ['insight1', 'insight2', 'insight3']
        }
        
        logger.info("✅ Metrics analysis completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to analyze metrics: {e}")
        raise self.retry(exc=e, countdown=120)

@celery_app.task(bind=True, max_retries=2)
def cleanup_old_data(self, days: int):
    """Очистка старых данных"""
    try:
        logger.info(f"🧹 Cleaning up data older than {days} days")
        
        # Здесь должна быть реальная очистка
        # Для примера имитируем
        import time
        time.sleep(10)
        
        result = {
            'cleaned_days': days,
            'cleaned_at': datetime.now().isoformat(),
            'records_deleted': 1000  # Пример
        }
        
        logger.info(f"✅ Cleanup completed for {days} days")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup data: {e}")
        raise self.retry(exc=e, countdown=300)

# Создаем экземпляр очереди
task_queue = TaskQueue()

# Функции для удобного использования
async def queue_ai_report(user_id: int, report_data: Dict[str, Any]) -> str:
    """Поставить AI отчет в очередь"""
    return await task_queue.send_ai_report(user_id, report_data)

async def queue_notification(user_id: int, message: str, message_type: str = "info") -> str:
    """Поставить уведомление в очередь"""
    return await task_queue.send_notification(user_id, message, message_type)

async def queue_order_processing(order_id: int, order_data: Dict[str, Any]) -> str:
    """Поставить обработку заказа в очередь"""
    return await task_queue.process_order(order_id, order_data)

async def queue_metrics_analysis(metrics_data: Dict[str, Any]) -> str:
    """Поставить анализ метрик в очередь"""
    return await task_queue.analyze_metrics(metrics_data)

async def queue_cleanup(days: int = 30) -> str:
    """Поставить очистку в очередь"""
    return await task_queue.cleanup_old_data(days)

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Получить статус задачи"""
    return task_queue.get_task_status(task_id)

def get_queue_statistics() -> Dict[str, Any]:
    """Получить статистику очередей"""
    return task_queue.get_queue_stats()
