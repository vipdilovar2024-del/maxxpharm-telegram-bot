"""
🔒 Bot Lock System - Система предотвращения TelegramConflictError
Гарантирует что только один экземпляр бота работает одновременно
"""

import redis
import logging
import time
import os
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("bot_lock")

class BotLock:
    """Система блокировки для предотвращения конфликтов бота"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[redis.Redis] = None
        self.lock_key = "maxxpharm_bot_lock"
        self.heartbeat_key = "maxxpharm_bot_heartbeat"
        self.lock_ttl = 60  # 60 секунд
        self.heartbeat_interval = 30  # 30 секунд
        self.instance_id = f"{os.getpid()}_{int(time.time())}"
        self.logger = logging.getLogger("bot_lock")
        
    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Проверяем соединение
            self.redis_client.ping()
            self.logger.info(f"🔒 Connected to Redis: {self.redis_url}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def acquire_lock(self) -> bool:
        """Получение блокировки"""
        try:
            if not self.redis_client:
                if not await self.connect():
                    self.logger.error("❌ Cannot connect to Redis for lock")
                    return False
            
            # Пытаемся получить блокировку
            lock_acquired = self.redis_client.set(
                self.lock_key,
                self.instance_id,
                nx=True,
                ex=self.lock_ttl
            )
            
            if lock_acquired:
                self.logger.info(f"🔒 Lock acquired by instance: {self.instance_id}")
                # Запускаем heartbeat
                await self._start_heartbeat()
                return True
            else:
                # Проверяем кто держит блокировку
                current_holder = self.redis_client.get(self.lock_key)
                self.logger.warning(f"⚠️ Lock held by another instance: {current_holder}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error acquiring lock: {e}")
            return False
    
    async def release_lock(self):
        """Освобождение блокировки"""
        try:
            if self.redis_client:
                # Проверяем что это наша блокировка
                current_holder = self.redis_client.get(self.lock_key)
                if current_holder == self.instance_id:
                    self.redis_client.delete(self.lock_key)
                    self.redis_client.delete(self.heartbeat_key)
                    self.logger.info(f"🔓 Lock released by instance: {self.instance_id}")
                else:
                    self.logger.warning(f"⚠️ Attempted to release lock held by: {current_holder}")
        except Exception as e:
            self.logger.error(f"❌ Error releasing lock: {e}")
    
    async def _start_heartbeat(self):
        """Запуск heartbeat для поддержания блокировки"""
        try:
            # Обновляем heartbeat
            self.redis_client.setex(
                self.heartbeat_key,
                self.lock_ttl * 2,  # Heartbeat живет дольше
                self.instance_id
            )
            self.logger.debug(f"💓 Heartbeat updated: {self.instance_id}")
        except Exception as e:
            self.logger.error(f"❌ Error updating heartbeat: {e}")
    
    async def check_lock_status(self) -> dict:
        """Проверка статуса блокировки"""
        try:
            if not self.redis_client:
                return {"status": "no_redis", "holder": None}
            
            current_holder = self.redis_client.get(self.lock_key)
            heartbeat = self.redis_client.get(self.heartbeat_key)
            
            return {
                "status": "locked" if current_holder else "free",
                "holder": current_holder,
                "heartbeat": heartbeat,
                "self_holds": current_holder == self.instance_id
            }
        except Exception as e:
            self.logger.error(f"❌ Error checking lock status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def force_release_lock(self) -> bool:
        """Принудительное освобождение блокировки (только для админа)"""
        try:
            if self.redis_client:
                self.redis_client.delete(self.lock_key)
                self.redis_client.delete(self.heartbeat_key)
                self.logger.warning("🔓 Lock force released")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Error force releasing lock: {e}")
            return False
    
    @asynccontextmanager
    async def lock_context(self):
        """Контекст менеджер для блокировки"""
        acquired = await self.acquire_lock()
        if not acquired:
            raise RuntimeError("Cannot acquire bot lock - another instance is running")
        
        try:
            yield
        finally:
            await self.release_lock()

# Глобальный экземпляр блокировки
bot_lock: Optional[BotLock] = None

def get_bot_lock(redis_url: str = None) -> BotLock:
    """Получение экземпляра блокировки"""
    global bot_lock
    if bot_lock is None:
        bot_lock = BotLock(redis_url)
    return bot_lock

# Удобные функции для использования
async def ensure_single_instance() -> bool:
    """Гарантирует что только один экземпляр бота запущен"""
    lock = get_bot_lock()
    
    if not await lock.acquire_lock():
        logger.error("❌ Another bot instance is already running!")
        logger.error("💡 Please stop the other instance first")
        return False
    
    logger.info("✅ Single instance ensured")
    return True

async def release_bot_lock():
    """Освобождение блокировки бота"""
    lock = get_bot_lock()
    await lock.release_lock()

@asynccontextmanager
async def single_bot_context():
    """Контекст менеджер для одного экземпляра бота"""
    lock = get_bot_lock()
    
    if not await lock.acquire_lock():
        raise RuntimeError("Another bot instance is already running!")
    
    try:
        yield
    finally:
        await lock.release_lock()

# Функция для проверки в main.py
def check_for_existing_bot() -> bool:
    """Проверка существующего бота при запуске"""
    try:
        import asyncio
        lock = get_bot_lock()
        
        # Синхронная проверка
        status = asyncio.run(lock.check_lock_status())
        
        if status["status"] == "locked":
            logger.error(f"❌ Bot is already running (instance: {status['holder']})")
            logger.error("💡 Please stop the other instance first")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking existing bot: {e}")
        return True  # Разрешаем запуск если не удалось проверить

# Класс для мониторинга блокировок
class LockMonitor:
    """Мониторинг блокировок бота"""
    
    def __init__(self, bot_lock: BotLock):
        self.bot_lock = bot_lock
        self.logger = logging.getLogger("lock_monitor")
    
    async def start_monitoring(self):
        """Запуск мониторинга блокировок"""
        self.logger.info("🔒 Lock monitoring started")
        
        while True:
            try:
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
                status = await self.bot_lock.check_lock_status()
                
                if status["status"] == "locked":
                    if not status["self_holds"]:
                        self.logger.warning(f"⚠️ Lock held by another instance: {status['holder']}")
                    else:
                        self.logger.debug("✅ We hold the lock")
                else:
                    self.logger.warning("⚠️ Lock is free - this shouldn't happen!")
                
                # Обновляем heartbeat если мы держим блокировку
                if status["self_holds"]:
                    await self.bot_lock._start_heartbeat()
                
            except Exception as e:
                self.logger.error(f"❌ Lock monitoring error: {e}")
                await asyncio.sleep(30)

# Декоратор для функций требующих блокировку
def require_bot_lock(func):
    """Декоратор для функций требующих блокировку бота"""
    async def wrapper(*args, **kwargs):
        lock = get_bot_lock()
        
        if not await lock.acquire_lock():
            raise RuntimeError("Cannot acquire bot lock - another instance is running")
        
        try:
            return await func(*args, **kwargs)
        finally:
            await lock.release_lock()
    
    return wrapper

# Утилиты для отладки
async def debug_lock_status():
    """Отладочная информация о статусе блокировки"""
    lock = get_bot_lock()
    status = await lock.check_lock_status()
    
    debug_info = f"""
🔒 **Lock Debug Info**

Status: {status['status']}
Holder: {status['holder']}
Heartbeat: {status['heartbeat']}
Self Holds: {status['self_holds']}
Instance ID: {lock.instance_id}
Redis URL: {lock.redis_url}

🔑 Lock Key: {lock.lock_key}
💓 Heartbeat Key: {lock.heartbeat_key}
⏰ TTL: {lock.lock_ttl}s
💓 Interval: {lock.heartbeat_interval}s
"""
    
    return debug_info
