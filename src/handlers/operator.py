"""
🔹 Обработчики операторов MAXXPHARM CRM
"""

from typing import List, Dict, Any
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..models.database import UserRole, OrderStatus
from ..services.user_service import UserService
from ..services.order_service import OrderService
from ..database import get_db


class OperatorHandlers:
    """Обработчики для операторов"""
    
    def __init__(self):
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.router.message(F.text == "📥 Новые заявки")
        async def handle_new_orders(message: Message):
            """Просмотр новых заявок"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.OPERATOR:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем новые заявки
                new_orders = await order_service.get_pending_orders_for_operator()
                
                if not new_orders:
                    await message.answer(
                        "📭 <b>Новых заявок нет</b>\n\n"
                        "🎯 Все заявки обработаны\n"
                        "⏱️ Ожидайте новые заказы"
                    )
                    return
                
                text = f"📥 <b>Новые заявки ({len(new_orders)})</b>\n\n"
                
                keyboard_buttons = []
                
                for i, order in enumerate(new_orders[:10], 1):  # Показываем первые 10
                    status_display = self._get_status_display(order.status)
                    
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"👤 Клиент: {order.client.full_name}\n"
                    text += f"🏥 Аптека: {order.pharmacy.name}\n"
                    text += f"💰 Сумма: {order.total_amount} сомони\n"
                    text += f"📊 Статус: {status_display}\n"
                    text += f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    
                    if order.notes:
                        text += f"📝 Примечание: {order.notes[:50]}...\n"
                    
                    text += "\n"
                    
                    # Кнопки действий
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"✅ Принять {order.order_number}",
                            callback_data=f"accept_order_{order.id}"
                        ),
                        InlineKeyboardButton(
                            text=f"❌ Отказать {order.order_number}",
                            callback_data=f"reject_order_{order.id}"
                        )
                    ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                
                await message.answer(text, reply_markup=keyboard)
        
        @self.router.callback_query(F.data.startswith("accept_order_"))
        async def handle_accept_order(callback: types.CallbackQuery):
            """Подтверждение заказа"""
            order_id = int(callback.data.split("_")[2])
            
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                operator = await user_service.get_user_by_telegram_id(callback.from_user.id)
                if not operator or operator.role != UserRole.OPERATOR:
                    await callback.answer("❌ Доступ запрещен", show_alert=True)
                    return
                
                # Обновляем статус заказа
                order = await order_service.update_order_status(
                    order_id=order_id,
                    new_status=OrderStatus.CONFIRMED,
                    operator_id=operator.id
                )
                
                if order:
                    await callback.message.edit_text(
                        f"✅ <b>Заказ подтвержден!</b>\n\n"
                        f"📝 Номер: {order.order_number}\n"
                        f"👤 Оператор: {operator.full_name}\n"
                        f"📊 Статус: {self._get_status_display(order.status)}\n\n"
                        f"🔄 Заказ передан в сборку\n\n"
                        f"🏥 MAXXPHARM - Эффективная обработка!"
                    )
                    
                    await callback.answer("✅ Заказ подтвержден")
                else:
                    await callback.answer("❌ Ошибка подтверждения", show_alert=True)
        
        @self.router.callback_query(F.data.startswith("reject_order_"))
        async def handle_reject_order(callback: types.CallbackQuery):
            """Отклонение заказа"""
            order_id = int(callback.data.split("_")[2])
            
            # Запрос причины отказа
            await callback.message.edit_text(
                f"❌ <b>Отклонение заказа #{order_id}</b>\n\n"
                "📝 <b>Укажите причину отказа:</b>\n\n"
                "1. 📦 Нет в наличии\n"
                "2. 💰 Минимальная сумма\n"
                "3. 📍 Далеко доставка\n"
                "4. 🕐 Время работы\n"
                "5. 📝 Другое\n\n"
                "📝 Напишите причину:"
            )
            
            await callback.answer()
        
        @self.router.message(F.text == "📦 В работе")
        async def handle_orders_in_work(message: Message):
            """Просмотр заказов в работе"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.OPERATOR:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем заказы в работе
                work_orders = await order_service.get_orders_by_status(OrderStatus.CONFIRMED)
                
                if not work_orders:
                    await message.answer(
                        "📭 <b>Заказов в работе нет</b>\n\n"
                        "🎯 Все обработанные заказы переданы дальше"
                    )
                    return
                
                text = f"📦 <b>Заказы в работе ({len(work_orders)})</b>\n\n"
                
                for order in work_orders[:10]:
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"👤 Клиент: {order.client.full_name}\n"
                    text += f"🏥 Аптека: {order.pharmacy.name}\n"
                    text += f"💰 Сумма: {order.total_amount} сомони\n"
                    text += f"📊 Статус: {self._get_status_display(order.status)}\n"
                    text += f"📅 Подтвержден: {order.confirmed_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                await message.answer(text)
        
        @self.router.message(F.text == "💳 Оплата")
        async def handle_payment_check(message: Message):
            """Проверка оплаты"""
            await message.answer(
                "💳 <b>Проверка оплаты</b>\n\n"
                "📋 <b>Как проверить оплату:</b>\n\n"
                "1. 📸 Фото чека\n"
                "   • Клиент отправляет фото\n"
                "   • Проверяйте реквизиты\n"
                "   • Сумма и получатель\n\n"
                "2. 📱 Номер операции\n"
                "   • Запросите у клиента\n"
                "   • Проверьте в системе\n\n"
                "3. 💰 Наличные\n"
                "   • Курьер подтверждает\n"
                "   • Торговый представитель\n\n"
                "📊 <b>После проверки:</b>\n"
                "• ✅ Подтвердите оплату\n"
                "• ❌ Укажите проблему\n\n"
                "🏥 MAXXPHARM - Контроль платежей"
            )
        
        @self.router.message(F.text == "✅ Принять")
        async def handle_quick_accept(message: Message):
            """Быстрое принятие"""
            await message.answer(
                "✅ <b>Быстрое принятие заказа</b>\n\n"
                "📝 <b>Для принятия заказа:</b>\n\n"
                "1. 📥 Перейдите в 'Новые заявки'\n"
                "2. 📋 Выберите заказ\n"
                "3. ✅ Нажмите 'Принять'\n\n"
                "⚡ <b>Быстрые действия:</b>\n"
                "• 📥 Новые заявки - список\n"
                "• 📦 В работе - принятые\n"
                "• ❌ Отказать - с причиной\n\n"
                "🏥 MAXXPHARM - Эффективная работа!"
            )
        
        @self.router.message(F.text == "❌ Отказать")
        async def handle_quick_reject(message: Message):
            """Быстрый отказ"""
            await message.answer(
                "❌ <b>Отклонение заказа</b>\n\n"
                "📝 <b>Причины отказа:</b>\n\n"
                "1. 📦 <b>Нет в наличии</b>\n"
                "   • Лекарства закончились\n"
                "   • Снято с производства\n\n"
                "2. 💰 <b>Минимальная сумма</b>\n"
                "   • Меньше 500 сомони\n"
                "   • Доставка не рентабельна\n\n"
                "3. 📍 <b>Далеко доставка</b>\n"
                "   • За пределы города\n"
                "   • Сложный маршрут\n\n"
                "4. 🕐 <b>Время работы</b>\n"
                "   • Ночное время\n"
                "   • Выходной день\n\n"
                "5. 📝 <b>Другое</b>\n"
                "   • Укажите причину\n\n"
                "🏥 MAXXPHARM - Профессиональный подход!"
            )
        
        @self.router.message(F.text == "📊 Статистика")
        async def handle_operator_stats(message: Message):
            """Статистика оператора"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.OPERATOR:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем статистику
                stats = await order_service.get_order_statistics()
                
                text = f"""
