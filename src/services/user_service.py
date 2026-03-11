"""
👤 Сервис управления пользователями MAXXPHARM CRM
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from ..models.database import User, UserRole, Pharmacy, ActivityLog
from ..database import get_db


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        telegram_id: int,
        full_name: str,
        username: Optional[str] = None,
        phone: Optional[str] = None,
        role: UserRole = UserRole.CLIENT
    ) -> User:
        """Создание нового пользователя"""
        
        # Проверяем, существует ли пользователь
        existing_user = await self.get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            phone=phone,
            role=role.value
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        # Логирование действия
        await self.log_activity(
            user_id=user.id,
            action="user_created",
            details={
                "telegram_id": telegram_id,
                "role": role.value
            }
        )
        
        return user
    
    async def update_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """Обновление роли пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        old_role = user.role
        user.role = new_role.value
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        # Логирование изменения роли
        await self.log_activity(
            user_id=user_id,
            action="role_changed",
            details={
                "old_role": old_role,
                "new_role": new_role.value
            }
        )
        
        return user
    
    async def block_user(self, user_id: int) -> bool:
        """Блокировка пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_blocked = True
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        # Логирование блокировки
        await self.log_activity(
            user_id=user_id,
            action="user_blocked",
            details={"blocked_by": "admin"}
        )
        
        return True
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Получение пользователей по роли"""
        result = await self.session.execute(
            select(User).where(User.role == role.value, User.is_active == True)
        )
        return result.scalars().all()
    
    async def get_active_users(self) -> List[User]:
        """Получение всех активных пользователей"""
        result = await self.session.execute(
            select(User).where(User.is_active == True, User.is_blocked == False)
        )
        return result.scalars().all()
    
    async def search_users(self, query: str) -> List[User]:
        """Поиск пользователей по имени или username"""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.phone.ilike(search_pattern)
                ),
                User.is_active == True
            )
        )
        return result.scalars().all()
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Получение статистики пользователей"""
        # Общее количество пользователей
        total_result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        total_users = len(total_result.scalars().all())
        
        # Пользователи по ролям
        role_stats = {}
        for role in UserRole:
            role_result = await self.session.execute(
                select(User).where(
                    User.role == role.value,
                    User.is_active == True
                )
            )
            role_stats[role.value] = len(role_result.scalars().all())
        
        # Заблокированные пользователи
        blocked_result = await self.session.execute(
            select(User).where(User.is_blocked == True)
        )
        blocked_users = len(blocked_result.scalars().all())
        
        return {
            "total_users": total_users,
            "blocked_users": blocked_users,
            "role_distribution": role_stats
        }
    
    async def create_pharmacy_for_user(
        self,
        user_id: int,
        name: str,
        address: str,
        license_number: Optional[str] = None,
        contact_person: Optional[str] = None
    ) -> Optional[Pharmacy]:
        """Создание аптеки для пользователя"""
        
        # Проверяем, есть ли уже аптека
        existing_pharmacy = await self.session.execute(
            select(Pharmacy).where(Pharmacy.user_id == user_id)
        )
        if existing_pharmacy.scalar_one_or_none():
            return None
        
        pharmacy = Pharmacy(
            user_id=user_id,
            name=name,
            address=address,
            license_number=license_number,
            contact_person=contact_person
        )
        
        self.session.add(pharmacy)
        await self.session.commit()
        await self.session.refresh(pharmacy)
        
        # Логирование
        await self.log_activity(
            user_id=user_id,
            action="pharmacy_created",
            details={
                "pharmacy_name": name,
                "address": address
            }
        )
        
        return pharmacy
    
    async def log_activity(
        self,
        user_id: int,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Логирование действия пользователя"""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {}
        )
        
        self.session.add(log)
        await self.session.commit()
        
        return log
    
    async def get_user_activity_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[ActivityLog]:
        """Получение истории действий пользователя"""
        result = await self.session.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Функция для получения сервиса
async def get_user_service() -> UserService:
    """Получение экземпляра UserService"""
    async for session in get_db():
        return UserService(session)
