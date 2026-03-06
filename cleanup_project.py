#!/usr/bin/env python3
"""
🗑️ Очистка проекта от лишних файлов
Оставляем только необходимые для full_bot.py
"""

import os
import shutil

# Файлы которые нужно удалить (не влияют на full_bot.py)
FILES_TO_DELETE = [
    # Дублирующие боты
    "maxxpharm_starter.py",
    "maxxpharm_complete.py", 
    "maxxpharm_system.py",
    "maxxpharm_production_bot.py",
    "simple_production_bot.py",
    "main.py",
    "enterprise_bot.py",
    "visual_crm_bot.py", 
    "uber_crm_bot.py",
    "saas_crm_bot.py",
    "production_bot.py",
    
    # Тестовые файлы
    "test.py",
    "test_bot.py",
    "test_bot_connection.py",
    "simple_test_bot.py",
    "debug_bot.py",
    "debug_start.py",
    "clean_bot.py",
    "minimal_bot.py",
    "simple.py",
    "simple_bot.py",
    "simple_start.py",
    "simple_health.py",
    
    # Вспомогательные
    "run.py",
    "run_both.py",
    "run_render_bot.py",
    "start_render.py",
    "start_with_health.py",
    "stop_bot.py",
    "stop_all.py",
    "reset_bot.py",
    "working_bot.py",
    "reliable_bot.py",
    "high_performance_bot.py",
    "self_healing_bot.py",
    "full_bot_broken.py",
    
    # Демо и примеры
    "demo_database.py",
    "demo_auto_assignment.py",
    "demo_buttons.py",
    "demo_uber_architecture.py",
    "create_production_structure.py",
    "index.py",
    "server.py",
    "app.py"
]

# Файлы которые нужно ОСТАВИТЬ
FILES_TO_KEEP = [
    "full_bot.py",           # Основной бот
    "ai_brain.py",           # AI Brain
    "ai_director.py",        # AI Director  
    "ai_scheduler.py",       # AI Scheduler
    "data_pipeline.py",      # Data Pipeline
    "database.py",           # База данных
    "render.yaml",           # Конфиг Render
    "requirements.txt",      # Зависимости
]

def cleanup_project():
    """Очистка проекта от лишних файлов"""
    
    print("🗑️ НАЧИНАЮ ОЧИСТКУ ПРОЕКТА")
    print()
    
    deleted_count = 0
    kept_count = 0
    
    # Удаляем лишние файлы
    for filename in FILES_TO_DELETE:
        filepath = os.path.join(os.getcwd(), filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️ УДАЛЕН: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Ошибка удаления {filename}: {e}")
        else:
            print(f"ℹ️ Файл не найден: {filename}")
    
    print()
    print("✅ ПРОВЕРКА ОСТАВШИХСЯ ФАЙЛОВ")
    print()
    
    # Проверяем что остались нужные файлы
    for filename in FILES_TO_KEEP:
        filepath = os.path.join(os.getcwd(), filename)
        if os.path.exists(filepath):
            print(f"✅ ОСТАВЛЕН: {filename}")
            kept_count += 1
        else:
            print(f"❌ ПРОПУЩЕН: {filename}")
    
    print()
    print("📊 СТАТИСТИКА ОЧИСТКИ:")
    print(f"🗑️ Удалено файлов: {deleted_count}")
    print(f"✅ Оставлено файлов: {kept_count}")
    print(f"📁 Всего обработано: {deleted_count + kept_count}")
    print()
    
    if deleted_count > 0:
        print("🎉 ПРОЕКТ ОЧИЩЕН!")
        print("🚀 Остались только необходимые файлы для full_bot.py")
        print("📦 Система стала проще и надежнее")
    else:
        print("ℹ️ Файлы для удаления не найдены")
    
    return deleted_count, kept_count

if __name__ == "__main__":
    cleanup_project()
