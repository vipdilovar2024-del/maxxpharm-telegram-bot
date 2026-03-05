"""
📦 Order Cards - Карточки заказов с кнопками действий
aiogram 3.4.1 compatible
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any, Optional

def format_order_text(order: Dict[str, Any]) -> str:
    """Форматирование текста карточки заказа"""
    
    # Эмодзи для статусов
    status_emoji = {
        "created": "📝",
        "waiting_payment": "💳",
        "accepted": "✅",
        "processing": "🔄",
        "ready": "📦",
        "checking": "🔍",
        "waiting_courier": "🚚",
        "on_way": "📍",
        "delivered": "✅",
        "cancelled": "❌"
    }
    
    emoji = status_emoji.get(order.get("status", "created"), "📋")
    status_title = order.get("status", "created").replace("_", " ").title()
    
    # Формируем товары
    items_text = ""
    if order.get("items"):
        items_text = "\n💊 <b>Товары:</b>\n"
        for item in order["items"]:
            items_text += f"• {item.get('product', 'Товар')} × {item.get('quantity', 1)}\n"
    elif order.get("comment"):
        items_text = f"\n📝 <b>Комментарий:</b>\n{order['comment'][:100]}..."
    
    return f"""
📦 <b>Заказ #{order['id']}</b>

{emoji} <b>Статус:</b> {status_title}

👤 <b>Клиент:</b> {order.get('client_name', 'Не указано')}
📞 <b>Телефон:</b> {order.get('client_phone', 'Не указано')}
📍 <b>Адрес:</b> {order.get('client_address', 'Не указано')}

{items_text}
💰 <b>Сумма:</b> {order.get('amount', 0):.0f} сомони

🕐 <b>Создан:</b> {order.get('created_at', '').strftime('%d.%m.%Y %H:%M') if order.get('created_at') else 'Не указано'}
"""

def operator_order_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки оператора для заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accept_order_{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отказать",
                    callback_data=f"reject_order_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Позвонить клиенту",
                    callback_data=f"call_client_{order_id}"
                )
            ]
        ]
    )

def picker_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки сборщика"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶ Начать сборку",
                    callback_data=f"start_pick_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Готово",
                    callback_data=f"picked_{order_id}"
                )
            ]
    ]
    )

def checker_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки проверщика"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Ошибка",
                    callback_data=f"check_error_{order_id}"
                ),
                InlineKeyboardButton(
                    text="✅ Проверено",
                    callback_data=f"checked_{order_id}"
                )
            ]
    ]
    )

def courier_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки курьера"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚚 Взять заказ",
                    callback_data=f"take_delivery_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Я в пути",
                    callback_data=f"on_way_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Доставлено",
                    callback_data=f"delivered_{order_id}"
                )
            ]
    ]
    )

def client_order_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки клиента"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    callback_data=f"pay_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Статус",
                    callback_data=f"status_{order_id}"
                )
            ]
    ]
)

def director_dashboard() -> InlineKeyboardMarkup:
    """Кнопки дашборда директора"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📈 Продажи",
                    callback_data="sales_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Статусы заказов",
                    callback_data="orders_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Доход",
                    callback_data="revenue_stats"
                )
            ]
        ]
    )

def admin_order_buttons(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки администратора"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Доставлено",
                    callback_data=f"force_delivered_{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"force_cancel_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Позвонить клиенту",
                    callback_data=f"call_client_{order_id}"
                )
            ]
    ]
)

def get_order_buttons(order: Dict[str, Any], user_role: str) -> InlineKeyboardMarkup:
    """Получение кнопок для заказа в зависимости от роли"""
    
    order_id = order["id"]
    
    if user_role == "operator":
        return operator_order_buttons(order_id)
    elif user_role == "picker":
        return picker_buttons(order_id)
    elif user_role == "checker":
        return checker_buttons(order_id)
    elif user_role == "courier":
        return courier_buttons(order_id)
    elif user_role == "client":
        return client_order_buttons(order_id)
    elif user_role in ["admin", "director"]:
        return admin_order_buttons(order_id)
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Детали", callback_data=f"details_{order_id}")]
            ]
        )

def format_order_with_buttons(order: Dict[str, Any], user_role: str) -> tuple[str, InlineKeyboardMarkup]:
    """Форматирование заказа с кнопками"""
    
    text = format_order_text(order)
    buttons = get_order_buttons(order, user_role)
    
    return text, buttons

# Удобные функции для использования
def create_order_card(order: Dict[str, Any], user_role: str) -> tuple[str, InlineKeyboardMarkup]:
    """Создание карточки заказа (alias)"""
    return format_order_with_buttons(order, user_role)

def get_order_status_emoji(status: str) -> str:
    """Получение эмодзи для статуса"""
    status_emoji = {
        "created": "📝",
        "waiting_payment": "💳",
        "accepted": "✅",
        "processing": "🔄",
        "ready": "📦",
        "checking": "🔍",
        "waiting_courier": "🚚",
        "on_way": "📍",
        "delivered": "✅",
        "cancelled": "❌"
    }
    return status_emoji.get(status, "📋")

def format_order_list(orders: list, title: str) -> str:
    """Форматирование списка заказов"""
    
    if not orders:
        return f"📭 <b>{title}</b>\n\nНет заказов"
    
    text = f"📋 <b>{title} ({len(orders)})</b>\n\n"
    
    for order in orders[:10]:  # Показываем первые 10
        emoji = get_order_status_emoji(order.get("status", "created"))
        client_name = order.get("client_name", "Клиент")
        amount = order.get("amount", 0)
        created_time = order.get("created_at", "").strftime("%H:%M") if order.get("created_at") else ""
        
        text += f"{emoji} <b>#{order['id']}</b> {client_name}\n"
        text += f"💰 {amount:.0f} сомони"
        
        if created_time:
            text += f" • 🕐 {created_time}"
        
        text += "\n\n"
    
    return text
