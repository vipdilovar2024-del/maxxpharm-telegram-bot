# 🔄 DATA PIPELINE - MAXXPHARM
# Автоматический сбор и обработка данных

import asyncio
import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from collections import defaultdict
import statistics

# Импорты наших модулей
import database
import ai_brain

# ================================
# 📊 КОНФИГУРАЦИЯ PIPELINE
# ================================

PIPELINE_CONFIG = {
    'collection_interval': 300,  # 5 минут
    'analysis_interval': 1800,   # 30 минут
    'cleanup_interval': 3600,    # 1 час
    'notification_threshold': 0.8,  # 80% для уведомлений
    'max_data_points': 1000,     # Максимум точек для анализа
    'retention_days': 90          # Хранение данных в днях
}

logger = logging.getLogger(__name__)

# ================================
# 📋 МОДЕЛИ ДАННЫХ PIPELINE
# ================================

@dataclass
class DataPoint:
    """Точка данных для сбора"""
    timestamp: datetime.datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]

@dataclass
class PipelineMetrics:
    """Метрики pipeline"""
    total_data_points: int
    processed_points: int
    failed_points: int
    last_run: datetime.datetime
    processing_time: float

@dataclass
class Alert:
    """Уведомление о проблеме"""
    id: str
    type: str
    severity: str
    message: str
    timestamp: datetime.datetime
    resolved: bool = False

# ================================
# 🔄 DATA COLLECTOR
# ================================

