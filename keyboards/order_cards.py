"""
🏗️ Order Cards - Универсальные карточки заказов с кнопками действий
"""

from typing import Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_order_card(order: Dict[str, Any]) -> str:
    """Форматирование базовой карточки заказа"""
    
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

def format_order_card_with_actions(order: Dict[str, Any], user_role: str) -> str:
    """Форматирование карточки заказа с кнопками действий"""
    
    # Базовая карточка
    card_text = format_order_card(order)
    
    # Добавляем информацию о назначенных сотрудниках
    if order.get("operator_name"):
        card_text += f"\n👨‍💻 <b>Оператор:</b> {order['operator_name']}"
    
    if order.get("picker_name"):
        card_text += f"\n📦 <b>Сборщик:</b> {order['picker_name']}"
    
    if order.get("checker_name"):
        card_text += f"\n🔍 <b>Проверщик:</b> {order['checker_name']}"
    
    if order.get("courier_name"):
        card_text += f"\n🚚 <b>Курьер:</b> {order['courier_name']}"
    
    return card_text

def get_order_action_keyboard(order: Dict[str, Any], user_role: str) -> InlineKeyboardMarkup:
    """Получение клавиатуры действий для заказа"""
    
    order_id = order["id"]
    status = order.get("status", "created")
    
    if user_role == "operator":
        return get_operator_keyboard(order_id, status)
    elif user_role == "picker":
        return get_picker_keyboard(order_id, status)
    elif user_role == "checker":
        return get_checker_keyboard(order_id, status)
    elif user_role == "courier":
        return get_courier_keyboard(order_id, status)
    elif user_role in ["admin", "director"]:
        return get_admin_keyboard(order_id, status)
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📋 Детали", callback_data=f"order_details_{order_id}")]]
        )

def get_operator_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для оператора"""
    
    buttons = []
    
    if status == "created":
        buttons.append([
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_order_{order_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_order_{order_id}")
        ])
    elif status == "waiting_payment":
        buttons.append([
            InlineKeyboardButton(text="💳 Подтвердить оплату", callback_data=f"confirm_payment_{order_id}")
        ])
    
    # Кнопка связи с клиентом
    buttons.append([
        InlineKeyboardButton(text="📞 Позвонить клиенту", callback_data=f"call_client_{order_id}")
    ])
    
    # Кнопка деталей
    buttons.append([
        InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_picker_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для сборщика"""
    
    buttons = []
    
    if status == "accepted":
        buttons.append([
            InlineKeyboardButton(text="▶ Начать сборку", callback_data=f"start_picking_{order_id}")
        ])
    elif status == "processing":
        buttons.append([
            InlineKeyboardButton(text="📦 Готово", callback_data=f"finish_picking_{order_id}")
        ])
    
    # Кнопка деталей
    buttons.append([
        InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_checker_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для проверщика"""
    
    buttons = []
    
    if status == "ready":
        buttons.append([
            InlineKeyboardButton(text="❌ Ошибка", callback_data=f"check_error_{order_id}"),
            InlineKeyboardButton(text="✅ Проверено", callback_data=f"check_passed_{order_id}")
        ])
    
    # Кнопка деталей
    buttons.append([
        InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_courier_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для курьера"""
    
    buttons = []
    
    if status == "waiting_courier":
        buttons.append([
            InlineKeyboardButton(text="🚚 Взять заказ", callback_data=f"take_delivery_{order_id}")
        ])
    elif status == "on_way":
        buttons.append([
            InlineKeyboardButton(text="✅ Доставлено", callback_data=f"delivered_{order_id}")
        ])
    
    # Кнопка деталей
    buttons.append([
        InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    ])
    
    # Кнопка связи с клиентом
    buttons.append([
        InlineKeyboardButton(text="📞 Позвонить клиенту", callback_data=f"call_client_{order_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для администратора"""
    
    buttons = []
    
    # Кнопки управления статусом
    status_buttons = []
    if status != "delivered":
        status_buttons.append(InlineKeyboardButton(text="✅ Доставлено", callback_data=f"force_delivered_{order_id}"))
    if status != "cancelled":
        status_buttons.append(InlineKeyboardButton(text="❌ Отменить", callback_data=f"force_cancel_{order_id}"))
    
    if status_buttons:
        buttons.append(status_buttons)
    
    # Кнопка деталей
    buttons.append([
        InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    ])
    
    # Кнопка связи с клиентом
    buttons.append([
        InlineKeyboardButton(text="📞 Позвонить клиенту", callback_data=f"call_client_{order_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def format_order_list(orders: list, title: str) -> str:
    """Форматирование списка заказов"""
    
    if not orders:
        return f"📭 <b>{title}</b>\n\nНет заказов"
    
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
    
    text = f"📋 <b>{title} ({len(orders)})</b>\n\n"
    
    for order in orders[:10]:  # Показываем первые 10
        emoji = status_emoji.get(order.get("status", "created"), "📋")
        client_name = order.get("client_name", "Клиент")
        amount = order.get("amount", 0)
        created_time = order.get("created_at", "").strftime("%H:%M") if order.get("created_at") else ""
        
        text += f"{emoji} <b>#{order['id']}</b> {client_name}\n"
        text += f"💰 {amount:.0f} сомони"
        
        if created_time:
            text += f" • 🕐 {created_time}"
        
        text += "\n\n"
    
    return text

def format_order_status_history(history: list) -> str:
    """Форматирование истории статусов заказа"""
    
    if not history:
        return "📝 <b>История статусов</b>\n\nНет записей"
    
    text = "📝 <b>История статусов</b>\n\n"
    
    for record in history:
        status = record.get("status", "").replace("_", " ").title()
        changed_by = record.get("changed_by_name", "Система")
        changed_at = record.get("changed_at", "").strftime("%d.%m.%Y %H:%M") if record.get("changed_at") else ""
        
        text += f"📊 {status}\n"
        text += f"👤 {changed_by}\n"
        text += f"🕐 {changed_at}\n\n"
    
    return text
