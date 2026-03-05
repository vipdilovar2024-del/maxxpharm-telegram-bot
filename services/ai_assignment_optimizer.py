"""
🧠 AI Assignment Optimizer - AI оптимизация системы распределения заказов
Умная система как в Uber/Glovo/Amazon
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import math

from database.db import get_db_connection
from database.models import UserRole, OrderStatus
from services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)

class AIAssignmentOptimizer:
    """AI оптимизатор системы распределения заказов"""
    
    def __init__(self, bot):
        self.bot = bot
        self.assignment_service = AssignmentService(bot)
        self.logger = logging.getLogger("ai_optimizer")
    
    async def calculate_worker_score(self, worker: Dict[str, Any], order: Dict[str, Any]) -> float:
        """Рассчитывает score для работника с учетом множества факторов"""
        
        try:
            # Базовые факторы
            active_orders = worker.get("active_orders", 0)
            max_orders = worker.get("max_orders", 5)
            is_online = worker.get("is_online", False)
            
            # Временные факторы
            minutes_since_last = self._get_minutes_since_last_assignment(worker.get("last_assigned_at"))
            
            # Географические факторы
            zone_match = self._calculate_zone_match(worker.get("zone"), order.get("zone"))
            distance_factor = self._calculate_distance_factor(worker, order)
            
            # Производительность работника
            performance_factor = await self._get_performance_factor(worker["id"])
            
            # Нагрузка (чем меньше, тем лучше)
            load_factor = (active_orders / max_orders) * 10  # 0-10
            
            # Время с последнего назначения (чем дольше, тем лучше)
            time_factor = max(0, (minutes_since_last / 60) - 2)  # 0-8 часов
            
            # Совпадение зоны (чем лучше, тем лучше)
            zone_factor = zone_match * 5  # 0-5
            
            # Расстояние (чем меньше, тем лучше)
            distance_score = distance_factor * 3  # 0-15
            
            # Производительность (чем выше, тем лучше)
            performance_score = performance_factor * 2  # 0-10
            
            # Онлайн статус
            online_bonus = 5 if is_online else -10
            
            # Рассчитываем общий score (чем меньше, тем лучше)
            total_score = (
                load_factor +
                (10 - time_factor) +  # Инвертируем, так как больше времени = лучше
                (10 - zone_factor) +  # Инвертируем
                distance_score +
                (10 - performance_score) +  # Инвертируем
                online_bonus
            )
            
            # Пенальти за перегрузку
            if active_orders >= max_orders:
                total_score += 50  # Большой пенальти за перегрузку
            
            return max(0, total_score)
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating worker score: {e}")
            return 999  # Высокий score для ошибочных случаев
    
    async def get_optimal_worker_advanced(self, role: UserRole, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Получение оптимального работника с AI оптимизацией"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем всех доступных работников
            workers = await conn.fetch("""
                SELECT 
                    id, telegram_id, name, role, zone, active_orders, max_orders,
                    is_online, last_assigned_at, created_at
                FROM users
                WHERE role = $1
                AND is_active = true
                AND is_online = true
                AND (zone = $2 OR $2 IS NULL)
                ORDER BY active_orders ASC
            """, role.value, order.get("zone"))
            
            await conn.close()
            
            if not workers:
                return None
            
            # Рассчитываем score для каждого работника
            best_worker = None
            best_score = float('inf')
            worker_scores = []
            
            for worker in workers:
                worker_dict = dict(worker)
                score = await self.calculate_worker_score(worker_dict, order)
                worker_scores.append((worker_dict, score))
                
                if score < best_score:
                    best_score = score
                    best_worker = worker_dict
            
            # Логирование для анализа
            self.logger.info(f"🧠 AI Optimization for {role.value}:")
            self.logger.info(f"📊 Best worker: {best_worker['name']} with score {best_score:.2f}")
            
            # Показываем топ-3 для анализа
            worker_scores.sort(key=lambda x: x[1])
            for i, (worker, score) in enumerate(worker_scores[:3]):
                self.logger.info(f"  {i+1}. {worker['name']}: {score:.2f}")
            
            return best_worker
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI optimization: {e}")
            return None
    
    async def predict_order_completion_time(self, order: Dict[str, Any]) -> Dict[str, int]:
        """Предсказание времени завершения заказа"""
        
        try:
            # Базовые времена в минутах
            base_times = {
                "processing": 30,  # Сборка
                "checking": 15,    # Проверка
                "delivery": 45     # Доставка
            }
            
            # Факторы влияния
            factors = {
                "order_complexity": await self._get_order_complexity(order),
                "time_of_day": self._get_time_of_day_factor(),
                "worker_performance": await self._get_avg_performance_for_role("picker"),
                "zone_factor": self._get_zone_delivery_factor(order.get("zone"))
            }
            
            # Рассчитываем время для каждого этапа
            predictions = {}
            
            for stage, base_time in base_times.items():
                # Применяем факторы
                adjusted_time = base_time * factors["order_complexity"]
                adjusted_time *= factors["time_of_day"]
                adjusted_time *= factors["worker_performance"]
                adjusted_time *= factors["zone_factor"]
                
                predictions[stage] = max(5, int(adjusted_time))  # Минимум 5 минут
            
            # Общее время
            total_time = sum(predictions.values())
            
            return {
                "processing": predictions["processing"],
                "checking": predictions["checking"],
                "delivery": predictions["delivery"],
                "total": total_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting completion time: {e}")
            return {"processing": 30, "checking": 15, "delivery": 45, "total": 90}
    
    async def optimize_worker_distribution(self) -> Dict[str, Any]:
        """Оптимизация распределения работников"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем текущую нагрузку
            current_load = await conn.fetch("""
                SELECT role, COUNT(*) as total, 
                       SUM(active_orders) as total_load,
                       COUNT(CASE WHEN is_online = true THEN 1 END) as online
                FROM users
                WHERE is_active = true
                AND role IN ('picker', 'checker', 'courier')
                GROUP BY role
            """)
            
            recommendations = []
            
            for load in current_load:
                role = load["role"]
                total = load["total"]
                online = load["online"]
                total_load = load["total_load"] or 0
                
                avg_load = total_load / max(1, online)
                
                # Анализ и рекомендации
                if avg_load > 4:
                    recommendations.append({
                        "role": role,
                        "issue": "high_load",
                        "message": f"Высокая нагрузка {role}: {avg_load:.1f} заказов на работника",
                        "suggestion": "Рекомендуется увеличить количество {role} или оптимизировать распределение"
                    })
                elif avg_load < 1:
                    recommendations.append({
                        "role": role,
                        "issue": "low_load",
                        "message": f"Низкая нагрузка {role}: {avg_load:.1f} заказов на работника",
                        "suggestion": f"Можно уменьшить количество {role} или увеличить зону обслуживания"
                    })
                elif online < total * 0.7:
                    recommendations.append({
                        "role": role,
                        "issue": "low_online",
                        "message": f"Мало {role} онлайн: {online}/{total}",
                        "suggestion": "Рекомендуется проверить доступность работников"
                    })
            
            await conn.close()
            
            return {
                "current_load": [dict(load) for load in current_load],
                "recommendations": recommendations,
                "optimization_score": self._calculate_optimization_score(current_load)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing distribution: {e}")
            return {}
    
    async def get_demand_forecast(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Прогноз спроса на следующие часы"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем исторические данные за последние 7 дней
            historical_data = await conn.fetch("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as order_count,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 60) as avg_completion_time
                FROM orders
                WHERE created_at >= NOW() - INTERVAL '7 days'
                AND status = 'delivered'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """)
            
            # Текущий час
            current_hour = datetime.now().hour
            
            # Прогноз на основе исторических данных
            forecast = {}
            
            for hour_offset in range(hours_ahead):
                forecast_hour = (current_hour + hour_offset) % 24
                
                # Находим исторические данные для этого часа
                hour_data = [row for row in historical_data if int(row["hour"]) == forecast_hour]
                
                if hour_data:
                    avg_orders = sum(row["order_count"] for row in hour_data) / len(hour_data)
                    avg_time = sum(row["avg_completion_time"] or 0 for row in hour_data) / len(hour_data)
                else:
                    avg_orders = 2  # Базовое значение
                    avg_time = 60  # Базовое время
                
                # Применяем фактор дня недели
                day_factor = self._get_day_of_week_factor()
                
                forecast[f"+{hour_offset}h"] = {
                    "hour": forecast_hour,
                    "predicted_orders": int(avg_orders * day_factor),
                    "avg_completion_time": int(avg_time),
                    "required_workers": max(1, int((avg_orders * day_factor) / 3))  # 3 заказа на работника
                }
            
            await conn.close()
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"❌ Error forecasting demand: {e}")
            return {}
    
    async def auto_rebalance_if_needed(self) -> bool:
        """Автоматическая ребалансировка при необходимости"""
        
        try:
            # Получаем оптимизацию распределения
            optimization = await self.optimize_worker_distribution()
            
            # Если есть рекомендации по высокой нагрузке
            high_load_recommendations = [
                rec for rec in optimization.get("recommendations", [])
                if rec["issue"] == "high_load"
            ]
            
            if high_load_recommendations:
                self.logger.info("🔄 High load detected, initiating auto-rebalance")
                
                # Выполняем ребалансировку
                rebalanced_count = await self.assignment_service.rebalance_orders()
                
                if rebalanced_count > 0:
                    self.logger.info(f"✅ Auto-rebalanced {rebalanced_count} orders")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in auto-rebalance: {e}")
            return False
    
    # Вспомогательные методы
    def _get_minutes_since_last_assignment(self, last_assigned_at: Optional[datetime]) -> float:
        """Получение минут с последнего назначения"""
        if not last_assigned_at:
            return 999  # Большое значение для тех, кто давно не получал заказы
        
        return (datetime.now() - last_assigned_at).total_seconds() / 60
    
    def _calculate_zone_match(self, worker_zone: Optional[str], order_zone: Optional[str]) -> float:
        """Расчет совпадения зон"""
        if not worker_zone or not order_zone:
            return 0.5  # Нейтральное значение
        
        if worker_zone == order_zone:
            return 1.0  # Полное совпадение
        
        # Частичное совпадение (можно усложнить с матрицей расстояний)
        zone_distances = {
            ("центр", "север"): 0.7,
            ("центр", "юг"): 0.7,
            ("центр", "восток"): 0.7,
            ("центр", "запад"): 0.7,
            ("север", "юг"): 0.3,
            ("восток", "запад"): 0.3,
        }
        
        return zone_distances.get((worker_zone, order_zone), 0.3)
    
    def _calculate_distance_factor(self, worker: Dict[str, Any], order: Dict[str, Any]) -> float:
        """Расчет фактора расстояния"""
        # Упрощенная логика - можно заменить на реальное расстояние
        return 0.5  # Нейтральное значение
    
    async def _get_performance_factor(self, worker_id: int) -> float:
        """Получение фактора производительности работника"""
        try:
            conn = await get_db_connection()
            
            # Получаем среднюю производительность за последние 7 дней
            performance = await conn.fetchrow("""
                SELECT AVG(efficiency_score) as avg_score
                FROM worker_performance
                WHERE worker_id = $1
                AND date >= CURRENT_DATE - INTERVAL '7 days'
            """, worker_id)
            
            await conn.close()
            
            if performance and performance["avg_score"]:
                return min(2.0, performance["avg_score"] / 5.0)  # Нормализуем до 0-2
            
            return 1.0  # Базовое значение
            
        except Exception as e:
            self.logger.error(f"❌ Error getting performance factor: {e}")
            return 1.0
    
    async def _get_order_complexity(self, order: Dict[str, Any]) -> float:
        """Получение сложности заказа"""
        # Базовая сложность на основе суммы и количества товаров
        amount = order.get("amount", 0)
        
        if amount < 50:
            return 0.8  # Простые заказы
        elif amount < 150:
            return 1.0  # Средние заказы
        else:
            return 1.3  # Сложные заказы
    
    def _get_time_of_day_factor(self) -> float:
        """Фактор времени дня"""
        hour = datetime.now().hour
        
        # Пиковые часы
        if 9 <= hour <= 11 or 17 <= hour <= 19:
            return 1.2  # Высокая нагрузка
        elif 12 <= hour <= 14:
            return 1.1  # Средняя нагрузка
        else:
            return 0.9  # Низкая нагрузка
    
    async def _get_avg_performance_for_role(self, role: str) -> float:
        """Получение средней производительности для роли"""
        try:
            conn = await get_db_connection()
            
            performance = await conn.fetchrow("""
                SELECT AVG(efficiency_score) as avg_score
                FROM worker_performance
                WHERE role = $1
                AND date >= CURRENT_DATE - INTERVAL '7 days'
            """, role)
            
            await conn.close()
            
            if performance and performance["avg_score"]:
                return performance["avg_score"] / 5.0  # Нормализуем до 0-1
            
            return 1.0
            
        except Exception as e:
            self.logger.error(f"❌ Error getting avg performance: {e}")
            return 1.0
    
    def _get_zone_delivery_factor(self, zone: Optional[str]) -> float:
        """Фактор доставки по зоне"""
        zone_factors = {
            "центр": 0.8,   # Быстрее
            "север": 1.2,   # Медленнее
            "юг": 1.1,
            "восток": 1.0,
            "запад": 1.0
        }
        
        return zone_factors.get(zone, 1.0)
    
    def _calculate_optimization_score(self, current_load: List) -> float:
        """Расчет оценки оптимизации распределения"""
        if not current_load:
            return 0.0
        
        total_score = 0.0
        
        for load in current_load:
            role = load["role"]
            online = load["online"]
            total = load["total"]
            total_load = load["total_load"] or 0
            
            if online > 0:
                avg_load = total_load / online
                # Идеальная нагрузка 2-4 заказа на работника
                if 2 <= avg_load <= 4:
                    role_score = 1.0
                elif avg_load < 2:
                    role_score = 0.7  # Недогрузка
                else:
                    role_score = 0.5  # Перегрузка
            else:
                role_score = 0.0  # Никто онлайн
            
            total_score += role_score
        
        return total_score / len(current_load)
    
    def _get_day_of_week_factor(self) -> float:
        """Фактор дня недели"""
        weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        if weekday <= 4:  # Пн-Пт
            return 1.0
        elif weekday == 5:  # Сб
            return 0.8
        else:  # Вс
            return 0.6

# Удобные функции для использования
async def get_optimal_worker_with_ai(role: UserRole, order: Dict[str, Any], bot) -> Optional[Dict[str, Any]]:
    """Получение оптимального работника с AI оптимизацией"""
    optimizer = AIAssignmentOptimizer(bot)
    return await optimizer.get_optimal_worker_advanced(role, order)

async def predict_order_time(order: Dict[str, Any], bot) -> Dict[str, int]:
    """Предсказание времени выполнения заказа"""
    optimizer = AIAssignmentOptimizer(bot)
    return await optimizer.predict_order_completion_time(order)

async def optimize_distribution(bot) -> Dict[str, Any]:
    """Оптимизация распределения работников"""
    optimizer = AIAssignmentOptimizer(bot)
    return await optimizer.optimize_worker_distribution()