class DataCollector:
    """Сборщик данных из различных источников"""
    
    def __init__(self):
        self.metrics = PipelineMetrics(0, 0, 0, datetime.datetime.now(), 0.0)
        self.alerts: List[Alert] = []
    
    async def collect_order_metrics(self) -> List[DataPoint]:
        """Сбор метрик заказов"""
        try:
            db = await database.get_db()
            analytics = await db.get_orders_analytics(days=1)
            
            data_points = []
            now = datetime.datetime.now()
            
            # Базовые метрики заказов
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='total_orders_daily',
                value=analytics.get('total_orders', 0),
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='completed_orders_daily',
                value=analytics.get('completed_orders', 0),
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='cancelled_orders_daily',
                value=analytics.get('cancelled_orders', 0),
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            # Конверсия
            total = analytics.get('total_orders', 0)
            completed = analytics.get('completed_orders', 0)
            conversion_rate = (completed / total * 100) if total > 0 else 0
            
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='conversion_rate_daily',
                value=conversion_rate,
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            # Среднее время доставки
            avg_delivery = analytics.get('avg_delivery_time', 0)
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='avg_delivery_time_daily',
                value=avg_delivery,
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            # Средний чек
            avg_price = analytics.get('avg_price', 0)
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='avg_order_value_daily',
                value=avg_price,
                metadata={'source': 'orders', 'period': 'daily'}
            ))
            
            logger.info(f"📊 Collected {len(data_points)} order metrics")
            return data_points
            
        except Exception as e:
            logger.error(f"❌ Error collecting order metrics: {e}")
            return []
    
    async def collect_user_metrics(self) -> List[DataPoint]:
        """Сбор метрик пользователей"""
        try:
            db = await database.get_db()
            users = await db.get_all_users()
            sessions = await db.get_active_sessions()
            
            data_points = []
            now = datetime.datetime.now()
            
            # Общее количество пользователей
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='total_users',
                value=len(users),
                metadata={'source': 'users', 'period': 'total'}
            ))
            
            # Активные сессии
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='active_sessions',
                value=len(sessions),
                metadata={'source': 'sessions', 'period': 'current'}
            ))
            
            # Распределение по ролям
            role_counts = defaultdict(int)
            for user in users:
                role_counts[user.role] += 1
            
            for role, count in role_counts.items():
                data_points.append(DataPoint(
                    timestamp=now,
                    metric_type=f'users_by_role_{role}',
                    value=count,
                    metadata={'source': 'users', 'role': role}
                ))
            
            # Заблокированные пользователи
            blocked_count = len([u for u in users if u.blocked])
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='blocked_users',
                value=blocked_count,
                metadata={'source': 'users', 'period': 'total'}
            ))
            
            logger.info(f"👥 Collected {len(data_points)} user metrics")
            return data_points
            
        except Exception as e:
            logger.error(f"❌ Error collecting user metrics: {e}")
            return []
    
    async def collect_system_metrics(self) -> List[DataPoint]:
        """Сбор системных метрик"""
        try:
            data_points = []
            now = datetime.datetime.now()
            
            # Метрики AI-анализа
            db = await database.get_db()
            ai_metrics = await db.get_ai_metrics(hours=24)
            
            # Количество AI-анализов за сутки
            analysis_count = len([m for m in ai_metrics if m.metric_type == 'ai_analysis'])
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='ai_analyses_daily',
                value=analysis_count,
                metadata={'source': 'ai', 'period': 'daily'}
            ))
            
            # Среднее время обработки AI
            if analysis_count > 0:
                processing_times = [m.details.get('processing_time', 0) for m in ai_metrics if m.metric_type == 'ai_analysis']
                avg_processing_time = statistics.mean(processing_times) if processing_times else 0
                data_points.append(DataPoint(
                    timestamp=now,
                    metric_type='avg_ai_processing_time',
                    value=avg_processing_time,
                    metadata={'source': 'ai', 'period': 'daily'}
                ))
            
            # Метрики pipeline
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='pipeline_processing_time',
                value=self.metrics.processing_time,
                metadata={'source': 'pipeline', 'period': 'current'}
            ))
            
            data_points.append(DataPoint(
                timestamp=now,
                metric_type='pipeline_success_rate',
                value=(self.metrics.processed_points / self.metrics.total_data_points * 100) if self.metrics.total_data_points > 0 else 100,
                metadata={'source': 'pipeline', 'period': 'current'}
            ))
            
            logger.info(f"🔧 Collected {len(data_points)} system metrics")
            return data_points
            
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
            return []
    
    async def collect_all_metrics(self) -> List[DataPoint]:
        """Сбор всех метрик"""
        logger.info("🔄 Starting data collection...")
        
        all_data_points = []
        
        # Параллельный сбор метрик
        tasks = [
            self.collect_order_metrics(),
            self.collect_user_metrics(),
            self.collect_system_metrics()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Collection error: {result}")
                self.metrics.failed_points += 1
            else:
                all_data_points.extend(result)
                self.metrics.processed_points += len(result)
        
        self.metrics.total_data_points += len(all_data_points)
        self.metrics.last_run = datetime.datetime.now()
        
        logger.info(f"📊 Collected {len(all_data_points)} total data points")
        return all_data_points

# ================================
# 🧠 DATA PROCESSOR
# ================================

class DataProcessor:
    """Обработчик данных и запуск AI-анализа"""
    
    def __init__(self):
        self.ai_controller = ai_brain.ai_controller
        self.last_analysis = None
    
    async def process_data_points(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """Обработка точек данных"""
        logger.info(f"🧠 Processing {len(data_points)} data points...")
        
        # Группировка данных по типам
        grouped_data = defaultdict(list)
        for point in data_points:
            grouped_data[point.metric_type].append(point)
        
        # Сохранение метрик в базу данных
        db = await database.get_db()
        saved_metrics = 0
        
        for metric_type, points in grouped_data.items():
            for point in points:
                success = await db.save_ai_metric(
                    metric_type=point.metric_type,
                    value=point.value,
                    details=point.metadata
                )
                if success:
                    saved_metrics += 1
        
        logger.info(f"💾 Saved {saved_metrics} metrics to database")
        
        # Подготовка данных для AI-анализа
        ai_data = await self.prepare_ai_data(grouped_data)
        
        return {
            'processed_points': len(data_points),
            'saved_metrics': saved_metrics,
            'ai_data': ai_data,
            'timestamp': datetime.datetime.now()
        }
    
    async def prepare_ai_data(self, grouped_data: Dict[str, List[DataPoint]]) -> List[Dict]:
        """Подготовка данных для AI-анализа"""
        try:
            db = await database.get_db()
            orders = await db.get_orders(limit=100)
            
            # Конвертация заказов в формат для AI
            ai_orders = []
            for order in orders:
                ai_orders.append({
                    'id': order.id,
                    'client_id': order.client_id,
                    'created_at': order.created_at.isoformat(),
                    'status': order.status,
                    'operator_id': order.operator_id,
                    'courier_id': order.courier_id,
                    'delivery_time': order.delivery_time,
                    'price': float(order.price),
                    'cancel_reason': order.cancel_reason
                })
            
            return ai_orders
            
        except Exception as e:
            logger.error(f"❌ Error preparing AI data: {e}")
            return []
    
    async def run_ai_analysis(self, ai_data: List[Dict]) -> Dict[str, Any]:
        """Запуск AI-анализа"""
        logger.info("🧠 Running AI analysis...")
        
        try:
            analysis_result = await self.ai_controller.full_analysis_cycle(ai_data)
            self.last_analysis = analysis_result
            
            # Сохранение результатов анализа
            db = await database.get_db()
            await db.save_ai_metric(
                metric_type='ai_analysis',
                value=1.0,
                details={
                    'problems_count': len(analysis_result.get('problems', [])),
                    'recommendations_count': len(analysis_result.get('recommendations', [])),
                    'processing_time': analysis_result.get('processing_time', 0),
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            logger.info("✅ AI analysis completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error in AI analysis: {e}")
            return {}

# ================================
# 🚨 ALERT MANAGER
# ================================

class AlertManager:
    """Менеджер уведомлений о проблемах"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.notification_queue = asyncio.Queue()
    
    async def check_thresholds(self, data_points: List[DataPoint]) -> List[Alert]:
        """Проверка пороговых значений"""
        alerts = []
        
        for point in data_points:
            alert = await self.evaluate_threshold(point)
            if alert:
                alerts.append(alert)
        
        if alerts:
            self.alerts.extend(alerts)
            await self.send_notifications(alerts)
        
        return alerts
    
    async def evaluate_threshold(self, point: DataPoint) -> Optional[Alert]:
        """Оценка порогового значения"""
        thresholds = {
            'conversion_rate_daily': {'min': 85, 'severity': 'high'},
            'avg_delivery_time_daily': {'max': 90, 'severity': 'medium'},
            'pipeline_success_rate': {'min': 95, 'severity': 'medium'},
            'ai_analyses_daily': {'min': 1, 'severity': 'low'}
        }
        
        if point.metric_type in thresholds:
            threshold = thresholds[point.metric_type]
            
            if 'min' in threshold and point.value < threshold['min']:
                return Alert(
                    id=f"{point.metric_type}_{point.timestamp.isoformat()}",
                    type=point.metric_type,
                    severity=threshold['severity'],
                    message=f"Низкое значение {point.metric_type}: {point.value:.1f} (порог: {threshold['min']})",
                    timestamp=point.timestamp
                )
            
            if 'max' in threshold and point.value > threshold['max']:
                return Alert(
                    id=f"{point.metric_type}_{point.timestamp.isoformat()}",
                    type=point.metric_type,
                    severity=threshold['severity'],
                    message=f"Высокое значение {point.metric_type}: {point.value:.1f} (порог: {threshold['max']})",
                    timestamp=point.timestamp
                )
        
        return None
    
    async def send_notifications(self, alerts: List[Alert]):
        """Отправка уведомлений"""
        for alert in alerts:
            await self.notification_queue.put(alert)
    
    async def process_notifications(self):
        """Обработка очереди уведомлений"""
        while True:
            try:
                alert = await self.notification_queue.get()
                await self.send_alert_notification(alert)
                self.notification_queue.task_done()
            except Exception as e:
                logger.error(f"❌ Error processing notification: {e}")
    
    async def send_alert_notification(self, alert: Alert):
        """Отправка уведомления об алерте"""
        # Здесь будет интеграция с Telegram для отправки уведомлений
        logger.warning(f"🚨 ALERT: {alert.message}")
        
        # TODO: Интеграция с Telegram bot для отправки уведомлений администраторам

# ================================
# 🔄 DATA PIPELINE MANAGER
# ================================

class DataPipelineManager:
    """Главный менеджер data pipeline"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.processor = DataProcessor()
        self.alert_manager = AlertManager()
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Запуск pipeline"""
        if self.running:
            logger.warning("⚠️ Pipeline is already running")
            return
        
        self.running = True
        logger.info("🚀 Starting Data Pipeline...")
        
        # Запуск задач
        self.tasks = [
            asyncio.create_task(self.collection_loop()),
            asyncio.create_task(self.analysis_loop()),
            asyncio.create_task(self.cleanup_loop()),
            asyncio.create_task(self.alert_manager.process_notifications())
        ]
        
        logger.info("✅ Data Pipeline started successfully")
    
    async def stop(self):
        """Остановка pipeline"""
        self.running = False
        
        # Отмена задач
        for task in self.tasks:
            task.cancel()
        
        # Ожидание завершения
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("🛑 Data Pipeline stopped")
    
    async def collection_loop(self):
        """Цикл сбора данных"""
        while self.running:
            try:
                logger.info("🔄 Starting data collection cycle...")
                
                # Сбор данных
                data_points = await self.collector.collect_all_metrics()
                
                # Обработка данных
                if data_points:
                    await self.processor.process_data_points(data_points)
                    
                    # Проверка порогов
                    await self.alert_manager.check_thresholds(data_points)
                
                # Ожидание следующего цикла
                await asyncio.sleep(PIPELINE_CONFIG['collection_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in collection loop: {e}")
                await asyncio.sleep(60)  # Минутная пауза при ошибке
    
    async def analysis_loop(self):
        """Цикл AI-анализа"""
        while self.running:
            try:
                logger.info("🧠 Starting AI analysis cycle...")
                
                # Получение данных для анализа
                db = await database.get_db()
                orders = await db.get_orders(limit=100)
                
                ai_data = await self.processor.prepare_ai_data({'orders': orders})
                
                if ai_data:
                    await self.processor.run_ai_analysis(ai_data)
                
                # Ожидание следующего цикла
                await asyncio.sleep(PIPELINE_CONFIG['analysis_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in analysis loop: {e}")
                await asyncio.sleep(300)  # 5 минут пауза при ошибке
    
    async def cleanup_loop(self):
        """Цикл очистки данных"""
        while self.running:
            try:
                logger.info("🧹 Starting cleanup cycle...")
                
                db = await database.get_db()
                
                # Очистка истекших сессий
                cleaned_sessions = await db.cleanup_expired_sessions()
                logger.info(f"🧹 Cleaned {cleaned_sessions} expired sessions")
                
                # TODO: Очистка старых метрик (retention policy)
                
                # Ожидание следующего цикла
                await asyncio.sleep(PIPELINE_CONFIG['cleanup_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # 5 минут пауза при ошибке
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса pipeline"""
        return {
            'running': self.running,
            'collector_metrics': self.collector.metrics,
            'last_analysis': self.processor.last_analysis,
            'active_alerts': len([a for a in self.alert_manager.alerts if not a.resolved]),
            'total_alerts': len(self.alert_manager.alerts),
            'config': PIPELINE_CONFIG
        }

# ================================
# 🔄 ГЛОБАЛЬНЫЙ PIPELINE MANAGER
# ================================

# Глобальный экземпляр pipeline
pipeline_manager = DataPipelineManager()

# Функции для управления pipeline
async def start_pipeline():
    """Запуск data pipeline"""
    return await pipeline_manager.start()

async def stop_pipeline():
    """Остановка data pipeline"""
    return await pipeline_manager.stop()

def get_pipeline_status():
    """Получение статуса pipeline"""
    return pipeline_manager.get_status()

print("🔄 Data Pipeline module loaded")
