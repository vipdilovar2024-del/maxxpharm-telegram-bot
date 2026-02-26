from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
from src.models.log import Log
from src.models.user import User


class LogService:
    """Service for system logging operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_log(
        self,
        action: str,
        user_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> Log:
        """Create a new log entry"""
        log = Log(action=action, user_id=user_id, details=details)
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def get_all_logs(self, limit: int = 100) -> List[Log]:
        """Get all logs"""
        result = await self.session.execute(
            select(Log)
            .options(selectinload(Log.user))
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_user_logs(self, user_id: int, limit: int = 50) -> List[Log]:
        """Get logs for specific user"""
        result = await self.session.execute(
            select(Log)
            .where(Log.user_id == user_id)
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_logs_by_action(self, action: str, limit: int = 50) -> List[Log]:
        """Get logs by action type"""
        result = await self.session.execute(
            select(Log)
            .where(Log.action == action)
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Log]:
        """Get logs within date range"""
        result = await self.session.execute(
            select(Log)
            .where(Log.created_at >= start_date, Log.created_at <= end_date)
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_logs(self, hours: int = 24, limit: int = 50) -> List[Log]:
        """Get recent logs within specified hours"""
        start_date = datetime.now() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Log)
            .where(Log.created_at >= start_date)
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_action_statistics(self, days: int = 7) -> dict:
        """Get action statistics for specified days"""
        start_date = datetime.now() - timedelta(days=days)
        
        result = await self.session.execute(
            select(Log.action, func.count(Log.id))
            .where(Log.created_at >= start_date)
            .group_by(Log.action)
            .order_by(desc(func.count(Log.id)))
        )
        
        stats = {}
        for action, count in result.all():
            stats[action] = count
        
        return stats
    
    async def get_user_activity_summary(self, days: int = 7) -> List[dict]:
        """Get user activity summary"""
        start_date = datetime.now() - timedelta(days=days)
        
        result = await self.session.execute(
            select(
                User.full_name,
                User.username,
                func.count(Log.id).label('action_count')
            )
            .join(Log, User.id == Log.user_id)
            .where(Log.created_at >= start_date)
            .group_by(User.id, User.full_name, User.username)
            .order_by(desc(func.count(Log.id)))
            .limit(10)
        )
        
        return [
            {
                'full_name': row.full_name,
                'username': row.username,
                'action_count': row.action_count
            }
            for row in result.all()
        ]
    
    async def clear_old_logs(self, days: int = 90) -> int:
        """Clear logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        from sqlalchemy import delete
        result = await self.session.execute(
            delete(Log).where(Log.created_at < cutoff_date)
        )
        await self.session.commit()
        
        return result.rowcount
