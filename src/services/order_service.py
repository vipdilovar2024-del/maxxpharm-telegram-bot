from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from decimal import Decimal
from src.models.order import Order, OrderStatus
from src.models.order_item import OrderItem
from src.models.product import Product
from src.models.log import Log


class OrderService:
    """Service for order management operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_order(
        self,
        user_id: int,
        delivery_address: Optional[str] = None,
        phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Order:
        """Create a new order"""
        order = Order(
            user_id=user_id,
            status=OrderStatus.NEW,
            total_amount=Decimal('0.00'),
            delivery_address=delivery_address,
            phone=phone,
            notes=notes
        )
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        
        await self._log_action("order_created", user_id, f"Order {order.id} created")
        
        return order
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID with items"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.product))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.product))
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def add_order_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int
    ) -> Optional[OrderItem]:
        """Add item to order"""
        # Get product
        product_result = await self.session.execute(
            select(Product).where(Product.id == product_id, Product.is_active == True)
        )
        product = product_result.scalar_one_or_none()
        
        if not product or product.stock_quantity < quantity:
            return None
        
        # Check if item already exists in order
        existing_item_result = await self.session.execute(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.product_id == product_id
            )
        )
        existing_item = existing_item_result.scalar_one_or_none()
        
        if existing_item:
            # Update existing item
            new_quantity = existing_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                return None
            
            result = await self.session.execute(
                update(OrderItem)
                .where(OrderItem.id == existing_item.id)
                .values(quantity=new_quantity)
            )
        else:
            # Create new item
            existing_item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                price=product.price
            )
            self.session.add(existing_item)
        
        await self.session.commit()
        await self.session.refresh(existing_item)
        
        # Update order total
        await self._update_order_total(order_id)
        
        return existing_item
    
    async def remove_order_item(self, order_id: int, product_id: int) -> bool:
        """Remove item from order"""
        result = await self.session.execute(
            delete(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.product_id == product_id
            )
        )
        await self.session.commit()
        
        if result.rowcount > 0:
            await self._update_order_total(order_id)
            return True
        return False
    
    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        user_id: Optional[int] = None
    ) -> Optional[Order]:
        """Update order status"""
        result = await self.session.execute(
            update(Order).where(Order.id == order_id).values(status=new_status)
        )
        await self.session.commit()
        
        order = await self.get_order_by_id(order_id)
        if order:
            await self._log_action(
                "order_status_updated", 
                user_id, 
                f"Order {order_id} status changed to {new_status}"
            )
        
        return order
    
    async def confirm_order(self, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Confirm order and decrease stock"""
        order = await self.get_order_by_id(order_id)
        if not order or order.status != OrderStatus.NEW:
            return None
        
        # Check stock availability
        for item in order.order_items:
            if item.product.stock_quantity < item.quantity:
                return None
        
        # Decrease stock
        for item in order.order_items:
            await self.session.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(stock_quantity=Product.stock_quantity - item.quantity)
            )
        
        # Update order status
        return await self.update_order_status(order_id, OrderStatus.CONFIRMED, user_id)
    
    async def cancel_order(self, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Cancel order and restore stock"""
        order = await self.get_order_by_id(order_id)
        if not order or order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return None
        
        # Restore stock if order was confirmed
        if order.status == OrderStatus.CONFIRMED:
            for item in order.order_items:
                await self.session.execute(
                    update(Product)
                    .where(Product.id == item.product_id)
                    .values(stock_quantity=Product.stock_quantity + item.quantity)
                )
        
        # Update order status
        return await self.update_order_status(order_id, OrderStatus.CANCELLED, user_id)
    
    async def _update_order_total(self, order_id: int):
        """Update order total amount"""
        items_result = await self.session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = items_result.scalars().all()
        
        total = sum(item.price * item.quantity for item in items)
        
        await self.session.execute(
            update(Order).where(Order.id == order_id).values(total_amount=total)
        )
        await self.session.commit()
    
    async def get_order_statistics(self) -> dict:
        """Get order statistics"""
        stats = {}
        
        for status in OrderStatus:
            result = await self.session.execute(
                select(Order).where(Order.status == status)
            )
            count = len(result.scalars().all())
            stats[status.value] = count
        
        return stats
    
    async def _log_action(self, action: str, user_id: Optional[int], details: str):
        """Log order action"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
