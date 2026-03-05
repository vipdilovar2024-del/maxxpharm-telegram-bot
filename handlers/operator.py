"""
🏗️ Operator Handlers - Обработчики для операторов
"""

import logging
from aiogram import Router, F, types
from aiogram.filters import Command

from keyboards.operator_menu import get_operator_main_keyboard
from keyboards.order_cards import format_order_card_with_actions

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, role: str):
    """Обработчик /start для оператора"""
    if role != "operator":
        return
    
    await message.answer(
        "👨‍💻 <b>Панель оператора</b>\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_operator_main_keyboard()
    )

@router.message(F.text == "📥 Новые заявки")
async def cmd_new_orders(message: types.Message, role: str):
    """Новые заявки"""
    if role != "operator":
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from database.queries import get_new_orders
        
        orders = await get_new_orders()
        
        if not orders:
            await message.answer("📭 Новых заявок нет")
            return
        
        # Показываем список новых заявок
        orders_text = f"📥 <b>Новые заявки ({len(orders)})</b>\n\n"
        
        for order in orders[:5]:  # Показываем первые 5
            orders_text += f"📦 <b>#{order['id']}</b> {order['client_name']}\n"
            orders_text += f"💰 {order['amount']} сомони • 🕐 {order['created_at'].strftime('%H:%M')}\n\n"
        
        await message.answer(orders_text)
        
    except Exception as e:
        logger.error(f"❌ Error getting new orders: {e}")
        await message.answer("❌ Ошибка получения заявок")

@router.message(F.text == "💳 Подтверждение оплаты")
async def cmd_confirm_payment(message: types.Message, role: str):
    """Подтверждение оплаты"""
    if role != "operator":
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from database.queries import get_orders_by_status
        
        payment_orders = await get_orders_by_status("waiting_payment")
        
        if not payment_orders:
            await message.answer("📭 Заказов ожидающих оплату нет")
            return
        
        orders_text = f"💳 <b>Заказы ожидающие оплату ({len(payment_orders)})</b>\n\n"
        
        for order in payment_orders[:5]:
            orders_text += f"📦 <b>#{order['id']}</b> {order['client_name']}\n"
            orders_text += f"💰 {order['amount']} сомони\n\n"
        
        await message.answer(orders_text)
        
    except Exception as e:
        logger.error(f"❌ Error getting payment orders: {e}")
        await message.answer("❌ Ошибка получения заказов")

@router.message(F.text == "📦 Все заказы")
async def cmd_all_orders(message: types.Message, role: str):
    """Все заказы оператора"""
    if role != "operator":
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from database.queries import get_operator_orders
        
        orders = await get_operator_orders(message.from_user.id)
        
        if not orders:
            await message.answer("📭 У вас нет активных заказов")
            return
        
        orders_text = f"📊 <b>Мои заказы ({len(orders)})</b>\n\n"
        
        for order in orders:
            status_emoji = {
                "accepted": "✅",
                "processing": "🔄",
                "ready": "📦",
                "checking": "🔍",
                "waiting_courier": "🚚",
                "on_way": "📍",
                "delivered": "✅"
            }
            
            emoji = status_emoji.get(order["status"], "📋")
            orders_text += f"{emoji} <b>#{order['id']}</b> {order['client_name']}\n"
            orders_text += f"📊 {order['status'].replace('_', ' ').title()}\n\n"
        
        await message.answer(orders_text)
        
    except Exception as e:
        logger.error(f"❌ Error getting operator orders: {e}")
        await message.answer("❌ Ошибка получения заказов")

@router.message(F.text == "🔎 Найти заказ")
async def cmd_find_order(message: types.Message, role: str):
    """Поиск заказа"""
    if role != "operator":
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer(
        "🔎 <b>Поиск заказа</b>\n\n"
        "Введите номер заказа (например: 245):",
        reply_markup=get_operator_main_keyboard()
    )

@router.message()
async def handle_order_search(message: types.Message, role: str):
    """Обработка поиска заказа"""
    if role != "operator":
        return
    
    # Проверяем, является ли сообщение числом (номер заказа)
    if message.text.isdigit():
        try:
            from database.queries import get_order_by_id
            
            order_id = int(message.text)
            order = await get_order_by_id(order_id)
            
            if not order:
                await message.answer(f"❌ Заказ #{order_id} не найден")
                return
            
            # Формируем карточку заказа с кнопками действий
            order_card = format_order_card_with_actions(order, "operator")
            
            await message.answer(order_card)
            
        except Exception as e:
            logger.error(f"❌ Error finding order: {e}")
            await message.answer("❌ Ошибка поиска заказа")

