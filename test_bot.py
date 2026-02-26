#!/usr/bin/env python3
"""
Test script for Maxxpharm Telegram Bot
"""

import asyncio
import logging
from src.config import settings
from src.database import init_db, get_session
from src.services.user_service import UserService
from src.services.category_service import CategoryService
from src.services.product_service import ProductService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test database connection"""
    try:
        await init_db()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def test_user_service():
    """Test user service"""
    async for session in get_session():
        try:
            user_service = UserService(session)
            
            # Test creating a user
            user = await user_service.create_user(
                telegram_id=123456789,
                full_name="Test User",
                username="testuser"
            )
            logger.info(f"✅ User created: {user.full_name}")
            
            # Test getting user by telegram ID
            found_user = await user_service.get_user_by_telegram_id(123456789)
            logger.info(f"✅ User found: {found_user.full_name}")
            
            return True
        except Exception as e:
            logger.error(f"❌ User service test failed: {e}")
            return False


async def test_category_service():
    """Test category service"""
    async for session in get_session():
        try:
            category_service = CategoryService(session)
            
            # Test creating a category
            category = await category_service.create_category(
                name="Test Category",
                description="Test description"
            )
            logger.info(f"✅ Category created: {category.name}")
            
            # Test getting all categories
            categories = await category_service.get_all_categories()
            logger.info(f"✅ Found {len(categories)} categories")
            
            return True
        except Exception as e:
            logger.error(f"❌ Category service test failed: {e}")
            return False


async def test_product_service():
    """Test product service"""
    async for session in get_session():
        try:
            product_service = ProductService(session)
            category_service = CategoryService(session)
            
            # Get or create a category
            category = await category_service.get_category_by_name("Test Category")
            if not category:
                category = await category_service.create_category(
                    name="Test Category",
                    description="Test description"
                )
            
            # Test creating a product
            product = await product_service.create_product(
                name="Test Product",
                price=1000.0,
                category_id=category.id,
                stock_quantity=50,
                description="Test product description"
            )
            logger.info(f"✅ Product created: {product.name}")
            
            # Test getting all products
            products = await product_service.get_all_products()
            logger.info(f"✅ Found {len(products)} products")
            
            return True
        except Exception as e:
            logger.error(f"❌ Product service test failed: {e}")
            return False


async def test_configuration():
    """Test configuration"""
    try:
        logger.info(f"✅ BOT_TOKEN: {'✅ Set' if settings.BOT_TOKEN else '❌ Not set'}")
        logger.info(f"✅ ADMIN_TELEGRAM_ID: {settings.ADMIN_TELEGRAM_ID}")
        logger.info(f"✅ DATABASE_URL: {'✅ Set' if settings.DATABASE_URL else '❌ Not set'}")
        logger.info(f"✅ DEBUG: {settings.DEBUG}")
        logger.info(f"✅ LOG_LEVEL: {settings.LOG_LEVEL}")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def run_tests():
    """Run all tests"""
    logger.info("🚀 Starting Maxxpharm Bot Tests...")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("User Service", test_user_service),
        ("Category Service", test_category_service),
        ("Product Service", test_product_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Bot is ready to start.")
    else:
        logger.warning("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total


if __name__ == "__main__":
    try:
        result = asyncio.run(run_tests())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        exit(1)
