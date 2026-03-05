"""
🏗️ Order Service - Сервис управления заказами
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from database.db import get_db_connection
from database.models import OrderStatus

logger = logging.getLogger(__name__)

async def create_order(
    client_id: int,
    text: str,
    message_type: str = "text",
    photo_file_id: Optional[str] = None,
    voice_file_id: Optional[str] = None
) -> Dict[str, Any]:
    """Создание нового заказа"""
    
    try:
        conn = await get_db_connection()
        
        # Рассчитываем сумму (для примера - базовая цена)
        amount = calculate_order_amount(text)
        
        # Создаем заказ
        order = await conn.fetchrow("""
            INSERT INTO orders (
                client_id, 
                comment, 
                amount, 
                status, 
                message_type,
                photo_file_id,
                voice_file_id,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, client_id, comment, amount, status, created_at
        """, 
            client_id, 
            text, 
            amount, 
            OrderStatus.CREATED.value,
            message_type,
            photo_file_id,
            voice_file_id,
            datetime.now(),
            datetime.now()
        )
        
        await conn.close()
        
        # Конвертируем Record в dict
        order_dict = dict(order)
        
        logger.info(f"📦 Order {order_dict['id']} created for client {client_id}")
        
        return order_dict
        
    except Exception as e:
        logger.error(f"❌ Error creating order: {e}")
        raise

async def accept_order(order_id: int, operator_id: int) -> bool:
    """Принятие заказа оператором"""
    
    try:
        conn = await get_db_connection()
        
        # Обновляем статус и назначаем оператора
        await conn.execute("""
            UPDATE orders 
            SET status = $1, 
                operator_id = $2, 
                updated_at = $3
            WHERE id = $4 AND status = $5
        """, 
            OrderStatus.ACCEPTED.value,
            operator_id,
            datetime.now(),
            order_id,
            OrderStatus.CREATED.value
        )
        
        await conn.close()
        
        logger.info(f"✅ Order {order_id} accepted by operator {operator_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error accepting order: {e}")
        return False

async def reject_order(order_id: int, operator_id: int, reason: str = "") -> bool:
    """Отклонение заказа оператором"""
    
    try:
        conn = await get_db_connection()
        
        # Обновляем статус и добавляем причину
        await conn.execute("""
            UPDATE orders 
            SET status = $1, 
                operator_id = $2, 
                rejection_reason = $3,
                updated_at = $4
            WHERE id = $5
        """, 
            OrderStatus.CANCELLED.value,
            operator_id,
            reason,
            datetime.now(),
            order_id
        )
        
        await conn.close()
        
        logger.info(f"❌ Order {order_id} rejected by operator {operator_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error rejecting order: {e}")
        return False

async def confirm_payment(order_id: int, operator_id: int) -> bool:
    """Подтверждение оплаты заказа"""
    
    try:
        conn = await get_db_connection()
        
        # Обновляем статус оплаты
        await conn.execute("""
            UPDATE orders 
            SET status = $1, 
                payment_confirmed_at = $2,
                payment_confirmed_by = $3,
                updated_at = $4
            WHERE id = $5 AND status = $6
        """, 
            OrderStatus.ACCEPTED.value,
            datetime.now(),
            operator_id,
            datetime.now(),
            order_id,
            OrderStatus.WAITING_PAYMENT.value
        )
        
        await conn.close()
        
        logger.info(f"💳 Payment confirmed for order {order_id} by operator {operator_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error confirming payment: {e}")
        return False

async def update_order_status(order_id: int, new_status: OrderStatus, updated_by: int) -> bool:
    """Обновление статуса заказа"""
    
    try:
        conn = await get_db_connection()
        
        # Обновляем статус
        await conn.execute("""
            UPDATE orders 
            SET status = $1, 
                updated_at = $2,
                updated_by = $3
            WHERE id = $4
        """, 
            new_status.value,
            datetime.now(),
            updated_by,
            order_id
        )
        
        await conn.close()
        
        logger.info(f"📊 Order {order_id} status updated to {new_status.value}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating order status: {e}")
        return False

async def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """Получение детальной информации о заказе"""
    
    try:
        conn = await get_db_connection()
        
        order = await conn.fetchrow("""
            SELECT o.*, u.name as client_name, u.phone as client_phone, u.address as client_address
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.id = $1
        """, order_id)
        
        await conn.close()
        
        if order:
            order_dict = dict(order)
            return order_dict
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting order details: {e}")
        return None

async def get_orders_by_status(status: OrderStatus, limit: int = 50) -> list:
    """Получение заказов по статусу"""
    
    try:
        conn = await get_db_connection()
        
        orders = await conn.fetch("""
            SELECT o.*, u.name as client_name
            FROM orders o
            LEFT JOIN users u ON o.client_id = u.id
            WHERE o.status = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, status.value, limit)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting orders by status: {e}")
        return []

async def get_user_orders(user_id: int, user_role: str) -> list:
    """Получение заказов пользователя"""
    
    try:
        conn = await get_db_connection()
        
        if user_role == "client":
            orders = await conn.fetch("""
                SELECT o.*, u.name as client_name
                FROM orders o
                LEFT JOIN users u ON o.client_id = u.id
                WHERE o.client_id = $1
                ORDER BY o.created_at DESC
                LIMIT 20
            """, user_id)
        else:
            # Для сотрудников - заказы, назначенные на них
            field_map = {
                "operator": "operator_id",
                "picker": "picker_id", 
                "checker": "checker_id",
                "courier": "courier_id"
            }
            
            field = field_map.get(user_role, "operator_id")
            
            orders = await conn.fetch(f"""
                SELECT o.*, u.name as client_name
                FROM orders o
                LEFT JOIN users u ON o.client_id = u.id
                WHERE o.{field} = $1
                ORDER BY o.created_at DESC
                LIMIT 20
            """, user_id)
        
        await conn.close()
        
        return [dict(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error getting user orders: {e}")
        return []

def calculate_order_amount(text: str) -> float:
    """Расчет суммы заказа на основе текста"""
    
    # Простая логика расчета - можно улучшить
    base_price = 50.0  # Базовая цена
    
    # Если есть упоминание конкретных препаратов, добавляем цену
    if any(drug in text.lower() for drug in ["парацетамол", "амоксиклав", "нурофен"]):
        base_price += 30.0
    
    # Если есть упоминание количества
    if any(word in text.lower() for word in ["штуки", "упаковки", "коробки"]):
        base_price *= 1.5
    
    return base_price

# Удобные функции для использования в handlers
async def create_order_from_text(client_id: int, text: str) -> Dict[str, Any]:
    """Создание заказа из текста"""
    return await create_order(client_id, text, "text")

async def create_order_from_photo(client_id: int, caption: str, photo_file_id: str) -> Dict[str, Any]:
    """Создание заказа из фото"""
    return await create_order(client_id, caption, "photo", photo_file_id=photo_file_id)

async def create_order_from_voice(client_id: int, voice_file_id: str) -> Dict[str, Any]:
    """Создание заказа из голосового сообщения"""
    return await create_order(client_id, "Голосовое сообщение", "voice", voice_file_id=voice_file_id)
