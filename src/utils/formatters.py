from datetime import datetime
from typing import Union
from decimal import Decimal


def format_price(price: Union[int, float, Decimal]) -> str:
    """Format price with currency symbol"""
    if isinstance(price, (int, float)):
        return f"{price:,.0f} ₽"
    elif isinstance(price, Decimal):
        return f"{price:,.0f} ₽"
    return f"{price} ₽"


def format_date(date: datetime, format_type: str = "full") -> str:
    """Format datetime according to type"""
    if format_type == "full":
        return date.strftime("%d.%m.%Y %H:%M")
    elif format_type == "date":
        return date.strftime("%d.%m.%Y")
    elif format_type == "time":
        return date.strftime("%H:%M")
    elif format_type == "short":
        return date.strftime("%d.%m %H:%M")
    else:
        return date.strftime("%d.%m.%Y %H:%M")


def format_order_status(status: str) -> str:
    """Format order status with emoji"""
    status_map = {
        "NEW": "🆕 Новый",
        "CONFIRMED": "✅ Подтвержден",
        "IN_PROGRESS": "⏳ В обработке",
        "IN_DELIVERY": "🚚 В доставке",
        "COMPLETED": "✔️ Завершен",
        "CANCELLED": "❌ Отменен"
    }
    return status_map.get(status, status)


def format_user_role(role: str) -> str:
    """Format user role with emoji"""
    role_map = {
        "CLIENT": "👤 Клиент",
        "COURIER": "🚚 Курьер",
        "MANAGER": "📦 Менеджер",
        "ADMIN": "👑 Администратор",
        "SUPER_ADMIN": "🔥 Супер-администратор"
    }
    return role_map.get(role, role)


def format_phone(phone: str) -> str:
    """Format phone number"""
    if not phone:
        return "Не указан"
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 12 and digits.startswith('998'):
        # Uzbekistan format
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}"
    elif len(digits) == 11 and digits.startswith('7'):
        # Russian format
        return f"+{digits[:1]} {digits[1:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}"
    else:
        return phone


def format_address(address: str) -> str:
    """Format address"""
    if not address:
        return "Не указан"
    return address.strip()


def format_product_info(product) -> str:
    """Format product information"""
    stock_status = "✅ В наличии" if product.stock_quantity > 0 else "❌ Нет в наличии"
    
    text = f"🛍️ *{product.name}*\n\n"
    text += f"💰 Цена: {format_price(product.price)}\n"
    text += f"📦 В наличии: {product.stock_quantity} шт. {stock_status}\n"
    
    if product.category:
        text += f"🏷️ Категория: {product.category.name}\n"
    
    if product.description:
        text += f"\n📝 Описание: {product.description}\n"
    
    return text


def format_order_info(order) -> str:
    """Format order information"""
    text = f"📦 *Заказ #{order.id}*\n\n"
    text += f"👤 Клиент: {order.user.full_name}\n"
    text += f"📊 Статус: {format_order_status(order.status.value)}\n"
    text += f"💰 Сумма: {format_price(order.total_amount)}\n"
    text += f"📅 Создан: {format_date(order.created_at)}\n"
    
    if order.phone:
        text += f"📞 Телефон: {format_phone(order.phone)}\n"
    
    if order.delivery_address:
        text += f"📍 Адрес: {format_address(order.delivery_address)}\n"
    
    if order.notes:
        text += f"📝 Примечание: {order.notes}\n"
    
    # Add order items
    if order.order_items:
        text += f"\n🛍️ *Товары в заказе:*\n"
        for item in order.order_items:
            text += f"• {item.product.name} - {item.quantity} шт. × {format_price(item.price)} = {format_price(item.price * item.quantity)}\n"
    
    return text
