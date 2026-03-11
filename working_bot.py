#!/usr/bin/env python3
"""
🏥 MAXXPHARM AI-CRM - Рабочий бот
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# 🤖 Telegram imports
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# 📦 Токен
BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
ADMIN_ID = 697780123  # Число, не строка!

print("🔥 MAXXPHARM BOT STARTING!")
print(f"🔥 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔥 ADMIN_ID: {ADMIN_ID}")

if not BOT_TOKEN:
    print("❌ FATAL: BOT_TOKEN не установлен!")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🗄️ In-memory storage
users_db = {}
orders_db = {}
order_counter = 1

# 🤖 Bot Class
class MaxxpharmBot:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            """Обработчик /start"""
            user_id = message.from_user.id
            
            # Создаем пользователя если нет
            if user_id not in users_db:
                users_db[user_id] = {
                    'name': message.from_user.full_name,
                    'username': message.from_user.username or "unknown",
                    'role': "client",
                    'created_at': datetime.now()
                }
            
            user = users_db[user_id]
            
            # Определяем роль
            if user_id == ADMIN_ID:
                user['role'] = "admin"
                role_display = "👑 АДМИНИСТРАТОР"
                buttons = [
                    [KeyboardButton(text="📊 Все заявки"), KeyboardButton(text="👥 Пользователи")],
                    [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🧾 Логи")]
                ]
            else:
                role_display = "🔹 КЛИЕНТ"
                buttons = [
                    [KeyboardButton(text="📦 Сделать заявку"), KeyboardButton(text="💳 Оплата")],
                    [KeyboardButton(text="📍 Статус заявки"), KeyboardButton(text="📞 Связаться")]
                ]
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=False
            )
            
            welcome_text = f"""
🏥 <b>MAXXPHARM AI-CRM</b>

👋 Добро пожаловать, <b>{user['name']}</b>!

{role_display}

📅 Регистрация: {user['created_at'].strftime('%d.%m.%Y %H:%M')}

