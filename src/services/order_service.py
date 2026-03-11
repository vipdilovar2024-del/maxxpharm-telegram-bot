"""
📦 Сервис управления заказами MAXXPHARM CRM
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models.database import (
    Order, OrderStatus, OrderItem, User, Pharmacy,
    Payment, PaymentType, Debt
)
from ..database import get_db


class OrderService:
    """Сервис для работы с заказами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_order(
        self,
        client_id: int,
        pharmacy_id: int,
        items: List[Dict[str, Any]],
        notes: Optional[str] = None,
        delivery_address: Optional[str] = None
    ) -> Order:
        """Создание нового заказа"""
        
        # Генерация номера заказа
        order_number = await self._generate_order_number()
        
        # Расчет общей суммы
        total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
        
        # Создание заказа
        order = Order(
            order_number=order_number,
            client_id=client_id,
            pharmacy_id=pharmacy_id,
            status=OrderStatus.CREATED,
            total_amount=total_amount,
            notes=notes,
            delivery_address=delivery_address
        )
        
        self.session.add(order)
        await self.session.flush()  # Получаем ID заказа
        
        # Создание элементов заказа
        for item_data in items:
            item = OrderItem(
                order_id=order.id,
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['quantity'] * item_data['unit_price']
            )
            self.session.add(item)
        
        await self.session.commit()
        await self.session.refresh(order)
        
        return order
    
    async def _generate_order_number(self) -> str:
        """Генерация уникального номера заказа"""
        today = datetime.now().strftime("%Y%m%d")
        
        # Получаем количество заказов за сегодня
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= today_start)
        )
        count = result.scalar() or 0
        
        return f"ORD-{today}-{count + 1:04d}"
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Получение заказа по ID с элементами"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .options(selectinload(Order.payments))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Получение заказа по номеру"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .options(selectinload(Order.payments))
            .where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Получение заказов по статусу"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .options(selectinload(Order.client))
            .where(Order.status == status.value)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_orders_by_client(self, client_id: int) -> List[Order]:
        """Получение заказов клиента"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.client_id == client_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        operator_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[Order]:
        """Обновление статуса заказа"""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        old_status = order.status
        order.status = new_status.value
        order.updated_at = datetime.utcnow()
        
        # Установка временных меток
        if new_status == OrderStatus.CONFIRMED:
            order.confirmed_at = datetime.utcnow()
            order.operator_id = operator_id
        elif new_status == OrderStatus.COLLECTED:
            order.collected_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        
        if notes:
            order.notes = notes
        
        await self.session.commit()
        
        # Логирование изменения статуса
        await self._log_order_status_change(
            order_id, old_status, new_status.value, operator_id
        )
        
        return order
    
    async def assign_order_to_employee(
        self,
        order_id: int,
        employee_id: int,
        employee_role: str
    ) -> Optional[Order]:
        """Назначение заказа сотруднику"""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        if employee_role == "collector":
            order.collector_id = employee_id
        elif employee_role == "checker":
            order.checker_id = employee_id
        elif employee_role == "courier":
            order.courier_id = employee_id
        
        order.updated_at = datetime.utcnow()
        await self.session.commit()
        
        return order
    
    async def reject_order(
        self,
        order_id: int,
        operator_id: int,
        rejection_reason: str
    ) -> Optional[Order]:
        """Отклонение заказа"""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        order.status = OrderStatus.REJECTED.value
        order.operator_id = operator_id
        order.rejection_reason = rejection_reason
        order.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        # Логирование
        await self._log_order_status_change(
            order_id, OrderStatus.CREATED.value, OrderStatus.REJECTED.value, operator_id
        )
        
        return order
    
    async def get_pending_orders_for_operator(self) -> List[Order]:
        """Получение заказов, ожидающих рассмотрения оператором"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .options(selectinload(Order.client))
            .where(Order.status == OrderStatus.CREATED.value)
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_orders_for_collector(self) -> List[Order]:
        """Получение заказов для сборщика"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status == OrderStatus.CONFIRMED.value)
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_orders_for_checker(self) -> List[Order]:
        """Получение заказов для проверщика"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status == OrderStatus.COLLECTED.value)
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_orders_for_courier(self) -> List[Order]:
        """Получение заказов для курьера"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status == OrderStatus.READY_FOR_DELIVERY.value)
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_order_statistics(self) -> Dict[str, Any]:
        """Получение статистики заказов"""
        # Общая статистика
        total_result = await self.session.execute(select(func.count(Order.id)))
        total_orders = total_result.scalar()
        
        # Статистика по статусам
        status_stats = {}
        for status in OrderStatus:
            status_result = await self.session.execute(
                select(func.count(Order.id))
                .where(Order.status == status.value)
            )
            status_stats[status.value] = status_result.scalar()
        
        # Статистика за сегодня
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.session.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= today)
        )
        today_orders = today_result.scalar()
        
        # Общая сумма заказов
        total_amount_result = await self.session.execute(
            select(func.sum(Order.total_amount))
        )
        total_amount = total_amount_result.scalar() or 0
        
        return {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "status_distribution": status_stats,
            "total_amount": float(total_amount)
        }
    
    async def search_orders(self, query: str) -> List[Order]:
        """Поиск заказов по номеру или имени клиента"""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .options(selectinload(Order.client))
            .join(User, Order.client_id == User.id)
            .where(
                or_(
                    Order.order_number.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def _log_order_status_change(
        self,
        order_id: int,
        old_status: str,
        new_status: str,
        operator_id: Optional[int] = None
    ):
        """Логирование изменения статуса заказа"""
        from .user_service import UserService
        
        user_service = UserService(self.session)
        await user_service.log_activity(
            user_id=operator_id or 0,
            action="order_status_changed",
            entity_type="order",
            entity_id=order_id,
            details={
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Функция для получения сервиса
async def get_order_service() -> OrderService:
    """Получение экземпляра OrderService"""
    async for session in get_db():
        return OrderService(session)
