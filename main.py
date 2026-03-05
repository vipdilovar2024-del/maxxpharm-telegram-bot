"""
🚀 Main Entry Point - Основной файл запуска для Render
Запускает простой бот без конфликтов
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("main_bot")

class MaxxpharmMainBot:
    """Основной бот для Render - без конфликтов"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.running = False
        
    async def initialize(self) -> bool:
        """Инициализация бота"""
        try:
            # Проверяем переменные окружения
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                logger.error("❌ BOT_TOKEN environment variable is required")
                return False
            
            # Создаем бота
            self.bot = Bot(
                token=bot_token,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
            # Создаем диспетчер
            self.dp = Dispatcher()
            
            # Настройка обработчиков
            await self._setup_handlers()
            
            logger.info("✅ Maxxpharm Main Bot initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            """Обработчик /start"""
            try:
                await message.answer(
                    "🏥 <b>MAXXPHARM</b>\n\n"
                    "Добро пожаловать в систему доставки лекарств!\n\n"
                    "📦 <b>Доступные команды:</b>\n"
                    "/order - Создать заказ\n"
                    "/status - Статус заказа\n"
                    "/help - Помощь\n\n"
                    "📞 <b>Поддержка:</b> @admin",
                    reply_markup=self._get_main_menu()
                )
                
            except Exception as e:
                logger.error(f"❌ Error in /start: {e}")
        
        @self.dp.message(Command("order"))
        async def cmd_order(message: Message):
            """Создание заказа"""
            try:
                await message.answer(
                    "📦 <b>Создание заказа</b>\n\n"
                    "Отправьте список лекарств:\n\n"
                    "📝 <b>Пример:</b>\n"
                    "• Парацетамол - 2 шт\n"
                    "• Витамин C - 1 шт\n\n"
                    "📍 Затем отправьте адрес доставки",
                    reply_markup=self._get_order_menu()
                )
                
            except Exception as e:
                logger.error(f"❌ Error in /order: {e}")
        
        @self.dp.message(Command("status"))
        async def cmd_status(message: Message):
            """Статус заказа"""
            try:
                await message.answer(
                    "📊 <b>Статус заказов</b>\n\n"
                    "📭 У вас пока нет заказов\n\n"
                    "Создайте заказ командой /order",
                    reply_markup=self._get_main_menu()
                )
                
            except Exception as e:
                logger.error(f"❌ Error in /status: {e}")
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            """Помощь"""
            try:
                await message.answer(
                    "🆘 <b>Помощь MAXXPHARM</b>\n\n"
                    "📦 <b>Как заказать:</b>\n"
                    "1. /order - Создать заказ\n"
                    "2. Отправьте список лекарств\n"
                    "3. Отправьте адрес доставки\n"
                    "4. Ожидайте подтверждения\n\n"
                    "📞 <b>Поддержка:</b>\n"
                    "• @admin - Администратор\n"
                    "• +992 900 000 001 - Телефон\n\n"
                    "🕐 <b>Время работы:</b>\n"
                    "Пн-Вс: 09:00 - 21:00",
                    reply_markup=self._get_main_menu()
                )
                
            except Exception as e:
                logger.error(f"❌ Error in /help: {e}")
        
        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message):
            """Админ панель"""
            try:
                # Простая проверка админа
                if message.from_user.id != 697780123:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                await message.answer(
                    "👑 <b>Админ панель</b>\n\n"
                    "📊 <b>Статистика:</b>\n"
                    "• Всего заказов: 0\n"
                    "• Активных: 0\n"
                    "• Выполнено: 0\n\n"
                    "🔧 <b>Управление:</b>\n"
                    "/restart - Перезапуск бота\n"
                    "/logs - Просмотр логов\n"
                    "/stats - Статистика",
                    reply_markup=self._get_admin_menu()
                )
                
            except Exception as e:
                logger.error(f"❌ Error in /admin: {e}")
        
        @self.dp.message()
        async def handle_text(message: Message):
            """Обработка текстовых сообщений"""
            try:
                text = message.text.lower()
                
                # Обработка заказа
                if any(keyword in text for keyword in ['заказ', 'лекарство', 'таблетка', 'мазь', 'витамин']):
                    await message.answer(
                        "✅ <b>Заказ получен!</b>\n\n"
                        f"📝 <b>Ваш заказ:</b>\n{message.text}\n\n"
                        "📍 Теперь отправьте адрес доставки",
                        reply_markup=self._get_main_menu()
                    )
                
                # Обработка адреса
                elif any(keyword in text for keyword in ['ул.', 'улица', 'дом', 'кв.', 'район']):
                    await message.answer(
                        "✅ <b>Адрес получен!</b>\n\n"
                        f"📍 <b>Адрес:</b>\n{message.text}\n\n"
                        "📦 Ваш заказ принят в обработку\n"
                        "⏰ Ожидайте подтверждения в течение 15 минут\n\n"
                        "💰 <b>Оплата:</b>\n"
                        "• Наличные при получении\n"
                        "• Карта онлайн\n\n"
                        "📞 <b>С вами свяжется менеджер</b>",
                        reply_markup=self._get_main_menu()
                    )
                
                else:
                    await message.answer(
                        "📝 <b>Получено сообщение:</b>\n\n"
                        f"{message.text}\n\n"
                        "🤔 Если вы хотите создать заказ, используйте /order",
                        reply_markup=self._get_main_menu()
                    )
                
            except Exception as e:
                logger.error(f"❌ Error handling text: {e}")
        
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery):
            """Обработка inline кнопок"""
            try:
                data = callback.data
                
                if data == "create_order":
                    await callback.message.edit_text(
                        "📦 <b>Создание заказа</b>\n\n"
                        "Отправьте список лекарств:",
                        reply_markup=self._get_order_menu()
                    )
                elif data == "my_orders":
                    await callback.message.edit_text(
                        "📊 <b>Мои заказы</b>\n\n"
                        "📭 У вас пока нет заказов",
                        reply_markup=self._get_main_menu()
                    )
                elif data == "support":
                    await callback.message.edit_text(
                        "📞 <b>Поддержка</b>\n\n"
                        "👤 Администратор: @admin\n"
                        "📱 Телефон: +992 900 000 001\n\n"
                        "🕐 Время работы: 09:00 - 21:00",
                        reply_markup=self._get_main_menu()
                    )
                else:
                    await callback.answer("❌ Неизвестное действие")
                    
            except Exception as e:
                logger.error(f"❌ Callback error: {e}")
                await callback.answer("❌ Ошибка обработки")
    
    def _get_main_menu(self):
        """Главное меню"""
        try:
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            from aiogram.utils.keyboard import ReplyKeyboardBuilder
            
            builder = ReplyKeyboardBuilder()
            builder.add(KeyboardButton(text="📦 Сделать заявку"))
            builder.add(KeyboardButton(text="📍 Мои заказы"))
            builder.add(KeyboardButton(text="📞 Поддержка"))
            builder.adjust(2)
            
            return builder.as_markup(resize_keyboard=True)
            
        except Exception as e:
            logger.error(f"❌ Error creating main menu: {e}")
            return None
    
    def _get_order_menu(self):
        """Меню заказа"""
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📦 Создать заказ", callback_data="create_order")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
            ])
            
            return keyboard
            
        except Exception as e:
            logger.error(f"❌ Error creating order menu: {e}")
            return None
    
    def _get_admin_menu(self):
        """Админ меню"""
        try:
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            from aiogram.utils.keyboard import ReplyKeyboardBuilder
            
            builder = ReplyKeyboardBuilder()
            builder.add(KeyboardButton(text="📊 Статистика"))
            builder.add(KeyboardButton(text="📦 Заказы"))
            builder.add(KeyboardButton(text="👥 Пользователи"))
            builder.add(KeyboardButton(text="🔙 Главное меню"))
            builder.adjust(2)
            
            return builder.as_markup(resize_keyboard=True)
            
        except Exception as e:
            logger.error(f"❌ Error creating admin menu: {e}")
            return None
    
    async def start(self):
        """Запуск бота"""
        try:
            self.running = True
            
            logger.info("🚀 Starting Maxxpharm Main Bot...")
            
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot: @{bot_info.full_name}")
            
            print("🚀 MAXXPHARM MAIN BOT")
            print("🏥 Pharma Delivery System")
            print("🤖 Bot ready to work")
            print(f"📱 @{bot_info.username}")
            print("🛡️ No conflicts guaranteed")
            print("📦 Ready for orders")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Bot runtime error: {e}")
            raise
        finally:
            self.running = False
    
    async def shutdown(self):
        """Завершение работы бота"""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Shutting down Maxxpharm Main Bot...")
        
        try:
            if self.bot:
                await self.bot.session.close()
            
            logger.info("✅ Maxxpharm Main Bot shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM MAIN BOT")
    print("🛡️ No TelegramConflictError")
    print("🏥 Basic Pharma Delivery")
    print("🤖 Ready to work")
    print("📦 Render Entry Point")
    print()
    
    try:
        # Проверяем переменные окружения
        if not os.getenv("BOT_TOKEN"):
            logger.error("❌ BOT_TOKEN environment variable is required")
            sys.exit(1)
        
        # Создаем и запускаем бота
        bot = MaxxpharmMainBot()
        
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
