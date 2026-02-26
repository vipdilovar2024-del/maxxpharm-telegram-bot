from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.models.user import User
from src.models.log import Log


class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def authenticate_user(self, telegram_id: int, full_name: str, username: Optional[str] = None) -> User:
        """Authenticate or register user"""
        # Try to find existing user
        from src.services.user_service import UserService
        user_service = UserService(self.session)
        
        user = await user_service.get_user_by_telegram_id(telegram_id)
        
        if user and not user.is_active:
            raise ValueError("User is blocked")
        
        if not user:
            # Create new user
            user = await user_service.create_user(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                role="CLIENT"
            )
            await self._log_action("user_registered", user.id, f"New user registered: {full_name}")
        else:
            await self._log_action("user_login", user.id, f"User logged in: {full_name}")
        
        return user
    
    async def check_permission(self, user: User, required_role: str) -> bool:
        """Check if user has required permission"""
        role_hierarchy = {
            "CLIENT": 0,
            "COURIER": 1,
            "MANAGER": 2,
            "ADMIN": 3,
            "SUPER_ADMIN": 4
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    async def is_admin(self, user: User) -> bool:
        """Check if user is admin or higher"""
        return await self.check_permission(user, "ADMIN")
    
    async def is_manager(self, user: User) -> bool:
        """Check if user is manager or higher"""
        return await self.check_permission(user, "MANAGER")
    
    async def is_courier(self, user: User) -> bool:
        """Check if user is courier or higher"""
        return await self.check_permission(user, "COURIER")
    
    async def can_access_admin_panel(self, user: User) -> bool:
        """Check if user can access admin panel"""
        return await self.is_admin(user)
    
    async def can_manage_orders(self, user: User) -> bool:
        """Check if user can manage orders"""
        return await self.is_manager(user)
    
    async def can_deliver_orders(self, user: User) -> bool:
        """Check if user can deliver orders"""
        return await self.is_courier(user)
    
    async def can_manage_users(self, user: User) -> bool:
        """Check if user can manage other users"""
        return await self.check_permission(user, "SUPER_ADMIN")
    
    async def can_manage_products(self, user: User) -> bool:
        """Check if user can manage products"""
        return await self.is_admin(user)
    
    async def can_view_statistics(self, user: User) -> bool:
        """Check if user can view statistics"""
        return await self.is_admin(user)
    
    async def _log_action(self, action: str, user_id: Optional[int], details: str):
        """Log authentication action"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