@router.callback_query()
async def handle_operator_callback(callback: types.CallbackQuery, role: str):
    """Обработка callback от оператора"""
    if role != "operator":
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        data = callback.data
        
        if data.startswith("accept_order_"):
            order_id = int(data.split("_")[2])
            await handle_accept_order(callback, order_id)
        
        elif data.startswith("reject_order_"):
            order_id = int(data.split("_")[2])
            await handle_reject_order(callback, order_id)
        
        elif data.startswith("confirm_payment_"):
            order_id = int(data.split("_")[2])
            await handle_confirm_payment_callback(callback, order_id)
        
        elif data.startswith("call_client_"):
            order_id = int(data.split("_")[2])
            await handle_call_client(callback, order_id)
        
        else:
            await callback.answer("❌ Неизвестное действие")
            
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")
        await callback.answer("❌ Ошибка обработки")

async def handle_accept_order(callback: types.CallbackQuery, order_id: int):
    """Принятие заказа"""
    try:
        from services.order_service import accept_order
        from services.notification_service import notify_client
        
        # Принимаем заказ
        success = await accept_order(order_id, callback.from_user.id)
        
        if success:
            # Отправляем уведомление клиенту
            await notify_client(order_id, "📦 Ваша заявка принята в обработку")
            
            await callback.answer("✅ Заказ принят")
            await callback.message.edit_text("✅ <b>Заказ принят в обработку</b>")
            
            logger.info(f"✅ Order {order_id} accepted by operator {callback.from_user.id}")
        else:
            await callback.answer("❌ Не удалось принять заказ")
            
    except Exception as e:
        logger.error(f"❌ Error accepting order: {e}")
        await callback.answer("❌ Ошибка принятия заказа")

async def handle_reject_order(callback: types.CallbackQuery, order_id: int):
    """Отклонение заказа"""
    try:
        from services.order_service import reject_order
        from services.notification_service import notify_client
        
        # Отклоняем заказ
        success = await reject_order(order_id, callback.from_user.id)
        
        if success:
            # Отправляем уведомление клиенту
            await notify_client(order_id, "❌ Ваша заявка отклонена")
            
            await callback.answer("❌ Заказ отклонен")
            await callback.message.edit_text("❌ <b>Заказ отклонен</b>")
            
            logger.info(f"❌ Order {order_id} rejected by operator {callback.from_user.id}")
        else:
            await callback.answer("❌ Не удалось отклонить заказ")
            
    except Exception as e:
        logger.error(f"❌ Error rejecting order: {e}")
        await callback.answer("❌ Ошибка отклонения заказа")

async def handle_confirm_payment_callback(callback: types.CallbackQuery, order_id: int):
    """Подтверждение оплаты"""
    try:
        from services.order_service import confirm_payment
        from services.notification_service import notify_client
        from services.assignment_service import assign_picker
        
        # Подтверждаем оплату
        success = await confirm_payment(order_id, callback.from_user.id)
        
        if success:
            # Автоматически назначаем сборщика
            await assign_picker(order_id)
            
            # Отправляем уведомление клиенту
            await notify_client(order_id, "💳 Оплата подтверждена. Заказ передан в сборку")
            
            await callback.answer("💳 Оплата подтверждена")
            await callback.message.edit_text("💳 <b>Оплата подтверждена</b>\n\n📦 Заказ передан в сборку")
            
            logger.info(f"💳 Payment confirmed for order {order_id} by operator {callback.from_user.id}")
        else:
            await callback.answer("❌ Не удалось подтвердить оплату")
            
    except Exception as e:
        logger.error(f"❌ Error confirming payment: {e}")
        await callback.answer("❌ Ошибка подтверждения оплаты")

async def handle_call_client(callback: types.CallbackQuery, order_id: int):
    """Позвонить клиенту"""
    try:
        from database.queries import get_order_by_id
        
        order = await get_order_by_id(order_id)
        
        if order and order.get("client_phone"):
            phone = order["client_phone"]
            await callback.answer(f"📞 Телефон клиента: {phone}")
        else:
            await callback.answer("❌ Телефон клиента не найден")
            
    except Exception as e:
        logger.error(f"❌ Error getting client phone: {e}")
        await callback.answer("❌ Ошибка получения телефона")
