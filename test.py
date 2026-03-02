#!/usr/bin/env python3
"""
Test.py - check if bot token works
"""

import asyncio
import logging
from aiogram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

async def test_bot():
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot works: {bot_info.full_name} (@{bot_info.username})")
        logger.info(f"🆔 Bot ID: {bot_info.id}")
        
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted")
        
        await bot.session.close()
        logger.info("✅ Test completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())
