"""
🗄️ Database Models - Python модели для работы с PostgreSQL
Современные модели с SQLAlchemy для MAXXPHARM CRM
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
import asyncpg

# Настройка логирования
logger = logging.getLogger("database_models")

# 🎯 Перечисления для типов данных
class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    OPERATOR = "operator"
    PICKER = "picker"
    CHECKER = "checker"
    COURIER = "courier"
    DIRECTOR = "director"

class OrderStatus(str, Enum):
    """Статусы заказов"""
    CREATED = "created"
    WAITING_PAYMENT = "waiting_payment"
    ACCEPTED = "accepted"
    PICKING = "picking"
    CHECKING = "checking"
    READY = "ready"
    WAITING_COURIER = "waiting_courier"
    ON_DELIVERY = "on_delivery"
    DELIVERED = "delivered"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    """Методы оплаты"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    TERMINAL = "terminal"
    ONLINE = "online"
    CRYPTO = "crypto"

class PaymentStatus(str, Enum):
    """Статусы оплаты"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"

class DeliveryStatus(str, Enum):
    """Статусы доставки"""
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    FAILED = "failed"

class LogLevel(str, Enum):
    """Уровни логирования"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Zone(str, Enum):
    """Зоны доставки"""
    CENTER = "центр"
    NORTH = "север"
    SOUTH = "юг"
    EAST = "восток"
    WEST = "запад"

