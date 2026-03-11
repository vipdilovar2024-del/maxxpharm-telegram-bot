"""
🔹 Обработчики клиентов MAXXPHARM CRM
"""

from typing import List, Dict, Any
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..models.database import UserRole, OrderStatus
from ..services.user_service import UserService
from ..services.order_service import OrderService
from ..database import get_db


class OrderCreationStates(StatesGroup):
    """Состояния создания заказа"""
    order_type = State()
    order_text = State()
    order_photo = State()
    order_voice = State()


class ClientHandlers:
    """Обработчики для клиентов"""
    
    def __init__(self):
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.router.message(F.text == "📦 Создать заявку")
        async def handle_create_order(message: Message, state: FSMContext):
            """Начало создания заявки"""
            await state.set_state(OrderCreationStates.order_type)
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📝 Текстом", callback_data="order_text"),
                        InlineKeyboardButton(text="📷 Фото рецепта", callback_data="order_photo"),
                        InlineKeyboardButton(text="🎤 Голосом", callback_data="order_voice")
                    ]
                ]
            )
            
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "📝 Выберите способ оформления заявки:",
                reply_markup=keyboard
            )
        
        @self.router.callback_query(F.data.startswith("order_"))
        async def handle_order_type(callback: types.CallbackQuery, state: FSMContext):
            """Обработка выбора типа заказа"""
            order_type = callback.data.split("_")[1]
            
            if order_type == "text":
                await state.set_state(OrderCreationStates.order_text)
                await callback.message.answer(
                    "📝 <b>Создание заявки текстом</b>\n\n"
                    "📋 Напишите список лекарств:\n\n"
                    "📝 <b>Пример:</b>\n"
                    "• Парацетамол - 50 шт\n"
                    "• Цефтриаксон - 20 ампул\n"
                    "• Сироп Нурофен - 10 флаконов\n\n"
                    "💊 Укажите название, количество и форму выпуска"
                )
                
            elif order_type == "photo":
                await state.set_state(OrderCreationStates.order_photo)
                await callback.message.answer(
                    "📷 <b>Создание заявки фото</b>\n\n"
                    "📸 Отправьте фото рецепта или списка лекарств\n\n"
                    "📝 После фото напишите:\n"
                    "• 📞 Контактный телефон\n"
                    "• 🏥 Адрес доставки\n\n"
                    "📷 Фото должно быть четким и читаемым"
                )
                
            elif order_type == "voice":
                await state.set_state(OrderCreationStates.order_voice)
                await callback.message.answer(
                    "🎤 <b>Создание заявки голосом</b>\n\n"
                    "🎤 Запишите голосовое сообщение со списком лекарств\n\n"
                    "📝 <b>Что сказать:</b>\n"
                    "• Названия лекарств\n"
                    "• Количество\n"
                    "• Форма выпуска\n\n"
                    "⏱️ Говорите четко и не быстро"
                )
            
            await callback.answer()
        
        @self.router.message(OrderCreationStates.order_text)
        async def handle_order_text(message: Message, state: FSMContext):
            """Обработка текстового заказа"""
            order_text = message.text
            
            # Парсинг заказа
            items = self._parse_order_text(order_text)
            
            if not items:
                await message.answer(
                    "❌ <b>Ошибка в формате заказа</b>\n\n"
                    "📝 <b>Правильный формат:</b>\n"
                    "• Название лекарства - количество\n\n"
                    "📝 <b>Пример:</b>\n"
                    "• Парацетамол - 50 шт\n"
                    "• Цефтриаксон - 20 ампул\n\n"
                    "🔄 Попробуйте еще раз"
                )
                return
            
            # Создание заказа
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or not user.pharmacy:
                    await message.answer("❌ Ошибка: профиль не найден")
                    await state.clear()
                    return
                
                try:
                    order = await order_service.create_order(
                        client_id=user.id,
                        pharmacy_id=user.pharmacy.id,
                        items=items,
                        notes=f"Заказ через Telegram: {order_text[:100]}..."
                    )
                    
                    await message.answer(
                        f"✅ <b>Заявка создана!</b>\n\n"
                        f"📝 Номер: {order.order_number}\n"
                        f"👤 Клиент: {user.full_name}\n"
                        f"🏥 Аптека: {user.pharmacy.name}\n"
                        f"💰 Сумма: {order.total_amount} сомони\n"
                        f"📊 Статус: {self._get_status_display(order.status)}\n\n"
                        f"🔄 Заявка передана оператору\n"
                        f"⏱️ Ожидайте подтверждения\n\n"
                        f"📞 <b>Срочно?</b> +992 900 000 001\n\n"
                        f"🏥 MAXXPHARM - Ваша надежная аптека!"
                    )
                    
                    await state.clear()
                    
                except Exception as e:
                    await message.answer(f"❌ Ошибка создания заказа: {str(e)}")
                    await state.clear()
        
        @self.router.message(F.text == "📋 Мои заявки")
        async def handle_my_orders(message: Message):
            """Просмотр заявок клиента"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    await message.answer("❌ Пользователь не найден")
                    return
                
                orders = await order_service.get_orders_by_client(user.id)
                
                if not orders:
                    await message.answer(
                        "📭 <b>У вас пока нет заявок</b>\n\n"
                        "📦 Хотите создать заявку?\n"
                        "Нажмите 'Создать заявку' в меню"
                    )
                    return
                
                text = "📋 <b>Ваши заявки</b>\n\n"
                
                for order in orders[:10]:  # Последние 10
                    status_display = self._get_status_display(order.status)
                    
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"📊 Статус: {status_display}\n"
                    text += f"💰 Сумма: {order.total_amount} сомони\n"
                    text += f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    
                    if order.delivered_at:
                        text += f"✅ Доставлен: {order.delivered_at.strftime('%d.%m.%Y %H:%M')}\n"
                    
                    text += "\n"
                
                await message.answer(text)
        
        @self.router.message(F.text == "📊 Статус заявки")
        async def handle_order_status(message: Message):
            """Проверка статуса конкретной заявки"""
            await message.answer(
                "📊 <b>Статус заявки</b>\n\n"
                "📝 Введите номер заявки для проверки:\n\n"
                "📋 <b>Пример:</b> ORD-20240311-0001\n\n"
                "📞 Или посмотрите все заявки в 'Мои заявки'"
            )
        
        @self.router.message(F.text == "💳 Оплатить заказ")
        async def handle_payment(message: Message):
            """Оплата заказа"""
            await message.answer(
                "💳 <b>Оплата заказа</b>\n\n"
                "💰 <b>Реквизиты для оплаты:</b>\n\n"
                "🏦 <b>Банк:</b> Эсхата Банк\n"
                "📱 <b>Карта:</b> 4242 4242 4242 4242\n"
                "👤 <b>Получатель:</b> ООО МАКСФАРМ\n\n"
                "💵 <b>Способы оплаты:</b>\n"
                "• 💳 Перевод на карту\n"
                "• 💰 Наличными курьеру\n"
                "• 📱 Банковское приложение\n\n"
                "📸 <b>После оплаты:</b>\n"
                "• Отправьте фото чека\n"
                "• Или номер операции\n\n"
                "🏥 MAXXPHARM - Спасибо за доверие!"
            )
        
        @self.router.message(F.text == "💬 Связаться с оператором")
        async def handle_contact_operator(message: Message):
            """Связь с оператором"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📞 Позвонить", url="tel:+99290000001"),
                        InlineKeyboardButton(text="💬 Написать", url="https://t.me/maxxpharm_support")
                    ]
                ]
            )
            
            await message.answer(
                "💬 <b>Связь с оператором MAXXPHARM</b>\n\n"
                "👥 <b>Наши операторы:</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 📞 Телефон: +992 900 000 002\n"
                "• 💬 Telegram: @maxxpharm_support\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n"
                "• 🕐 Время работы: 09:00 - 21:00\n\n"
                "⚡ <b>Среднее время ответа: 2 минуты</b>\n\n"
                "🏥 MAXXPHARM - Всегда на связи!",
                reply_markup=keyboard
            )
        
        @self.router.message(F.text == "📚 Каталог")
        async def handle_catalog(message: Message):
            """Просмотр каталога"""
            catalog_text = """
📚 <b>Каталог MAXXPHARM</b>

🌡️ <b>Против температуры и боли:</b>
• Парацетамол 500мг - 45 сомони
• Ибупрофен 400мг - 80 сомони
• Аспирин 100мг - 35 сомони
• Анальгин 500мг - 25 сомони

🦠 <b>Противовирусные:</b>
• Арбидол - 250 сомони
• Кагоцел - 200 сомони
• Ремантадин - 150 сомони
• Осельтамивир - 300 сомони

💊 <b>Сердечно-сосудистые:</b>
• Лозартан 50мг - 120 сомони
• Эналаприл 10мг - 90 сомони
• Амлодипин 5мг - 85 сомони

💪 <b>Витамины и БАДы:</b>
• Витамин D3 - 60 сомони
• Витамин C - 40 сомони
• Омега-3 - 150 сомони
• Кальций D3 - 80 сомони

🌿 <b>Травы и фитопрепараты:</b>
• Ромашка - 30 сомони
• Шалфей - 25 сомони
• Эхинацея - 45 сомони

💉 <b>Инъекционные препараты:</b>
• Цефтриаксон 1г - 150 сомони
• Новокаин 0.5% - 45 сомони
• Физраствор - 35 сомони

🏥 <b>MAXXPHARM - Качественные лекарства по доступным ценам!</b>

📞 <b>Для заказа:</b>
• 📝 В этом чате
• 📞 Телефон: +992 900 000 001
• 🌐 Сайт: www.maxxpharm.tj

⚡ <b>Доставка по Душанбе: 60 минут!</b>
            """
            
            await message.answer(catalog_text)
    
    def _parse_order_text(self, text: str) -> List[Dict[str, Any]]:
        """Парсинг текстового заказа"""
        items = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('•'):
                line = line.replace('•', '').strip()
            
            # Парсинг формата: "Название - количество"
            if ' - ' in line:
                parts = line.split(' - ')
                if len(parts) >= 2:
                    product_name = parts[0].strip()
                    quantity_info = parts[1].strip()
                    
                    # Извлечение количества
                    quantity = 1
                    try:
                        # Ищем цифры в строке количества
                        import re
                        numbers = re.findall(r'\d+', quantity_info)
                        if numbers:
                            quantity = int(numbers[0])
                    except:
                        pass
                    
                    # Расчет примерной цены
                    unit_price = self._estimate_price(product_name)
                    
                    items.append({
                        'product_name': product_name,
                        'quantity': quantity,
                        'unit_price': unit_price
                    })
        
        return items
    
    def _estimate_price(self, product_name: str) -> float:
        """Оценка цены товара"""
        product_name_lower = product_name.lower()
        
        # Базовые цены для популярных товаров
        price_map = {
            'парацетамол': 45.0,
            'ибупрофен': 80.0,
            'аспирин': 35.0,
            'анальгин': 25.0,
            'арбидол': 250.0,
            'кагоцел': 200.0,
            'ремантадин': 150.0,
            'осельтамивир': 300.0,
            'лозартан': 120.0,
            'эналаприл': 90.0,
            'амлодипин': 85.0,
            'витамин': 50.0,
            'ромашка': 30.0,
            'шалфей': 25.0,
            'эхинацея': 45.0,
            'цефтриаксон': 150.0,
            'новокаин': 45.0,
            'физраствор': 35.0
        }
        
        for key, price in price_map.items():
            if key in product_name_lower:
                return price
        
        # Стандартная цена для неизвестных товаров
        return 100.0
    
    def _get_status_display(self, status: str) -> str:
        """Получение отображения статуса"""
        status_map = {
            OrderStatus.CREATED.value: "📝 Создана",
            OrderStatus.PENDING_OPERATOR.value: "⏳ На рассмотрении",
            OrderStatus.CONFIRMED.value: "✅ Подтверждена",
            OrderStatus.REJECTED.value: "❌ Отклонена",
            OrderStatus.COLLECTING.value: "🔄 В сборке",
            OrderStatus.COLLECTED.value: "📦 Собрана",
            OrderStatus.CHECKING.value: "🔍 На проверке",
            OrderStatus.READY_FOR_DELIVERY.value: "🚀 Готова к доставке",
            OrderStatus.IN_DELIVERY.value: "🚚 В пути",
            OrderStatus.DELIVERED.value: "✅ Доставлена",
            OrderStatus.PAID.value: "💳 Оплачена",
            OrderStatus.PARTIALLY_PAID.value: "💰 Частично оплачена",
            OrderStatus.DEBT.value: "💸 Долг"
        }
        
        return status_map.get(status, status)
