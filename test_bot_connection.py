#!/usr/bin/env python3
"""
Test script to check bot connection and configuration
"""

import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
ADMIN_ID = "697780123"

async def test_bot_token():
    """Test if bot token is valid"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                if data.get("ok"):
                    bot_info = data["result"]
                    logger.info(f"✅ Bot token is valid!")
                    logger.info(f"   Name: {bot_info.get('first_name')}")
                    logger.info(f"   Username: @{bot_info.get('username')}")
                    logger.info(f"   ID: {bot_info.get('id')}")
                    return True
                else:
                    logger.error(f"❌ Bot token is invalid: {data.get('description')}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Error testing bot token: {e}")
        return False

async def test_render_health():
    """Test Render health endpoint"""
    url = "https://maxxpharm-telegram-bot.onrender.com/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Render health check passed!")
                    logger.info(f"   Status: {data.get('status')}")
                    logger.info(f"   Database: {data.get('database')}")
                    logger.info(f"   Bot token: {data.get('bot_token')}")
                    logger.info(f"   Admin ID: {data.get('admin_id')}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: HTTP {response.status}")
                    return False
                    
    except asyncio.TimeoutError:
        logger.error("❌ Health check timeout - bot may be starting")
        return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🔍 Starting bot connection tests...")
    logger.info("=" * 50)
    
    # Test 1: Bot token
    logger.info("📱 Testing bot token...")
    token_ok = await test_bot_token()
    logger.info("")
    
    # Test 2: Render health
    logger.info("🌐 Testing Render health...")
    health_ok = await test_render_health()
    logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Results Summary:")
    logger.info(f"   Bot Token: {'✅ OK' if token_ok else '❌ FAILED'}")
    logger.info(f"   Render Health: {'✅ OK' if health_ok else '❌ FAILED'}")
    
    if token_ok and health_ok:
        logger.info("🎉 All tests passed! Bot should be working.")
        logger.info("💡 If bot still doesn't respond to /start:")
        logger.info("   1. Check if bot is running locally (conflict)")
        logger.info("   2. Try sending /start again")
        logger.info("   3. Check Telegram for any bot restrictions")
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        
    return token_ok and health_ok

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        exit(1)
