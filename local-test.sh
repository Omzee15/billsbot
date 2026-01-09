#!/bin/bash

# Local Development & Testing Script for BillBot

echo "🧾 BillBot Local Testing Setup"
echo "================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 ngrok is not installed. Let's install it..."
    echo ""
    echo "Choose your installation method:"
    echo "1. Homebrew: brew install ngrok/ngrok/ngrok"
    echo "2. Download from: https://ngrok.com/download"
    echo ""
    read -p "Press Enter after installing ngrok..."
fi

echo "✅ ngrok is ready"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to start (15 seconds)..."
sleep 15

# Check if services are running
if docker ps | grep -q "bill-ai-backend"; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start. Check logs: docker-compose logs backend"
    exit 1
fi

echo ""
echo "🌐 Starting ngrok tunnel..."
echo ""

# Start ngrok in background and capture URL
ngrok http 8000 > /dev/null &
NGROK_PID=$!

echo "⏳ Waiting for ngrok to start (5 seconds)..."
sleep 5

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Make sure ngrok is running."
    exit 1
fi

echo "✅ ngrok tunnel established!"
echo ""
echo "📱 Your webhook URL: $NGROK_URL/webhook/telegram"
echo ""

# Set Telegram webhook
echo "🔗 Setting Telegram webhook..."
BOT_TOKEN="8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU"
WEBHOOK_URL="$NGROK_URL/webhook/telegram"

WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$WEBHOOK_URL")

if echo "$WEBHOOK_RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook set successfully!"
else
    echo "⚠️  Webhook response: $WEBHOOK_RESPONSE"
fi

echo ""
echo "🎉 Everything is ready!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Open Telegram and search for: @biillss_bot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Try these commands:"
echo "  /start          - Start the bot"
echo "  [Send image]    - Upload a bill photo"
echo ""
echo "Useful links:"
echo "  • API Health: http://localhost:8000/health"
echo "  • ngrok Dashboard: http://localhost:4040"
echo "  • Bot Logs: docker-compose logs -f backend"
echo ""
echo "Press Ctrl+C to stop (will stop ngrok and ask about Docker)"
echo ""

# Wait for Ctrl+C
trap ctrl_c INT

function ctrl_c() {
    echo ""
    echo "🛑 Stopping ngrok..."
    kill $NGROK_PID 2>/dev/null
    
    echo ""
    read -p "Stop Docker services too? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🐳 Stopping Docker services..."
        docker-compose down
        echo "✅ All services stopped"
    else
        echo "ℹ️  Docker services still running. Stop with: docker-compose down"
    fi
    exit 0
}

# Keep script running
while true; do
    sleep 1
done
