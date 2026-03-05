"""
🧭 Ready Example - Готовый пример использования кнопок MAXXPHARM CRM
aiogram 3.4.1 compatible
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Импортируем наши компоненты
from keyboards.main_menu import get_main_menu
from keyboards.order_cards_new import format_order_with_buttons, format_order_list
from keyboards.notifications import NotificationService
from handlers.callback_handlers import get_callback_router
from middlewares.role_middleware import RoleMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные
TEST_ORDERS = [
    {
        "id": 245,
        "client_name": "Ахмад",
        "client_phone": "+992900000000",
        "client_address": "г. Душанбе, ул. Айни 45",
        "comment": "Нужны лекарства: Парацетамол и Амоксиклав",
        "amount": 145.0,
        "status": "created",
        "created_at": "2024-03-05 14:30:00"
    },
    {
        "id": 246,
        "client_name": "Карим",
        "client_phone": "+992900000001",
        "client_address": "г. Душанбе, ул. Рудаки 12",
        "comment": "Витамины для детей",
        "amount": 89.0,
        "status": "processing",
        "created_at": "2024-03-05 13:15:00"
    }
]

# Тестовые пользователи
TEST_USERS = {
    697780123: {"role": "director", "name": "Мухаммадмуссо"},
    697780124: {"role": "operator", "name": "Оператор Али"},
    697780125: {"role": "picker", "name": "Сборщик Рустам"},
    697780126: {"role": "checker", "name": "Проверщик Камол"},
    697780127: {"role": "courier", "name": "Курьер Бекзод"},
    697780128: {"role": "client", "name": "Клиент Ахмад"},
}

async def get_user_role(user_id: int) -> str:
    """Получение роли пользователя (тестовая функция)"""
    user = TEST_USERS.get(user_id)
    return user["role"] if user else "unknown"

async def main():
    """Основная функция примера"""
    
    # Создаем бота (используйте ваш токен)
    bot = Bot(token="YOUR_BOT_TOKEN_HERE")
    dp = Dispatcher()
    
    # Добавляем middleware
    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())
    
    # Добавляем callback обработчики
    dp.include_router(get_callback_router())
    
    # Обработчик /start
    @dp.message(Command("start"))
    async def cmd_start(message: Message, role: str):
        """Обработчик /start"""
        
        user = TEST_USERS.get(message.from_user.id)
        user_name = user["name"] if user else "Пользователь"
        
        welcome_text = f"""
👋 <b>Здравствуйте, {user_name}!</b>

Добро пожаловать в MAXXPHARM CRM 🏥

Ваша роль: <b>{role}</b>

