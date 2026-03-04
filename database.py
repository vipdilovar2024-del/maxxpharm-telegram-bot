# 🗄️ DATABASE INTEGRATION - MAXXPHARM
# PostgreSQL база данных для CRM-системы

import asyncio
import asyncpg
import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os

# ================================
# 📊 КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ
# ================================

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'maxxpharm_crm'),
    'min_size': 5,
    'max_size': 20
}

# ================================
# 📋 МОДЕЛИ ДАННЫХ
# ================================

@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: int
    full_name: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    pharmacy_name: Optional[str] = None
    blocked: bool = False
    created_at: datetime.datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

@dataclass
class Order:
    """Модель заказа"""
    id: int
    client_id: int
    operator_id: Optional[int] = None
    courier_id: Optional[int] = None
    status: str = 'Новая'
    type: str = 'text'
    content: str = ''
    price: float = 0.0
    delivery_time: Optional[int] = None
    cancel_reason: Optional[str] = None
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.datetime.now()

@dataclass
class ActivityLog:
    """Модель лога активности"""
    id: int
    user_id: int
    action: str
    details: str
    timestamp: datetime.datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

@dataclass
class AIMetrics:
    """Модель AI-метрик"""
    id: int
    metric_type: str
    value: float
    details: Dict[str, Any]
    timestamp: datetime.datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

@dataclass
class Session:
    """Модель сессии"""
    id: int
    user_id: int
    role: str
    expires: datetime.datetime
    active: bool = True
    created_at: datetime.datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

# ================================
# 🗄️ DATABASE MANAGER
# ================================

