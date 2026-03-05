#!/usr/bin/env python3
"""
🛡️ Watchdog Module - Автоперезапуск бота
"""

import asyncio
import traceback
import time
import logging
from datetime import datetime

class BotWatchdog:
    def __init__(self, bot_core):
        self.bot_core = bot_core
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 5
        self.logger = logging.getLogger("watchdog")
        
    async def run_with_watchdog(self):
        """Запуск бота с автоперезапуском"""
        self.logger.info("🛡️ Watchdog started")
        
        while self.restart_count < self.max_restarts:
            try:
                self.logger.info(f"🚀 Bot starting (attempt {self.restart_count + 1})")
                await self.bot_core.start()
                
            except Exception as e:
                self.restart_count += 1
                error_msg = f"❌ Bot crashed: {str(e)}"
                self.logger.error(error_msg)
                
                # Записываем ошибку
                await self._log_error(e)
                
                if self.restart_count < self.max_restarts:
                    self.logger.info(f"🔄 Restarting in {self.restart_delay} seconds...")
                    await asyncio.sleep(self.restart_delay)
                else:
                    self.logger.error("🚨 Max restarts reached! Stopping...")
                    await self._notify_admin("Bot stopped after max restarts")
                    break
    
    async def _log_error(self, error):
        """Логирование ошибки"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_trace = traceback.format_exc()
        
        with open("bot_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"⏰ Time: {timestamp}\n")
            f.write(f"🔄 Restart: {self.restart_count}\n")
            f.write(f"❌ Error: {str(error)}\n")
            f.write(f"📋 Traceback:\n{error_trace}\n")
            f.write(f"{'='*50}\n")
    
    async def _notify_admin(self, message):
        """Уведомление администратора"""
        try:
            await self.bot_core.bot.send_message(
                chat_id=self.bot_core.ADMIN_ID,
                text=f"🚨 <b>Watchdog Alert</b>\n\n{message}"
            )
        except:
            pass  # Если бот упал, не можем отправить
