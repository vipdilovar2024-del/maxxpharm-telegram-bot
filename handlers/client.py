"""
🏗️ Client Handlers - Обработчики для клиентов
"""

import logging
from aiogram import Router, F, types
from aiogram.filters import Command

from services.order_service import create_order
from keyboards.client_menu import get_client_main_keyboard
from keyboards.order_cards import format_order_card

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, role: str):
    """Обработчик /start для клиента"""
    if role != "client":
        return
    
    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Добро пожаловать в MAXXPHARM 🏥\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_client_main_keyboard()
    )

@router.message(F.text == "📦 Сделать заявку")
async def cmd_create_order(message: types.Message, role: str):
    """Создание заявки"""
    if role != "client":
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer(
        "📦 <b>Новая заявка</b>\n\n"
        "Отправьте список препаратов, фото рецепта или голосовое сообщение:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "📍 Мои заказы")
async def cmd_my_orders(message: types.Message, role: str):
    """Мои заказы"""
    if role != "client":
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from database.queries import get_client_orders
        
        orders = await get_client_orders(message.from_user.id)
        
        if not orders:
            await message.answer("📭 У вас нет заказов")
            return
        
        # Формируем список заказов
        orders_text = "📍 <b>Мои заказы</b>\n\n"
        for order in orders:
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
            
            emoji = status_emoji.get(order["status"], "📋")
            orders_text += f"{emoji} <b>#{order['id']}</b> {order['status'].replace('_', ' ').title()}\n"
            orders_text += f"💰 {order['amount']} сомони • 🕐 {order['created_at'].strftime('%d.%m %H:%M')}\n\n"
        
        await message.answer(orders_text)
        
    except Exception as e:
        logger.error(f"❌ Error getting client orders: {e}")
        await message.answer("❌ Ошибка получения заказов")

@router.message(F.text == "💳 Оплата")
async def cmd_payment(message: types.Message, role: str):
    """Оплата заказа"""
    if role != "client":
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from database.queries import get_client_last_order
        
        last_order = await get_client_last_order(message.from_user.id)
        
        if not last_order:
            await message.answer("📭 У вас нет активных заказов")
            return
        
        if last_order["status"] == "created":
            await message.answer(
                f"💳 <b>Оплата заказа #{last_order['id']}</b>\n\n"
                f"💰 Сумма: {last_order['amount']} сомони\n\n"
                "Отправьте фото чека или подтверждение оплаты:",
                reply_markup=get_client_main_keyboard()
            )
        else:
            await message.answer("💳 Заказ уже оплачен или находится в обработке")
            
    except Exception as e:
        logger.error(f"❌ Error in payment: {e}")
        await message.answer("❌ Ошибка обработки оплаты")

@router.message(F.text == "📞 Менеджер")
async def cmd_manager(message: types.Message, role: str):
    """Связь с менеджером"""
    if role != "client":
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer(
        "📞 <b>Связь с менеджером</b>\n\n"
        "📱 Телефон: +998 90 123 45 67\n"
        "💬 WhatsApp: +998 90 123 45 67\n"
        "📧 Email: manager@maxxpharm.com\n\n"
        "⏰ Время работы: 9:00 - 18:00"
    )

@router.message()
async def handle_order_text(message: types.Message, role: str):
    """Обработка текста для создания заказа"""
    if role != "client":
        return
    
    # Если сообщение достаточно длинное, создаем заказ
    if len(message.text) > 10:
        try:
            order = await create_order(
                client_id=message.from_user.id,
                text=message.text,
                message_type="text"
            )
            
            # Формируем карточку заказа
            order_card = format_order_card(order)
            
            await message.answer(
                f"✅ <b>Заявка создана!</b>\n\n"
                f"{order_card}"
                f"Мы скоро проверим ваш заказ",
                reply_markup=get_client_main_keyboard()
            )
            
            logger.info(f"📦 Order #{order['id']} created by client {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            await message.answer("❌ Ошибка создания заявки")

@router.message(F.photo)
async def handle_order_photo(message: types.Message, role: str):
    """Обработка фото для создания заказа"""
    if role != "client":
        return
    
    try:
        # Получаем фото и caption
        photo = message.photo[-1]  # Самое большое фото
        caption = message.caption or "Фото рецепта"
        
        order = await create_order(
            client_id=message.from_user.id,
            text=caption,
            message_type="photo",
            photo_file_id=photo.file_id
        )
        
        await message.answer(
            f"✅ <b>Заявка создана!</b>\n\n"
            f"📦 Номер: #{order['id']}\n"
            f"📝 Фото рецепта получено\n\n"
            f"Мы скоро проверим ваш заказ",
            reply_markup=get_client_main_keyboard()
        )
        
        logger.info(f"📦 Order #{order['id']} created with photo by client {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error creating order from photo: {e}")
        await message.answer("❌ Ошибка создания заявки")

@router.message(F.voice)
async def handle_order_voice(message: types.Message, role: str):
    """Обработка голосового сообщения для создания заказа"""
    if role != "client":
        return
    
    try:
        voice = message.voice
        
        order = await create_order(
            client_id=message.from_user.id,
            text="Голосовое сообщение",
            message_type="voice",
            voice_file_id=voice.file_id
        )
        
        await message.answer(
            f"✅ <b>Заявка создана!</b>\n\n"
            f"📦 Номер: #{order['id']}\n"
            f"🎙️ Голосовое сообщение получено\n\n"
            f"Мы скоро проверим ваш заказ",
            reply_markup=get_client_main_keyboard()
        )
        
        logger.info(f"📦 Order #{order['id']} created with voice by client {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error creating order from voice: {e}")
        await message.answer("❌ Ошибка создания заявки")
