"""
🧠 Auto-Assignment Service - Умная система распределения заказов уровня Uber
aiogram 3.4.1 compatible
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from database.db import get_db_connection
from database.models import UserRole, OrderStatus
from keyboards.notifications import NotificationService

logger = logging.getLogger(__name__)

class AssignmentService:
    """Сервис автоматического распределения заказов"""
    
    def __init__(self, bot):
        self.bot = bot
        self.notification_service = NotificationService(bot)
        self.logger = logging.getLogger("assignment_service")
    
    async def assign_picker(self, order_id: int, zone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Назначение сборщика с минимальной нагрузкой"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем сборщика с минимальной нагрузкой
            picker = await conn.fetchrow("""
                SELECT id, telegram_id, name, active_orders, zone
                FROM users
                WHERE role = $1
                AND is_active = true
                AND is_online = true
                AND (zone = $2 OR $2 IS NULL)
                ORDER BY active_orders ASC, last_assigned_at ASC
                LIMIT 1
            """, UserRole.PICKER.value, zone)
            
            if not picker:
                self.logger.warning(f"⚠️ No available picker found for order {order_id}")
                await conn.close()
                return None
            
            # Назначаем сборщика заказу
            await conn.execute("""
                UPDATE orders
                SET picker_id = $1,
                    status = $2,
                    picker_assigned_at = $3,
                    updated_at = $3
                WHERE id = $4
            """, picker["id"], OrderStatus.PROCESSING.value, datetime.now(), order_id)
            
            # Увеличиваем нагрузку сборщика
            await conn.execute("""
                UPDATE users
                SET active_orders = active_orders + 1,
                last_assigned_at = $1
                WHERE id = $2
            """, datetime.now(), picker["id"])
            
            await conn.close()
            
            # Отправляем уведомление сборщику
            order = await self._get_order_details(order_id)
            if order:
                await self.notification_service.notify_picker_assigned(picker["telegram_id"], order)
            
            self.logger.info(f"📦 Picker {picker['name']} assigned to order {order_id}")
            return dict(picker)
            
        except Exception as e:
            self.logger.error(f"❌ Error assigning picker: {e}")
            return None
    
    async def assign_checker(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Назначение проверщика с минимальной нагрузкой"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем проверщика с минимальной нагрузкой
            checker = await conn.fetchrow("""
                SELECT id, telegram_id, name, active_orders
                FROM users
                WHERE role = $1
                AND is_active = true
                AND is_online = true
                ORDER BY active_orders ASC, last_assigned_at ASC
                LIMIT 1
            """, UserRole.CHECKER.value)
            
            if not checker:
                self.logger.warning(f"⚠️ No available checker found for order {order_id}")
                await conn.close()
                return None
            
            # Назначаем проверщика заказу
            await conn.execute("""
                UPDATE orders
                SET checker_id = $1,
                    status = $2,
                    checker_assigned_at = $3,
                    updated_at = $3
                WHERE id = $4
            """, checker["id"], OrderStatus.CHECKING.value, datetime.now(), order_id)
            
            # Увеличиваем нагрузку проверщика
            await conn.execute("""
                UPDATE users
                SET active_orders = active_orders + 1,
                last_assigned_at = $1
                WHERE id = $2
            """, datetime.now(), checker["id"])
            
            await conn.close()
            
            # Отправляем уведомление проверщику
            order = await self._get_order_details(order_id)
            if order:
                await self.notification_service.notify_checker_assigned(checker["telegram_id"], order)
            
            self.logger.info(f"🔍 Checker {checker['name']} assigned to order {order_id}")
            return dict(checker)
            
        except Exception as e:
            self.logger.error(f"❌ Error assigning checker: {e}")
            return None
    
    async def assign_courier(self, order_id: int, zone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Назначение курьера с минимальной нагрузкой"""
        
        try:
            conn = await get_db_connection()
            
            # Получаем курьера с минимальной нагрузкой
            courier = await conn.fetchrow("""
                SELECT id, telegram_id, name, active_orders, zone
                FROM users
                WHERE role = $1
                AND is_active = true
                AND is_online = true
                AND (zone = $2 OR $2 IS NULL)
                ORDER BY active_orders ASC, last_assigned_at ASC
                LIMIT 1
            """, UserRole.COURIER.value, zone)
            
            if not courier:
                self.logger.warning(f"⚠️ No available courier found for order {order_id}")
                await conn.close()
                return None
            
            # Назначаем курьера заказу
            await conn.execute("""
                UPDATE orders
                SET courier_id = $1,
                    status = $2,
                    courier_assigned_at = $3,
                    updated_at = $3
                WHERE id = $4
            """, courier["id"], OrderStatus.WAITING_COURIER.value, datetime.now(), order_id)
            
            # Увеличиваем нагрузку курьера
            await conn.execute("""
                UPDATE users
                SET active_orders = active_orders + 1,
                last_assigned_at = $1
                WHERE id = $2
            """, datetime.now(), courier["id"])
            
            await conn.close()
            
            # Отправляем уведомление курьеру
            order = await self._get_order_details(order_id)
            if order:
                await self.notification_service.notify_courier_assigned(courier["telegram_id"], order)
            
            self.logger.info(f"🚚 Courier {courier['name']} assigned to order {order_id}")
            return dict(courier)
            
        except Exception as e:
            self.logger.error(f"❌ Error assigning courier: {e}")
            return None
    
    async def release_worker(self, worker_id: int, role: UserRole):
        """Освобождение работника от нагрузки"""
        
        try:
            conn = await get_db_connection()
            
            # Уменьшаем нагрузку работника
            await conn.execute("""
                UPDATE users
                SET active_orders = GREATEST(active_orders - 1, 0)
                WHERE id = $1 AND role = $2
            """, worker_id, role.value)
            
            await conn.close()
            
            self.logger.info(f"✅ Worker {worker_id} ({role.value}) released")
            
        except Exception as e:
            self.logger.error(f"❌ Error releasing worker: {e}")
    
    async def get_worker_load(self, role: UserRole) -> List[Dict[str, Any]]:
        """Получение нагрузки работников"""
        
        try:
            conn = await get_db_connection()
            
            workers = await conn.fetch("""
                SELECT id, telegram_id, name, active_orders, is_online, zone
                FROM users
                WHERE role = $1
                AND is_active = true
                ORDER BY active_orders ASC, name ASC
            """, role.value)
            
            await conn.close()
            
            return [dict(worker) for worker in workers]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting worker load: {e}")
            return []
    
    async def get_optimal_worker(self, role: UserRole, zone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Получение оптимального работника с учетом score системы"""
        
        try:
            conn = await get_db_connection()
            
            # Рассчитываем score для каждого работника
            workers = await conn.fetch("""
                SELECT 
                    id, telegram_id, name, active_orders, is_online, zone,
                    last_assigned_at,
                    CASE 
                        WHEN last_assigned_at IS NULL THEN 0
                        ELSE EXTRACT(EPOCH FROM (NOW() - last_assigned_at)) / 60
                    END as minutes_since_last_assignment
                FROM users
                WHERE role = $1
                AND is_active = true
                AND is_online = true
                AND (zone = $2 OR $2 IS NULL)
            """, role.value, zone)
            
            if not workers:
                return None
            
            # Рассчитываем score для каждого работника
            best_worker = None
            best_score = float('inf')
            
            for worker in workers:
                # Score = (active_orders * 2) + (minutes_since_last_assignment / 10)
                active_orders = worker["active_orders"] or 0
                minutes_since_last = worker["minutes_since_last_assignment"] or 0
                
                # Чем меньше заказов и чем дольше не было назначений, тем лучше
                score = (active_orders * 2) - (minutes_since_last / 10)
                
                if score < best_score:
                    best_score = score
                    best_worker = worker
            
            await conn.close()
            
            if best_worker:
                return dict(best_worker)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting optimal worker: {e}")
            return None
    
    async def auto_assign_pipeline(self, order_id: int) -> bool:
        """Автоматический pipeline распределения"""
        
        try:
            order = await self._get_order_details(order_id)
            if not order:
                return False
            
            status = order.get("status")
            zone = order.get("zone")
            
            self.logger.info(f"🔄 Auto-assignment pipeline for order {order_id}, status: {status}")
            
            if status == OrderStatus.ACCEPTED.value:
                # Назначаем сборщика
                picker = await self.assign_picker(order_id, zone)
                if picker:
                    self.logger.info(f"✅ Picker assigned: {picker['name']}")
                    return True
                else:
                    self.logger.warning(f"⚠️ No picker available for order {order_id}")
                    return False
            
            elif status == OrderStatus.READY.value:
                # Назначаем проверщика
                checker = await self.assign_checker(order_id)
                if checker:
                    self.logger.info(f"✅ Checker assigned: {checker['name']}")
                    return True
                else:
                    self.logger.warning(f"⚠️ No checker available for order {order_id}")
                    return False
            
            elif status == OrderStatus.WAITING_COURIER.value:
                # Назначаем курьера
                courier = await self.assign_courier(order_id, zone)
                if courier:
                    self.logger.info(f"✅ Courier assigned: {courier['name']}")
                    return True
                else:
                    self.logger.warning(f"⚠️ No courier available for order {order_id}")
                    return False
            
            else:
                self.logger.info(f"ℹ️ No assignment needed for status: {status}")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in auto-assignment pipeline: {e}")
            return False
    
    async def _get_order_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получение деталей заказа"""
        
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
            self.logger.error(f"❌ Error getting order details: {e}")
            return None
    
    async def get_assignment_stats(self) -> Dict[str, Any]:
        """Получение статистики распределения"""
        
        try:
            conn = await get_db_connection()
            
            # Статистика по ролям
            stats = {}
            
            for role in [UserRole.PICKER, UserRole.CHECKER, UserRole.COURIER]:
                workers = await conn.fetch("""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN is_online = true THEN 1 END) as online,
                           SUM(active_orders) as total_load
                    FROM users
                    WHERE role = $1 AND is_active = true
                """, role.value)
                
                if workers:
                    stat = workers[0]
                    stats[role.value] = {
                        "total": stat["total"],
                        "online": stat["online"],
                        "total_load": stat["total_load"] or 0,
                        "avg_load": (stat["total_load"] or 0) / max(1, stat["online"])
                    }
            
            await conn.close()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error getting assignment stats: {e}")
            return {}
    
    async def rebalance_orders(self) -> int:
        """Перебалансировка заказов между работниками"""
        
        try:
            conn = await get_db_connection()
            
            # Находим работников с высокой нагрузкой
            overloaded_workers = await conn.fetch("""
                SELECT id, telegram_id, name, role, active_orders
                FROM users
                WHERE is_active = true
                AND is_online = true
                AND active_orders > 5
                ORDER BY active_orders DESC
            """)
            
            rebalanced_count = 0
            
            for worker in overloaded_workers:
                # Находим свободных работников той же роли
                free_workers = await conn.fetch("""
                    SELECT id, telegram_id, name
                    FROM users
                    WHERE role = $1
                    AND is_active = true
                    AND is_online = true
                    AND active_orders < 3
                    AND id != $2
                    ORDER BY active_orders ASC
                    LIMIT 1
                """, worker["role"], worker["id"])
                
                if free_workers:
                    free_worker = free_workers[0]
                    
                    # Переназначаем некоторые заказы
                    orders_to_reassign = await conn.fetch("""
                        SELECT id
                        FROM orders
                        WHERE status = 'processing'
                        AND picker_id = $1
                        LIMIT 2
                    """ if worker["role"] == "picker" else """
                        SELECT id
                        FROM orders
                        WHERE status = 'checking'
                        AND checker_id = $1
                        LIMIT 2
                    """ if worker["role"] == "checker" else """
                        SELECT id
                        FROM orders
                        WHERE status = 'waiting_courier'
                        AND courier_id = $1
                        LIMIT 2
                    """, worker["id"])
                    
                    for order in orders_to_reassign:
                        # Переназначаем заказ свободному работнику
                        field = "picker_id" if worker["role"] == "picker" else "checker_id" if worker["role"] == "checker" else "courier_id"
                        
                        await conn.execute(f"""
                            UPDATE orders
                            SET {field} = $1
                            WHERE id = $2
                        """, free_worker["id"], order["id"])
                        
                        # Обновляем нагрузку
                        await conn.execute("""
                            UPDATE users
                            SET active_orders = active_orders - 1
                            WHERE id = $1
                        """, worker["id"])
                        
                        await conn.execute("""
                            UPDATE users
                            SET active_orders = active_orders + 1
                            WHERE id = $1
                        """, free_worker["id"])
                        
                        rebalanced_count += 1
                        
                        # Отправляем уведомление
                        await self.bot.send_message(
                            free_worker["telegram_id"],
                            f"🔄 <b>Новый заказ переназначен</b>\n\n"
                            f"Заказ #{order['id']} переназначен вам"
                        )
            
            await conn.close()
            
            self.logger.info(f"🔄 Rebalanced {rebalanced_count} orders")
            return rebalanced_count
            
        except Exception as e:
            self.logger.error(f"❌ Error rebalancing orders: {e}")
            return 0

# Удобные функции для использования
async def assign_picker(order_id: int, zone: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Назначение сборщика (удобная функция)"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    service = AssignmentService(bot)
    return await service.assign_picker(order_id, zone)

async def assign_checker(order_id: int) -> Optional[Dict[str, Any]]:
    """Назначение проверщика (удобная функция)"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    service = AssignmentService(bot)
    return await service.assign_checker(order_id)

async def assign_courier(order_id: int, zone: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Назначение курьера (удобная функция)"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    service = AssignmentService(bot)
    return await service.assign_courier(order_id, zone)

async def auto_assign_order(order_id: int) -> bool:
    """Автоматическое распределение заказа (удобная функция)"""
    from aiogram import Bot
    bot = Bot.get_current() or Bot(token="dummy")
    service = AssignmentService(bot)
    return await service.auto_assign_pipeline(order_id)