Выберите действие из меню ниже 👇
"""
        
        keyboard = get_main_menu(role)
        await message.answer(welcome_text, reply_markup=keyboard)
    
    # Обработчики для демонстрации кнопок
    @dp.message(Command("demo_order"))
    async def cmd_demo_order(message: Message, role: str):
        """Демонстрация карточки заказа"""
        
        # Берем первый тестовый заказ
        order = TEST_ORDERS[0]
        
        # Формируем карточку с кнопками
        text, keyboard = format_order_with_buttons(order, role)
        
        await message.answer(text, reply_markup=keyboard)
    
    @dp.message(Command("demo_list"))
    async def cmd_demo_list(message: Message, role: str):
        """Демонстрация списка заказов"""
        
        # Формируем список заказов
        text = format_order_list(TEST_ORDERS, "Демонстрационные заказы")
        
        await message.answer(text)
    
    @dp.message(Command("demo_notification"))
    async def cmd_demo_notification(message: Message, role: str):
        """Демонстрация уведомлений"""
        
        if role in ["admin", "director"]:
            notification_service = NotificationService(bot)
            
            # Тестовая статистика
            test_stats = {
                "date": "05.03.2024",
                "total_orders": 15,
                "delivered_orders": 12,
                "cancelled_orders": 1,
                "in_progress_orders": 2,
                "total_revenue": 2340.50,
                "recommendations": [
                    "Увеличить количество курьеров",
                    "Оптимизировать время сборки",
                    "Добавить новые препараты"
                ]
            }
            
            await notification_service.send_daily_report(message.from_user.id, test_stats)
            await message.answer("📊 Демонстрационное уведомление отправлено")
        else:
            await message.answer("❌ Доступ запрещен")
    
    # Обработчики для демонстрации меню
    @dp.message()
    async def handle_menu_buttons(message: Message, role: str):
        """Обработчики кнопок меню"""
        
        text = message.text
        
        if text == "📦 Сделать заявку":
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "Отправьте список препаратов, фото рецепта или голосовое сообщение:",
                reply_markup=get_main_menu(role)
            )
        
        elif text == "📍 Мои заказы":
            if role == "client":
                orders_text = format_order_list([TEST_ORDERS[0]], "Мои заказы")
                await message.answer(orders_text)
            else:
                await message.answer("❌ Эта функция доступна только для клиентов")
        
        elif text == "📥 Новые заявки":
            if role == "operator":
                orders_text = format_order_list([TEST_ORDERS[0]], "Новые заявки")
                await message.answer(orders_text)
            else:
                await message.answer("❌ Эта функция доступна только для операторов")
        
        elif text == "📦 Заказы на сборке":
            if role == "picker":
                orders_text = format_order_list([TEST_ORDERS[1]], "Заказы на сборке")
                await message.answer(orders_text)
            else:
                await message.answer("❌ Эта функция доступна только для сборщиков")
        
        elif text == "🔍 Заказы на проверке":
            if role == "checker":
                await message.answer("🔍 <b>Заказы на проверке</b>\n\nНет заказов для проверки")
            else:
                await message.answer("❌ Эта функция доступна только для проверщиков")
        
        elif text == "🚚 Заказы к доставке":
            if role == "courier":
                await message.answer("🚚 <b>Заказы к доставке</b>\n\nНет заказов для доставки")
            else:
                await message.answer("❌ Эта функция доступна только для курьеров")
        
        elif text == "📊 Аналитика":
            if role in ["admin", "director"]:
                await message.answer(
                    "📊 <b>Аналитика MAXXPHARM</b>\n\n"
                    "📈 Сегодня: 15 заказов\n"
                    "💰 Выручка: 2 340 сомони\n"
                    "✅ Доставлено: 12\n"
                    "🔄 В работе: 3"
                )
            else:
                await message.answer("❌ Эта функция доступна только для администраторов")
        
        elif text == "📞 Менеджер":
            await message.answer(
                "📞 <b>Связь с менеджером</b>\n\n"
                "📱 Телефон: +998 90 123 45 67\n"
                "💬 WhatsApp: +998 90 123 45 67\n"
                "📧 Email: manager@maxxpharm.com\n\n"
                "⏰ Время работы: 9:00 - 18:00"
            )
        
        elif text == "ℹ️ Информация":
            await message.answer(
                "ℹ️ <b>О MAXXPHARM</b>\n\n"
                "🏥 <b>Система заказов фармпрепаратов</b>\n\n"
                "📱 <b>Наши преимущества:</b>\n"
                "• Быстрая доставка по городу\n"
                "• Только качественные препараты\n"
                "• Удобная оплата\n"
                "• Отслеживание заказа\n\n"
                "🚚 <b>Доставка:</b>\n"
                "• По Душанбе: 1-2 часа\n"
                "• По району: 3-4 часа\n"
                "• Бесплатно при заказе от 100 сомони"
            )
    
    # Удаляем webhook и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🧭 MAXXPHARM CRM Demo Bot starting...")
    logger.info("📋 Available commands:")
    logger.info("  /start - запуск бота")
    logger.info("  /demo_order - демонстрация карточки заказа")
    logger.info("  /demo_list - демонстрация списка заказов")
    logger.info("  /demo_notification - демонстрация уведомлений")
    logger.info("👥 Test users:")
    logger.info("  697780123 - Директор")
    logger.info("  697780124 - Оператор")
    logger.info("  697780125 - Сборщик")
    logger.info("  697780126 - Проверщик")
    logger.info("  697780127 - Курьер")
    logger.info("  697780128 - Клиент")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot runtime error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    print("🧭 MAXXPHARM CRM Demo Bot")
    print("📋 Готовые кнопки для aiogram 3.4.1")
    print("🔄 Полный цикл заказа: Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено")
    print("\n🚀 Запуск...")
    asyncio.run(main())
