"""
🏗️ Database Queries - SQL запросы для CRM
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from database.db import get_db_connection, release_db_connection
from database.models import OrderStatus

logger = logging.getLogger(__name__)

# Запросы для заказов
async def get_new_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение новых заказов"""
    
    try:
        conn = await get_db_connection()
        
        orders = await conn.fetch("""
            SELECT o.*, u.name as client_name, u.phone as client_phone, u.address as client_address
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.status = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, OrderStatus.CREATED.value, limit)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting new orders: {e}")
        return []

async def get_orders_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Получение заказов по статусу"""
    
    try:
        conn = await get_db_connection()
        
        orders = await conn.fetch("""
            SELECT o.*, u.name as client_name, u.phone as client_phone, u.address as client_address
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.status = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, status, limit)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting orders by status: {e}")
        return []

async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    """Получение заказа по ID"""
    
    try:
        conn = await get_db_connection()
        
        order = await conn.fetchrow("""
            SELECT o.*, 
                   u.name as client_name, u.phone as client_phone, u.address as client_address,
                   op.name as operator_name,
                   pi.name as picker_name,
                   ch.name as checker_name,
                   co.name as courier_name
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            LEFT JOIN users op ON o.operator_id = op.id
            LEFT JOIN users pi ON o.picker_id = pi.id
            LEFT JOIN users ch ON o.checker_id = ch.id
            LEFT JOIN users co ON o.courier_id = co.id
            WHERE o.id = $1
        """, order_id)
        
        await conn.close()
        
        if order:
            return dict(order)
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting order by ID: {e}")
        return None

async def get_client_orders(client_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Получение заказов клиента"""
    
    try:
        conn = await get_db_connection()
        
        orders = await conn.fetch("""
            SELECT o.*, u.name as client_name
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.client_id = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, client_id, limit)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting client orders: {e}")
        return []

async def get_client_last_order(client_id: int) -> Optional[Dict[str, Any]]:
    """Получение последнего заказа клиента"""
    
    try:
        conn = await get_db_connection()
        
        order = await conn.fetchrow("""
            SELECT o.*, u.name as client_name
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.client_id = $1
            ORDER BY o.created_at DESC
            LIMIT 1
        """, client_id)
        
        await conn.close()
        
        if order:
            return dict(order)
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting client last order: {e}")
        return None

async def get_operator_orders(operator_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Получение заказов оператора"""
    
    try:
        conn = await get_db_connection()
        
        orders = await conn.fetch("""
            SELECT o.*, u.name as client_name
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.operator_id = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, operator_id, limit)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting operator orders: {e}")
        return []

# Запросы для пользователей
async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя по Telegram ID"""
    
    try:
        conn = await get_db_connection()
        
        user = await conn.fetchrow("""
            SELECT * FROM users 
            WHERE telegram_id = $1 AND is_active = true
        """, telegram_id)
        
        await conn.close()
        
        if user:
            return dict(user)
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting user by Telegram ID: {e}")
        return None

async def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """Получение пользователей по роли"""
    
    try:
        conn = await get_db_connection()
        
        users = await conn.fetch("""
            SELECT * FROM users 
            WHERE role = $1 AND is_active = true
            ORDER BY name
        """, role)
        
        await conn.close()
        
        return [dict(user) for user in users]
        
    except Exception as e:
        logger.error(f"❌ Error getting users by role: {e}")
        return []

# Запросы для статистики
async def get_daily_stats(date: datetime = None) -> Dict[str, Any]:
    """Получение дневной статистики"""
    
    if date is None:
        date = datetime.now().date()
    
    try:
        conn = await get_db_connection()
        
        # Общее количество заказов
        total_orders = await conn.fetchval("""
            SELECT COUNT(*) FROM orders 
            WHERE DATE(created_at) = $1
        """, date)
        
        # Доставленные заказы
        delivered_orders = await conn.fetchval("""
            SELECT COUNT(*) FROM orders 
            WHERE DATE(created_at) = $1 AND status = $2
        """, date, OrderStatus.DELIVERED.value)
        
        # Отмененные заказы
        cancelled_orders = await conn.fetchval("""
            SELECT COUNT(*) FROM orders 
            WHERE DATE(created_at) = $1 AND status = $2
        """, date, OrderStatus.CANCELLED.value)
        
        # Общая выручка
        total_revenue = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM orders 
            WHERE DATE(created_at) = $1 AND status = $2
        """, date, OrderStatus.DELIVERED.value)
        
        await conn.close()
        
        return {
            "date": date.strftime("%d.%m.%Y"),
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "in_progress_orders": total_orders - delivered_orders - cancelled_orders,
            "total_revenue": float(total_revenue)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting daily stats: {e}")
        return {
            "date": date.strftime("%d.%m.%Y"),
            "total_orders": 0,
            "delivered_orders": 0,
            "cancelled_orders": 0,
            "in_progress_orders": 0,
            "total_revenue": 0.0
        }

# Запросы для автоматического распределения
async def get_least_loaded_worker(role: str) -> Optional[Dict[str, Any]]:
    """Получение работника с минимальной нагрузкой"""
    
    try:
        conn = await get_db_connection()
        
        worker = await conn.fetchrow("""
            SELECT u.*, COUNT(o.id) as active_orders
            FROM users u
            LEFT JOIN orders o ON u.id = o.operator_id AND o.status NOT IN ('delivered', 'cancelled')
            WHERE u.role = $1 AND u.is_active = true
            GROUP BY u.id, u.telegram_id, u.name, u.phone, u.address, u.role, u.is_active, u.created_at, u.updated_at
            ORDER BY active_orders ASC, u.created_at ASC
            LIMIT 1
        """, role)
        
        await conn.close()
        
        if worker:
            return dict(worker)
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting least loaded worker: {e}")
        return None

# Запросы для уведомлений
async def create_notification(user_id: int, order_id: Optional[int], notification_type: str, message: str) -> int:
    """Создание уведомления"""
    
    try:
        conn = await get_db_connection()
        
        notification_id = await conn.fetchval("""
            INSERT INTO notifications (user_id, order_id, type, message, is_sent, created_at)
            VALUES ($1, $2, $3, $4, false, NOW())
            RETURNING id
        """, user_id, order_id, notification_type, message)
        
        await conn.close()
        
        return notification_id
        
    except Exception as e:
        logger.error(f"❌ Error creating notification: {e}")
        return 0

async def mark_notification_sent(notification_id: int) -> bool:
    """Отметка об отправке уведомления"""
    
    try:
        conn = await get_db_connection()
        
        await conn.execute("""
            UPDATE notifications 
            SET is_sent = true, sent_at = NOW()
            WHERE id = $1
        """, notification_id)
        
        await conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error marking notification sent: {e}")
        return False
