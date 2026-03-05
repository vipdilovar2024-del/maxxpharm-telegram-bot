#!/usr/bin/env python3
"""
⚙️ Worker Service - Обработка фоновых задач
"""

import os
import sys
import logging
from celery import Celery
from task_queue import create_celery_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('worker.log')
    ]
)

logger = logging.getLogger("worker")

def create_worker():
    """Создание worker"""
    # Получаем URL Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Создаем Celery приложение
    celery_app = create_celery_app(redis_url)
    
    logger.info("⚙️ Worker service created")
    return celery_app

def start_worker():
    """Запуск worker"""
    try:
        logger.info("🚀 Starting MAXXPHARM Worker Service...")
        
        # Создаем worker
        celery_app = create_worker()
        
        # Запускаем worker с настройками
        celery_app.start([
            'worker',
            '--loglevel=info',
            '--queues=ai_queue,notification_queue,order_queue,analytics_queue,maintenance_queue',
            '--concurrency=4',
            '--max-tasks-per-child=1000',
            '--time-limit=300',
            '--soft-time-limit=240'
        ])
        
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_worker()
