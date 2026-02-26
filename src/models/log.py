from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base


class Log(Base):
    """System log model"""
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="logs")
    
    def __repr__(self):
        return f"<Log(id={self.id}, action={self.action}, user_id={self.user_id})>"
