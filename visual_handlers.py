#!/usr/bin/env python3
"""
🎨 Visual Handlers - Визуальные обработчики с UX интерфейсом
"""

import asyncio
import logging
from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from datetime import datetime

# Импортируем UX интерфейсы
from ux_interface import (
    ClientUX, OperatorUX, PickerUX, CheckerUX, 
    CourierUX, DirectorUX, AdminUX, UXHelper
)
from saas_crm_core import SaaSCRMCore, UserRole, OrderStatus

class VisualHandlers:
    """Визуальные обработчики с красивым UX"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
        self.logger = logging.getLogger("visual_handlers")
    
    def register_handlers(self, dp):
        """Регистрация всех обработчиков"""
        
        # 🎨 Клиентские обработчики
        @dp.message(Command("start"))
        async def cmd_start_visual(message: types.Message):
            """Визуальный /start"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                # Создаем нового клиента
                user = self.crm.create_user(
                    message.from_user.id,
                    message.from_user.full_name,
                    "+998900000000",
                    UserRole.CLIENT
                )
            
            # Показываем приветствие и меню
            welcome_text = ClientUX.format_welcome_message(user.name)
            await message.answer(welcome_text, reply_markup=ClientUX.get_welcome_keyboard())
        
        @dp.message(F.text == "📦 Сделать заявку")
        async def cmd_create_order_visual(message: types.Message):
            """Визуальное создание заявки"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен!")
                return
            
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "Выберите способ отправки заявки:",
                reply_markup=ClientUX.get_order_creation_keyboard()
            )
        
        @dp.message(F.text == "📍 Моя заявка")
        async def cmd_my_orders_visual(message: types.Message):
            """Визуальные мои заявки"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен!")
                return
            
            orders = self.crm.get_user_orders(user.id)
            
            if not orders:
                await message.answer(UXHelper.get_empty_state_message("Заявок"))
                return
            
            # Показываем последнюю заявку
            last_order = orders[-1]
            order_card = ClientUX.format_order_card({
                'id': last_order.id,
                'status': last_order.status.value,
                'status_text': last_order.status.value.replace('_', ' ').title(),
                'amount': last_order.amount,
                'created_at': last_order.created_at,
                'updated_at': last_order.created_at,
                'text': last_order.text
            })
            
            await message.answer(order_card)
        
        # 👨‍💻 Операторские обработчики
        @dp.message(F.text == "📥 Новые заявки")
        async def cmd_new_orders_visual(message: types.Message):
            """Визуальные новые заявки"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем новые заявки
            new_orders = [
                order for order in self.crm.orders.values()
                if order.status in [OrderStatus.CREATED, OrderStatus.WAITING_PAYMENT]
            ]
            
            orders_list = OperatorUX.format_new_orders_list([
                {
                    'id': order.id,
                    'client_name': f"Клиент #{order.client_id}",
                    'amount': order.amount,
                    'status': order.status.value,
                    'created_at': order.created_at
                }
                for order in new_orders
            ])
            
            await message.answer(orders_list)
        
        @dp.message(F.text == "💳 Проверить оплату")
        async def cmd_check_payment_visual(message: types.Message):
            """Визуальная проверка оплаты"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем заявки ожидающие оплаты
            waiting_orders = [
                order for order in self.crm.orders.values()
                if order.status == OrderStatus.WAITING_PAYMENT
            ]
            
            if not waiting_orders:
                await message.answer(UXHelper.get_empty_state_message("Заявок ожидающих оплаты"))
                return
            
            orders_text = "💳 <b>Заявки ожидающие оплаты:</b>\n\n"
            
            for order in waiting_orders:
                orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
                orders_text += f"💰 ${order.amount}\n"
                orders_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        # 📦 Обработчики сборщика
        @dp.message(F.text == "📦 Заявки в сборке")
        async def cmd_picker_orders_visual(message: types.Message):
            """Визуальные заявки сборщика"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.PICKER:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем заказы сборщика
            picker_orders = [
                order for order in self.crm.orders.values()
                if order.assigned_picker == user.id and order.status in [OrderStatus.ACCEPTED, OrderStatus.PROCESSING]
            ]
            
            orders_text = PickerUX.format_picker_orders([
                {
                    'id': order.id,
                    'text': order.text,
                    'amount': order.amount,
                    'created_at': order.created_at,
                    'urgent': False
                }
                for order in picker_orders
            ])
            
            await message.answer(orders_text)
        
        # 🔍 Обработчики проверщика
        @dp.message(F.text == "🔍 На проверке")
        async def cmd_checker_orders_visual(message: types.Message):
            """Визуальные заявки проверщика"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CHECKER:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем заказы проверщика
            checker_orders = [
                order for order in self.crm.orders.values()
                if order.assigned_checker == user.id and order.status == OrderStatus.READY
            ]
            
            if not checker_orders:
                await message.answer(UXHelper.get_empty_state_message("Заявок на проверке"))
                return
            
            # Показываем первый заказ на проверку
            order = checker_orders[0]
            order_text = CheckerUX.format_checking_order({
                'id': order.id,
                'items_text': order.text,
                'amount': order.amount
            })
            
            await message.answer(
                order_text,
                reply_markup=CheckerUX.get_checker_actions_keyboard(order.id)
            )
        
        # 🚚 Обработчики курьера
        @dp.message(F.text == "🚚 Заявки к доставке")
        async def cmd_courier_orders_visual(message: types.Message):
            """Визуальные заявки курьера"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.COURIER:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем заказы курьера
            courier_orders = [
                order for order in self.crm.orders.values()
                if order.assigned_courier == user.id and order.status in [OrderStatus.WAITING_COURIER, OrderStatus.ON_WAY]
            ]
            
            if not courier_orders:
                await message.answer(UXHelper.get_empty_state_message("Заявок к доставке"))
                return
            
            # Показываем первый заказ
            order = courier_orders[0]
            order_text = CourierUX.format_delivery_order({
                'id': order.id,
                'client_name': f"Клиент #{order.client_id}",
                'address': "Адрес будет здесь",
                'phone': "+998900000000",
                'items_text': order.text,
                'amount': order.amount
            })
            
            await message.answer(
                order_text,
                reply_markup=CourierUX.get_courier_actions_keyboard(order.id)
            )
        
        # 👑 Обработчики директора
        @dp.message(F.text == "📊 Дашборд")
        async def cmd_dashboard_visual(message: types.Message):
            """Визуальный дашборд"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем данные дашборда
            dashboard_data = self.crm.get_dashboard_data()
            
            dashboard_text = DirectorUX.format_dashboard(dashboard_data)
            await message.answer(dashboard_text)
        
        @dp.message(F.text == "📦 Воронка заказов")
        async def cmd_sales_funnel_visual(message: types.Message):
            """Визуальная воронка заказов"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем данные воронки
            funnel_data = {
                'created': len([o for o in self.crm.orders.values() if o.status == OrderStatus.CREATED]),
                'paid': len([o for o in self.crm.orders.values() if o.status == OrderStatus.ACCEPTED]),
                'accepted': len([o for o in self.crm.orders.values() if o.status == OrderStatus.PROCESSING]),
                'processing': len([o for o in self.crm.orders.values() if o.status == OrderStatus.READY]),
                'delivered': len([o for o in self.crm.orders.values() if o.status == OrderStatus.DELIVERED])
            }
            
            funnel_text = DirectorUX.format_sales_funnel(funnel_data)
            await message.answer(funnel_text)
        
        @dp.message(F.text == "🧠 AI Анализ")
        async def cmd_ai_analysis_visual(message: types.Message):
            """Визуальный AI анализ"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Создаем тестовый AI отчет
            ai_report = {
                'orders': 142,
                'revenue': 24500,
                'clients': 89,
                'problems': [
                    'Сборщик №2 делает ошибки в 12% заказов',
                    'Среднее время доставки увеличилось на 15 минут'
                ],
                'recommendations': [
                    'Дополнительное обучение для сборщика №2',
                    'Оптимизация маршрутов доставки'
                ],
                'forecast_orders': 156,
                'forecast_revenue': 26800
            }
            
            report_text = DirectorUX.format_ai_report(ai_report)
            await message.answer(report_text)
        
        # 🎨 Callback обработчики
        @dp.callback_query(F.data.startswith("accept_order_"))
        async def callback_accept_order(callback: CallbackQuery):
            """Принятие заказа"""
            try:
                order_id = int(callback.data.split("_")[2])
                user = self._get_user_by_telegram_id(callback.from_user.id)
                
                if not user or user.role != UserRole.OPERATOR:
                    await callback.answer("❌ Доступ запрещен!", show_alert=True)
                    return
                
                # Меняем статус заказа
                if self.crm.change_order_status(order_id, OrderStatus.ACCEPTED, user.id):
                    await callback.answer("✅ Заказ принят!", show_alert=True)
                    await callback.message.edit_text("✅ <b>Заказ принят в обработку</b>")
                else:
                    await callback.answer("❌ Не удалось принять заказ", show_alert=True)
                    
            except Exception as e:
                self.logger.error(f"❌ Accept order error: {e}")
                await callback.answer("❌ Ошибка при принятии заказа", show_alert=True)
        
        @dp.callback_query(F.data.startswith("reject_order_"))
        async def callback_reject_order(callback: CallbackQuery):
            """Отклонение заказа"""
            try:
                order_id = int(callback.data.split("_")[2])
                user = self._get_user_by_telegram_id(callback.from_user.id)
                
                if not user or user.role != UserRole.OPERATOR:
                    await callback.answer("❌ Доступ запрещен!", show_alert=True)
                    return
                
                # Меняем статус заказа
                if self.crm.change_order_status(order_id, OrderStatus.REJECTED, user.id):
                    await callback.answer("❌ Заказ отклонен", show_alert=True)
                    await callback.message.edit_text("❌ <b>Заказ отклонен</b>")
                else:
                    await callback.answer("❌ Не удалось отклонить заказ", show_alert=True)
                    
            except Exception as e:
                self.logger.error(f"❌ Reject order error: {e}")
                await callback.answer("❌ Ошибка при отклонении заказа", show_alert=True)
        
        @dp.callback_query(F.data.startswith("check_passed_"))
        async def callback_check_passed(callback: CallbackQuery):
            """Проверка пройдена"""
            try:
                order_id = int(callback.data.split("_")[2])
                user = self._get_user_by_telegram_id(callback.from_user.id)
                
                if not user or user.role != UserRole.CHECKER:
                    await callback.answer("❌ Доступ запрещен!", show_alert=True)
                    return
                
                # Меняем статус заказа
                if self.crm.change_order_status(order_id, OrderStatus.WAITING_COURIER, user.id):
                    await callback.answer("✅ Проверка пройдена!", show_alert=True)
                    await callback.message.edit_text("✅ <b>Заказ проверен и передан курьеру</b>")
                else:
                    await callback.answer("❌ Не удалось подтвердить проверку", show_alert=True)
                    
            except Exception as e:
                self.logger.error(f"❌ Check passed error: {e}")
                await callback.answer("❌ Ошибка при проверке", show_alert=True)
        
        @dp.callback_query(F.data.startswith("delivered_"))
        async def callback_delivered(callback: CallbackQuery):
            """Доставка завершена"""
            try:
                order_id = int(callback.data.split("_")[1])
                user = self._get_user_by_telegram_id(callback.from_user.id)
                
                if not user or user.role != UserRole.COURIER:
                    await callback.answer("❌ Доступ запрещен!", show_alert=True)
                    return
                
                # Меняем статус заказа
                if self.crm.change_order_status(order_id, OrderStatus.DELIVERED, user.id):
                    await callback.answer("✅ Заказ доставлен!", show_alert=True)
                    await callback.message.edit_text("✅ <b>Заказ успешно доставлен!</b>")
                else:
                    await callback.answer("❌ Не подтвердить доставку", show_alert=True)
                    
            except Exception as e:
                self.logger.error(f"❌ Delivered error: {e}")
                await callback.answer("❌ Ошибка при доставке", show_alert=True)
        
        # 🎨 Тестовые команды
        @dp.message(Command("test_visual"))
        async def cmd_test_visual(message: types.Message):
            """Тест визуального интерфейса"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            # Создаем тестовый заказ
            order = self.crm.create_order(
                client_id=user.id,
                text="Тестовая заявка на лекарства с визуальным интерфейсом",
                items=[
                    {"product": "Парацетамол", "quantity": 2, "price": 5.0},
                    {"product": "Ибупрофен", "quantity": 1, "price": 8.0}
                ]
            )
            
            # Показываем красивую карточку заказа
            order_card = ClientUX.format_order_card({
                'id': order.id,
                'status': order.status.value,
                'status_text': order.status.value.replace('_', ' ').title(),
                'amount': order.amount,
                'created_at': order.created_at,
                'updated_at': order.created_at,
                'text': order.text
            })
            
            await message.answer("✅ <b>Тестовый заказ создан</b>\n\n" + order_card)
        
        @dp.message(Command("demo_ux"))
        async def cmd_demo_ux(message: types.Message):
            """Демонстрация UX интерфейсов"""
            demo_text = """
🎨 <b>Демонстрация UX интерфейсов</b>

📱 <b>Клиент:</b>
📦 Сделать заявку
💳 Оплата
📍 Моя заявка

👨‍💻 <b>Оператор:</b>
📥 Новые заявки
💳 Проверить оплату
📊 Мои заявки

📦 <b>Сборщик:</b>
📦 Заявки в сборке
🔄 В обработке
✅ Готово

🔍 <b>Проверщик:</b>
🔍 На проверке
❌ Ошибка
✅ Проверено

🚚 <b>Курьер:</b>
🚚 Заявки к доставке
📍 В пути
✅ Доставлено

👑 <b>Директор:</b>
📊 Дашборд
📈 Продажи
📦 Воронка заказов
🧠 AI Анализ

Используйте /start для тестирования!
"""
            
            await message.answer(demo_text)
    
    def _get_user_by_telegram_id(self, telegram_id: int):
        """Получение пользователя по telegram_id"""
        for user in self.crm.users.values():
            if user.telegram_id == telegram_id:
                return user
        return None