📊 <b>Статистика оператора</b>

👤 <b>Оператор:</b> {user.full_name}
📅 <b>Сегодня:</b> {user.created_at.strftime('%d.%m.%Y')}

📈 <b>Общая статистика:</b>
• 📦 Всего заказов: {stats['total_orders']}
• 📦 Заказов сегодня: {stats['today_orders']}
• 💰 Общая сумма: {stats['total_amount']:.2f} сомони

📊 <b>По статусам:</b>
• 📝 Создано: {stats['status_distribution'].get('created', 0)}
• ⏳ На рассмотрении: {stats['status_distribution'].get('pending_operator', 0)}
• ✅ Подтверждено: {stats['status_distribution'].get('confirmed', 0)}
• ❌ Отклонено: {stats['status_distribution'].get('rejected', 0)}
• 🔄 В сборке: {stats['status_distribution'].get('collecting', 0)}
• 📦 Собрано: {stats['status_distribution'].get('collected', 0)}
• 🚚 Доставлено: {stats['status_distribution'].get('delivered', 0)}

🎯 <b>Эффективность:</b>
• ✅ Подтверждено: {self._calculate_confirmation_rate(stats):.1f}%
• ⚡ Среднее время: 5 минут

🏥 <b>MAXXPHARM - Аналитика в реальном времени</b>
                """
                
                await message.answer(text)
    
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
    
    def _calculate_confirmation_rate(self, stats: Dict[str, Any]) -> float:
        """Расчет процента подтверждения"""
        confirmed = stats['status_distribution'].get('confirmed', 0)
        rejected = stats['status_distribution'].get('rejected', 0)
        
        if confirmed + rejected == 0:
            return 0.0
        
        return (confirmed / (confirmed + rejected)) * 100