🚀 <b>Система готова к работе!</b>
            """
            
            await message.answer(welcome_text, reply_markup=keyboard)
            logger.info(f"User {user['name']} ({user_id}) started bot")
        
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def handle_make_order(message: Message):
            """Создание заявки"""
            global order_counter
            order_id = f"ORD-{order_counter:06d}"
            order_counter += 1
            
            # Создаем заявку
            orders_db[order_id] = {
                'order_id': order_id,
                'client_name': message.from_user.full_name,
                'client_id': message.from_user.id,
                'status': "📝 Заявка создана",
                'created_at': datetime.now(),
                'items': [],
                'total': 0.0
            }
            
            await message.answer(
                f"✅ <b>Заявка создана!</b>\n\n"
                f"📝 Номер: {order_id}\n"
                f"👤 Клиент: {message.from_user.full_name}\n\n"
                "🔄 Заявка передана оператору\n"
                "💳 Ожидайте подтверждения оплаты\n\n"
                "📝 <b>Теперь отправьте:</b>\n"
                "• Список лекарств\n"
                "• Фото рецепта\n"
                "• Или контакт для связи\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
            
            logger.info(f"Order {order_id} created by {message.from_user.full_name}")
        
        @self.dp.message(F.text == "💳 Оплата")
        async def handle_payment(message: Message):
            """Оплата заявки"""
            await message.answer(
                "💳 <b>Оплата заявки</b>\n\n"
                "💰 <b>Реквизиты:</b>\n"
                "📱 Карта: 1234 5678 9012 3456\n"
                "🏦 Банк: Евросеть, получатель: ООО МАКСФАРМ\n\n"
                "📸 <b>После оплаты отправьте:</b>\n"
                "• Фото чека\n"
                "• Или номер операции\n\n"
                "🏥 <b>MAXXPHARM - Спасибо за доверие!</b>"
            )
        
        @self.dp.message(F.text == "📍 Статус заявки")
        async def handle_order_status(message: Message):
            """Проверка статуса заявки"""
            user_orders = [order for order in orders_db.values() 
                          if order.get('client_id') == message.from_user.id]
            
            if not user_orders:
                await message.answer(
                    "📍 <b>Статус заявки</b>\n\n"
                    "📭 У вас пока нет активных заявок\n\n"
                    "📦 <b>Хотите создать заявку?</b>\n"
                    "Нажмите 'Сделать заявку' в меню"
                )
                return
            
            text = "📍 <b>Ваши заявки</b>\n\n"
            for order in user_orders[-3:]:  # Последние 3
                text += f"📝 {order['order_id']}\n"
                text += f"📊 {order['status']}\n"
                text += f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text)
        
        @self.dp.message(F.text == "📞 Связаться")
        async def handle_contact(message: Message):
            """Связь с менеджером"""
            await message.answer(
                "📞 <b>Связь с MAXXPHARM</b>\n\n"
                "👥 <b>Наши менеджеры:</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 📞 Телефон: +992 900 000 002\n"
                "• 💬 Telegram: @maxxpharm_support\n"
                "• 🌐 Сайт: www.maxxpharm.tj\n"
                "• 🕐 Время работы: 09:00 - 21:00\n\n"
                "🏥 <b>MAXXPHARM - Всегда рады помочь!</b>"
            )
        
        # 📊 Обработчики для администратора
        @self.dp.message(F.text == "📊 Все заявки")
        async def handle_all_orders(message: Message):
            """Все заявки для админа"""
            if message.from_user.id != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            if not orders_db:
                await message.answer("📭 Заявок пока нет")
                return
            
            text = "📊 <b>Все заявки</b>\n\n"
            for order in list(orders_db.values())[-10:]:  # Последние 10
                text += f"📝 {order['order_id']}\n"
                text += f"👤 {order['client_name']}\n"
                text += f"📊 {order['status']}\n"
                text += f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text)
        
        @self.dp.message(F.text == "👥 Пользователи")
        async def handle_users(message: Message):
            """Пользователи для админа"""
            if message.from_user.id != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            text = "👥 <b>Пользователи системы</b>\n\n"
            for user_id, user in list(users_db.items())[-10:]:
                text += f"👤 {user['name']} (@{user['username']})\n"
                text += f"🎯 Роль: {user['role']}\n"
                text += f"📅 {user['created_at'].strftime('%d.%m.%Y')}\n\n"
            
            await message.answer(text)
        
        @self.dp.message(F.text == "⚙️ Настройки")
        async def handle_settings(message: Message):
            """Настройки для админа"""
            if message.from_user.id != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "⚙️ <b>Настройки системы</b>\n\n"
                f"🤖 Бот: @solimfarm_bot\n"
                f"👑 Администратор: {users_db.get(ADMIN_ID, {}).get('name', 'Unknown')}\n"
                f"📊 Всего заявок: {len(orders_db)}\n"
                f"👥 Всего пользователей: {len(users_db)}\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b>"
            )
        
        @self.dp.message(F.text == "🧾 Логи")
        async def handle_logs(message: Message):
            """Логи для админа"""
            if message.from_user.id != ADMIN_ID:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "🧾 <b>Логи системы</b>\n\n"
                "📝 Последние действия:\n"
                f"• 🚀 Бот запущен\n"
                f"• 📊 Создано заявок: {len(orders_db)}\n"
                f"• 👥 Пользователей: {len(users_db)}\n"
                f"• 🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                "🏥 <b>MAXXPHARM AI-CRM</b>"
            )
        
        # Обработка текста (для заявок)
        @self.dp.message()
        async def handle_text(message: Message):
            """Обработка текстовых сообщений"""
            # Проверяем, есть ли у пользователя активная заявка
            user_orders = [order for order in orders_db.values() 
                          if order.get('client_id') == message.from_user.id 
                          and order['status'] == "📝 Заявка создана"]
            
            if user_orders:
                # Добавляем текст к последней заявке
                last_order = user_orders[-1]
                last_order['items'].append(message.text)
                last_order['status'] = "💳 Ожидает оплаты"
                
                await message.answer(
                    f"✅ <b>Информация добавлена к заявке {last_order['order_id']}</b>\n\n"
                    f"📝 Текст: {message.text}\n\n"
                    "💳 Заявка передана на проверку оплаты\n"
                    "📊 Ожидайте подтверждения от оператора\n\n"
                    "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
                )
                return
            
            # Если это не заявка, обрабатываем как обычное сообщение
            await message.answer(
                "🤔 <b>Сообщение получено</b>\n\n"
                "📋 <b>Основные команды:</b>\n"
                "/start - Главное меню\n\n"
                "🎯 <b>Используйте кнопки меню</b> для навигации\n\n"
                "📞 <b>Нужна помощь?</b>\n"
                "• 📞 Телефон: +992 900 000 001\n"
                "• 💬 Telegram: @maxxpharm_support\n\n"
                "🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>"
            )
        
        logger.info("✅ All handlers registered")
    
    async def start(self):
        """Запуск бота"""
        try:
            print("🚀 Starting MAXXPHARM Bot...")
            
            # Регистрация обработчиков
            self.register_handlers()
            
            # Запуск polling
            print("🤖 Starting polling...")
            await self.dp.start_polling(
                self.bot,
                handle_signals=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            print(f"❌ Bot error: {e}")
            raise

# 🚀 Main function
async def main():
    """Основная функция"""
    print("🚀 BOT MAIN FUNCTION STARTED!")
    
    try:
        # Создаем и запускаем бота
        bot = MaxxpharmBot()
        
        print("🔧 Starting bot...")
        await bot.start()
        
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🔥 STARTING BOT!")
    asyncio.run(main())
