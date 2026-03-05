#!/usr/bin/env python3
"""
🎨 MAXXPHARM Visual CRM - Красивый визуальный интерфейс как приложение
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
from visual_handlers import VisualHandlers
from notification_system import NotificationSystem
from ai_director import AIDirector
from automated_reports import AutomatedReports
from ux_interface import (
    ClientUX, OperatorUX, PickerUX, CheckerUX,
    CourierUX, DirectorUX, AdminUX, UXHelper
)

class VisualCRMBot:
    """Визуальный CRM бот с красивым UX"""
    
    def __init__(self):
        self.logger = logging.getLogger("visual_crm_bot")
        self.crm = SaaSCRMCore()
        self.bot = None
        self.dp = None
        self.notification_system = None
        self.ai_director = None
        self.automated_reports = None
        self.visual_handlers = None
        
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
            self.visual_handlers = VisualHandlers(self.crm, self.bot)
            
            # Настройка обработчиков
            await self._setup_handlers()
            
            # Создаем тестовых пользователей
            await self._create_test_users()
            
            self.logger.info("✅ Visual CRM Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    async def _create_test_users(self):
        """Создание тестовых пользователей с красивыми именами"""
        # Создаем тестовых пользователей разных ролей
        test_users = [
            (697780123, "Директор Мухаммадмуссо", "+998900000001", UserRole.DIRECTOR),
            (697780124, "Оператор Али", "+998900000002", UserRole.OPERATOR),
            (697780125, "Сборщик Рустам", "+998900000003", UserRole.PICKER),
            (697780126, "Проверщик Камол", "+998900000004", UserRole.CHECKER),
            (697780127, "Курьер Бекзод", "+998900000005", UserRole.COURIER),
            (697780128, "Клиент Ахмад", "+998900000006", UserRole.CLIENT),
            (697780129, "Клиент Фарход", "+998900000007", UserRole.CLIENT),
            (697780130, "Администратор Сарвар", "+998900000008", UserRole.ADMIN),
        ]
        
        for telegram_id, name, phone, role in test_users:
            if telegram_id not in [user.telegram_id for user in self.crm.users.values()]:
                self.crm.create_user(telegram_id, name, phone, role)
                self.logger.info(f"👤 Created test user: {name} ({role.value})")
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        
        # 🎨 Регистрируем визуальные обработчики
        self.visual_handlers.register_handlers(self.dp)
        
        # 🎨 Дополнительные обработчики для разных ролей
        @dp.message(Command("menu"))
        async def cmd_menu(message: types.Message):
            """Показать меню для роли"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            # Показываем меню в зависимости от роли
            if user.role == UserRole.CLIENT:
                await message.answer("📱 <b>Меню клиента</b>", reply_markup=ClientUX.get_welcome_keyboard())
            elif user.role == UserRole.OPERATOR:
                await message.answer("👨‍💻 <b>Меню оператора</b>", reply_markup=OperatorUX.get_main_keyboard())
            elif user.role == UserRole.PICKER:
                await message.answer("📦 <b>Меню сборщика</b>", reply_markup=PickerUX.get_main_keyboard())
            elif user.role == UserRole.CHECKER:
                await message.answer("🔍 <b>Меню проверщика</b>", reply_markup=CheckerUX.get_main_keyboard())
            elif user.role == UserRole.COURIER:
                await message.answer("🚚 <b>Меню курьера</b>", reply_markup=CourierUX.get_main_keyboard())
            elif user.role == UserRole.DIRECTOR:
                await message.answer("👑 <b>Меню директора</b>", reply_markup=DirectorUX.get_main_keyboard())
            elif user.role == UserRole.ADMIN:
                await message.answer("👑 <b>Меню администратора</b>", reply_markup=AdminUX.get_main_keyboard())
            else:
                await message.answer("❌ Роль не определена")
        
        @dp.message(F.text == "📞 Менеджер")
        async def cmd_manager(message: types.Message):
            """Связь с менеджером"""
            await message.answer(
                "📞 <b>Связь с менеджером</b>\n\n"
                "📱 Телефон: +998 90 123 45 67\n"
                "💬 WhatsApp: +998 90 123 45 67\n"
                "📧 Email: manager@maxxpharm.com\n\n"
                "⏰ Время работы: 9:00 - 18:00\n"
                "📍 Адрес: г. Душанбе, ул. Айни, 45"
            )
        
        @dp.message(F.text == "ℹ️ Информация")
        async def cmd_info(message: types.Message):
            """Информация о сервисе"""
            info_text = """
ℹ️ <b>О MAXXPHARM</b>

🏥 <b>Система заказов фармпрепаратов</b>

📱 <b>Наши преимущества:</b>
• Быстрая доставка по городу
• Только качественные препараты
• Удобная оплата
• Отслеживание заказа

🚚 <b>Доставка:</b>
• По Душанбе: 1-2 часа
• По району: 3-4 часа
• Бесплатно при заказе от 100 сомони

💳 <b>Оплата:</b>
• Наличными курьеру
• Банковской картой
• Через платежные системы

📞 <b>Контакты:</b>
• Телефон: +998 90 123 45 67
• Email: info@maxxpharm.com
• Сайт: www.maxxpharm.com

🕐 <b>Время работы:</b>
• Пн-Пт: 9:00 - 18:00
• Сб: 9:00 - 15:00
• Вс: выходной

Спасибо, что выбрали нас! 🙏
"""
            
            await message.answer(info_text)
        
        @dp.message(F.text == "📈 Статистика")
        async def cmd_statistics_visual(message: types.Message):
            """Визуальная статистика"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role not in [UserRole.OPERATOR, UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем статистику
            analytics = self.crm.get_analytics(days=7)
            
            stats_text = f"""
