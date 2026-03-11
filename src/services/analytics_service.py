"""
📊 Сервис аналитики MAXXPHARM CRM с AI
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..models.database import (
    Order, OrderStatus, User, UserRole, Payment, 
    PaymentType, Debt, ActivityLog
)
from ..config import settings


class AnalyticsService:
    """Сервис для аналитики и AI отчетов"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Генерация ежедневного отчета"""
        
        if date is None:
            date = datetime.utcnow()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Статистика заказов за день
        orders_result = await self.session.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= start_of_day,
                    Order.created_at <= end_of_day
                )
            )
        )
        total_orders = orders_result.scalar() or 0
        
        # Статистика по статусам
        status_stats = {}
        for status in OrderStatus:
            status_result = await self.session.execute(
                select(func.count(Order.id))
                .where(
                    and_(
                        Order.status == status.value,
                        Order.created_at >= start_of_day,
                        Order.created_at <= end_of_day
                    )
                )
            )
            status_stats[status.value] = status_result.scalar() or 0
        
        # Финансовая статистика
        revenue_result = await self.session.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.status == OrderStatus.DELIVERED.value,
                    Order.delivered_at >= start_of_day,
                    Order.delivered_at <= end_of_day
                )
            )
        )
        total_revenue = revenue_result.scalar() or 0
        
        # Статистика оплат
        payments_result = await self.session.execute(
            select(func.sum(Payment.amount))
            .where(
                and_(
                    Payment.created_at >= start_of_day,
                    Payment.created_at <= end_of_day
                )
            )
        )
        total_payments = payments_result.scalar() or 0
        
        # Статистика долгов
        debts_result = await self.session.execute(
            select(func.sum(Debt.remaining_amount))
            .where(
                and_(
                    Debt.created_at >= start_of_day,
                    Debt.created_at <= end_of_day
                )
            )
        )
        total_debts = debts_result.scalar() or 0
        
        # Эффективность сотрудников
        employee_stats = await self._get_employee_efficiency(start_of_day, end_of_day)
        
        report = {
            'date': date.strftime('%d.%m.%Y'),
            'total_orders': total_orders,
            'confirmed_orders': status_stats.get(OrderStatus.CONFIRMED.value, 0),
            'rejected_orders': status_stats.get(OrderStatus.REJECTED.value, 0),
            'collected_orders': status_stats.get(OrderStatus.COLLECTED.value, 0),
            'delivered_orders': status_stats.get(OrderStatus.DELIVERED.value, 0),
            'total_revenue': float(total_revenue),
            'total_payments': float(total_payments),
            'total_debts': float(total_debts),
            'confirmation_rate': self._calculate_rate(
                status_stats.get(OrderStatus.CONFIRMED.value, 0),
                status_stats.get(OrderStatus.CREATED.value, 0)
            ),
            'delivery_rate': self._calculate_rate(
                status_stats.get(OrderStatus.DELIVERED.value, 0),
                status_stats.get(OrderStatus.CONFIRMED.value, 0)
            ),
            'employee_stats': employee_stats
        }
        
        return report
    
    async def get_weekly_report(self, start_date: datetime = None) -> Dict[str, Any]:
        """Генерация недельного отчета"""
        
        if start_date is None:
            today = datetime.utcnow().date()
            start_date = datetime.combine(
                today - timedelta(days=today.weekday()),
                datetime.min.time()
            )
        
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # Собираем ежедневные отчеты
        daily_reports = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            daily_report = await self.get_daily_report(
                datetime.combine(current_date, datetime.min.time())
            )
            daily_reports.append(daily_report)
            current_date += timedelta(days=1)
        
        # Агрегируем данные
        weekly_total = {
            'total_orders': sum(report['total_orders'] for report in daily_reports),
            'confirmed_orders': sum(report['confirmed_orders'] for report in daily_reports),
            'rejected_orders': sum(report['rejected_orders'] for report in daily_reports),
            'delivered_orders': sum(report['delivered_orders'] for report in daily_reports),
            'total_revenue': sum(report['total_revenue'] for report in daily_reports),
            'total_payments': sum(report['total_payments'] for report in daily_reports),
            'total_debts': sum(report['total_debts'] for report in daily_reports)
        }
        
        # Рассчитываем средние значения
        avg_daily_orders = weekly_total['total_orders'] / 7 if weekly_total['total_orders'] > 0 else 0
        avg_daily_revenue = weekly_total['total_revenue'] / 7 if weekly_total['total_revenue'] > 0 else 0
        
        return {
            'period': f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            'daily_reports': daily_reports,
            'weekly_total': weekly_total,
            'avg_daily_orders': round(avg_daily_orders, 1),
            'avg_daily_revenue': round(avg_daily_revenue, 2),
            'weekly_confirmation_rate': self._calculate_rate(
                weekly_total['confirmed_orders'],
                weekly_total['total_orders']
            ),
            'weekly_delivery_rate': self._calculate_rate(
                weekly_total['delivered_orders'],
                weekly_total['confirmed_orders']
            )
        }
    
    async def get_monthly_report(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """Генерация месячного отчета"""
        
        if year is None:
            year = datetime.utcnow().year
        if month is None:
            month = datetime.utcnow().month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Статистика за месяц
        orders_result = await self.session.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
        )
        total_orders = orders_result.scalar() or 0
        
        # Выручка за месяц
        revenue_result = await self.session.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.status == OrderStatus.DELIVERED.value,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
        )
        total_revenue = revenue_result.scalar() or 0
        
        # Топ клиенты
        top_clients = await self._get_top_clients(start_date, end_date)
        
        # Топ товары (простая реализация)
        top_products = await self._get_top_products(start_date, end_date)
        
        return {
            'period': start_date.strftime('%B %Y'),
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'avg_daily_orders': round(total_orders / 30, 1),
            'avg_daily_revenue': round(float(total_revenue) / 30, 2),
            'top_clients': top_clients,
            'top_products': top_products
        }
    
    async def generate_ai_report(self, report_type: str = 'daily') -> str:
        """Генерация AI отчета с помощью ChatGPT"""
        
        if not settings.openai_api_key:
            return "❌ AI API ключ не настроен"
        
        try:
            # Получаем данные для отчета
            if report_type == 'daily':
                data = await self.get_daily_report()
                prompt = self._create_daily_ai_prompt(data)
            elif report_type == 'weekly':
                data = await self.get_weekly_report()
                prompt = self._create_weekly_ai_prompt(data)
            elif report_type == 'monthly':
                data = await self.get_monthly_report()
                prompt = self._create_monthly_ai_prompt(data)
            else:
                return "❌ Неизвестный тип отчета"
            
            # Генерируем отчет с помощью AI
            ai_report = await self._call_openai_api(prompt)
            
            return ai_report
            
        except Exception as e:
            return f"❌ Ошибка генерации AI отчета: {str(e)}"
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Вызов OpenAI API"""
        
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты - аналитик CRM системы MAXXPHARM. Создавай профессиональные и информативные отчеты на русском языке."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _create_daily_ai_prompt(self, data: Dict[str, Any]) -> str:
        """Создание промпта для ежедневного отчета"""
        
        prompt = f"""
