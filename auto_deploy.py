#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ЧИСТОГО БОТА НА GITHUB
"""
import subprocess
import json
import os
import requests
from requests.auth import HTTPBasicAuth

def auto_deploy_clean_bot():
    """Автоматическая загрузка чистого бота"""
    print("🚀 АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ЧИСТОГО БОТА")
    print("=" * 60)
    
    # Шаг 1: Создаем новый репозиторий
    print("📝 ШАГ 1: Создание репозитория...")
    
    # Получаем токен
    try:
        with open(r"C:\Users\vipdi\CascadeProjects\telegram_admin_bot\BOT_TOKEN.txt", 'r') as f:
            github_token = f.read().strip()
        print("✅ GitHub токен получен")
    except:
        print("❌ Не удалось получить GitHub токен")
        return False
    
    # Создаем репозиторий через API
    repo_data = {
        "name": "clean-telegram-bot-maxxpharm",
        "description": "Clean Telegram Bot for Maxxpharm - Fresh Start",
        "private": False,
        "auto_init": False
    }
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.post(
            "https://api.github.com/user/repos",
            json=repo_data,
            headers=headers
        )
        
        if response.status_code == 201:
            repo_info = response.json()
            print(f"✅ Репозиторий создан: {repo_info['html_url']}")
            clone_url = repo_info['clone_url']
        else:
            print(f"❌ Ошибка создания репозитория: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Шаг 2: Настраиваем Git и отправляем код
    print("\n📤 ШАГ 2: Отправка кода...")
    
    try:
        # Переходим в папку с чистым ботом
        os.chdir(r"C:\Users\vipdi\CascadeProjects\clean_telegram_bot")
        
        # Добавляем remote
        subprocess.run(['git', 'remote', 'remove', 'origin'], 
                      capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin', clone_url], 
                      capture_output=True, check=True)
        print("✅ Remote добавлен")
        
        # Отправляем код
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                      capture_output=True, check=True)
        print("✅ Код отправлен на GitHub")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка Git: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    print(f"\n🎉 ЧИСТЫЙ БОТ ЗАГРУЖЕН!")
    print(f"🌐 Репозиторий: {repo_info['html_url']}")
    print(f"🎯 Теперь можно развернуть на Render")
    
    return True

if __name__ == "__main__":
    success = auto_deploy_clean_bot()
    if success:
        print("\n🚀 ГОТОВО К РАЗВЕРТЫВАНИЮ НА RENDER!")
    else:
        print("\n❌ Ошибка при загрузке")
