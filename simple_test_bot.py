#!/usr/bin/env python3
"""
Simple test bot to check if Telegram API works
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

# Create bot and dispatcher
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    logger.info(f"Received /start from user {message.from_user.id}")
    
    try:
        await message.answer(
            "🚀 <b>SOLIMPHARM Bot работает!</b>\n\n"
            "📱 Ваш ID: <code>{user_id}</code>\n"
            "👤 Имя: {name}\n\n"
            "✅ Бот успешно отвечает на команды!"
            .format(
                user_id=message.from_user.id,
                name=message.from_user.full_name
            )
        )
        logger.info(f"✅ Successfully replied to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error replying to user {message.from_user.id}: {e}")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    logger.info(f"Received /help from user {message.from_user.id}")
    
    try:
        await message.answer(
            "🆘 <b>Помощь SOLIMPHARM Bot</b>\n\n"
            "📋 Доступные команды:\n"
            "• /start - Запуск бота\n"
            "• /help - Эта справка\n\n"
            "✅ Бот работает в тестовом режиме!"
        )
        logger.info(f"✅ Successfully sent help to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error sending help to user {message.from_user.id}: {e}")

@dp.message()
async def echo_message(message: types.Message):
    """Echo all messages"""
    logger.info(f"Received message from user {message.from_user.id}: {message.text}")
    
    try:
        await message.answer(
            f"📨 Эхо: <b>{message.text}</b>\n\n"
            f"👤 От: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}"
        )
        logger.info(f"✅ Successfully echoed message from user {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error echoing message from user {message.from_user.id}: {e}")

async def main():
    """Start the bot"""
    logger.info("🚀 Starting simple test bot...")
    logger.info(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
    
    try:
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot info: {bot_info.full_name} (@{bot_info.username})")
        
        # Start polling
        await dp.start_polling(
            bot,
            handle_signals=False
        )
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
