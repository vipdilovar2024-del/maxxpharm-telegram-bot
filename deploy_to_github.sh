#!/bin/bash

echo "🚀 Deploying Maxxpharm Telegram Bot to GitHub..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📝 Adding files..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "🚀 Deploy Maxxpharm Telegram Bot - Full Implementation

✅ Features:
- Complete role-based system (CLIENT, COURIER, MANAGER, ADMIN, SUPER_ADMIN)
- Full catalog and product management
- Order processing and tracking
- User management and statistics
- Warehouse management
- Telegram bot integration
- PostgreSQL database
- Render deployment ready

🔧 Tech Stack:
- Python 3.11+
- Aiogram 3.x
- SQLAlchemy 2.x
- PostgreSQL
- FastAPI for health checks
- Render deployment

📱 Ready for production deployment"

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Adding remote repository..."
    git remote add origin https://github.com/vipdilovar2024-del/maxxpharm-telegram-bot.git
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin main

echo "✅ Successfully deployed to GitHub!"
echo ""
echo "🌐 Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Login with vip.dilovar.2024@gmail.com"
echo "3. Create new Web Service"
echo "4. Connect this repository"
echo "5. Follow DEPLOY_INSTRUCTIONS.md"
