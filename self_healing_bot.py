#!/usr/bin/env python3
"""
🛡️ Self-Healing Telegram Bot - Production-level архитектура
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Импортируем наши модули
from watchdog import BotWatchdog
from instance_lock import InstanceLock
from error_monitor import ErrorMonitor
from ai_diagnostics import AIDiagnostics
from health_checker import HealthChecker

# Импортируем основной бот
import aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import Message

class SelfHealingBot:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.logger = logging.getLogger("self_healing_bot")
        
        # Инициализируем модули
        self.error_monitor = ErrorMonitor()
        self.ai_diagnostics = None  # Будет инициализирован позже
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('self_healing_bot.log')
            ]
        )
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            # Получаем токен
            BOT_TOKEN = os.getenv("BOT_TOKEN")
            ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))
            
            if not BOT_TOKEN:
                self.logger.error("❌ BOT_TOKEN не найден!")
                return False
            
            # Инициализируем бота
            self.bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
            self.dp = Dispatcher()
            
            # Инициализируем AI диагностику (если есть OpenAI ключ)
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            if OPENAI_API_KEY:
                try:
                    from openai import AsyncOpenAI
                    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
                    self.ai_diagnostics = AIDiagnostics(openai_client)
                    self.logger.info("🧠 AI Diagnostics initialized")
                except Exception as e:
                    self.logger.warning(f"⚠️ AI Diagnostics failed: {e}")
            
            # Инициализируем Health Checker
            self.health_checker = HealthChecker(self.bot)
            
            # Настройка базовых обработчиков
            await self._setup_handlers()
            
            self.logger.info("✅ Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            await self.error_monitor.log_error(e, "initialization")
            return False
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message()
        async def cmd_start(message: Message):
            """Обработчик /start"""
            await message.answer(
                "🛡️ <b>Self-Healing MAXXPHARM Bot</b>\n\n"
                "🤖 Бот работает в режиме самовосстановления\n"
                "📊 Статус: 🟢 Работает\n"
                "🧠 AI-диагностика: ✅ Активна\n"
                "🏥 Health Check: ✅ Мониторинг\n\n"
                "Используйте /health для проверки здоровья системы"
            )
        
        @self.dp.message()
        async def cmd_health(message: Message):
            """Обработчик /health"""
            if message.from_user.id != int(os.getenv("ADMIN_ID", "697780123")):
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем статус здоровья
            health_status = await self.health_checker.check_all_systems()
            
            # Формируем отчет
            report = f"🏥 <b>Отчет о здоровье системы</b>\n\n"
            report += f"📊 Общий статус: {health_status['overall_status']}\n"
            
            for name, check in health_status['checks'].items():
                emoji = {'healthy': '🟢', 'warning': '🟡', 'critical': '🔴'}
                report += f"\n{emoji[check['status']]} {name}: {check['message']}"
            
            if health_status['critical_issues']:
                report += f"\n\n🚨 Критические проблемы: {', '.join(health_status['critical_issues'])}"
            
            await message.answer(report)
        
        @self.dp.message()
        async def cmd_diagnostics(message: Message):
            """Обработчик /diagnostics"""
            if message.from_user.id != int(os.getenv("ADMIN_ID", "697780123")):
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем сводку ошибок
            error_summary = self.error_monitor.get_error_summary()
            
            report = f"📊 <b>Диагностика системы</b>\n\n"
            report += f"📈 Всего ошибок: {error_summary['total_errors']}\n"
            report += f"🔥 Критических: {error_summary['critical_errors']}\n"
            
            if error_summary['most_common']:
                report += f"\n📋 Самые частые ошибки:\n"
                for error in error_summary['most_common'][:3]:
                    report += f"• {error['type']}: {error['count']} раз\n"
            
            # Если есть AI диагностика, анализируем последнюю ошибку
            if self.ai_diagnostics and self.error_monitor.errors:
                last_error = self.error_monitor.errors[-1]
                ai_analysis = await self.ai_diagnostics.analyze_error(last_error)
                
                report += f"\n🧠 <b>AI анализ последней ошибки:</b>\n"
                report += f"🔴 Тяжесть: {ai_analysis['severity']}\n"
                report += f"🔍 Причина: {ai_analysis['root_cause']}\n"
                report += f"⚡ Действие: {ai_analysis['immediate_action']}\n"
            
            await message.answer(report)
    
    async def start(self):
        """Запуск Self-Healing бота"""
        self.logger.info("🛡️ Starting Self-Healing Bot...")
        
        # Инициализация
        if not await self.initialize():
            self.logger.error("❌ Failed to initialize bot")
            return False
        
        try:
            # Запускаем мониторинг здоровья в фоне
            health_task = asyncio.create_task(self.health_checker.start_health_monitoring())
            
            # Запускаем бота с watchdog
            watchdog = BotWatchdog(self)
            await watchdog.run_with_watchdog()
            
        except Exception as e:
            self.logger.error(f"❌ Bot runtime error: {e}")
            await self.error_monitor.log_error(e, "runtime")
            
            # Пробуем перезапустить
            await asyncio.sleep(5)
            return await self.start()

async def main():
    """Основная функция запуска"""
    print("🛡️ Self-Healing MAXXPHARM Bot starting...")
    
    # Используем Instance Lock для предотвращения конфликтов
    with InstanceLock() as lock:
        print(f"🔒 Instance lock acquired: {lock.instance_id}")
        
        # Создаем и запускаем бот
        bot = SelfHealingBot()
        await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
