#!/usr/bin/env python3
"""
STOP ALL BOT INSTANCES - Emergency script
"""

import asyncio
import logging
from aiogram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

async def stop_all_instances():
    """Force stop all bot instances"""
    logger.info("🛑 STOPPING ALL BOT INSTANCES")
    
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Delete webhook with force
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted")
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: {bot_info.full_name} (@{bot_info.username})")
        
        # Close bot session
        await bot.session.close()
        logger.info("✅ Bot session closed")
        
        logger.info("🎯 ALL INSTANCES STOPPED - Ready for fresh start")
        
    except Exception as e:
        logger.error(f"❌ Error stopping instances: {e}")
    
    await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(stop_all_instances())
        print("✅ All bot instances stopped successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
