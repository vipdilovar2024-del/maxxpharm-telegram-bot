#!/bin/bash

# Render build script for Maxxpharm Telegram Bot

echo "🚀 Building Maxxpharm Telegram Bot..."

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs

# Set permissions
chmod +x start.sh

echo "✅ Build completed successfully!"
