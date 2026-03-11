"""
🗄️ Модели базы данных MAXXPHARM CRM
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, 
    Text, ForeignKey, JSON, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserRole(str, Enum):
    """Роли пользователей"""
    DIRECTOR = "director"
    ADMIN = "admin"
    OPERATOR = "operator"
    COLLECTOR = "collector"
    CHECKER = "checker"
    COURIER = "courier"
    SALES_REP = "sales_rep"
    CLIENT = "client"


class OrderStatus(str, Enum):
    """Статусы заказов"""
    CREATED = "created"
    PENDING_OPERATOR = "pending_operator"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COLLECTING = "collecting"
    COLLECTED = "collected"
    CHECKING = "checking"
    READY_FOR_DELIVERY = "ready_for_delivery"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DEBT = "debt"


class PaymentType(str, Enum):
    """Типы оплаты"""
    CASH = "cash"
    ONLINE = "online"
    DEBT = "debt"


class User(Base):
    """Пользователи системы"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), default=UserRole.CLIENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    pharmacy = relationship("Pharmacy", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="client")
    locations = relationship("Location", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")


class Pharmacy(Base):
    """Аптеки (клиенты)"""
    __tablename__ = "pharmacies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    license_number = Column(String(100), nullable=True)
    contact_person = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    user = relationship("User", back_populates="pharmacy")
    orders = relationship("Order", back_populates="pharmacy")


class Order(Base):
    """Заказы"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    collector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    checker_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    status = Column(String(50), default=OrderStatus.CREATED, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    debt_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительная информация
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    delivery_address = Column(Text, nullable=True)
    
    # Отношения
    client = relationship("User", foreign_keys=[client_id], back_populates="orders")
    pharmacy = relationship("Pharmacy", back_populates="orders")
    operator = relationship("User", foreign_keys=[operator_id])
    collector = relationship("User", foreign_keys=[collector_id])
    checker = relationship("User", foreign_keys=[checker_id])
    courier = relationship("User", foreign_keys=[courier_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Элементы заказа"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Отношения
    order = relationship("Order", back_populates="items")


class Payment(Base):
    """Платежи"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    payment_type = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Детали оплаты
    bank_name = Column(String(255), nullable=True)
    recipient_name = Column(String(255), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    check_image_url = Column(String(500), nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Отношения
    order = relationship("Order", back_populates="payments")


class Debt(Base):
    """Долги"""
    __tablename__ = "debts"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    
    # Статус долга
    is_active = Column(Boolean, default=True, nullable=False)
    collected_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Торговый представитель
    collected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    client = relationship("User", foreign_keys=[client_id])
    collector = relationship("User", foreign_keys=[collected_by])


class Location(Base):
    """Геолокация"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Координаты
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    address = Column(Text, nullable=True)
    
    # Метаданные
    accuracy = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    user = relationship("User", back_populates="locations")


class ActivityLog(Base):
    """Лог действий"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)  # order, user, payment и т.д.
    entity_id = Column(Integer, nullable=True)
    
    # Детали
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    user = relationship("User", back_populates="activity_logs")
