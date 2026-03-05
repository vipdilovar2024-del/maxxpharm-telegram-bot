#!/usr/bin/env python3
"""
📊 Automated Reports Module - Автоматические отчеты для директора
"""

import asyncio
import logging
from datetime import datetime, time
from ai_director import AIDirector

class AutomatedReports:
    """Автоматические отчеты для директора"""
    
    def __init__(self, bot, ai_director: AIDirector, admin_id: int):
        self.bot = bot
        self.ai_director = ai_director
        self.admin_id = admin_id
        self.logger = logging.getLogger("automated_reports")
        self.daily_report_time = time(19, 0)  # 19:00 каждый день
        
    async def start_daily_reports(self):
        """Запуск ежедневных отчетов"""
        self.logger.info("📊 Daily reports started")
        
        while True:
            try:
                # Проверяем время отправки отчета
                now = datetime.now()
                
                if now.time() >= self.daily_report_time:
                    # Отправляем ежедневный отчет
                    await self.send_daily_report()
                    
                    # Ждем до следующего дня
                    await asyncio.sleep(86400)  # 24 часа
                else:
                    # Проверяем каждые 10 минут
                    await asyncio.sleep(600)
                    
            except Exception as e:
                self.logger.error(f"❌ Daily report error: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    async def send_daily_report(self):
        """Отправка ежедневного отчета"""
        try:
            # Получаем бизнес-метрики
            metrics = self.ai_director.get_business_metrics(days=1)
            
            # Анализируем проблемы
            analysis = await self.ai_director.analyze_business_problems(metrics)
            
            # Генерируем отчет
            report = self.ai_director.generate_daily_report(metrics, analysis)
            
            # Добавляем заголовок ежедневного отчета
            daily_report = f"""
🌅 <b>Ежедневный отчет MAXXPHARM</b>
📅 {datetime.now().strftime('%d %B %Y')}

{report}
"""
            
            # Отправляем отчет директору
            await self.bot.send_message(
                chat_id=self.admin_id,
                text=daily_report
            )
            
            self.logger.info("📊 Daily report sent successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send daily report: {e}")
    
    async def send_weekly_report(self):
        """Отправка еженедельного отчета"""
        try:
            # Получаем бизнес-метрики за неделю
            metrics = self.ai_director.get_business_metrics(days=7)
            
            # Получаем прогноз
            forecast = await self.ai_director.generate_forecast(days_ahead=7)
            
            # Анализируем проблемы
            analysis = await self.ai_director.analyze_business_problems(metrics)
            
            # Генерируем еженедельный отчет
            report = f"""
📈 <b>Еженедельный отчет MAXXPHARM</b>
📅 {datetime.now().strftime('%d %B %Y')} - {(datetime.now() + timedelta(days=7)).strftime('%d %B %Y')}

📊 <b>Результаты недели:</b>
• Заявок: {metrics['total_leads']}
• Продаж: {metrics['total_sales']}
• Конверсия: {metrics['conversion_rate']}%
• Общая выручка: ${metrics['total_revenue']}
• Средний чек: ${metrics['avg_sale_amount']}

🏆 <b>Лучший менеджер:</b> {analysis['best_manager']}

📈 <b>Прогноз на следующую неделю:</b>
• Заявок: {forecast['forecast_leads']}
• Продаж: {forecast['forecast_sales']}
• Выручка: ${forecast['forecast_revenue']}

🔍 <b>Проблемы:</b>
"""
            
            for problem in analysis['problems']:
                report += f"• {problem}\n"
            
            report += f"\n💡 <b>Рекомендации AI:</b>\n"
            for rec in analysis['recommendations']:
                report += f"• {rec}\n"
            
            report += f"\n📊 <b>Тренды:</b>\n"
            report += f"• Заявки: {forecast['leads_trend']}%\n"
            report += f"• Продажи: {forecast['sales_trend']}%\n"
            
            # Отправляем отчет
            await self.bot.send_message(
                chat_id=self.admin_id,
                text=report
            )
            
            self.logger.info("📊 Weekly report sent successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send weekly report: {e}")
    
    async def send_alert(self, alert_type: str, message: str):
        """Отправка алерта"""
        try:
            alert_emoji = {
                'critical': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️'
            }
            
            alert_text = f"""
{alert_emoji.get(alert_type, '📢')} <b>MAXXPHARM Alert</b>

{message}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await self.bot.send_message(
                chat_id=self.admin_id,
                text=alert_text
            )
            
            self.logger.info(f"📊 Alert sent: {alert_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert: {e}")

# Импортируем timedelta
from datetime import timedelta