📊 <b>Статистика за {analytics['period_days']} дней</b>

📈 <b>Заказы:</b>
• Всего: {analytics['total_orders']}
• Доставлено: {analytics['delivered_orders']}
• Конверсия: {analytics['conversion_rate']}%

💰 <b>Финансы:</b>
• Общая выручка: ${analytics['total_revenue']:,}
• Выручка в день: ${analytics['revenue_per_day']:,}
• Средний чек: ${analytics['total_revenue']/analytics['delivered_orders'] if analytics['delivered_orders'] > 0 else 0:.2f}

⏱️ <b>Время обработки:</b>
• Среднее: {analytics['avg_processing_time']:.1f} часов

📅 <b>Дата:</b> {datetime.now().strftime('%d %B %Y')}
"""
            
            await message.answer(stats_text)
        
        @dp.message(F.text == "👥 Пользователи")
        async def cmd_users_visual(message: types.Message):
            """Визуальный список пользователей"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Формируем список пользователей
            users_list = []
            for u in self.crm.users.values():
                users_list.append({
                    'name': u.name,
                    'phone': u.phone,
                    'role': u.role.value,
                    'created_at': u.created_at,
                    'is_active': u.is_active
                })
            
            users_text = AdminUX.format_users_list(users_list)
            await message.answer(users_text)
        
        @dp.message(F.text == "⏱ Время обработки")
        async def cmd_processing_time(message: types.Message):
            """Время обработки заказов"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Анализ времени обработки
            processing_times = []
            for order in self.crm.orders.values():
                if order.status == OrderStatus.DELIVERED:
                    processing_time = (datetime.now() - order.created_at).total_seconds() / 3600
                    processing_times.append(processing_time)
            
            if not processing_times:
                await message.answer("📊 <b>Время обработки</b>\n\nНет данных для анализа")
                return
            
            avg_time = sum(processing_times) / len(processing_times)
            min_time = min(processing_times)
            max_time = max(processing_times)
            
            time_text = f"""
⏱️ <b>Время обработки заказов</b>

📊 <b>Статистика:</b>
• Среднее время: {avg_time:.1f} часов
• Минимальное: {min_time:.1f} часов
• Максимальное: {max_time:.1f} часов
• Обработано заказов: {len(processing_times)}

