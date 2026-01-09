#!/bin/bash

# Simple script to get ngrok URL and set webhook

echo "Checking ngrok..."

# Wait for ngrok
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if tunnels:
        print(tunnels[0]['public_url'])
    else:
        print('ERROR')
except:
    print('ERROR')
" 2>/dev/null)

if [ "$NGROK_URL" = "ERROR" ] || [ -z "$NGROK_URL" ]; then
    echo "❌ Could not get ngrok URL"
    echo ""
    echo "Please run ngrok manually in a new terminal:"
    echo "  ngrok http 8000"
    echo ""
    echo "Then copy the HTTPS URL and run:"
    echo "  curl -X POST \"https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/setWebhook?url=YOUR_NGROK_URL/webhook/telegram\""
    exit 1
fi

echo "✅ ngrok URL: $NGROK_URL"
echo ""

# Set Telegram webhook
BOT_TOKEN="8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU"
WEBHOOK_URL="$NGROK_URL/webhook/telegram"

echo "Setting webhook to: $WEBHOOK_URL"
echo ""

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$WEBHOOK_URL")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook set successfully!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Everything is ready!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📱 Open Telegram and search for: @biillss_bot"
    echo ""
    echo "Try:"
    echo "  1. Send /start"
    echo "  2. Upload a bill image"
    echo "  3. Choose description option"
    echo ""
    echo "Monitor logs:"
    echo "  docker-compose logs -f backend"
    echo ""
    echo "ngrok dashboard:"
    echo "  http://localhost:4040"
    echo ""
else
    echo "⚠️  Webhook response: $RESPONSE"
fi
