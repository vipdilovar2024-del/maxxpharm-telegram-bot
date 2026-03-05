#!/usr/bin/env python3
"""
🏥 Health Check Module - Мониторинг здоровья системы
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class HealthChecker:
    def __init__(self, bot, db_connection=None):
        self.bot = bot
        self.db_connection = db_connection
        self.logger = logging.getLogger("health_checker")
        self.health_history = []
        self.last_check = None
        
    async def start_health_monitoring(self):
        """Запуск мониторинга здоровья"""
        self.logger.info("🏥 Health monitoring started")
        
        while True:
            try:
                health_status = await self.check_all_systems()
                self.health_history.append({
                    'timestamp': datetime.now(),
                    'status': health_status
                })
                
                # Логируем статус
                await self._log_health_status(health_status)
                
                # Если есть критические проблемы, отправляем уведомление
                if health_status.get('critical_issues'):
                    await self._send_alert(health_status)
                
                self.last_check = datetime.now()
                
            except Exception as e:
                self.logger.error(f"❌ Health check error: {e}")
            
            # Проверяем каждые 5 минут
            await asyncio.sleep(300)
    
    async def check_all_systems(self) -> Dict[str, Any]:
        """Проверка всех систем"""
        checks = {
            'telegram_api': await self._check_telegram_api(),
            'database': await self._check_database(),
            'memory': await self._check_memory(),
            'performance': await self._check_performance(),
            'error_rate': await self._check_error_rate()
        }
        
        # Определяем общий статус
        overall_status = self._calculate_overall_status(checks)
        
        return {
            'timestamp': datetime.now(),
            'overall_status': overall_status,
            'checks': checks,
            'critical_issues': [name for name, check in checks.items() if check.get('status') == 'critical'],
            'warnings': [name for name, check in checks.items() if check.get('status') == 'warning']
        }
    
    async def _check_telegram_api(self) -> Dict[str, Any]:
        """Проверка Telegram API"""
        try:
            start_time = time.time()
            bot_info = await self.bot.get_me()
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if response_time < 2 else 'warning',
                'response_time': response_time,
                'bot_info': {
                    'id': bot_info.id,
                    'username': bot_info.username,
                    'name': bot_info.full_name
                },
                'message': 'Telegram API работает нормально'
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': f'Ошибка Telegram API: {str(e)}'
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Проверка базы данных"""
        if not self.db_connection:
            return {
                'status': 'warning',
                'message': 'База данных не подключена'
            }
        
        try:
            start_time = time.time()
            # Простая проверка подключения
            await self.db_connection.fetchval('SELECT 1')
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if response_time < 1 else 'warning',
                'response_time': response_time,
                'message': 'База данных работает нормально'
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': f'Ошибка базы данных: {str(e)}'
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Проверка использования памяти"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Использование памяти в процентах
            memory_percent = memory.percent
            
            status = 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 90 else 'critical'
            
            return {
                'status': status,
                'memory_percent': memory_percent,
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'message': f'Использование памяти: {memory_percent:.1f}%'
            }
        except ImportError:
            return {
                'status': 'warning',
                'message': 'psutil не установлен, проверка памяти недоступна'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': f'Ошибка проверки памяти: {str(e)}'
            }
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Проверка производительности"""
        try:
            # Проверяем время ответа последних операций
            if not self.health_history:
                return {
                    'status': 'healthy',
                    'message': 'Первичная проверка производительности'
                }
            
            # Берем последние 5 проверок
            recent_checks = self.health_history[-5:]
            if len(recent_checks) < 2:
                return {
                    'status': 'healthy',
                    'message': 'Собираем статистику производительности'
                }
            
            # Анализируем тренд
            critical_count = sum(1 for check in recent_checks 
                               if check['status'].get('critical_issues'))
            
            status = 'healthy' if critical_count == 0 else 'warning' if critical_count < 3 else 'critical'
            
            return {
                'status': status,
                'critical_issues_last_5': critical_count,
                'message': f'Критических проблем за последние 5 проверок: {critical_count}'
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': f'Ошибка проверки производительности: {str(e)}'
            }
    
    async def _check_error_rate(self) -> Dict[str, Any]:
        """Проверка частоты ошибок"""
        try:
            # Здесь должна быть интеграция с ErrorMonitor
            # Для примера используем простую логику
            if not self.health_history:
                return {
                    'status': 'healthy',
                    'error_rate': 0,
                    'message': 'Собираем статистику ошибок'
                }
            
            # Проверяем ошибки за последний час
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_checks = [check for check in self.health_history 
                           if check['timestamp'] > one_hour_ago]
            
            error_count = sum(len(check['status'].get('critical_issues', [])) 
                           for check in recent_checks)
            
            status = 'healthy' if error_count == 0 else 'warning' if error_count < 5 else 'critical'
            
            return {
                'status': status,
                'error_rate': error_count,
                'message': f'Ошибок за последний час: {error_count}'
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': f'Ошибка проверки ошибок: {str(e)}'
            }
    
    def _calculate_overall_status(self, checks: Dict[str, Any]) -> str:
        """Расчет общего статуса системы"""
        statuses = [check.get('status') for check in checks.values()]
        
        if 'critical' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'
    
    async def _log_health_status(self, status: Dict[str, Any]):
        """Логирование статуса здоровья"""
        overall = status['overall_status']
        emoji = {'healthy': '🟢', 'warning': '🟡', 'critical': '🔴'}
        
        self.logger.info(f"{emoji[overall]} Health check - {overall}")
        
        for name, check in status['checks'].items():
            check_emoji = {'healthy': '✅', 'warning': '⚠️', 'critical': '❌'}
            self.logger.info(f"  {check_emoji[check['status']]} {name}: {check['message']}")
    
    async def _send_alert(self, status: Dict[str, Any]):
        """Отправка алерта администратору"""
        try:
            critical_issues = status['critical_issues']
            alert_text = f"🚨 <b>Health Alert</b>\n\n"
            alert_text += f"🔴 Критические проблемы:\n"
            
            for issue in critical_issues:
                check_info = status['checks'][issue]
                alert_text += f"• {issue}: {check_info.get('message', 'Unknown error')}\n"
            
            alert_text += f"\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Здесь должна быть реальная отправка сообщения админу
            self.logger.critical(f"ALERT: {alert_text}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert: {e}")
    
    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки здоровья за период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [check for check in self.health_history 
                       if check['timestamp'] > cutoff_time]
        
        if not recent_checks:
            return {'message': 'Нет данных за указанный период'}
        
        # Анализируем тренды
        healthy_count = sum(1 for check in recent_checks 
                          if check['status']['overall_status'] == 'healthy')
        
        return {
            'total_checks': len(recent_checks),
            'healthy_checks': healthy_count,
            'health_percentage': (healthy_count / len(recent_checks)) * 100,
            'last_check': self.health_history[-1] if self.health_history else None,
            'time_range': f"Last {hours} hours"
        }