class DatabaseManager:
    """Менеджер базы данных PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.connected = False
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(
                **DATABASE_CONFIG,
                command_timeout=60
            )
            self.connected = True
            print("🗄️ Database connected successfully")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            self.connected = False
            print("🗄️ Database disconnected")
    
    async def init_tables(self):
        """Инициализация таблиц"""
        if not self.connected:
            await self.connect()
        
        create_tables_sql = """
        -- Таблица пользователей
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            pharmacy_name VARCHAR(255),
            blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица заказов
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES users(telegram_id),
            operator_id INTEGER REFERENCES users(telegram_id),
            courier_id INTEGER REFERENCES users(telegram_id),
            status VARCHAR(50) DEFAULT 'Новая',
            type VARCHAR(50) DEFAULT 'text',
            content TEXT,
            price DECIMAL(10,2) DEFAULT 0.0,
            delivery_time INTEGER,
            cancel_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица логов активности
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(telegram_id),
            action VARCHAR(100) NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица AI-метрик
        CREATE TABLE IF NOT EXISTS ai_metrics (
            id SERIAL PRIMARY KEY,
            metric_type VARCHAR(100) NOT NULL,
            value DECIMAL(10,2) NOT NULL,
            details JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица сессий
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(telegram_id),
            role VARCHAR(50) NOT NULL,
            expires TIMESTAMP NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Индексы для оптимизации
        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_ai_metrics_timestamp ON ai_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires);
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(create_tables_sql)
            print("🗄️ Database tables initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            return False
    
    # ================================
    # 👤 ПОЛЬЗОВАТЕЛИ
    # ================================
    
    async def create_user(self, user: User) -> bool:
        """Создание пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (telegram_id, full_name, role, phone, address, pharmacy_name, blocked)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        role = EXCLUDED.role,
                        phone = EXCLUDED.phone,
                        address = EXCLUDED.address,
                        pharmacy_name = EXCLUDED.pharmacy_name,
                        blocked = EXCLUDED.blocked
                    """,
                    user.telegram_id, user.full_name, user.role, 
                    user.phone, user.address, user.pharmacy_name, user.blocked
                )
            return True
        except Exception as e:
            print(f"❌ Create user error: {e}")
            return False
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE telegram_id = $1",
                    telegram_id
                )
                if row:
                    return User(
                        id=row['id'],
                        telegram_id=row['telegram_id'],
                        full_name=row['full_name'],
                        role=row['role'],
                        phone=row['phone'],
                        address=row['address'],
                        pharmacy_name=row['pharmacy_name'],
                        blocked=row['blocked'],
                        created_at=row['created_at']
                    )
            return None
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return None
    
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
                return [
                    User(
                        id=row['id'],
                        telegram_id=row['telegram_id'],
                        full_name=row['full_name'],
                        role=row['role'],
                        phone=row['phone'],
                        address=row['address'],
                        pharmacy_name=row['pharmacy_name'],
                        blocked=row['blocked'],
                        created_at=row['created_at']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get all users error: {e}")
            return []
    
    # ================================
    # 📦 ЗАКАЗЫ
    # ================================
    
    async def create_order(self, order: Order) -> bool:
        """Создание заказа"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO orders (client_id, operator_id, courier_id, status, type, content, price, delivery_time, cancel_reason)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    order.client_id, order.operator_id, order.courier_id,
                    order.status, order.type, order.content, order.price,
                    order.delivery_time, order.cancel_reason
                )
            return True
        except Exception as e:
            print(f"❌ Create order error: {e}")
            return False
    
    async def get_orders(self, limit: int = 100) -> List[Order]:
        """Получение заказов"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM orders ORDER BY created_at DESC LIMIT $1",
                    limit
                )
                return [
                    Order(
                        id=row['id'],
                        client_id=row['client_id'],
                        operator_id=row['operator_id'],
                        courier_id=row['courier_id'],
                        status=row['status'],
                        type=row['type'],
                        content=row['content'],
                        price=float(row['price']),
                        delivery_time=row['delivery_time'],
                        cancel_reason=row['cancel_reason'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get orders error: {e}")
            return []
    
    async def get_orders_by_client(self, client_id: int) -> List[Order]:
        """Получение заказов клиента"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM orders WHERE client_id = $1 ORDER BY created_at DESC",
                    client_id
                )
                return [
                    Order(
                        id=row['id'],
                        client_id=row['client_id'],
                        operator_id=row['operator_id'],
                        courier_id=row['courier_id'],
                        status=row['status'],
                        type=row['type'],
                        content=row['content'],
                        price=float(row['price']),
                        delivery_time=row['delivery_time'],
                        cancel_reason=row['cancel_reason'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get orders by client error: {e}")
            return []
    
    async def update_order_status(self, order_id: int, status: str, operator_id: int = None) -> bool:
        """Обновление статуса заказа"""
        try:
            async with self.pool.acquire() as conn:
                if operator_id:
                    await conn.execute(
                        "UPDATE orders SET status = $1, operator_id = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
                        status, operator_id, order_id
                    )
                else:
                    await conn.execute(
                        "UPDATE orders SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                        status, order_id
                    )
            return True
        except Exception as e:
            print(f"❌ Update order status error: {e}")
            return False
    
    # ================================
    # 📝 ЛОГИ АКТИВНОСТИ
    # ================================
    
    async def log_activity(self, user_id: int, action: str, details: str) -> bool:
        """Логирование активности"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO activity_logs (user_id, action, details) VALUES ($1, $2, $3)",
                    user_id, action, details
                )
            return True
        except Exception as e:
            print(f"❌ Log activity error: {e}")
            return False
    
    async def get_activity_logs(self, limit: int = 100) -> List[ActivityLog]:
        """Получение логов активности"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT $1",
                    limit
                )
                return [
                    ActivityLog(
                        id=row['id'],
                        user_id=row['user_id'],
                        action=row['action'],
                        details=row['details'],
                        timestamp=row['timestamp']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get activity logs error: {e}")
            return []
    
    # ================================
    # 🧠 AI-МЕТРИКИ
    # ================================
    
    async def save_ai_metric(self, metric_type: str, value: float, details: Dict[str, Any]) -> bool:
        """Сохранение AI-метрики"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO ai_metrics (metric_type, value, details) VALUES ($1, $2, $3)",
                    metric_type, value, json.dumps(details)
                )
            return True
        except Exception as e:
            print(f"❌ Save AI metric error: {e}")
            return False
    
    async def get_ai_metrics(self, metric_type: str = None, hours: int = 24) -> List[AIMetrics]:
        """Получение AI-метрик"""
        try:
            async with self.pool.acquire() as conn:
                if metric_type:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM ai_metrics 
                        WHERE metric_type = $1 AND timestamp >= NOW() - INTERVAL '$2 hours'
                        ORDER BY timestamp DESC
                        """,
                        metric_type, hours
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM ai_metrics 
                        WHERE timestamp >= NOW() - INTERVAL '$1 hours'
                        ORDER BY timestamp DESC
                        """,
                        hours
                    )
                return [
                    AIMetrics(
                        id=row['id'],
                        metric_type=row['metric_type'],
                        value=float(row['value']),
                        details=json.loads(row['details']) if row['details'] else {},
                        timestamp=row['timestamp']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get AI metrics error: {e}")
            return []
    
    # ================================
    # 🔐 СЕССИИ
    # ================================
    
    async def create_session(self, user_id: int, role: str, expires: datetime.datetime) -> bool:
        """Создание сессии"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO sessions (user_id, role, expires) VALUES ($1, $2, $3)",
                    user_id, role, expires
                )
            return True
        except Exception as e:
            print(f"❌ Create session error: {e}")
            return False
    
    async def get_active_sessions(self) -> List[Session]:
        """Получение активных сессий"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM sessions WHERE active = TRUE AND expires > NOW() ORDER BY created_at DESC"
                )
                return [
                    Session(
                        id=row['id'],
                        user_id=row['user_id'],
                        role=row['role'],
                        expires=row['expires'],
                        active=row['active'],
                        created_at=row['created_at']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Get active sessions error: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Очистка истекших сессий"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE sessions SET active = FALSE WHERE expires <= NOW()"
                )
                # Возвращаем количество обновленных строк
                return int(result.split()[-1])
        except Exception as e:
            print(f"❌ Cleanup sessions error: {e}")
            return 0
    
    # ================================
    # 📊 АНАЛИТИКА ДЛЯ AI
    # ================================
    
    async def get_orders_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Получение аналитики заказов для AI"""
        try:
            async with self.pool.acquire() as conn:
                # Общая статистика
                stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_orders,
                        COUNT(CASE WHEN status = 'Выполнена' THEN 1 END) as completed_orders,
                        COUNT(CASE WHEN status = 'Отменена' THEN 1 END) as cancelled_orders,
                        AVG(price) as avg_price,
                        AVG(delivery_time) as avg_delivery_time
                    FROM orders 
                    WHERE created_at >= NOW() - INTERVAL '$1 days'
                    """,
                    days
                )
                
                # Почасовое распределение
                hourly = await conn.fetch(
                    """
                    SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                    FROM orders 
                    WHERE created_at >= NOW() - INTERVAL '$1 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY hour
                    """,
                    days
                )
                
                # Нагрузка операторов
                operator_load = await conn.fetch(
                    """
                    SELECT operator_id, COUNT(*) as load
                    FROM orders 
                    WHERE created_at >= NOW() - INTERVAL '$1 days' AND operator_id IS NOT NULL
                    GROUP BY operator_id
                    ORDER BY load DESC
                    """,
                    days
                )
                
                return {
                    'total_orders': stats['total_orders'] or 0,
                    'completed_orders': stats['completed_orders'] or 0,
                    'cancelled_orders': stats['cancelled_orders'] or 0,
                    'avg_price': float(stats['avg_price']) if stats['avg_price'] else 0.0,
                    'avg_delivery_time': float(stats['avg_delivery_time']) if stats['avg_delivery_time'] else 0.0,
                    'hourly_distribution': {int(row['hour']): row['count'] for row in hourly},
                    'operator_load': {row['operator_id']: row['load'] for row in operator_load}
                }
        except Exception as e:
            print(f"❌ Get orders analytics error: {e}")
            return {}

# ================================
# 🗄️ ГЛОБАЛЬНЫЙ МЕНЕДЖЕР БАЗЫ ДАННЫХ
# ================================

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()

# Функции для удобного использования
async def init_database():
    """Инициализация базы данных"""
    success = await db_manager.connect()
    if success:
        await db_manager.init_tables()
    return success

async def get_db():
    """Получение менеджера базы данных"""
    if not db_manager.connected:
        await db_manager.connect()
    return db_manager

print("🗄️ Database module loaded")
