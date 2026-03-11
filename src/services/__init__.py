"""
🔧 Сервисы MAXXPHARM CRM
"""

from .user_service import UserService
from .order_service import OrderService
from .payment_service import PaymentService
from .analytics_service import AnalyticsService
from .notification_service import NotificationService
from .location_service import LocationService

__all__ = [
    "UserService",
    "OrderService", 
    "PaymentService",
    "AnalyticsService",
    "NotificationService",
    "LocationService"
]
