"""
🏗️ Uber Bot - Telegram CRM с архитектурой уровня Uber
Разделение интерфейса от бизнес-логики через API Layer
"""

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode

# Импортируем наши компоненты
from api_layer import get_api_layer
from services.queue_service import enqueue_task, TaskPriority
from keyboards.main_menu import get_main_menu
from keyboards.order_cards_new import format_order_with_buttons
from middlewares.role_middleware import RoleMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/uber_bot.log')
    ]
)

logger = logging.getLogger("uber_bot")

class UberBot:
    """Uber-архитектура Telegram CRM бот"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.api_layer = None
        self.logger = logging.getLogger("uber_bot")
        
        # Создаем директорию для логов
        os.makedirs("logs", exist_ok=True)
    
    async def initialize(self) -> bool:
        """Инициализация бота"""
        try:
            # Получаем токен
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                raise ValueError("BOT_TOKEN environment variable is required")
            
            # Создаем бота
            self.bot = Bot(
                token=bot_token,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
            # Создаем диспетчер
            self.dp = Dispatcher()
            
            # Создаем API слой
            self.api_layer = get_api_layer(self.bot)
            
            # Настраиваем обработчики
            await self._setup_handlers()
            
            # Настраиваем middleware
            await self._setup_middlewares()
            
            self.logger.info("✅ Uber Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        
        # 📱 Обработчики клиента
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, role: str):
            """Обработчик /start"""
            user = await self._get_user_info(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            welcome_text = self._get_welcome_text(user)
            keyboard = get_main_menu(role)
            
            await message.answer(welcome_text, reply_markup=keyboard)
        
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def cmd_create_order(message: Message, role: str):
            """Создание заявки клиента"""
            if role != "client":
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "📦 <b>Новая заявка</b>\n\n"
                "Отправьте список препаратов, фото рецепта или голосовое сообщение:",
                reply_markup=get_main_menu(role)
            )
        
        @self.dp.message(F.text == "📍 Мои заказы")
        async def cmd_my_orders(message: Message, role: str):
            """Мои заказы клиента"""
            if role != "client":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_user_orders(message.from_user.id)
            
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
        
        @self.dp.message(F.text == "💳 Оплата")
        async def cmd_payment(message: Message, role: str):
            """Оплата заказа"""
            if role != "client":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_user_orders(message.from_user.id, limit=1)
            
            if not orders:
                await message.answer("📭 У вас нет активных заказов")
                return
            
            last_order = orders[0]
            if last_order["status"] == "created":
                await message.answer(
                    f"💳 <b>Оплата заказа #{last_order['id']}</b>\n\n"
                    f"💰 Сумма: {last_order['amount']} сомони\n\n"
                    "Отправьте фото чека или подтверждение оплаты:",
                    reply_markup=get_main_menu(role)
                )
            else:
                await message.answer("💳 Заказ уже оплачен или находится в обработке")
        
        # 👨‍💻 Обработчики оператора
        @self.dp.message(F.text == "📥 Новые заявки")
        async def cmd_new_orders(message: Message, role: str):
            """Новые заявки оператора"""
            if role != "operator":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_new_orders(message.from_user.id)
            
            if not orders:
                await message.answer("📭 Новых заявок нет")
                return
            
            # Формируем список новых заявок
            orders_text = f"📥 <b>Новые заявки ({len(orders)})</b>\n\n"
            
            for order in orders[:5]:  # Показываем первые 5
                orders_text += f"📦 <b>#{order['id']}</b> {order['client_name']}\n"
                orders_text += f"💰 {order['amount']} сомони • 🕐 {order['created_at'].strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "💳 Подтверждение оплаты")
        async def cmd_confirm_payment(message: Message, role: str):
            """Подтверждение оплаты"""
            if role != "operator":
                await message.answer("❌ Доступ запрещен")
                return
            
            # Здесь логика подтверждения оплаты
            await message.answer("💳 В разработке...")
        
        @self.dp.message(F.text == "📦 Все заказы")
        async def cmd_all_orders(message: Message, role: str):
            """Все заказы оператора"""
            if role != "operator":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_worker_orders(message.from_user.id, "operator")
            
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
        
        # 📦 Обработчики сборщика
        @self.dp.message(F.text == "📦 Заказы на сборку")
        async def cmd_picker_orders(message: Message, role: str):
            """Заказы сборщика"""
            if role != "picker":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_worker_orders(message.from_user.id, "picker")
            
            if not orders:
                await message.answer("📭 У вас нет заказов для сборки")
                return
            
            # Формируем карточки заказов
            for order in orders:
                text, keyboard = format_order_with_buttons(order, role)
                await message.answer(text, reply_markup=keyboard)
        
        # 🔍 Обработчики проверщика
        @self.dp.message(F.text == "🔍 Заказы на проверке")
        async def cmd_checker_orders(message: Message, role: str):
            """Заказы проверщика"""
            if role != "checker":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_worker_orders(message.from_user.id, "checker")
            
            if not orders:
                await message.answer("📭 Нет заказов на проверке")
                return
            
            # Формируем карточки заказов
            for order in orders:
                text, keyboard = format_order_with_buttons(order, role)
                await message.answer(text, reply_markup=keyboard)
        
        # 🚚 Обработчики курьера
        @self.dp.message(F.text == "🚚 Заказы к доставке")
        async def cmd_courier_orders(message: Message, role: str):
            """Заказы курьера"""
            if role != "courier":
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = await self.api_layer.get_worker_orders(message.from_user.id, "courier")
            
            if not orders:
                await message.answer("📭 Нет заказов для доставки")
                return
            
            # Формируем карточки заказов
            for order in orders:
                text, keyboard = format_order_with_buttons(order, role)
                await message.answer(text, reply_markup=keyboard)
        
        # 👑 Обработчики директора
        @self.dp.message(F.text == "📊 Дашборд")
        async def cmd_dashboard(message: Message, role: str):
            """Дашборд директора"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            stats = await self.api_layer.get_dashboard_stats(message.from_user.id, role)
            
            if not stats:
                await message.answer("📊 Нет данных")
                return
            
            # Формируем дашборд
            dashboard_text = f"📊 <b>Дашборд MAXXPHARM</b>\n\n"
            dashboard_text += f"📦 <b>Сегодня:</b>\n"
            dashboard_text += f"• Заказов: {stats.get('total_orders', 0)}\n"
            dashboard_text += f"• Доставлено: {stats.get('delivered_orders', 0)}\n"
            dashboard_text += f"• В работе: {stats.get('in_progress_orders', 0)}\n"
            dashboard_text += f"• Отменено: {stats.get('cancelled_orders', 0)}\n\n"
            dashboard_text += f"💰 <b>Выручка:</b> {stats.get('total_revenue', 0):.0f} сомони"
            
            await message.answer(dashboard_text)
        
        @self.dp.message(F.text == "📈 Продажи")
        async def cmd_sales(message: Message, role: str):
            """Продажи"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            # Здесь логика анализа продаж
            await message.answer("📈 Анализ продаж в разработке...")
        
        @self.dp.message(F.text == "👥 Сотрудники")
        async def cmd_staff(message: Message, role: str):
            """Сотрудники"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            # Здесь логика управления сотрудниками
            await message.answer("👥 Управление сотрудниками в разработке...")
        
        # 🧪 Тестовые команды
        @self.dp.message(Command("test_uber"))
        async def cmd_test_uber(message: Message, role: str):
            """Тест Uber-архитектуры"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer("🧱 <b>Тест Uber-архитектуры</b>\n\n")
            
            # Тестируем создание заказа через API
            try:
                order_data = {
                    "comment": "Тестовый заказ",
                    "amount": 150.0,
                    "items": [{"product": "Парацетамол", "quantity": 2}]
                }
                
                order = await self.api_layer.create_order(message.from_user.id, order_data)
                
                await message.answer(f"✅ Заказ #{order['id']} создан через API")
                await message.answer(f"📋 Задача отправлена в очередь")
                
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
        
        @self.dp.message(Command("queue_status"))
        async def cmd_queue_status(message: Message, role: str):
            """Статус очереди"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            status = await self.api_layer.get_queue_status()
            
            status_text = "📊 <b>Статус очереди</b>\n\n"
            
            for queue_name, queue_info in status.get("queues", {}).items():
                status_text += f"📋 {queue_name}:\n"
                status_text += f"  • В очереди: {queue_info['pending']}\n"
                status_text += f"  • Отложено: {queue_info['delayed']}\n\n"
            
            status_text += f"🔄 Активные задачи: {status.get('active_tasks', 0)}\n"
            status_text += f"⏰ Отложенные задачи: {status.get('delayed_tasks', 0)}\n\n"
            
            stats = status.get("stats", {})
            status_text += f"📈 Статистика:\n"
            status_text += f"  • Всего задач: {stats.get('total_tasks', 0)}\n"
            status_text += f"  • Выполнено: {stats.get('completed_tasks', 0)}\n"
            status_text += f"  • Провалено: {stats.get('failed_tasks', 0)}\n"
            status_text += f"  • Среднее время: {stats.get('avg_processing_time', 0):.1f}с"
            
            await message.answer(status_text)
        
        # 📱 Обработка текстовых сообщений для создания заказов
        @self.dp.message()
        async def handle_text_message(message: Message, role: str):
            """Обработка текстовых сообщений"""
            if role != "client":
                return
            
            # Если сообщение достаточно длинное, создаем заявку
            if len(message.text) > 10:
                try:
                    order_data = {
                        "comment": message.text,
                        "amount": 50.0,  # Базовая цена
                        "items": [{"product": "Препарат", "quantity": 1}]
                    }
                    
                    order = await self.api_layer.create_order(message.from_user.id, order_data)
                    
                    # Отправляем карточку заказа
                    order_card = format_order_with_buttons(order, role)[0]
                    
                    await message.answer(
                        f"✅ <b>Заявка создана!</b>\n\n"
                        f"{order_card}"
                        f"Мы скоро проверим ваш заказ",
                        reply_markup=get_main_menu(role)
                    )
                    
                    self.logger.info(f"📦 Order #{order['id']} created via API by client {message.from_user.id}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error creating order: {e}")
                    await message.answer("❌ Ошибка создания заявки")
        
        # 🎯 Callback обработчики
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery, role: str):
            """Обработка inline кнопок"""
            try:
                data = callback.data
                
                if data.startswith("accept_order_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.accept_order(order_id, callback.from_user.id)
                    
                    if success:
                        await callback.answer("✅ Заказ принят")
                        await callback.message.edit_text("✅ <b>Заказ принят в обработку</b>")
                    else:
                        await callback.answer("❌ Не удалось принять заказ")
                
                elif data.startswith("reject_order_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "cancelled", callback.from_user.id)
                    
                    if success:
                        await callback.answer("❌ Заказ отклонен")
                        await callback.message.edit_text("❌ <b>Заказ отклонен</b>")
                    else:
                        await callback.answer("❌ Не удалось отклонить заказ")
                
                elif data.startswith("start_pick_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "processing", callback.from_user.id)
                    
                    if success:
                        await callback.answer("🔄 Сборка начата")
                        await callback.message.edit_text("🔄 <b>Сборка начата</b>")
                    else:
                        await callback.answer("❌ Не удалось начать сборку")
                
                elif data.startswith("finish_picking_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "ready", callback.from_user.id)
                    
                    if success:
                        await callback.answer("📦 Собрано")
                        await callback.message.edit_text("📦 <b>Заказ собран</b>")
                    else:
                        await callback.answer("❌ Не удалось завершить сборку")
                
                elif data.startswith("check_passed_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "checking", callback.from_user.id)
                    
                    if success:
                        await callback.answer("✅ Проверено")
                        await callback.message.edit_text("✅ <b>Проверка пройдена</b>")
                    else:
                        await callback.answer("❌ Не удалось подтвердить проверку")
                
                elif data.startswith("take_delivery_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "on_way", callback.from_user.id)
                    
                    if success:
                        await callback.answer("🚚 Заказ взят")
                        await callback.message.edit_text("🚚 <b>Заказ взят на доставку</b>")
                    else:
                        await callback.answer("❌ Не удалось взять заказ")
                
                elif data.startswith("delivered_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "delivered", callback.from_user.id)
                    
                    if success:
                        await callback.answer("✅ Доставлено")
                        await callback.message.edit_text("✅ <b>Заказ доставлен</b>")
                    else:
                        await callback.answer("❌ Не удалось подтвердить доставку")
                
                else:
                    await callback.answer("❌ Неизвестное действие")
                    
            except Exception as e:
                self.logger.error(f"❌ Callback error: {e}")
                await callback.answer("❌ Ошибка обработки")
    
    async def _setup_middlewares(self):
        """Настройка middleware"""
        self.dp.message.middleware(RoleMiddleware())
        self.dp.callback_query.middleware(RoleMiddleware())
    
    async def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            from database.queries import get_user_by_telegram_id
            return await get_user_by_telegram_id(user_id)
        except Exception as e:
            self.logger.error(f"❌ Error getting user info: {e}")
            return None
    
    def _get_welcome_text(self, user: Dict[str, Any]) -> str:
        """Получение приветствия"""
        role = user.get("role", "unknown")
        name = user.get("name", "Пользователь")
        
        role_texts = {
            "client": "👤 <b>Здравствуйте!</b>\n\nДобро пожаловать в MAXXPHARM 🏥\n\nВыберите действие из меню ниже:",
            "operator": "👨‍💻 <b>Панель оператора</b>\n\nВыберите действие из меню ниже:",
            "picker": "📦 <b>Панель сборщика</b>\n\nВыберите действие из меню ниже:",
            "checker": "🔍 <b>Панель проверщика</b>\n\nВыберите действие из меню ниже:",
            "courier": "🚚 <b>Панель курьера</b>\n\nВыберите действие из меню ниже:",
            "admin": "👑 <b>Панель администратора</b>\n\nВыберите действие из меню ниже:",
            "director": "👑 <b>Панель директора</b>\n\nВыберите действие из меню ниже:"
        }
        
        return role_texts.get(role, f"👋 <b>Здравствуйте, {name}!</b>")
    
    async def start(self):
        """Запуск бота"""
        try:
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            
            logger.info("🏗️ Uber Bot starting...")
            logger.info(f"🤖 Bot: @{bot_info.username}")
            logger.info("📋 Uber-architecture loaded")
            logger.info("🔄 Queue system ready")
            logger.info("📊 API Layer ready")
            
            print("🏗️ MAXXPHARM Uber Bot")
            print("🚀 Uber-architecture: Bot → API → Queue → Workers → Database")
            print(f"🤖 Bot: @{bot_info.username}")
            print("📋 Queue system ready")
            print("📊 API Layer ready")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Bot runtime error: {e}")
            raise

async def main():
    """Основная функция"""
    print("🏗️ MAXXPHARM Uber Bot starting...")
    print("🚀 Uber-architecture: Bot → API → Queue → Workers → Database")
    print("📋 Разделение интерфейса от бизнес-логики")
    print("🔄 Queue система для распределения нагрузки")
    
    try:
        # Создаем и запускаем бот
        bot = UberBot()
        
        if await bot.initialize():
            await bot.start()
        else:
            logger.error("❌ Failed to initialize bot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