Проанализируй данные за {data['date']} и создай краткий, но информативный отчет для руководства:

📊 Данные:
- Всего заказов: {data['total_orders']}
- Подтверждено: {data['confirmed_orders']}
- Отклонено: {data['rejected_orders']}
- Собрано: {data['collected_orders']}
- Доставлено: {data['delivered_orders']}
- Общая выручка: {data['total_revenue']:.2f} сомони
- Оплачено: {data['total_payments']:.2f} сомони
- Долги: {data['total_debts']:.2f} сомони
- Процент подтверждения: {data['confirmation_rate']:.1f}%
- Процент доставки: {data['delivery_rate']:.1f}%

👥 Эффективность сотрудников:
{self._format_employee_stats(data['employee_stats'])}

Создай отчет в формате:
1. Ключевые показатели
2. Проблемы и решения
3. Рекомендации
4. Прогноз на завтра

Отчет должен быть кратким, профессиональным и содержать конкретные цифры.
        """
        
        return prompt
    
    def _create_weekly_ai_prompt(self, data: Dict[str, Any]) -> str:
        """Создание промпта для недельного отчета"""
        
        prompt = f"""
Проанализируй данные за неделю {data['period']} и создай стратегический отчет:

📊 Недельные итоги:
- Всего заказов: {data['weekly_total']['total_orders']}
- Доставлено: {data['weekly_total']['delivered_orders']}
- Общая выручка: {data['weekly_total']['total_revenue']:.2f} сомони
- Средне заказов в день: {data['avg_daily_orders']}
- Средняя выручка в день: {data['avg_daily_revenue']:.2f} сомони
- Процент подтверждения: {data['weekly_confirmation_rate']:.1f}%
- Процент доставки: {data['weekly_delivery_rate']:.1f}%

Создай стратегический отчет включающий:
1. Анализ динамики по дням
2. Выявленные тренды
3. Эффективность команды
4. Рекомендации по оптимизации
5. Прогноз на следующую неделю

Отчет должен быть аналитическим и содержать выводы для принятия управленческих решений.
        """
        
        return prompt
    
    def _create_monthly_ai_prompt(self, data: Dict[str, Any]) -> str:
        """Создание промпта для месячного отчета"""
        
        prompt = f"""
Проанализируй данные за {data['period']} и создай комплексный бизнес-отчет:

📊 Месячные итоги:
- Всего заказов: {data['total_orders']}
- Общая выручка: {data['total_revenue']:.2f} сомони
- Средне заказов в день: {data['avg_daily_orders']}
- Средняя выручка в день: {data['avg_daily_revenue']:.2f} сомони

👥 Топ клиенты:
{self._format_top_clients(data['top_clients'])}

💊 Топ товары:
{self._format_top_products(data['top_products'])}

Создай бизнес-отчет включающий:
1. Финансовый анализ
2. Анализ клиентской базы
3. Анализ ассортимента
4. Операционная эффективность
5. Стратегические рекомендации
6. Прогноз на следующий месяц

Отчет должен быть подробным и содержать конкретные бизнес-выводы.
        """
        
        return prompt
    
    async def _get_employee_efficiency(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Получение эффективности сотрудников"""
        
        # Эффективность операторов
        operators_result = await self.session.execute(
            select(
                User.full_name,
                func.count(Order.id).label('orders_processed'),
                func.sum(Order.total_amount).label('total_revenue')
            )
            .join(Order, User.id == Order.operator_id)
            .where(
                and_(
                    User.role == UserRole.OPERATOR.value,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .group_by(User.id, User.full_name)
        )
        
        operators = operators_result.all()
        
        # Эффективность курьеров
        couriers_result = await self.session.execute(
            select(
                User.full_name,
                func.count(Order.id).label('orders_delivered'),
                func.sum(Order.total_amount).label('total_revenue')
            )
            .join(Order, User.id == Order.courier_id)
            .where(
                and_(
                    User.role == UserRole.COURIER.value,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .group_by(User.id, User.full_name)
        )
        
        couriers = couriers_result.all()
        
        return {
            'operators': [
                {
                    'name': op.full_name,
                    'orders_processed': op.orders_processed,
                    'total_revenue': float(op.total_revenue or 0)
                }
                for op in operators
            ],
            'couriers': [
                {
                    'name': courier.full_name,
                    'orders_delivered': courier.orders_delivered,
                    'total_revenue': float(courier.total_revenue or 0)
                }
                for courier in couriers
            ]
        }
    
    async def _get_top_clients(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение топ клиентов"""
        
        result = await self.session.execute(
            select(
                User.full_name,
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_amount')
            )
            .join(Order, User.id == Order.client_id)
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .group_by(User.id, User.full_name)
            .order_by(func.sum(Order.total_amount).desc())
            .limit(limit)
        )
        
        return [
            {
                'name': client.full_name,
                'order_count': client.order_count,
                'total_amount': float(client.total_amount or 0)
            }
            for client in result.all()
        ]
    
    async def _get_top_products(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение топ товаров (упрощенная версия)"""
        
        # Это упрощенная реализация
        # В реальной системе нужно анализировать OrderItem
        return [
            {'name': 'Парацетамол', 'quantity': 150, 'revenue': 6750.0},
            {'name': 'Ибупрофен', 'quantity': 120, 'revenue': 9600.0},
            {'name': 'Витамин D3', 'quantity': 200, 'revenue': 12000.0}
        ]
    
    def _calculate_rate(self, numerator: int, denominator: int) -> float:
        """Расчет процента"""
        if denominator == 0:
            return 0.0
        return (numerator / denominator) * 100
    
    def _format_employee_stats(self, stats: Dict[str, Any]) -> str:
        """Форматирование статистики сотрудников"""
        
        text = ""
        
        if stats['operators']:
            text += "\n🔹 Операторы:\n"
            for op in stats['operators']:
                text += f"• {op['name']}: {op['orders_processed']} заказов\n"
        
        if stats['couriers']:
            text += "\n🚚 Курьеры:\n"
            for courier in stats['couriers']:
                text += f"• {courier['name']}: {courier['orders_delivered']} доставок\n"
        
        return text
    
    def _format_top_clients(self, clients: List[Dict[str, Any]]) -> str:
        """Форматирование топ клиентов"""
        
        if not clients:
            return "Нет данных"
        
        text = ""
        for i, client in enumerate(clients[:5], 1):
            text += f"{i}. {client['name']}: {client['order_count']} заказов, {client['total_amount']:.2f} сомони\n"
        
        return text
    
    def _format_top_products(self, products: List[Dict[str, Any]]) -> str:
        """Форматирование топ товаров"""
        
        if not products:
            return "Нет данных"
        
        text = ""
        for i, product in enumerate(products[:5], 1):
            text += f"{i}. {product['name']}: {product['quantity']} шт., {product['revenue']:.2f} сомони\n"
        
        return text


# Функция для получения сервиса
async def get_analytics_service() -> AnalyticsService:
    """Получение экземпляра AnalyticsService"""
    from ..database import get_db
    
    async for session in get_db():
        return AnalyticsService(session)