# 🗄️ Dataclass модели
@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    zone: Optional[Zone] = None
    is_online: bool = True
    active_orders: int = 0
    max_orders: int = 5
    performance_score: float = 5.0
    last_assigned_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Client:
    """Модель клиента"""
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    zone: Optional[Zone] = None
    is_active: bool = True
    total_orders: int = 0
    total_spent: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Order:
    """Модель заказа"""
    id: Optional[int] = None
    client_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    operator_id: Optional[int] = None
    picker_id: Optional[int] = None
    checker_id: Optional[int] = None
    courier_id: Optional[int] = None
    total_price: float = 0.0
    delivery_price: float = 0.0
    zone: Optional[Zone] = None
    address: Optional[str] = None
    comment: Optional[str] = None
    priority: int = 1
    estimated_time: Optional[int] = None
    actual_time: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class OrderItem:
    """Модель товара в заказе"""
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int = 0
    price: float = 0.0
    total_price: float = 0.0
    requires_prescription: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class OrderStatusHistory:
    """Модель истории статусов заказа"""
    id: Optional[int] = None
    order_id: Optional[int] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    changed_by: Optional[int] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Payment:
    """Модель оплаты"""
    id: Optional[int] = None
    order_id: Optional[int] = None
    amount: float = 0.0
    method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    proof_photo: Optional[str] = None
    transaction_id: Optional[str] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Delivery:
    """Модель доставки"""
    id: Optional[int] = None
    order_id: Optional[int] = None
    courier_id: Optional[int] = None
    status: Optional[DeliveryStatus] = None
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    actual_distance: Optional[float] = None
    delivery_notes: Optional[str] = None
    client_rating: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class SystemLog:
    """Модель системного лога"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    client_id: Optional[int] = None
    order_id: Optional[int] = None
    action: Optional[str] = None
    details: Optional[str] = None
    level: Optional[LogLevel] = LogLevel.INFO
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Setting:
    """Модель настройки"""
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# 🗄️ Database Manager
class DatabaseManager:
    """Менеджер базы данных для MAXXPHARM CRM"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
        self.logger = logging.getLogger("database_manager")
    
    async def initialize(self):
        """Инициализация пула соединений"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self.logger.info("✅ Database pool initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize database pool: {e}")
            return False
    
    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            self.logger.info("🔒 Database pool closed")
    
    async def execute(self, query: str, *args) -> Any:
        """Выполнение SQL запроса"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[dict]:
        """Получение записей"""
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, *args)
            return [dict(record) for record in records]
    
    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """Получение одной записи"""
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, *args)
            return dict(record) if record else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Получение одного значения"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    # 📦 Методы для работы с пользователями
    async def create_user(self, user: User) -> int:
        """Создание пользователя"""
        query = """
        INSERT INTO users (telegram_id, name, phone, role, zone, is_online, active_orders, max_orders, performance_score)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """
        result = await self.fetchval(
            query,
            user.telegram_id, user.name, user.phone, user.role.value,
            user.zone.value if user.zone else None, user.is_online,
            user.active_orders, user.max_orders, user.performance_score
        )
        return result
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        query = """
        SELECT id, telegram_id, name, phone, role, zone, is_online, active_orders, max_orders, performance_score, last_assigned_at, created_at, updated_at
        FROM users WHERE telegram_id = $1
        """
        record = await self.fetchrow(query, telegram_id)
        if record:
            return User(
                id=record['id'],
                telegram_id=record['telegram_id'],
                name=record['name'],
                phone=record['phone'],
                role=UserRole(record['role']),
                zone=Zone(record['zone']) if record['zone'] else None,
                is_online=record['is_online'],
                active_orders=record['active_orders'],
                max_orders=record['max_orders'],
                performance_score=record['performance_score'],
                last_assigned_at=record['last_assigned_at'],
                created_at=record['created_at'],
                updated_at=record['updated_at']
            )
        return None
    
    async def get_optimal_worker(self, role: UserRole, zone: Optional[Zone] = None) -> Optional[User]:
        """Получение оптимального сотрудника"""
        query = """
        SELECT id, telegram_id, name, phone, role, zone, is_online, active_orders, max_orders, performance_score, last_assigned_at, created_at, updated_at
        FROM get_optimal_worker($1, $2)
        """
        record = await self.fetchrow(query, role.value, zone.value if zone else None)
        if record:
            return User(
                id=record['id'],
                telegram_id=record['telegram_id'],
                name=record['name'],
                phone=record['phone'],
                role=UserRole(record['role']),
                zone=Zone(record['zone']) if record['zone'] else None,
                is_online=record['is_online'],
                active_orders=record['active_orders'],
                max_orders=record['max_orders'],
                performance_score=record['performance_score'],
                last_assigned_at=record['last_assigned_at'],
                created_at=record['created_at'],
                updated_at=record['updated_at']
            )
        return None
    
    async def update_worker_load(self, user_id: int, delta: int) -> bool:
        """Обновление нагрузки сотрудника"""
        query = "SELECT update_worker_load($1, $2)"
        result = await self.fetchval(query, user_id, delta)
        return result
    
    # 👤 Методы для работы с клиентами
    async def create_client(self, client: Client) -> int:
        """Создание клиента"""
        query = """
        INSERT INTO clients (telegram_id, name, phone, address, zone, is_active, total_orders, total_spent)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        result = await self.fetchval(
            query,
            client.telegram_id, client.name, client.phone, client.address,
            client.zone.value if client.zone else None, client.is_active,
            client.total_orders, client.total_spent
        )
        return result
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """Получение клиента по Telegram ID"""
        query = """
        SELECT id, telegram_id, name, phone, address, zone, is_active, total_orders, total_spent, created_at, updated_at
        FROM clients WHERE telegram_id = $1
        """
        record = await self.fetchrow(query, telegram_id)
        if record:
            return Client(
                id=record['id'],
                telegram_id=record['telegram_id'],
                name=record['name'],
                phone=record['phone'],
                address=record['address'],
                zone=Zone(record['zone']) if record['zone'] else None,
                is_active=record['is_active'],
                total_orders=record['total_orders'],
                total_spent=record['total_spent'],
                created_at=record['created_at'],
                updated_at=record['updated_at']
            )
        return None
    
    # 📦 Методы для работы с заказами
    async def create_order(self, order: Order) -> int:
        """Создание заказа"""
        query = """
        INSERT INTO orders (client_id, status, total_price, delivery_price, zone, address, comment, priority, estimated_time)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """
        result = await self.fetchval(
            query,
            order.client_id, order.status.value, order.total_price, order.delivery_price,
            order.zone.value if order.zone else None, order.address, order.comment,
            order.priority, order.estimated_time
        )
        
        # Обновляем статистику клиента
        await self.execute(
            "UPDATE clients SET total_orders = total_orders + 1, total_spent = total_spent + $1 WHERE id = $2",
            order.total_price, order.client_id
        )
        
        return result
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Получение заказа по ID"""
        query = """
        SELECT id, client_id, status, operator_id, picker_id, checker_id, courier_id, total_price, delivery_price, 
               zone, address, comment, priority, estimated_time, actual_time, created_at, updated_at, completed_at
        FROM orders WHERE id = $1
        """
        record = await self.fetchrow(query, order_id)
        if record:
            return Order(
                id=record['id'],
                client_id=record['client_id'],
                status=OrderStatus(record['status']),
                operator_id=record['operator_id'],
                picker_id=record['picker_id'],
                checker_id=record['checker_id'],
                courier_id=record['courier_id'],
                total_price=record['total_price'],
                delivery_price=record['delivery_price'],
                zone=Zone(record['zone']) if record['zone'] else None,
                address=record['address'],
                comment=record['comment'],
                priority=record['priority'],
                estimated_time=record['estimated_time'],
                actual_time=record['actual_time'],
                created_at=record['created_at'],
                updated_at=record['updated_at'],
                completed_at=record['completed_at']
            )
        return None
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus, changed_by: Optional[int] = None, reason: Optional[str] = None) -> bool:
        """Обновление статуса заказа"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Получаем старый статус
                old_status = await conn.fetchval("SELECT status FROM orders WHERE id = $1", order_id)
                
                # Обновляем статус
                await conn.execute(
                    "UPDATE orders SET status = $1 WHERE id = $2",
                    new_status.value, order_id
                )
                
                # Записываем в историю
                await conn.execute(
                    "INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, reason) VALUES ($1, $2, $3, $4, $5)",
                    order_id, old_status, new_status.value, changed_by, reason
                )
                
                return True
    
    async def get_orders_by_status(self, status: OrderStatus, limit: int = 50) -> List[Order]:
        """Получение заказов по статусу"""
        query = """
        SELECT id, client_id, status, operator_id, picker_id, checker_id, courier_id, total_price, delivery_price,
               zone, address, comment, priority, estimated_time, actual_time, created_at, updated_at, completed_at
        FROM orders WHERE status = $1 ORDER BY created_at DESC LIMIT $2
        """
        records = await self.fetch(query, status.value, limit)
        return [
            Order(
                id=record['id'],
                client_id=record['client_id'],
                status=OrderStatus(record['status']),
                operator_id=record['operator_id'],
                picker_id=record['picker_id'],
                checker_id=record['checker_id'],
                courier_id=record['courier_id'],
                total_price=record['total_price'],
                delivery_price=record['delivery_price'],
                zone=Zone(record['zone']) if record['zone'] else None,
                address=record['address'],
                comment=record['comment'],
                priority=record['priority'],
                estimated_time=record['estimated_time'],
                actual_time=record['actual_time'],
                created_at=record['created_at'],
                updated_at=record['updated_at'],
                completed_at=record['completed_at']
            )
            for record in records
        ]
    
    async def get_client_orders(self, client_id: int, limit: int = 20) -> List[Order]:
        """Получение заказов клиента"""
        query = """
        SELECT id, client_id, status, operator_id, picker_id, checker_id, courier_id, total_price, delivery_price,
               zone, address, comment, priority, estimated_time, actual_time, created_at, updated_at, completed_at
        FROM orders WHERE client_id = $1 ORDER BY created_at DESC LIMIT $2
        """
        records = await self.fetch(query, client_id, limit)
        return [
            Order(
                id=record['id'],
                client_id=record['client_id'],
                status=OrderStatus(record['status']),
                operator_id=record['operator_id'],
                picker_id=record['picker_id'],
                checker_id=record['checker_id'],
                courier_id=record['courier_id'],
                total_price=record['total_price'],
                delivery_price=record['delivery_price'],
                zone=Zone(record['zone']) if record['zone'] else None,
                address=record['address'],
                comment=record['comment'],
                priority=record['priority'],
                estimated_time=record['estimated_time'],
                actual_time=record['actual_time'],
                created_at=record['created_at'],
                updated_at=record['updated_at'],
                completed_at=record['completed_at']
            )
            for record in records
        ]
    
    # 📋 Методы для работы с товарами в заказах
    async def create_order_item(self, item: OrderItem) -> int:
        """Создание товара в заказе"""
        query = """
        INSERT INTO order_items (order_id, product_name, quantity, price, total_price, requires_prescription, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        return await self.fetchval(
            query,
            item.order_id, item.product_name, item.quantity, item.price,
            item.total_price, item.requires_prescription, item.notes
        )
    
    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Получение товаров заказа"""
        query = """
        SELECT id, order_id, product_name, quantity, price, total_price, requires_prescription, notes, created_at
        FROM order_items WHERE order_id = $1 ORDER BY id
        """
        records = await self.fetch(query, order_id)
        return [
            OrderItem(
                id=record['id'],
                order_id=record['order_id'],
                product_name=record['product_name'],
                quantity=record['quantity'],
                price=record['price'],
                total_price=record['total_price'],
                requires_prescription=record['requires_prescription'],
                notes=record['notes'],
                created_at=record['created_at']
            )
            for record in records
        ]
    
    # 📊 Методы для аналитики
    async def get_daily_statistics(self, date_from: date = None, date_to: date = None) -> List[Dict[str, Any]]:
        """Получение дневной статистики"""
        if not date_from:
            date_from = date.today()
        if not date_to:
            date_to = date.today()
        
        query = """
        SELECT * FROM get_order_statistics($1, $2)
        """
        return await self.fetch(query, date_from, date_to)
    
    async def get_worker_performance(self, user_id: int, date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """Получение производительности сотрудника"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        query = """
        SELECT * FROM get_worker_performance($1, $2, $3)
        """
        record = await self.fetchrow(query, user_id, date_from, date_to)
        return dict(record) if record else {}
    
    async def get_system_logs(self, level: Optional[LogLevel] = None, limit: int = 100) -> List[SystemLog]:
        """Получение системных логов"""
        if level:
            query = """
            SELECT id, user_id, client_id, order_id, action, details, level, ip_address, user_agent, created_at
            FROM system_logs WHERE level = $1 ORDER BY created_at DESC LIMIT $2
            """
            records = await self.fetch(query, level.value, limit)
        else:
            query = """
            SELECT id, user_id, client_id, order_id, action, details, level, ip_address, user_agent, created_at
            FROM system_logs ORDER BY created_at DESC LIMIT $1
            """
            records = await self.fetch(query, limit)
        
        return [
            SystemLog(
                id=record['id'],
                user_id=record['user_id'],
                client_id=record['client_id'],
                order_id=record['order_id'],
                action=record['action'],
                details=record['details'],
                level=LogLevel(record['level']),
                ip_address=record['ip_address'],
                user_agent=record['user_agent'],
                created_at=record['created_at']
            )
            for record in records
        ]
    
    async def log_action(self, user_id: Optional[int], client_id: Optional[int], order_id: Optional[int], 
                         action: str, details: Optional[str] = None, level: LogLevel = LogLevel.INFO) -> None:
        """Запись системного лога"""
        query = """
        INSERT INTO system_logs (user_id, client_id, order_id, action, details, level)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        await self.execute(query, user_id, client_id, order_id, action, details, level.value)

# 🗄️ Глобальный экземпляр
db_manager: Optional[DatabaseManager] = None

async def get_database_manager(connection_string: str) -> DatabaseManager:
    """Получение экземпляра менеджера базы данных"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(connection_string)
        await db_manager.initialize()
    return db_manager

# Удобные функции для использования
async def create_user(telegram_id: int, name: str, role: UserRole, phone: str = None, zone: Zone = None) -> int:
    """Создание пользователя (удобная функция)"""
    from bot.config import DATABASE_URL
    db = await get_database_manager(DATABASE_URL)
    user = User(telegram_id=telegram_id, name=name, role=role, phone=phone, zone=zone)
    return await db.create_user(user)

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Получение пользователя по Telegram ID (удобная функция)"""
    from bot.config import DATABASE_URL
    db = await get_database_manager(DATABASE_URL)
    return await db.get_user_by_telegram_id(telegram_id)

async def create_order_with_items(client_id: int, total_price: float, zone: Zone, address: str, 
                                comment: str = None, items: List[Dict[str, Any]] = None) -> int:
    """Создание заказа с товарами (удобная функция)"""
    from bot.config import DATABASE_URL
    db = await get_database_manager(DATABASE_URL)
    
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            # Создаем заказ
            order = Order(
                client_id=client_id,
                status=OrderStatus.CREATED,
                total_price=total_price,
                zone=zone,
                address=address,
                comment=comment
            )
            order_id = await db.create_order(order)
            
            # Создаем товары
            if items:
                for item_data in items:
                    item = OrderItem(
                        order_id=order_id,
                        product_name=item_data['product_name'],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        total_price=item_data['quantity'] * item_data['price'],
                        requires_prescription=item_data.get('requires_prescription', False)
                    )
                    await db.create_order_item(item)
            
            return order_id

async def update_order_status_with_history(order_id: int, new_status: OrderStatus, changed_by: int, reason: str = None) -> bool:
    """Обновление статуса заказа с историей (удобная функция)"""
    from bot.config import DATABASE_URL
    db = await get_database_manager(DATABASE_URL)
    return await db.update_order_status(order_id, new_status, changed_by, reason)
