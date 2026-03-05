"""
🎯 Callback Handlers - Обработчики inline кнопок
aiogram 3.4.1 compatible
"""

import logging
from aiogram import Router, F, types
from aiogram.filters import CallbackData

from keyboards.order_cards_new import format_order_text
from keyboards.notifications import NotificationService

logger = logging.getLogger(__name__)

# Создаем роутер для callback
callback_router = Router()

# Фильтры для callback
class OrderCallback(CallbackData, prefix="order"):
    action: str
    order_id: int

class StatsCallback(CallbackData, prefix="stats"):
    type: str

# Обработчики для оператора
@callback_router.callback_query(OrderCallback.filter(F.action == "accept_order"))
async def accept_order_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Принятие заказа оператором"""
    
    try:
        from services.order_service import accept_order
        from database.queries import get_order_by_id
        from database.queries import get_users_by_role
        
        order_id = callback_data.order_id
        
        # Принимаем заказ
        success = await accept_order(order_id, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Отправляем уведомление клиенту
                bot = callback.bot
                notification_service = NotificationService(bot)
                await notification_service.notify_payment_confirmed(
                    order['client_id'], 
                    order_id
                )
                
                # Автоматически назначаем сборщика
                from services.assignment_service import assign_picker
                picker = await assign_picker(order_id)
                
                if picker:
                    await notification_service.notify_picker_assigned(picker['id'], order)
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"✅ <b>Заказ #{order_id} принят</b>\n\n"
                    f"💳 Оплата подтверждена\n"
                    f"📦 Заказ передан в сборку"
                )
                
                await callback.answer("✅ Заказ принят")
                logger.info(f"✅ Order {order_id} accepted by operator {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось принять заказ")
            
    except Exception as e:
        logger.error(f"❌ Error accepting order: {e}")
        await callback.answer("❌ Ошибка принятия заказа")

@callback_router.callback_query(OrderCallback.filter(F.action == "reject_order"))
async def reject_order_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Отклонение заказа оператором"""
    
    try:
        from services.order_service import reject_order
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Отклоняем заказ
        success = await reject_order(order_id, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Отправляем уведомление клиенту
                bot = callback.bot
                notification_service = NotificationService(bot)
                await notification_service.notify_order_cancelled(
                    order['client_id'], 
                    order_id,
                    "Заказ отклонен оператором"
                )
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"❌ <b>Заказ #{order_id} отклонен</b>"
                )
                
                await callback.answer("❌ Заказ отклонен")
                logger.info(f"❌ Order {order_id} rejected by operator {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось отклонить заказ")
            
    except Exception as e:
        logger.error(f"❌ Error rejecting order: {e}")
        await callback.answer("❌ Ошибка отклонения заказа")

