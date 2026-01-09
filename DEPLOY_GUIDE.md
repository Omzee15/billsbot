# Deployment Guide - BillBot

## Option 1: Render.com (Recommended - Free Tier)

### Prerequisites
1. GitHub account
2. Render.com account (free)

### Step-by-Step Deployment

#### 1. Push Code to GitHub
```bash
cd /Users/pikachu/Desktop/J/Create/billbot

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - BillBot"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/billbot.git
git push -u origin main
```

#### 2. Deploy on Render

**A. Create PostgreSQL Database**
1. Go to https://render.com/
2. Click "New +" → "PostgreSQL"
3. Configure:
   - Name: `billbot-db`
   - Database: `billbot`
   - User: `postgres`
   - Region: Choose closest to your users (Singapore for Indian users)
   - Plan: **Free**
4. Click "Create Database"
5. **Copy the Internal Database URL** (starts with `postgres://`)

**B. Deploy Backend Service**
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - Name: `billbot-backend`
   - Region: Same as database
   - Branch: `main`
   - Root Directory: Leave blank
   - Environment: **Docker**
   - Plan: **Free**
   - Dockerfile Path: `./Dockerfile`

4. **Add Environment Variables:**
   Click "Advanced" → "Add Environment Variable"
   
   ```
   DATABASE_URL = [Paste Internal Database URL from step A]
   TELEGRAM_BOT_TOKEN = 8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU
   GEMINI_API_KEY = AIzaSyCXp9oSizSf5GjzMMuWrQBCTYzmJY9TX6M
   SMTP_SERVER = smtp.gmail.com
   SMTP_PORT = 587
   SMTP_USERNAME = [Your Gmail]
   SMTP_PASSWORD = [Your Gmail App Password]
   SMTP_FROM_EMAIL = [Your Gmail]
   ```

5. Click "Create Web Service"
6. Wait 5-10 minutes for deployment
7. Your app will be live at: `https://billbot-backend.onrender.com`

#### 3. Update Telegram Webhook

Once deployed, update the webhook URL:

```bash
# Replace YOUR_APP_URL with your Render URL
curl -X POST "https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://billbot-backend.onrender.com/webhook/telegram"}'
```

Verify webhook:
```bash
curl "https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/getWebhookInfo"
```

#### 4. Test Your Bot
Send `/start` to @biillss_bot on Telegram!

---

## Option 2: Railway.app (Alternative - Easy Setup)

### Step-by-Step

1. **Create Account**: Go to https://railway.app/
2. **New Project**: Click "New Project"
3. **Add PostgreSQL**: 
   - Click "Add Service" → "PostgreSQL"
   - Copy the `DATABASE_URL` provided

4. **Deploy from GitHub**:
   - Click "Add Service" → "GitHub Repo"
   - Connect and select your repository
   - Railway will auto-detect Docker

5. **Add Environment Variables**:
   - Click on your service
   - Go to "Variables" tab
   - Add all the environment variables listed above

6. **Generate Domain**:
   - Go to "Settings" → "Networking"
   - Click "Generate Domain"
   - Copy your Railway domain

7. **Update Telegram Webhook** (same as Render instructions)

---

## Option 3: DigitalOcean App Platform (Production-Ready)

### Quick Deploy
1. Go to https://cloud.digitalocean.com/
2. Click "Create" → "Apps"
3. Connect GitHub repository
4. Select "Dockerfile" as build method
5. Add PostgreSQL database (Dev tier = $7/month)
6. Add environment variables
7. Deploy and update webhook

**Cost**: ~$5-12/month for basic setup

---

## Option 4: Self-Hosted VPS (Most Control)

### Quick Setup on Ubuntu VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Clone your repository
git clone https://github.com/YOUR_USERNAME/billbot.git
cd billbot

# Create .env file
nano .env
# (Paste your environment variables)

# Start services
docker-compose up -d

# Check status
docker-compose logs -f

# Update webhook to http://your-vps-ip:8000/webhook/telegram
```

**Recommended VPS Providers**:
- DigitalOcean ($5-6/month)
- Linode ($5/month)
- Vultr ($5-6/month)
- Hetzner ($4/month, EU-based)

---

## Post-Deployment Checklist

✅ Database accessible and initialized
✅ Backend service running
✅ Webhook URL updated
✅ Environment variables set correctly
✅ Bot responds to `/start`
✅ Image upload and parsing works
✅ Export and email commands functional

---

## Monitoring & Maintenance

### Check Logs (Render)
- Dashboard → Your Service → Logs tab

### Restart Service (Render)
- Dashboard → Your Service → Manual Deploy → "Clear build cache & deploy"

### Database Backup
- Render automatically backs up free PostgreSQL daily
- For production, enable continuous backup (paid plan)

---

## Free Tier Limitations

**Render Free Tier:**
- Spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- 750 hours/month (enough for 1 service running 24/7)
- PostgreSQL expires after 90 days (export before expiry)

**To Avoid Spin-Down:**
- Upgrade to paid plan ($7/month for always-on)
- Or use a service like UptimeRobot to ping every 10 minutes

---

## Troubleshooting

### Bot not responding
```bash
# Check webhook status
curl "https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/getWebhookInfo"

# Delete and reset webhook
curl -X POST "https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/deleteWebhook"
curl -X POST "https://api.telegram.org/bot8500941834:AAGTfvS5k7OiaRQ2V0QOZSHfdFTrflhgTaU/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://YOUR_APP_URL/webhook/telegram"}'
```

### Database connection issues
- Check `DATABASE_URL` in environment variables
- Ensure it's the Internal URL (not External) on Render
- Format: `postgres://user:pass@host:port/database`

### Image processing errors
- Check GEMINI_API_KEY is set correctly
- Check logs for API quota limits
- Verify file upload paths are writable

---

## Need Help?

- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app/
- Telegram Bot API: https://core.telegram.org/bots/api

**Your Bot**: @biillss_bot
