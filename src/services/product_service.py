from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import relationship
from typing import Optional, List
from src.models.product import Product
from src.models.category import Category
from src.models.log import Log


class ProductService:
    """Service for product management operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_product(
        self,
        name: str,
        price: float,
        category_id: int,
        description: Optional[str] = None,
        stock_quantity: int = 0,
        image_url: Optional[str] = None
    ) -> Product:
        """Create a new product"""
        product = Product(
            name=name,
            price=price,
            category_id=category_id,
            description=description,
            stock_quantity=stock_quantity,
            image_url=image_url
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        
        await self._log_action("product_created", None, f"Product {name} created")
        
        return product
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        result = await self.session.execute(
            select(Product).where(Product.id == product_id, Product.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_all_products(self) -> List[Product]:
        """Get all active products"""
        result = await self.session.execute(
            select(Product).where(Product.is_active == True).order_by(Product.name)
        )
        return result.scalars().all()
    
    async def get_products_by_category(self, category_id: int) -> List[Product]:
        """Get products by category"""
        result = await self.session.execute(
            select(Product).where(
                Product.category_id == category_id, 
                Product.is_active == True
            ).order_by(Product.name)
        )
        return result.scalars().all()
    
    async def search_products(self, query: str) -> List[Product]:
        """Search products by name"""
        result = await self.session.execute(
            select(Product).where(
                Product.name.ilike(f"%{query}%"),
                Product.is_active == True
            ).order_by(Product.name)
        )
        return result.scalars().all()
    
    async def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
        stock_quantity: Optional[int] = None,
        image_url: Optional[str] = None
    ) -> Optional[Product]:
        """Update product"""
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if price is not None:
            update_data['price'] = price
        if description is not None:
            update_data['description'] = description
        if stock_quantity is not None:
            update_data['stock_quantity'] = stock_quantity
        if image_url is not None:
            update_data['image_url'] = image_url
        
        if update_data:
            result = await self.session.execute(
                update(Product).where(Product.id == product_id).values(**update_data)
            )
            await self.session.commit()
            
            product = await self.get_product_by_id(product_id)
            if product:
                await self._log_action("product_updated", None, f"Product {product.name} updated")
            
            return product
        
        return await self.get_product_by_id(product_id)
    
    async def delete_product(self, product_id: int) -> bool:
        """Soft delete product"""
        result = await self.session.execute(
            update(Product).where(Product.id == product_id).values(is_active=False)
        )
        await self.session.commit()
        
        if result.rowcount > 0:
            await self._log_action("product_deleted", None, f"Product {product_id} deleted")
            return True
        return False
    
    async def update_stock(self, product_id: int, quantity: int) -> Optional[Product]:
        """Update product stock quantity"""
        result = await self.session.execute(
            update(Product).where(Product.id == product_id).values(stock_quantity=quantity)
        )
        await self.session.commit()
        
        product = await self.get_product_by_id(product_id)
        if product:
            await self._log_action("stock_updated", None, f"Stock for {product.name} updated to {quantity}")
        
        return product
    
    async def decrease_stock(self, product_id: int, quantity: int) -> Optional[Product]:
        """Decrease product stock quantity"""
        product = await self.get_product_by_id(product_id)
        if product and product.stock_quantity >= quantity:
            new_quantity = product.stock_quantity - quantity
            return await self.update_stock(product_id, new_quantity)
        return None
    
    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock"""
        result = await self.session.execute(
            select(Product).where(
                Product.stock_quantity <= threshold,
                Product.is_active == True
            ).order_by(Product.stock_quantity)
        )
        return result.scalars().all()
    
    async def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        result = await self.session.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name)
        )
        return result.scalars().all()
    
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        result = await self.session.execute(
            select(Category).where(Category.name == name, Category.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get product by name"""
        result = await self.session.execute(
            select(Product).where(Product.name == name, Product.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def _log_action(self, action: str, user_id: Optional[int], details: str):
        """Log product action"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
