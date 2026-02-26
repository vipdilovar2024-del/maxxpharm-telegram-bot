#!/usr/bin/env python3
"""
ПОДГОТОВКА ФАЙЛОВ ДЛЯ НОВОГО РЕПОЗИТОРИЯ
"""
import shutil
import os

def prepare_files():
    """Подготовка файлов для нового репозитория"""
    print("📁 ПОДГОТОВКА ФАЙЛОВ ДЛЯ НОВОГО РЕПОЗИТОРИЯ")
    print("=" * 60)
    
    source_dir = r"C:\Users\vipdi\CascadeProjects\clean_telegram_bot"
    target_dir = r"C:\Users\vipdi\CascadeProjects\deploy_clean_bot"
    
    # Создаем целевую папку
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)
    
    # Файлы для копирования
    files_to_copy = [
        "bot.py",
        "requirements.txt", 
        "render.yaml",
        "README.md"
    ]
    
    print("📋 Копируемые файлы:")
    for file in files_to_copy:
        print(f"   📄 {file}")
    
    # Копируем файлы
    for file in files_to_copy:
        source_path = os.path.join(source_dir, file)
        target_path = os.path.join(target_dir, file)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            print(f"✅ Скопирован: {file}")
        else:
            print(f"❌ Не найден: {file}")
    
    print(f"\n📁 Файлы подготовлены в: {target_dir}")
    print("🎯 Теперь можно:")
    print("   1. Создать новый репозиторий на GitHub")
    print("   2. Скопировать файлы из deploy_clean_bot")
    print("   3. Загрузить на GitHub")
    print("   4. Развернуть на Render")
    
    return target_dir

if __name__ == "__main__":
    prepare_files()
