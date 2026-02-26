import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid phone number (10-15 digits)
    return len(digits) >= 10 and len(digits) <= 15 and digits.isdigit()


def validate_email(email: str) -> bool:
    """Validate email address"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_name(name: str) -> bool:
    """Validate person name"""
    if not name:
        return False
    
    # Check if name contains only letters, spaces, and some punctuation
    pattern = r'^[a-zA-Zа-яА-ЯёЁ\s\-\.]+$'
    return bool(re.match(pattern, name.strip())) and len(name.strip()) >= 2


def validate_price(price: str) -> bool:
    """Validate price"""
    if not price:
        return False
    
    try:
        price_value = float(price.replace(',', '.'))
        return price_value > 0
    except ValueError:
        return False


def validate_quantity(quantity: str) -> bool:
    """Validate quantity"""
    if not quantity:
        return False
    
    try:
        qty = int(quantity)
        return qty > 0 and qty <= 1000  # Max 1000 items
    except ValueError:
        return False


def validate_address(address: str) -> bool:
    """Validate address"""
    if not address:
        return False
    
    # Basic validation - at least 5 characters
    return len(address.strip()) >= 5


def validate_product_name(name: str) -> bool:
    """Validate product name"""
    if not name:
        return False
    
    # Product name should be at least 2 characters and max 255
    return 2 <= len(name.strip()) <= 255


def validate_category_name(name: str) -> bool:
    """Validate category name"""
    if not name:
        return False
    
    # Category name should be at least 2 characters and max 100
    return 2 <= len(name.strip()) <= 100


def validate_order_id(order_id: str) -> bool:
    """Validate order ID"""
    if not order_id:
        return False
    
    try:
        order_id_int = int(order_id)
        return order_id_int > 0
    except ValueError:
        return False


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    return sanitized[:max_length].strip()


def validate_telegram_username(username: str) -> bool:
    """Validate Telegram username"""
    if not username:
        return True  # Username is optional
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Telegram username rules: 5-32 characters, letters, numbers, underscores
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return re.match(pattern, username) is not None