@callback_router.callback_query(OrderCallback.filter(F.action == "call_client"))
async def call_client_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Позвонить клиенту"""
    
    try:
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        order = await get_order_by_id(order_id)
        
        if order and order.get("client_phone"):
            phone = order["client_phone"]
            await callback.answer(f"📞 Телефон клиента: {phone}", show_alert=True)
        else:
            await callback.answer("❌ Телефон клиента не найден", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Error getting client phone: {e}")
        await callback.answer("❌ Ошибка получения телефона")

# Обработчики для сборщика
@callback_router.callback_query(OrderCallback.filter(F.action == "start_pick"))
async def start_pick_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Начать сборку"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Обновляем статус
        success = await update_order_status(order_id, OrderStatus.PROCESSING, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Отправляем уведомление клиенту
                bot = callback.bot
                notification_service = NotificationService(bot)
                await notification_service.notify_client_status_change(
                    order['client_id'], 
                    order_id,
                    "processing",
                    "Ваш заказ находится в сборке"
                )
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"🔄 <b>Заказ #{order_id} в сборке</b>\n\n"
                    f"📦 Начата сборка заказа"
                )
                
                await callback.answer("🔄 Сборка начата")
                logger.info(f"🔄 Order {order_id} picking started by {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось начать сборку")
            
    except Exception as e:
        logger.error(f"❌ Error starting pick: {e}")
        await callback.answer("❌ Ошибка начала сборки")

@callback_router.callback_query(OrderCallback.filter(F.action == "picked"))
async def picked_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Заказ собран"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Обновляем статус
        success = await update_order_status(order_id, OrderStatus.READY, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Автоматически назначаем проверщика
                from services.assignment_service import assign_checker
                checker = await assign_checker(order_id)
                
                if checker:
                    # Отправляем уведомление проверщику
                    bot = callback.bot
                    notification_service = NotificationService(bot)
                    await notification_service.notify_checker_assigned(checker['id'], order)
                
                # Отправляем уведомление клиенту
                await notification_service.notify_order_ready(order['client_id'], order_id)
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"📦 <b>Заказ #{order_id} собран</b>\n\n"
                    f"✅ Сборка завершена\n"
                    f"🔍 Заказ передан на проверку"
                )
                
                await callback.answer("📦 Собрано")
                logger.info(f"📦 Order {order_id} picked by {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось завершить сборку")
            
    except Exception as e:
        logger.error(f"❌ Error completing pick: {e}")
        await callback.answer("❌ Ошибка завершения сборки")

# Обработчики для проверщика
@callback_router.callback_query(OrderCallback.filter(F.action == "check_error"))
async def check_error_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Ошибка при проверке"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        
        order_id = callback_data.order_id
        
        # Возвращаем заказ в обработку
        success = await update_order_status(order_id, OrderStatus.PROCESSING, callback.from_user.id)
        
        if success:
            await callback.message.edit_text(
                f"❌ <b>Заказ #{order_id} возвращен в сборку</b>\n\n"
                f"🔄 Обнаружена ошибка при проверке"
            )
            
            await callback.answer("❌ Обнаружена ошибка")
            logger.info(f"❌ Order {order_id} check error by {callback.from_user.id}")
        else:
            await callback.answer("❌ Не удалось вернуть заказ")
            
    except Exception as e:
        logger.error(f"❌ Error in check error: {e}")
        await callback.answer("❌ Ошибка проверки")

@callback_router.callback_query(OrderCallback.filter(F.action == "checked"))
async def checked_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Проверка пройдена"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Обновляем статус
        success = await update_order_status(order_id, OrderStatus.WAITING_COURIER, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Автоматически назначаем курьера
                from services.assignment_service import assign_courier
                courier = await assign_courier(order_id)
                
                if courier:
                    # Отправляем уведомление курьеру
                    bot = callback.bot
                    notification_service = NotificationService(bot)
                    await notification_service.notify_courier_assigned(courier['id'], order)
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"✅ <b>Заказ #{order_id} проверен</b>\n\n"
                    f"🔍 Проверка пройдена\n"
                    f"🚚 Заказ ожидает курьера"
                )
                
                await callback.answer("✅ Проверено")
                logger.info(f"✅ Order {order_id} checked by {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось подтвердить проверку")
            
    except Exception as e:
        logger.error(f"❌ Error in check passed: {e}")
        await callback.answer("❌ Ошибка проверки")

# Обработчики для курьера
@callback_router.callback_query(OrderCallback.filter(F.action == "take_delivery"))
async def take_delivery_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Взять заказ на доставку"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Обновляем статус
        success = await update_order_status(order_id, OrderStatus.ON_WAY, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Отправляем уведомление клиенту
                bot = callback.bot
                notification_service = NotificationService(bot)
                await notification_service.notify_courier_on_way(
                    order['client_id'], 
                    order_id,
                    callback.from_user.full_name or "Курьер"
                )
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"🚚 <b>Заказ #{order_id} взят на доставку</b>\n\n"
                    f"📍 Курьер в пути"
                )
                
                await callback.answer("🚚 Заказ взят")
                logger.info(f"🚚 Order {order_id} taken for delivery by {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не удалось взять заказ")
            
    except Exception as e:
        logger.error(f"❌ Error taking delivery: {e}")
        await callback.answer("❌ Error взятия заказа")

@callback_router.callback_query(OrderCallback.filter(F.action == "on_way"))
async def on_way_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Курьер в пути"""
    
    try:
        order_id = callback_data.order_id
        
        await callback.message.edit_text(
            f"📍 <b>Заказ #{order_id}</b>\n\n"
            f"🚚 Курьер в пути к клиенту"
        )
        
        await callback.answer("📍 В пути")
        logger.info(f"📍 Order {order_id} courier on way")
        
    except Exception as e:
        logger.error(f"❌ Error in on way: {e}")
        await callback.answer("❌ Ошибка обновления статуса")