📈 <b>Анализ:</b>
"""
            
            if avg_time > 4:
                time_text += "⚠️ Время обработки выше нормы. Рекомендуется оптимизировать процессы."
            elif avg_time > 2:
                time_text += "🟡 Время обработки в пределах нормы, но можно улучшить."
            else:
                time_text += "✅ Время обработки отличное!"
            
            await message.answer(time_text)
        
        @dp.message(F.text == "👥 Сотрудники")
        async def cmd_staff_visual(message: types.Message):
            """Визуальная информация о сотрудниках"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Собираем статистику по сотрудникам
            staff_stats = {}
            for u in self.crm.users.values():
                if u.role != UserRole.CLIENT:
                    role_name = u.role.value.title()
                    if role_name not in staff_stats:
                        staff_stats[role_name] = []
                    staff_stats[role_name].append(u)
            
            staff_text = "👥 <b>Сотрудники MAXXPHARM</b>\n\n"
            
            for role, users in staff_stats.items():
                active_users = [u for u in users if u.is_active]
                staff_text += f"👤 <b>{role}:</b> {len(active_users)}/{len(users)} активных\n"
                
                for u in active_users[:3]:  # Показываем первых 3
                    staff_text += f"  • {u.name}\n"
                
                if len(active_users) > 3:
                    staff_text += f"  • ... и еще {len(active_users) - 3}\n"
                
                staff_text += "\n"
            
            await message.answer(staff_text)
        
        # 🎨 Тестовые команды
        @dp.message(Command("test_order_visual"))
        async def cmd_test_order_visual(message: types.Message):
            """Создание тестового визуального заказа"""
            user = self._get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            # Создаем тестовый заказ
            order = self.crm.create_order(
                client_id=user.id,
                text="Тестовая заявка на лекарства с красивым визуальным интерфейсом",
                items=[
                    {"product": "Парацетамол 500мг", "quantity": 2, "price": 5.50},
                    {"product": "Ибупрофен 400мг", "quantity": 1, "price": 8.25},
                    {"product": "Витамин C 1000мг", "quantity": 1, "price": 12.00}
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
        
        @dp.message(Command("demo_all_roles"))
        async def cmd_demo_all_roles(message: types.Message):
            """Демонстрация всех ролей"""
            demo_text = """
🎨 <b>Демонстрация всех ролей MAXXPHARM</b>

📱 <b>Клиент</b> - создает заявки и отслеживает заказы
👨‍💻 <b>Оператор</b> - обрабатывает заявки и подтверждает оплату
📦 <b>Сборщик</b> - собирает заказы
🔍 <b>Проверщик</b> - контролирует качество
🚚 <b>Курьер</b> - доставляет заказы
👑 <b>Директор</b> - управляет бизнесом и анализирует данные
👨‍💼 <b>Администратор</b> - управляет системой

🎯 <b>Тестовые ID:</b>
• Директор: 697780123
• Оператор: 697780124
• Сборщик: 697780125
• Проверщик: 697780126
• Курьер: 697780127
• Клиент 1: 697780128
• Клиент 2: 697780129

🚀 <b>Команды для тестирования:</b>
• /start - запуск с определением роли
• /menu - показать меню роли
• /test_order_visual - создать тестовый заказ
• /demo_ux - демонстрация интерфейсов

💡 <b>Каждая роль видит свой интерфейс!</b>
"""
            
            await message.answer(demo_text)
    
    def _get_user_by_telegram_id(self, telegram_id: int):
        """Получение пользователя по telegram_id"""
        for user in self.crm.users.values():
            if user.telegram_id == telegram_id:
                return user
        return None
    
    async def start(self):
        """Запуск бота"""
        if not await self.initialize():
            return False
        
        try:
            # Запускаем автоматические отчеты
            reports_task = asyncio.create_task(self.automated_reports.start_daily_reports())
            
            # Удаляем webhook и запускаем polling
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            print("🎨 MAXXPHARM Visual CRM Bot starting...")
            print(f"🤖 Bot: @{(await self.bot.get_me()).username}")
            print(f"👥 Users: {len(self.crm.users)}")
            print(f"📦 Orders: {len(self.crm.orders)}")
            print("🎨 Beautiful UX Interface Ready!")
            
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"❌ Bot runtime error: {e}")
            return False

async def main():
    """Основная функция"""
    print("🎨 MAXXPHARM Visual CRM Bot starting...")
    print("📱 Beautiful UX Interface like mobile app!")
    
    bot = VisualCRMBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
