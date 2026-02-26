from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import Optional, List
from src.models.user import User
from src.models.log import Log


class UserService:
    """Service for user management operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(
        self, 
        telegram_id: int, 
        full_name: str, 
        username: Optional[str] = None,
        role: str = "CLIENT"
    ) -> User:
        """Create a new user"""
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            role=role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        # Log user creation
        await self._log_action("user_created", user.id, f"User {full_name} created")
        
        return user
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        result = await self.session.execute(select(User).where(User.is_active == True))
        return result.scalars().all()
    
    async def update_user_role(self, user_id: int, new_role: str) -> Optional[User]:
        """Update user role"""
        result = await self.session.execute(
            update(User).where(User.id == user_id).values(role=new_role)
        )
        await self.session.commit()
        
        user = await self.get_user_by_id(user_id)
        if user:
            await self._log_action("role_updated", user_id, f"Role changed to {new_role}")
        
        return user
    
    async def block_user(self, user_id: int) -> bool:
        """Block user"""
        result = await self.session.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )
        await self.session.commit()
        
        if result.rowcount > 0:
            await self._log_action("user_blocked", user_id, "User blocked")
            return True
        return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        result = await self.session.execute(
            update(User).where(User.id == user_id).values(is_active=True)
        )
        await self.session.commit()
        
        if result.rowcount > 0:
            await self._log_action("user_unblocked", user_id, "User unblocked")
            return True
        return False
    
    async def update_user_phone(self, user_id: int, phone: str) -> Optional[User]:
        """Update user phone number"""
        result = await self.session.execute(
            update(User).where(User.id == user_id).values(phone=phone)
        )
        await self.session.commit()
        
        return await self.get_user_by_id(user_id)
    
    async def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        result = await self.session.execute(
            select(User).where(User.role == role, User.is_active == True)
        )
        return result.scalars().all()
    
    async def _log_action(self, action: str, user_id: Optional[int], details: str):
        """Log user action"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