@callback_router.callback_query(OrderCallback.filter(F.action == "delivered"))
async def delivered_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Заказ доставлен"""
    
    try:
        from services.order_service import update_order_status
        from database.models import OrderStatus
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        
        # Обновляем статус
        success = await update_order_status(order_id, OrderStatus.DELIVERED, callback.from_user.id)
        
        if success:
            # Получаем информацию о заказе
            order = await get_order_by_id(order_id)
            
            if order:
                # Отправляем уведомление клиенту
                bot = callback.bot
                notification_service = NotificationService(bot)
                await notification_service.notify_order_delivered(order['client_id'], order_id)
                
                # Обновляем сообщение
                await callback.message.edit_text(
                    f"✅ <b>Заказ #{order_id} доставлен</b>\n\n"
                    f"🎉 Доставка завершена"
                )
                
                await callback.answer("✅ Доставлено")
                logger.info(f"✅ Order {order_id} delivered by {callback.from_user.id}")
            else:
                await callback.answer("❌ Заказ не найден")
        else:
            await callback.answer("❌ Не подтвердить доставку")
            
    except Exception as e:
        logger.error(f"❌ Error in delivered: {e}")
        await callback.answer("❌ Ошибка доставки")

# Обработчики для клиента
@callback_router.callback_query(OrderCallback.filter(F.action == "pay"))
async def pay_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Оплата заказа"""
    
    try:
        order_id = callback_data.order_id
        
        # Показываем варианты оплаты
        from keyboards.order_cards_new import payment_buttons
        
        await callback.message.edit_text(
            f"💳 <b>Оплата заказа #{order_id}</b>\n\n"
            f"Выберите способ оплаты:",
            reply_markup=payment_buttons(order_id)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in payment: {e}")
        await callback.answer("❌ Ошибка оплаты")

@callback_router.callback_query(OrderCallback.filter(F.action == "status"))
async def status_callback(callback: types.CallbackQuery, callback_data: OrderCallback):
    """Статус заказа"""
    
    try:
        from database.queries import get_order_by_id
        
        order_id = callback_data.order_id
        order = await get_order_by_id(order_id)
        
        if order:
            from keyboards.order_cards_new import format_order_text
            
            order_text = format_order_text(order)
            await callback.message.answer(order_text)
            await callback.answer("📋 Детали заказа")
        else:
            await callback.answer("❌ Заказ не найден")
            
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        await callback.answer("❌ Ошибка получения статуса")

# Обработчики для статистики
@callback_router.callback_query(StatsCallback.filter())
async def stats_callback(callback: types.CallbackQuery, callback_data: StatsCallback):
    """Статистика"""
    
    try:
        stats_type = callback_data.type
        
        if stats_type == "sales":
            await callback.answer("📈 Статистика продаж в разработке", show_alert=True)
        elif stats_type == "orders":
            await callback.answer("📦 Статистика заказов в разработке", show_alert=True)
        elif stats_type == "revenue":
            await callback.answer("💰 Статистика доходов в разработке", show_alert=True)
        else:
            await callback.answer("❌ Неизвестный тип статистики", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Error in stats: {e}")
        await callback.answer("❌ Ошибка статистики")

# Обработчик для неизвестных callback
@callback_router.callback_query()
async def unknown_callback(callback: types.CallbackQuery):
    """Обработчик неизвестных callback"""
    await callback.answer("❌ Неизвестное действие", show_alert=True)
    logger.warning(f"⚠️ Unknown callback: {callback.data}")

# Удобные функции для использования
def get_callback_router() -> Router:
    """Получение роутера callback обработчиков"""
    return callback_router
