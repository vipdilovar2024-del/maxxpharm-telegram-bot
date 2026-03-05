#!/usr/bin/env python3
"""
🚀 MAXXPHARM SaaS CRM - Основной бот уровня Uber/Amazon/Glovo
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Импортируем наши модули
from saas_crm_core import SaaSCRMCore, UserRole, OrderStatus
from role_handlers import (
    ClientHandlers, OperatorHandlers, PickerHandlers,
    CheckerHandlers, CourierHandlers, DirectorHandlers
)
from notification_system import NotificationSystem
from ai_director import AIDirector
from automated_reports import AutomatedReports

class SaaSCRMBot:
    """Основной SaaS CRM бот"""
    
    def __init__(self):
        self.logger = logging.getLogger("saas_crm_bot")
        self.crm = SaaSCRMCore()
        self.bot = None
        self.dp = None
        self.notification_system = None
        self.ai_director = None
        self.automated_reports = None
        
        # Обработчики для ролей
        self.client_handlers = None
        self.operator_handlers = None
        self.picker_handlers = None
        self.checker_handlers = None
        self.courier_handlers = None
        self.director_handlers = None
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            # Получаем токен
            BOT_TOKEN = os.getenv("BOT_TOKEN")
            ADMIN_ID = int(os.getenv("ADMIN_ID", "697780123"))
            
            if not BOT_TOKEN:
                self.logger.error("❌ BOT_TOKEN не найден!")
                return False
            
            # Инициализируем бота
            self.bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
            self.dp = Dispatcher()
            
            # Инициализируем модули
            self.notification_system = NotificationSystem(self.bot, self.crm)
            self.ai_director = AIDirector()
            self.automated_reports = AutomatedReports(self.bot, self.ai_director, ADMIN_ID)
            
            # Инициализируем обработчики
            self.client_handlers = ClientHandlers(self.crm, self.bot)
            self.operator_handlers = OperatorHandlers(self.crm, self.bot)
            self.picker_handlers = PickerHandlers(self.crm, self.bot)
            self.checker_handlers = CheckerHandlers(self.crm, self.bot)
            self.courier_handlers = CourierHandlers(self.crm, self.bot)
            self.director_handlers = DirectorHandlers(self.crm, self.bot)
            
            # Настройка обработчиков
            await self._setup_handlers()
            
            # Создаем тестовых пользователей
            await self._create_test_users()
            
            self.logger.info("✅ SaaS CRM Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    async def _create_test_users(self):
        """Создание тестовых пользователей"""
        # Создаем тестовых пользователей разных ролей
        test_users = [
            (697780123, "Директор", "+998900000001", UserRole.DIRECTOR),
            (697780124, "Оператор Али", "+998900000002", UserRole.OPERATOR),
            (697780125, "Сборщик Рустам", "+998900000003", UserRole.PICKER),
            (697780126, "Проверщик Камол", "+998900000004", UserRole.CHECKER),
            (697780127, "Курьер Бекзод", "+998900000005", UserRole.COURIER),
            (697780128, "Клиент 1", "+998900000006", UserRole.CLIENT),
            (697780129, "Клиент 2", "+998900000007", UserRole.CLIENT),
        ]
        
        for telegram_id, name, phone, role in test_users:
            if telegram_id not in [user.telegram_id for user in self.crm.users.values()]:
                self.crm.create_user(telegram_id, name, phone, role)
                self.logger.info(f"👤 Created test user: {name} ({role.value})")
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            """Обработчик /start"""
            user = None
            
            # Ищем пользователя по telegram_id
            for u in self.crm.users.values():
                if u.telegram_id == message.from_user.id:
                    user = u
                    break
            
            if not user:
                # Создаем нового пользователя как клиента
                user = self.crm.create_user(
                    message.from_user.id,
                    message.from_user.full_name,
                    "+998900000000",  # Будет обновлено позже
                    UserRole.CLIENT
                )
            
            # Показываем меню в зависимости от роли
            if user.role == UserRole.CLIENT:
                await self.client_handlers.cmd_start(message)
            elif user.role == UserRole.OPERATOR:
                await message.answer("👋 Добро пожаловать, оператор!", reply_markup=self.operator_handlers.get_operator_menu())
            elif user.role == UserRole.PICKER:
                await message.answer("👋 Добро пожаловать, сборщик!", reply_markup=self.picker_handlers.get_picker_menu())
            elif user.role == UserRole.CHECKER:
                await message.answer("👋 Добро пожаловать, проверщик!", reply_markup=self.checker_handlers.get_checker_menu())
            elif user.role == UserRole.COURIER:
                await message.answer("👋 Добро пожаловать, курьер!", reply_markup=self.courier_handlers.get_courier_menu())
            elif user.role == UserRole.DIRECTOR:
                await message.answer("👋 Добро пожаловать, директор!", reply_markup=self.director_handlers.get_director_menu())
            else:
                await message.answer("❌ Роль не определена")
        
        # Обработчики для клиентов
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def cmd_create_order(message: types.Message):
            await self.client_handlers.cmd_create_order(message)
        
        @self.dp.message(F.text == "📍 Моя заявка")
        async def cmd_my_orders(message: types.Message):
            await self.client_handlers.cmd_my_orders(message)
        
        # Обработчики для операторов
        @self.dp.message(F.text == "📥 Новые заявки")
        async def cmd_new_orders(message: types.Message):
            await self.operator_handlers.cmd_new_orders(message)
        
        @self.dp.message(F.text == "💳 Подтверждение оплаты")
        async def cmd_confirm_payment(message: types.Message):
            await self.operator_handlers.cmd_confirm_payment(message)
        
        @self.dp.message(Command("confirm_payment"))
        async def cmd_confirm_payment_id(message: types.Message):
            await self.operator_handlers.cmd_confirm_payment_id(message)
        
        # Обработчики для сборщиков
        @self.dp.message(F.text == "📦 Заявки в сборке")
        async def cmd_picker_orders(message: types.Message):
            await self.picker_handlers.cmd_picker_orders(message)
        
        # Обработчики для проверщиков
        @self.dp.message(F.text == "🔍 На проверке")
        async def cmd_checker_orders(message: types.Message):
            await self.checker_handlers.cmd_checker_orders(message)
        
        # Обработчики для курьеров
        @self.dp.message(F.text == "🚚 Заявки к доставке")
        async def cmd_courier_orders(message: types.Message):
            await self.courier_handlers.cmd_courier_orders(message)
        
        # Обработчики для директора
        @self.dp.message(F.text == "📊 Дашборд")
        async def cmd_dashboard(message: types.Message):
            await self.director_handlers.cmd_dashboard(message)
        
        @self.dp.message(F.text == "📈 Продажи")
        async def cmd_analytics(message: types.Message):
            await self.director_handlers.cmd_analytics(message)
        
        # AI Director команды
        @self.dp.message(Command("director"))
        async def cmd_director(message: types.Message):
            user = None
            for u in self.crm.users.values():
                if u.telegram_id == message.from_user.id:
                    user = u
                    break
            
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен! Только для директоров.")
                return
            
            # Получаем бизнес-метрики
            metrics = self.ai_director.get_business_metrics(days=7)
            
            # Анализируем проблемы
            analysis = await self.ai_director.analyze_business_problems(metrics)
            
            # Генерируем отчет
            report = self.ai_director.generate_daily_report(metrics, analysis)
            
            await message.answer(report)
        
        @self.dp.message(Command("forecast"))
        async def cmd_forecast(message: types.Message):
            user = None
            for u in self.crm.users.values():
                if u.telegram_id == message.from_user.id:
                    user = u
                    break
            
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен! Только для директоров.")
                return
            
            # Получаем прогноз
            forecast = await self.ai_director.generate_forecast(days_ahead=7)
            
            report = f"""
