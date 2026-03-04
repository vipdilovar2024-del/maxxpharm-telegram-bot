# 🧠 AI BRAIN ENGINE - MAXXPHARM CRM
# AI-ядро для управления бизнес-процессами

import asyncio
import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics

# ================================
# 📊 БАЗА ДАННЫХ ДЛЯ AI
# ================================

@dataclass
class OrderMetrics:
    """Метрики заказа"""
    id: int
    client_id: int
    created_at: datetime.datetime
    status: str
    operator_id: Optional[int]
    courier_id: Optional[int]
    delivery_time: Optional[int]  # в минутах
    price: float
    cancel_reason: Optional[str]

@dataclass
class OperatorMetrics:
    """Метрики оператора"""
    operator_id: int
    name: str
    orders_processed: int
    orders_cancelled: int
    avg_processing_time: float
    current_load: int
    efficiency_score: float

@dataclass
class SystemMetrics:
    """Общие метрики системы"""
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    avg_delivery_time: float
    conversion_rate: float
    operator_load: Dict[int, int]
    hourly_distribution: Dict[int, int]

# ================================
# 🧠 AI BRAIN ENGINE
# ================================

class AIBrainEngine:
    """Основной AI-движок для анализа и принятия решений"""
    
    def __init__(self):
        self.orders: List[OrderMetrics] = []
        self.operators: Dict[int, OperatorMetrics] = {}
        self.system_metrics: Optional[SystemMetrics] = None
        self.problems_detected: List[Dict] = []
        self.recommendations: List[Dict] = []
        self.forecasts: Dict[str, Any] = {}
        
        # Пороговые значения для детекции проблем
        self.thresholds = {
            'cancel_rate_max': 0.20,  # 20%
            'delivery_time_max': 90,   # 90 минут
            'operator_load_max': 40,   # 40 заявок
            'conversion_rate_min': 0.85 # 85%
        }
    
    async def analyze_data(self, orders_data: List[Dict]) -> SystemMetrics:
        """Анализ данных и расчет метрик"""
        print("🧠 AI: Начинаю анализ данных...")
        
        # Конвертация данных
        self.orders = [
            OrderMetrics(
                id=order['id'],
                client_id=order['client_id'],
                created_at=datetime.datetime.fromisoformat(order['created_at']),
                status=order['status'],
                operator_id=order.get('operator_id'),
                courier_id=order.get('courier_id'),
                delivery_time=order.get('delivery_time'),
                price=order['price'],
                cancel_reason=order.get('cancel_reason')
            )
            for order in orders_data
        ]
        
        # Расчет базовых метрик
        total_orders = len(self.orders)
        completed_orders = len([o for o in self.orders if o.status == 'Выполнена'])
        cancelled_orders = len([o for o in self.orders if o.status == 'Отменена'])
        
        # Среднее время доставки
        delivery_times = [o.delivery_time for o in self.orders if o.delivery_time]
        avg_delivery_time = statistics.mean(delivery_times) if delivery_times else 0
        
        # Конверсия
        conversion_rate = completed_orders / total_orders if total_orders > 0 else 0
        
        # Нагрузка операторов
        operator_load = defaultdict(int)
        for order in self.orders:
            if order.operator_id:
                operator_load[order.operator_id] += 1
        
        # Почасовое распределение
        hourly_distribution = defaultdict(int)
        for order in self.orders:
            hour = order.created_at.hour
            hourly_distribution[hour] += 1
        
        self.system_metrics = SystemMetrics(
            total_orders=total_orders,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
            avg_delivery_time=avg_delivery_time,
            conversion_rate=conversion_rate,
            operator_load=dict(operator_load),
            hourly_distribution=dict(hourly_distribution)
        )
        
        print(f"🧠 AI: Проанализировано {total_orders} заказов")
        return self.system_metrics
    
    async def detect_problems(self) -> List[Dict]:
        """Детекция проблем в системе"""
        print("🔍 AI: Ищу проблемы...")
        
        problems = []
        metrics = self.system_metrics
        
        if not metrics:
            return problems
        
        # 1. Высокий процент отмен
        cancel_rate = metrics.cancelled_orders / metrics.total_orders
        if cancel_rate > self.thresholds['cancel_rate_max']:
            problems.append({
                'type': 'high_cancel_rate',
                'severity': 'high',
                'description': f'Высокий процент отмен: {cancel_rate:.1%}',
                'current_value': cancel_rate,
                'threshold': self.thresholds['cancel_rate_max'],
                'impact': 'Потеря дохода и клиентов'
            })
        
        # 2. Медленная доставка
        if metrics.avg_delivery_time > self.thresholds['delivery_time_max']:
            problems.append({
                'type': 'slow_delivery',
                'severity': 'medium',
                'description': f'Медленная доставка: {metrics.avg_delivery_time:.0f} минут',
                'current_value': metrics.avg_delivery_time,
                'threshold': self.thresholds['delivery_time_max'],
                'impact': 'Снижение качества сервиса'
            })
        
        # 3. Перегрузка операторов
        overloaded_operators = [
            op_id for op_id, load in metrics.operator_load.items()
            if load > self.thresholds['operator_load_max']
        ]
        
        if overloaded_operators:
            problems.append({
                'type': 'operator_overload',
                'severity': 'medium',
                'description': f'Перегружены операторы: {overloaded_operators}',
                'current_value': len(overloaded_operators),
                'threshold': self.thresholds['operator_load_max'],
                'impact': 'Снижение качества обработки'
            })
        
        # 4. Низкая конверсия
        if metrics.conversion_rate < self.thresholds['conversion_rate_min']:
            problems.append({
                'type': 'low_conversion',
                'severity': 'high',
                'description': f'Низкая конверсия: {metrics.conversion_rate:.1%}',
                'current_value': metrics.conversion_rate,
                'threshold': self.thresholds['conversion_rate_min'],
                'impact': 'Потеря потенциальных клиентов'
            })
        
        self.problems_detected = problems
        print(f"🔍 AI: Найдено {len(problems)} проблем")
        return problems
    
    async def generate_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по решению проблем"""
        print("💡 AI: Генерирую рекомендации...")
        
        recommendations = []
        
        for problem in self.problems_detected:
            if problem['type'] == 'high_cancel_rate':
                recommendations.extend([
                    {
                        'type': 'process_improvement',
                        'priority': 'high',
                        'action': 'Проанализировать причины отмен',
                        'description': 'Изучить причины отмен и улучшить процесс',
                        'expected_impact': 'Снижение отмен на 30%'
                    },
                    {
                        'type': 'operator_training',
                        'priority': 'medium',
                        'action': 'Дополнительное обучение операторов',
                        'description': 'Научить операторов работать со сложными клиентами',
                        'expected_impact': 'Повышение качества обработки'
                    }
                ])
            
            elif problem['type'] == 'slow_delivery':
                recommendations.extend([
                    {
                        'type': 'resource_optimization',
                        'priority': 'high',
                        'action': 'Добавить курьеров в пиковые часы',
                        'description': f'Увеличить количество курьеров на {len(self.system_metrics.hourly_distribution)//10}',
                        'expected_impact': 'Сокращение времени доставки на 25%'
                    },
                    {
                        'type': 'route_optimization',
                        'priority': 'medium',
                        'action': 'Оптимизировать маршруты доставки',
                        'description': 'Внедрить систему оптимальных маршрутов',
                        'expected_impact': 'Экономия времени и топлива'
                    }
                ])
            
            elif problem['type'] == 'operator_overload':
                recommendations.extend([
                    {
                        'type': 'load_balancing',
                        'priority': 'high',
                        'action': 'Перераспределить нагрузку операторов',
                        'description': 'Равномерно распределить заявки между операторами',
                        'expected_impact': 'Снижение нагрузки на 40%'
                    },
                    {
                        'type': 'staff_increase',
                        'priority': 'medium',
                        'action': 'Нанять дополнительных операторов',
                        'description': 'Добавить 2-3 операторов в смену',
                        'expected_impact': 'Улучшение качества обслуживания'
                    }
                ])
            
            elif problem['type'] == 'low_conversion':
                recommendations.extend([
                    {
                        'type': 'conversion_optimization',
                        'priority': 'high',
                        'action': 'Оптимизировать воронку продаж',
                        'description': 'Улучшить процесс обработки заявок',
                        'expected_impact': 'Повышение конверсии на 20%'
                    }
                ])
        
        self.recommendations = recommendations
        print(f"💡 AI: Сгенерировано {len(recommendations)} рекомендаций")
        return recommendations
    
    async def forecast_metrics(self) -> Dict[str, Any]:
        """Прогнозирование метрик"""
        print("🔮 AI: Делаю прогноз...")
        
        if not self.system_metrics:
            return {}
        
        # Простой прогноз на основе трендов
        current_metrics = self.system_metrics
        
        # Прогноз заказов на завтра
        avg_daily_orders = current_metrics.total_orders / 30  # предположим, данные за месяц
        tomorrow_orders = int(avg_daily_orders * 1.1)  # +10% тренд
        
        # Прогноз загрузки операторов
        total_operators = len(current_metrics.operator_load)
        avg_load_per_operator = avg_daily_orders / total_operators if total_operators > 0 else 0
        
        forecast = {
            'tomorrow_orders': tomorrow_orders,
            'expected_load_per_operator': avg_load_per_operator,
            'risk_level': 'low' if avg_load_per_operator < 30 else 'medium' if avg_load_per_operator < 50 else 'high',
            'recommended_staff': max(total_operators, int(tomorrow_orders / 35)),
            'peak_hours': [hour for hour, count in sorted(current_metrics.hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]]
        }
        
        self.forecasts = forecast
        print(f"🔮 AI: Прогноз на завтра - {tomorrow_orders} заказов")
        return forecast
    
    async def generate_report(self) -> str:
        """Генерация AI-отчета"""
        print("📊 AI: Создаю отчет...")
        
        if not self.system_metrics:
            return "📊 Недостаточно данных для анализа"
        
        metrics = self.system_metrics
        problems = self.problems_detected
        recommendations = self.recommendations
        forecast = self.forecasts
        
        report = (
            f"📊 <b>AI-отчет MAXXPHARM</b>\n\n"
            f"📈 <b>Общие метрики:</b>\n"
            f"📦 Всего заказов: {metrics.total_orders}\n"
            f"✅ Выполнено: {metrics.completed_orders}\n"
            f"❌ Отменено: {metrics.cancelled_orders}\n"
            f"🔄 Конверсия: {metrics.conversion_rate:.1%}\n"
            f"⏱️ Среднее время доставки: {metrics.avg_delivery_time:.0f} мин\n\n"
        )
        
        if problems:
            report += f"🚨 <b>Обнаруженные проблемы ({len(problems)}):</b>\n\n"
            for i, problem in enumerate(problems, 1):
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                report += f"{i}. {severity_emoji.get(problem['severity'], '⚪')} {problem['description']}\n"
            report += "\n"
        
        if recommendations:
            report += f"💡 <b>Рекомендации ({len(recommendations)}):</b>\n\n"
            for i, rec in enumerate(recommendations[:3], 1):  # Только топ-3
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                report += f"{i}. {priority_emoji.get(rec['priority'], '⚪')} {rec['action']}\n"
            report += "\n"
        
        if forecast:
            report += (
                f"🔮 <b>Прогноз на завтра:</b>\n\n"
                f"📦 Ожидаемые заказы: {forecast['tomorrow_orders']}\n"
                f"👥 Рекомендуемый персонал: {forecast['recommended_staff']}\n"
                f"⚠️ Уровень риска: {forecast['risk_level']}\n"
                f"🕐 Пиковые часы: {', '.join(map(str, forecast['peak_hours']))}\n\n"
            )
        
        report += f"🤖 <b>AI Brain Engine</b>\n"
        report += f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return report

# ================================
# 🤖 AI-АГЕНТЫ
# ================================

class AIOperationsManager:
    """AI-менеджер операций"""
    
    def __init__(self, brain: AIBrainEngine):
        self.brain = brain
    
    async def optimize_operations(self) -> Dict[str, Any]:
        """Оптимизация операций"""
        print("🎯 AI Operations Manager: Оптимизирую операции...")
        
        # Анализ текущей ситуации
        await self.brain.analyze_data([])
        await self.brain.detect_problems()
        await self.brain.generate_recommendations()
        
        # Формирование плана действий
        optimization_plan = {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_strategy': []
        }
        
        for problem in self.brain.problems_detected:
            if problem['severity'] == 'high':
                optimization_plan['immediate_actions'].append({
                    'problem': problem['description'],
                    'action': 'Требуется немедленное вмешательство',
                    'deadline': '2 часа'
                })
        
        return optimization_plan

class AIAnalyst:
    """AI-аналитик"""
    
    def __init__(self, brain: AIBrainEngine):
        self.brain = brain
    
    async def deep_analysis(self) -> Dict[str, Any]:
        """Глубокий анализ данных"""
        print("📈 AI Analyst: Провожу глубокий анализ...")
        
        analysis = {
            'trends': {},
            'patterns': {},
            'insights': []
        }
        
        # Анализ трендов
        if self.brain.system_metrics:
            metrics = self.brain.system_metrics
            
            # Тренд по часам
            peak_hours = sorted(metrics.hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis['trends']['peak_hours'] = peak_hours
            
            # Анализ эффективности
            if metrics.total_orders > 0:
                analysis['insights'].append(
                    f"Пиковая нагрузка в {peak_hours[0][0]}:00 - {peak_hours[0][1]} заказов"
                )
        
        return analysis

class AIStrategyAdvisor:
    """AI-стратегический советник"""
    
    def __init__(self, brain: AIBrainEngine):
        self.brain = brain
    
    async def generate_strategy(self) -> Dict[str, Any]:
        """Генерация стратегии"""
        print("🎯 AI Strategy Advisor: Разрабатываю стратегию...")
        
        strategy = {
            'growth_opportunities': [],
            'risk_mitigation': [],
            'innovation_suggestions': []
        }
        
        # Анализ возможностей роста
        if self.brain.system_metrics:
            metrics = self.brain.system_metrics
            
            if metrics.conversion_rate < 0.9:
                strategy['growth_opportunities'].append({
                    'area': 'Конверсия',
                    'potential': f"+{(0.9 - metrics.conversion_rate) * 100:.1f}%",
                    'actions': ['Оптимизация воронки', 'Обучение персонала']
                })
            
            if metrics.avg_delivery_time > 60:
                strategy['growth_opportunities'].append({
                    'area': 'Доставка',
                    'potential': 'Сокращение времени на 30%',
                    'actions': ['Оптимизация маршрутов', 'Увеличение курьеров']
                })
        
        return strategy

# ================================
# 🚀 ГЛАВНЫЙ AI-КОНТРОЛЛЕР
# ================================

class AIController:
    """Главный AI-контроллер системы"""
    
    def __init__(self):
        self.brain = AIBrainEngine()
        self.operations_manager = AIOperationsManager(self.brain)
        self.analyst = AIAnalyst(self.brain)
        self.strategy_advisor = AIStrategyAdvisor(self.brain)
        
        print("🧠 AI Controller: Инициализация завершена")
    
    async def full_analysis_cycle(self, orders_data: List[Dict]) -> Dict[str, Any]:
        """Полный цикл анализа"""
        print("🔄 AI Controller: Запускаю полный анализ...")
        
        # 1. Анализ данных
        metrics = await self.brain.analyze_data(orders_data)
        
        # 2. Детекция проблем
        problems = await self.brain.detect_problems()
        
        # 3. Генерация рекомендаций
        recommendations = await self.brain.generate_recommendations()
        
        # 4. Прогнозирование
        forecast = await self.brain.forecast_metrics()
        
        # 5. Глубокий анализ
        deep_analysis = await self.analyst.deep_analysis()
        
        # 6. Оптимизация операций
        optimization = await self.operations_manager.optimize_operations()
        
        # 7. Стратегия
        strategy = await self.strategy_advisor.generate_strategy()
        
        # 8. Генерация отчета
        report = await self.brain.generate_report()
        
        result = {
            'metrics': metrics,
            'problems': problems,
            'recommendations': recommendations,
            'forecast': forecast,
            'deep_analysis': deep_analysis,
            'optimization': optimization,
            'strategy': strategy,
            'report': report
        }
        
        print("🧠 AI Controller: Анализ завершен")
        return result

# ================================
# 🎯 ИНИЦИАЛИЗАЦИЯ AI
# ================================

# Глобальный AI-контроллер
ai_controller = AIController()

# Функция для запуска AI-анализа
async def run_ai_analysis(orders_data: List[Dict] = None) -> Dict[str, Any]:
    """Запуск полного AI-анализа"""
    if orders_data is None:
        # Тестовые данные
        orders_data = [
            {
                'id': 1,
                'client_id': 123,
                'created_at': '2024-03-04T10:30:00',
                'status': 'Выполнена',
                'operator_id': 1,
                'courier_id': 2,
                'delivery_time': 45,
                'price': 1500.0,
                'cancel_reason': None
            },
            {
                'id': 2,
                'client_id': 124,
                'created_at': '2024-03-04T11:15:00',
                'status': 'Отменена',
                'operator_id': 1,
                'courier_id': None,
                'delivery_time': None,
                'price': 800.0,
                'cancel_reason': 'Долгое ожидание'
            }
        ]
    
    return await ai_controller.full_analysis_cycle(orders_data)

print("🧠 AI Brain Engine готов к работе!")
