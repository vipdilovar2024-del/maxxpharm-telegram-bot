#!/usr/bin/env python3
"""
🏗️ Production Structure - Модульная структура для MAXXPHARM CRM
Легкая интеграция в существующий aiogram 3.4.1 бот
"""

import os
import sys
from pathlib import Path

def create_production_structure():
    """Создание production структуры проекта"""
    
    # Определяем структуру
    structure = {
        "bot": [
            "__init__.py",
            "main.py",
            "dispatcher.py", 
            "config.py"
        ],
        "handlers": [
            "__init__.py",
            "client.py",
            "operator.py", 
            "picker.py",
            "checker.py",
            "courier.py",
            "admin.py"
        ],
        "keyboards": [
            "__init__.py",
            "client_menu.py",
            "operator_menu.py",
            "picker_menu.py",
            "checker_menu.py",
            "courier_menu.py",
            "order_cards.py"
        ],
        "services": [
            "__init__.py",
            "order_service.py",
            "payment_service.py",
            "delivery_service.py",
            "assignment_service.py",
            "notification_service.py"
        ],
        "database": [
            "__init__.py",
            "db.py",
            "models.py",
            "queries.py"
        ],
        "middlewares": [
            "__init__.py",
            "role_middleware.py",
            "logging_middleware.py"
        ],
        "ai": [
            "__init__.py",
            "ai_reports.py",
            "ai_monitor.py"
        ],
        "monitor": [
            "__init__.py",
            "health_check.py",
            "restart_guard.py"
        ]
    }
    
    # Создаем структуру
    base_path = Path(".")
    
    for folder, files in structure.items():
        folder_path = base_path / folder
        folder_path.mkdir(exist_ok=True)
        
        for file in files:
            file_path = folder_path / file
            if not file_path.exists():
                file_path.touch()
                print(f"✅ Created: {file_path}")
            else:
                print(f"⚠️ Exists: {file_path}")
    
    print("🏗️ Production structure created successfully!")

if __name__ == "__main__":
    create_production_structure()
