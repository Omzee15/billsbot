# 🚀 Deployment Guide - BillBot

## Prerequisites

Before deploying, ensure you have:

1. **Telegram Bot Token**
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Save the token provided

2. **Google Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Save the key

3. **Email Credentials** (for email features)
   - Gmail: Use App Password (not regular password)
   - Settings → Security → 2-Step Verification → App passwords

4. **Domain or Server**
   - Railway (recommended)
   - Render
   - Any VPS with Docker

---

## Option 1: Deploy to Railway (Easiest) ⭐

### Step 1: Prepare Your Code

```bash
cd billbot
cp .env.example .env
# Edit .env with your credentials
```

### Step 2: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin your-github-repo-url
git push -u origin main
```

### Step 3: Deploy on Railway

1. Go to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `billbot` repository
4. Railway will auto-detect Docker and deploy

### Step 4: Add Environment Variables

In Railway dashboard, add these variables:

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/bills_db
TELEGRAM_BOT_TOKEN=your_token_here
GEMINI_API_KEY=your_gemini_key_here
TELEGRAM_WEBHOOK_URL=https://your-railway-app.railway.app/webhook/telegram
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

### Step 5: Setup Telegram Webhook

Once deployed, get your Railway URL (e.g., `https://billbot.railway.app`)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-railway-app.railway.app/webhook/telegram"
```

### Step 6: Test

Send a bill image to your Telegram bot!

---

## Option 2: Deploy to Render

### Step 1: Create Render Account

Go to [Render](https://render.com) and sign up

### Step 2: Create PostgreSQL Database

1. New → PostgreSQL
2. Name: `billbot-db`
3. Copy the Internal Database URL

### Step 3: Create Web Service

1. New → Web Service
2. Connect your GitHub repo
3. Settings:
   - **Environment**: Docker
   - **Instance Type**: Free (or Starter $7/month)
   
### Step 4: Add Environment Variables

Same as Railway (see above)

### Step 5: Deploy

Render will automatically build and deploy

---

## Option 3: Deploy to VPS (Ubuntu)

### Step 1: SSH into Your Server

```bash
ssh user@your-server-ip
```

### Step 2: Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose -y
```

### Step 3: Clone Your Repository

```bash
git clone your-repo-url
cd billbot
```

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 5: Start Services

```bash
sudo docker-compose up -d
```

### Step 6: Setup Nginx (for HTTPS)

```bash
sudo apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/billbot
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/billbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Step 7: Set Telegram Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook/telegram"
```

---

## Testing Your Deployment

### 1. Check API Health

```bash
curl https://your-domain.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": ["telegram", "ocr", "export", "email"]
}
```

### 2. Test Telegram Bot

1. Find your bot on Telegram
2. Send `/start`
3. Send a bill image
4. Try `/export 2026-01-01 2026-01-31`

### 3. Check Docker Logs

```bash
docker-compose logs -f backend
```

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_WEBHOOK_URL` | Your webhook endpoint | `https://domain.com/webhook/telegram` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `SMTP_HOST` | Email server host | `smtp.gmail.com` |
| `SMTP_PORT` | Email server port | `587` |
| `SMTP_USERNAME` | Email username | `you@gmail.com` |
| `SMTP_PASSWORD` | Email password/app password | `your-app-password` |
| `SMTP_FROM_EMAIL` | Sender email | `you@gmail.com` |

---

## Troubleshooting

### Bot Not Responding

1. Check webhook is set:
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

2. Check logs:
```bash
docker-compose logs backend
```

3. Verify environment variables are set

### Database Connection Failed

```bash
docker-compose ps  # Check if db container is running
docker-compose restart db
```

### OCR Not Working

1. Verify Gemini API key is valid
2. Check API quotas at [Google AI Studio](https://makersuite.google.com)
3. Test with a clear, high-quality bill image

### Email Not Sending

1. For Gmail: Use App Password, not regular password
2. Enable "Less secure app access" if needed
3. Check SMTP credentials

---

## Maintenance

### View Logs

```bash
docker-compose logs -f
```

### Restart Services

```bash
docker-compose restart
```

### Update Application

```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Backup Database

```bash
docker exec bill-postgres pg_dump -U postgres bills_db > backup.sql
```

### Restore Database

```bash
docker exec -i bill-postgres psql -U postgres bills_db < backup.sql
```

---

## Cost Estimates

### Railway
- Free: 500 hours/month + $5 credit
- Hobby: $5/month + usage
- **Estimated**: ~$10-15/month

### Render
- Free tier available (limited)
- Starter: $7/month
- **Estimated**: $7-15/month

### VPS (DigitalOcean, Linode)
- Basic Droplet: $6-12/month
- **Estimated**: $6-12/month

### API Costs
- Gemini API: Free tier (60 requests/minute)
- Paid: ~$0.001-0.002/image
- **Estimated**: $0-5/month (depending on usage)

---

## Next Steps

- Add user authentication
- Implement budget tracking
- Add receipt categorization
- Create mobile app
- Support WhatsApp integration
- Multi-language support

---

Need help? Check the logs or create an issue on GitHub!
