#!/usr/bin/env python3
"""
🏥 MAXXPHARM CRM - Professional Pharmacy Management System
"""

import sys
import os
import asyncio
import logging

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем наше приложение
from main import app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting MAXXPHARM CRM...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
