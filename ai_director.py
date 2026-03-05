#!/usr/bin/env python3
"""
🧠 AI Director для MAXXPHARM CRM
Enterprise AI система для автоматизации бизнеса
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import pandas as pd

class AIDirector:
    """AI-директор для анализа CRM данных"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.logger = logging.getLogger("ai_director")
        self.crm_data = {
            'leads': [],
            'clients': [],
            'managers': [],
            'sales': [],
            'activities': []
        }
        
    def add_lead(self, lead_data: Dict):
        """Добавление новой заявки"""
        lead = {
            'id': len(self.crm_data['leads']) + 1,
            'client_name': lead_data.get('client_name', ''),
            'phone': lead_data.get('phone', ''),
            'product': lead_data.get('product', ''),
            'status': lead_data.get('status', 'new'),
            'manager': lead_data.get('manager', ''),
            'created_at': datetime.now(),
            'closed_at': None,
            'price': lead_data.get('price', 0)
        }
        self.crm_data['leads'].append(lead)
        self.logger.info(f"📊 New lead added: {lead['id']}")
        return lead
    
    def add_sale(self, sale_data: Dict):
        """Добавление продажи"""
        sale = {
            'id': len(self.crm_data['sales']) + 1,
            'lead_id': sale_data.get('lead_id'),
            'manager': sale_data.get('manager', ''),
            'amount': sale_data.get('amount', 0),
            'created_at': datetime.now(),
            'product': sale_data.get('product', '')
        }
        self.crm_data['sales'].append(sale)
        self.logger.info(f"💰 New sale added: {sale['id']}")
        return sale
    
    def calculate_conversion_rate(self, days: int = 7) -> float:
        """Расчет конверсии за период"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_leads = [l for l in self.crm_data['leads'] if l['created_at'] > cutoff_date]
        
        if not recent_leads:
            return 0.0
        
        closed_leads = [l for l in recent_leads if l['status'] == 'closed']
        return round((len(closed_leads) / len(recent_leads)) * 100, 2)
    
    def get_manager_stats(self, days: int = 7) -> Dict:
        """Статистика по менеджерам"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sales = [s for s in self.crm_data['sales'] if s['created_at'] > cutoff_date]
        
        manager_stats = defaultdict(lambda: {'sales': 0, 'amount': 0})
        for sale in recent_sales:
            manager_stats[sale['manager']]['sales'] += 1
            manager_stats[sale['manager']]['amount'] += sale['amount']
        
        return dict(manager_stats)
    
    def get_business_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Получение бизнес-метрик"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_leads = [l for l in self.crm_data['leads'] if l['created_at'] > cutoff_date]
        recent_sales = [s for s in self.crm_data['sales'] if s['created_at'] > cutoff_date]
        
        total_revenue = sum(s['amount'] for s in recent_sales)
        avg_sale_amount = total_revenue / len(recent_sales) if recent_sales else 0
        
        return {
            'period_days': days,
            'total_leads': len(recent_leads),
            'total_sales': len(recent_sales),
            'conversion_rate': self.calculate_conversion_rate(days),
            'total_revenue': total_revenue,
            'avg_sale_amount': round(avg_sale_amount, 2),
            'manager_stats': self.get_manager_stats(days)
        }
    
    async def analyze_business_problems(self, metrics: Dict) -> Dict[str, Any]:
        """AI анализ бизнес-проблем"""
        if not self.openai_client:
            return self._fallback_analysis(metrics)
        
        try:
            prompt = f"""
Проанализируй бизнес-метрики MAXXPHARM CRM:

Данные за {metrics['period_days']} дней:
- Заявок: {metrics['total_leads']}
- Продаж: {metrics['total_sales']}
- Конверсия: {metrics['conversion_rate']}%
- Общая выручка: ${metrics['total_revenue']}
- Средний чек: ${metrics['avg_sale_amount']}

Статистика менеджеров:
{json.dumps(metrics['manager_stats'], indent=2)}

Проанализируй и выдай:
1. Проблемы в бизнесе
2. Рекомендации по улучшению
3. Прогноз на завтра
4. Кто лучший менеджер

Ответ в формате JSON:
{{
    "problems": ["проблема1", "проблема2"],
    "recommendations": ["рекомендация1", "рекомендация2"],
    "forecast": "прогноз на завтра",
    "best_manager": "имя лучшего менеджера",
    "action_items": ["действие1", "действие2"]
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты AI бизнес-аналитик для MAXXPHARM CRM. Анализируй данные и давай конкретные рекомендации."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            return json.loads(ai_response)
            
        except Exception as e:
            self.logger.error(f"❌ AI analysis failed: {e}")
            return self._fallback_analysis(metrics)
    
    def _fallback_analysis(self, metrics: Dict) -> Dict[str, Any]:
        """Запасной анализ без AI"""
        problems = []
        recommendations = []
        
        # Анализ конверсии
        if metrics['conversion_rate'] < 30:
            problems.append("Низкая конверсия заявок")
            recommendations.append("Улучшить скрипты продаж")
        
        # Анализ количества заявок
        if metrics['total_leads'] < 10:
            problems.append("Мало новых заявок")
            recommendations.append("Увеличить рекламный бюджет")
        
        # Анализ менеджеров
        if not metrics['manager_stats']:
            problems.append("Нет активности менеджеров")
            recommendations.append("Проверить работу менеджеров")
        
        # Лучший менеджер
        best_manager = "Нет данных"
        if metrics['manager_stats']:
            best_manager = max(metrics['manager_stats'].items(), 
                             key=lambda x: x[1]['sales'])[0]
        
        return {
            'problems': problems,
            'recommendations': recommendations,
            'forecast': f"Ожидается {metrics['total_leads']//2 + 5} заявок завтра",
            'best_manager': best_manager,
            'action_items': recommendations[:2]
        }
    
    def generate_daily_report(self, metrics: Dict, analysis: Dict) -> str:
        """Генерация ежедневного отчета"""
        report = f"""
