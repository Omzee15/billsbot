#!/bin/bash

# BillBot Quick Setup Script
# This script helps you set up the BillBot application quickly

set -e

echo "🧾 BillBot Quick Setup"
echo "======================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials before continuing"
    echo ""
    echo "Required variables:"
    echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather)"
    echo "  - GEMINI_API_KEY (get from Google AI Studio)"
    echo "  - TELEGRAM_WEBHOOK_URL (your deployment URL)"
    echo ""
    read -p "Press Enter after you've updated .env file..."
else
    echo "✅ .env file exists"
fi

echo ""
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker ps | grep -q "bill-ai-backend"; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service failed to start"
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

if docker ps | grep -q "bill-postgres"; then
    echo "✅ Database service is running"
else
    echo "❌ Database service failed to start"
    echo "Check logs with: docker-compose logs db"
    exit 1
fi

echo ""
echo "🎉 BillBot is now running!"
echo ""
echo "Next steps:"
echo "1. Set your Telegram webhook:"
echo "   curl -X POST \"https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=<YOUR_URL>/webhook/telegram\""
echo ""
echo "2. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "3. Send a bill image to your Telegram bot"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