📈 <b>Прогноз MAXXPHARM на {forecast['days_ahead']} дней</b>

📊 Прогноз:
• Заявок: {forecast['forecast_leads']}
• Продаж: {forecast['forecast_sales']}
• Выручка: ${forecast['forecast_revenue']}

📈 Тренды:
• Заявки: {forecast['leads_trend']}%
• Продажи: {forecast['sales_trend']}%

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            await message.answer(report)
        
        # Тестовые команды
        @self.dp.message(Command("test_order"))
        async def cmd_test_order(message: types.Message):
            """Создание тестового заказа"""
            user = None
            for u in self.crm.users.values():
                if u.telegram_id == message.from_user.id:
                    user = u
                    break
            
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            # Создаем тестовый заказ
            order = self.crm.create_order(
                client_id=user.id,
                text="Тестовая заявка на лекарства",
                items=[
                    {"product": "Парацетамол", "quantity": 2, "price": 5.0},
                    {"product": "Ибупрофен", "quantity": 1, "price": 8.0}
                ]
            )
            
            await message.answer(f"✅ Тестовый заказ #{order.id} создан")
            
            # Отправляем уведомления
            await self.notification_system.notify_new_order(order.id)
        
        @self.dp.message(Command("test_status"))
        async def cmd_test_status(message: types.Message):
            """Тест изменения статуса"""
            try:
                order_id = int(message.text.split()[1])
                new_status = message.text.split()[2]
            except (IndexError, ValueError):
                await message.answer("❌ Используйте: /test_status [ID] [STATUS]")
                return
            
            user = None
            for u in self.crm.users.values():
                if u.telegram_id == message.from_user.id:
                    user = u
                    break
            
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            try:
                status = OrderStatus(new_status)
                old_status = self.crm.orders[order_id].status
                
                if self.crm.change_order_status(order_id, status, user.id):
                    await message.answer(f"✅ Статус заказа #{order_id} изменен на {status}")
                    
                    # Отправляем уведомления
                    await self.notification_system.notify_order_status_change(
                        order_id, old_status, status, user.id
                    )
                else:
                    await message.answer("❌ Не удалось изменить статус")
            except ValueError:
                await message.answer("❌ Неверный статус")
    
    async def start(self):
        """Запуск бота"""
        if not await self.initialize():
            return False
        
        try:
            # Запускаем автоматические отчеты
            reports_task = asyncio.create_task(self.automated_reports.start_daily_reports())
            
            # Удаляем webhook и запускаем polling
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            print("🚀 MAXXPHARM SaaS CRM Bot starting...")
            print(f"🤖 Bot: @{(await self.bot.get_me()).username}")
            print(f"👥 Users: {len(self.crm.users)}")
            print(f"📦 Orders: {len(self.crm.orders)}")
            
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"❌ Bot runtime error: {e}")
            return False

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM SaaS CRM Bot starting...")
    
    bot = SaaSCRMBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
