# 🚀 Quick Start Guide

Get BillBot running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Telegram account
- Google Gemini API key

## Step 1: Get Your API Keys

### Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (looks like: `AIzaSy...`)

## Step 2: Clone and Configure

```bash
# Clone the repository
cd ~/Desktop
git clone <your-repo-url> billbot
cd billbot

# Copy environment template
cp .env.example .env
```

Edit `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
TELEGRAM_WEBHOOK_URL=http://your-domain.com/webhook/telegram

# Email settings (optional, for email features)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Step 3: Deploy

### Option A: Local Development

```bash
# Run the setup script
./setup.sh

# Or manually:
docker-compose up -d
```

### Option B: Deploy to Railway

1. Push code to GitHub
2. Go to [Railway](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Add environment variables in Railway dashboard
6. Deploy!

## Step 4: Set Telegram Webhook

**For local development (using ngrok):**

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Set webhook:
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook/telegram"
```

**For production deployment:**

```bash
# Replace with your actual deployment URL
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.railway.app/webhook/telegram"
```

## Step 5: Test It!

1. Open Telegram
2. Search for your bot (the name you gave it)
3. Send `/start`
4. Send a bill image
5. Watch it get processed! 🎉

---

## Quick Commands

```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check API health
curl http://localhost:8000/health
```

---

## Troubleshooting

### Bot not responding?

```bash
# Check webhook status
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# Check logs
docker-compose logs backend
```

### Database issues?

```bash
# Restart database
docker-compose restart db

# Check database is running
docker-compose ps db
```

### Port 8000 already in use?

Edit `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

---

## Next Steps

- Read [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for all features
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [DEV_SETUP.md](DEV_SETUP.md) for development details

---

## Getting Help

- Check logs: `docker-compose logs`
- Review documentation in this repo
- Create an issue on GitHub

---

**That's it! You're ready to manage your bills with AI! 🧾✨**
