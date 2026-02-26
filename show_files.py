#!/usr/bin/env python3
"""
ПОКАЗАТЬ ВСЕ ФАЙЛЫ ЧИСТОГО БОТА
"""
import os

def show_all_files():
    """Показать все файлы для копирования"""
    print("📁 ВСЕ ФАЙЛЫ ЧИСТОГО БОТА ДЛЯ КОПИРОВАНИЯ")
    print("=" * 80)
    
    files = [
        "bot.py",
        "requirements.txt",
        "render.yaml",
        "README.md"
    ]
    
    for file in files:
        print(f"\n📄 {file}")
        print("=" * 80)
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
        
        print("\n" + "=" * 80)
    
    print("🎯 ИНСТРУКЦИЯ:")
    print("=" * 80)
    print("1. 🌐 Создайте репозиторий на GitHub: clean-telegram-bot-maxxpharm")
    print("2. 📁 Скопируйте все 4 файла выше в новый репозиторий")
    print("3. 🚀 Разверните на Render с настройкой BOT_TOKEN")
    print("4. ✅ Бот будет работать!")

if __name__ == "__main__":
    show_all_files()