📊 <b>Отчет MAXXPHARM CRM</b>

📈 <b>Метрики за {metrics['period_days']} дней:</b>
• Заявок: {metrics['total_leads']}
• Продаж: {metrics['total_sales']}
• Конверсия: {metrics['conversion_rate']}%
• Выручка: ${metrics['total_revenue']}
• Средний чек: ${metrics['avg_sale_amount']}

🏆 <b>Лучший менеджер:</b>
{analysis['best_manager']}

🔍 <b>Проблемы:</b>
"""
        
        for problem in analysis['problems']:
            report += f"• {problem}\n"
        
        report += f"\n💡 <b>Рекомендации AI:</b>\n"
        for rec in analysis['recommendations']:
            report += f"• {rec}\n"
        
        report += f"\n📅 <b>Прогноз на завтра:</b>\n{analysis['forecast']}\n\n"
        report += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return report.strip()
    
    async def generate_forecast(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Прогноз на будущее"""
        # Простое прогнозирование на основе тренда
        last_7_days = self.get_business_metrics(7)
        last_14_days = self.get_business_metrics(14)
        
        # Расчет тренда
        leads_trend = (last_7_days['total_leads'] - last_14_days['total_leads']/2) / (last_14_days['total_leads']/2) * 100
        sales_trend = (last_7_days['total_sales'] - last_14_days['total_sales']/2) / (last_14_days['total_sales']/2) * 100
        
        # Прогноз
        forecast_leads = int(last_7_days['total_leads'] * (1 + leads_trend/100) * days_ahead/7)
        forecast_sales = int(last_7_days['total_sales'] * (1 + sales_trend/100) * days_ahead/7)
        forecast_revenue = forecast_sales * last_7_days['avg_sale_amount']
        
        return {
            'days_ahead': days_ahead,
            'forecast_leads': forecast_leads,
            'forecast_sales': forecast_sales,
            'forecast_revenue': round(forecast_revenue, 2),
            'leads_trend': round(leads_trend, 2),
            'sales_trend': round(sales_trend, 2)
        }
