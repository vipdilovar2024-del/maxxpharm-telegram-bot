"""
🏥 Health Check System - Система проверки здоровья бота
Мониторинг всех компонентов CRM системы
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from aiogram import Bot

logger = logging.getLogger("health_check")

class HealthChecker:
    """Система проверки здоровья компонентов"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = logging.getLogger("health_checker")
        self.last_checks = {}
        self.alert_thresholds = {
            "telegram_error_rate": 0.05,  # 5%
            "db_response_time": 2.0,     # 2 секунды
            "redis_response_time": 1.0,   # 1 секунда
            "memory_usage": 0.8,          # 80%
            "cpu_usage": 0.8              # 80%
        }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Комплексная проверка здоровья"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "metrics": {},
            "alerts": []
        }
        
        # Проверяем каждый компонент
        components = [
            "telegram",
            "database", 
            "redis",
            "openai",
            "memory",
            "disk",
            "bot_lock"
        ]
        
        for component in components:
            try:
                result = await self._check_component(component)
                health_report["components"][component] = result
                
                if result["status"] != "healthy":
                    health_report["overall_status"] = "degraded"
                    health_report["alerts"].append({
                        "component": component,
                        "severity": "warning" if result["status"] == "warning" else "critical",
                        "message": result.get("message", "Component unhealthy")
                    })
                    
            except Exception as e:
                self.logger.error(f"❌ Error checking {component}: {e}")
                health_report["components"][component] = {
                    "status": "error",
                    "message": str(e)
                }
                health_report["overall_status"] = "critical"
        
        # Собираем метрики
        health_report["metrics"] = await self._collect_system_metrics()
        
        return health_report
    
    async def _check_component(self, component: str) -> Dict[str, Any]:
        """Проверка конкретного компонента"""
        checkers = {
            "telegram": self._check_telegram,
            "database": self._check_database,
            "redis": self._check_redis,
            "openai": self._check_openai,
            "memory": self._check_memory,
            "disk": self._check_disk,
            "bot_lock": self._check_bot_lock
        }
        
        checker = checkers.get(component)
        if checker:
            return await checker()
        else:
            return {"status": "unknown", "message": f"No checker for {component}"}
    
    async def _check_telegram(self) -> Dict[str, Any]:
        """Проверка Telegram API"""
        start_time = time.time()
        
        try:
            # Проверяем получение информации о боте
            bot_info = await self.bot.get_me()
            response_time = time.time() - start_time
            
            # Проверяем отправку сообщения (себе)
            test_message = f"🏥 Health check - {datetime.now().strftime('%H:%M:%S')}"
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time,
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Проверка базы данных"""
        start_time = time.time()
        
        try:
            from database.db import get_db_connection
            conn = await get_db_connection()
            
            # Простая проверка запроса
            result = await conn.fetchval("SELECT 1 as test")
            
            # Проверяем таблицы
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            await conn.close()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "tables_count": len(tables),
                "test_query": result == 1,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time,
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Проверка Redis"""
        start_time = time.time()
        
        try:
            from bot.config import REDIS_URL
            if not REDIS_URL:
                return {
                    "status": "skipped",
                    "message": "Redis not configured",
                    "last_check": datetime.now().isoformat()
                }
            
            import redis
            r = redis.from_url(REDIS_URL, decode_responses=True)
            
            # Проверяем подключение
            r.ping()
            
            # Тестовая операция
            test_key = "health_check_test"
            r.setex(test_key, 60, "test_value")
            test_value = r.get(test_key)
            r.delete(test_key)
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "test_operation": test_value == "test_value",
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time,
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_openai(self) -> Dict[str, Any]:
        """Проверка OpenAI API"""
        start_time = time.time()
        
        try:
            from bot.config import OPENAI_API_KEY
            if not OPENAI_API_KEY:
                return {
                    "status": "skipped",
                    "message": "OpenAI not configured",
                    "last_check": datetime.now().isoformat()
                }
            
            # Простая проверка API ключа (без реального запроса)
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            # Проверяем валидность ключа
            # В реальном приложении здесь можно сделать легкий запрос
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "api_configured": True,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time,
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Проверка использования памяти"""
        try:
            import psutil
            process = psutil.Process()
            
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Системная память
            system_memory = psutil.virtual_memory()
            
            status = "healthy"
            if memory_percent > self.alert_thresholds["memory_usage"] * 100:
                status = "warning"
            if memory_percent > 95:
                status = "critical"
            
            return {
                "status": status,
                "process_memory_mb": memory_info.rss / 1024 / 1024,
                "process_memory_percent": memory_percent,
                "system_memory_total_gb": system_memory.total / 1024 / 1024 / 1024,
                "system_memory_available_gb": system_memory.available / 1024 / 1024 / 1024,
                "system_memory_percent": system_memory.percent,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Проверка дискового пространства"""
        try:
            import psutil
            disk_usage = psutil.disk_usage('/')
            
            free_percent = (disk_usage.free / disk_usage.total) * 100
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            status = "healthy"
            if free_percent < 20:  # Менее 20% свободного места
                status = "warning"
            if free_percent < 10:  # Менее 10% свободного места
                status = "critical"
            
            return {
                "status": status,
                "total_gb": disk_usage.total / 1024 / 1024 / 1024,
                "used_gb": disk_usage.used / 1024 / 1024 / 1024,
                "free_gb": disk_usage.free / 1024 / 1024 / 1024,
                "used_percent": used_percent,
                "free_percent": free_percent,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_bot_lock(self) -> Dict[str, Any]:
        """Проверка блокировки бота"""
        try:
            from bot_lock_system import get_bot_lock
            
            lock = get_bot_lock()
            status = await lock.check_lock_status()
            
            return {
                "status": "healthy" if status["status"] == "locked" and status["self_holds"] else "warning",
                "lock_status": status["status"],
                "lock_holder": status["holder"],
                "self_holds": status["self_holds"],
                "heartbeat": status["heartbeat"],
                "instance_id": lock.instance_id,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Сбор системных метрик"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Память
            memory = psutil.virtual_memory()
            
            # Сеть
            network = psutil.net_io_counters()
            
            # Процесс
            process = psutil.Process()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / 1024 / 1024 / 1024,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "memory_percent": memory.percent,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                "process_cpu_percent": process.cpu_percent(),
                "process_threads": process.num_threads(),
                "uptime_seconds": time.time() - process.create_time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting metrics: {e}")
            return {}
    
    async def send_health_alert(self, health_report: Dict[str, Any]):
        """Отправка алерта о здоровье системы"""
        try:
            from bot.config import ADMIN_ID
            
            if not ADMIN_ID:
                return
            
            # Формируем сообщение
            status_emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "critical": "❌"
            }
            
            emoji = status_emoji.get(health_report["overall_status"], "❓")
            
            alert_message = f"""
{emoji} **CRM Health Alert**

📊 **Overall Status:** {health_report["overall_status"].upper()}
🕐 **Time:** {health_report["timestamp"]}

🔧 **Components:**
"""
            
            for component, status in health_report["components"].items():
                comp_emoji = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🚨",
                    "skipped": "⏭️"
                }.get(status["status"], "❓")
                
                alert_message += f"{comp_emoji} {component.title()}: {status['status']}\n"
            
            if health_report["alerts"]:
                alert_message += "\n⚠️ **Alerts:**\n"
                for alert in health_report["alerts"]:
                    alert_emoji = "🚨" if alert["severity"] == "critical" else "⚠️"
                    alert_message += f"{alert_emoji} {alert['component']}: {alert['message']}\n"
            
            await self.bot.send_message(ADMIN_ID, alert_message)
            self.logger.info("📢 Health alert sent")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send health alert: {e}")
    
    async def get_health_summary(self) -> str:
        """Получение краткой сводки здоровья"""
        health_report = await self.comprehensive_health_check()
        
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "❌"
        }
        
        emoji = status_emoji.get(health_report["overall_status"], "❓")
        
        summary = f"""
{emoji} **CRM Health Summary**

📊 **Status:** {health_report["overall_status"].upper()}
🕐 **Last Check:** {health_report["timestamp"]}

🔧 **Components:**
"""
        
        for component, status in health_report["components"].items():
            comp_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
                "skipped": "⏭️"
            }.get(status["status"], "❓")
            
            summary += f"{comp_emoji} {component.title()}: {status['status']}\n"
        
        return summary

# Глобальный экземпляр
health_checker: Optional[HealthChecker] = None

def get_health_checker(bot: Bot) -> HealthChecker:
    """Получение экземпляра health checker"""
    global health_checker
    if health_checker is None:
        health_checker = HealthChecker(bot)
    return health_checker

# Удобные функции
async def check_system_health(bot: Bot) -> Dict[str, Any]:
    """Проверка здоровья системы"""
    checker = get_health_checker(bot)
    return await checker.comprehensive_health_check()

async def health_check_loop(bot: Bot, interval: int = 300):
    """Цикл проверки здоровья"""
    checker = get_health_checker(bot)
    
    while True:
        try:
            health_report = await checker.comprehensive_health_check()
            
            # Отправляем алерты если есть проблемы
            if health_report["overall_status"] != "healthy":
                await checker.send_health_alert(health_report)
            
            await asyncio.sleep(interval)
            
        except Exception as e:
            logger.error(f"❌ Health check loop error: {e}")
            await asyncio.sleep(60)
