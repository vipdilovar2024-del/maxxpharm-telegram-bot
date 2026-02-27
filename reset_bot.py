#!/usr/bin/env python3
"""
Reset bot - remove webhook and start fresh
"""

import asyncio
import logging
from aiogram import Bot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

async def reset_bot():
    """Reset bot webhook and start fresh"""
    logger.info("🔄 Resetting bot...")
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: {bot_info.full_name} (@{bot_info.username})")
        
        # Remove webhook
        logger.info("🗑️ Removing webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook removed")
        
        # Get webhook info to confirm
        webhook_info = await bot.get_webhook_info()
        logger.info(f"🔗 Webhook info: {webhook_info.url}")
        
        await bot.session.close()
        
        logger.info("🎉 Bot reset complete!")
        
    except Exception as e:
        logger.error(f"❌ Error resetting bot: {e}")

if __name__ == "__main__":
    asyncio.run(reset_bot())
