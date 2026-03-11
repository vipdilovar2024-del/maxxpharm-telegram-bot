"""
🤖 Обработчики MAXXPHARM CRM
"""

from .client import ClientHandlers
from .operator import OperatorHandlers
from .admin import AdminHandlers
from .courier import CourierHandlers
from .common import CommonHandlers

__all__ = [
    "ClientHandlers",
    "OperatorHandlers",
    "AdminHandlers", 
    "CourierHandlers",
    "CommonHandlers"
]
