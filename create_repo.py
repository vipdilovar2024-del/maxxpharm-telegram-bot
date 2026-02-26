#!/usr/bin/env python3
"""
СОЗДАНИЕ НОВОГО РЕПОЗИТОРИЯ ДЛЯ ЧИСТОГО БОТА
"""
import subprocess
import json
import os

def create_new_repo():
    """Создание нового репозитория"""
    print("🚀 СОЗДАНИЕ НОВОГО РЕПОЗИТОРИЯ ДЛЯ ЧИСТОГО БОТА")
    print("=" * 60)
    
    # Получаем токен из файла
    try:
        with open(r"C:\Users\vipdi\CascadeProjects\telegram_admin_bot\BOT_TOKEN.txt", 'r') as f:
            github_token = f.read().strip()
        print("✅ GitHub токен получен")
    except:
        print("❌ Не удалось получить GitHub токен")
        return False
    
    # Создаем репозиторий через GitHub API
    import urllib.request
    import urllib.parse
    
    url = "https://api.github.com/user/repos"
    data = {
        "name": "clean-telegram-bot",
        "description": "Clean Telegram Bot for Maxxpharm",
        "private": False,
        "auto_init": False
    }
    
    json_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={
            'Authorization': f'token {github_token}',
            'Content-Type': 'application/json'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Репозиторий создан: {result['html_url']}")
            repo_url = result['clone_url']
            return repo_url
    except Exception as e:
        print(f"❌ Ошибка создания репозитория: {e}")
        return False

def push_to_github():
    """Отправка кода на GitHub"""
    print("\n🚀 ОТПРАВКА КОДА НА GITHUB")
    print("=" * 60)
    
    # Создаем репозиторий
    repo_url = create_new_repo()
    if not repo_url:
        print("❌ Не удалось создать репозиторий")
        return False
    
    # Добавляем remote
    try:
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], 
                      capture_output=True, check=True)
        print("✅ Remote добавлен")
    except:
        print("❌ Не удалось добавить remote")
        return False
    
    # Отправляем код
    try:
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                      capture_output=True, check=True)
        print("✅ Код отправлен на GitHub")
        return True
    except:
        print("❌ Не удалось отправить код")
        return False

if __name__ == "__main__":
    success = push_to_github()
    if success:
        print("\n🎉 ЧИСТЫЙ БОТ ЗАГРУЖЕН НА GITHUB!")
        print("🎯 Теперь можно развернуть на Render")
    else:
        print("\n❌ Ошибка при загрузке")
