from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import Optional, List
from src.models.category import Category
from src.models.log import Log


class CategoryService:
    """Service for category management operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Category:
        """Create a new category"""
        category = Category(
            name=name,
            description=description
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        
        await self._log_action("category_created", None, f"Category {name} created")
        
        return category
    
    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        result = await self.session.execute(
            select(Category).where(Category.name == name, Category.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_all_categories(self) -> List[Category]:
        """Get all active categories"""
        result = await self.session.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name)
        )
        return result.scalars().all()
    
    async def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Category]:
        """Update category"""
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        
        if update_data:
            result = await self.session.execute(
                update(Category).where(Category.id == category_id).values(**update_data)
            )
            await self.session.commit()
            
            category = await self.get_category_by_id(category_id)
            if category:
                await self._log_action("category_updated", None, f"Category {category.name} updated")
            
            return category
        
        return await self.get_category_by_id(category_id)
    
    async def delete_category(self, category_id: int) -> bool:
        """Soft delete category"""
        result = await self.session.execute(
            update(Category).where(Category.id == category_id).values(is_active=False)
        )
        await self.session.commit()
        
        if result.rowcount > 0:
            await self._log_action("category_deleted", None, f"Category {category_id} deleted")
            return True
        return False
    
    async def _log_action(self, action: str, user_id: Optional[int], details: str):
        """Log category action"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
