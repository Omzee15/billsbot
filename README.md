# 🧾 BillBot - AI Bill Management System

An intelligent Telegram bot that helps you manage bills by automatically parsing bill images using Google Gemini 2.5 Flash, storing data in PostgreSQL, and exporting to Excel.

## 🚀 Features

- 📱 **Telegram Bot Integration** - Send bill images directly via Telegram
- 🤖 **AI-Powered OCR** - Uses Google Gemini 2.5 Flash for accurate bill parsing
- 💾 **PostgreSQL Storage** - Relational database for structured bill data
- 📊 **Excel Export** - Generate Excel reports with custom date ranges
- 📧 **Email Reports** - Send bills and Excel exports via email
- 🐳 **Docker Deployment** - Easy deployment with Docker Compose

## 📋 Bill Data Extracted

- Shop name and type
- Location
- Total price and currency
- Tax amount
- Menu items (name, quantity, price)
- Description
- Timestamp

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **AI/OCR**: Google Gemini 2.5 Flash
- **Database**: PostgreSQL 15
- **Bot Framework**: python-telegram-bot
- **Export**: openpyxl
- **Containerization**: Docker + Docker Compose

## 📦 Quick Start

### Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Gemini API Key
- Email credentials (for email features)

### 1. Clone and Setup

```bash
cd billbot
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Environment Variables

Edit `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram
# ... other configs
```

### 3. Deploy with Docker Compose

```bash
docker-compose up -d
```

### 4. Setup Telegram Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook/telegram"
```

## 🎯 Usage

### Send a Bill

1. Send a bill image to your Telegram bot
2. Bot will parse and save it automatically
3. Receive confirmation with extracted details

### Export to Excel

```
/export 2026-01-01 2026-01-31
```

### Email Bills

```
/email your@email.com 2026-01-01 2026-01-31
```

## 🌐 API Endpoints

- `POST /webhook/telegram` - Telegram webhook receiver
- `POST /bills/upload` - Direct bill upload
- `GET /bills/user/{user_id}` - Get user's bills
- `GET /export/{user_id}` - Download Excel (with date filters)
- `POST /email/send` - Email bills and Excel

## 📁 Project Structure

```
billbot/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI application
│       ├── models.py            # Database models
│       ├── database.py          # DB connection
│       ├── services/
│       │   ├── ocr_service.py   # Gemini OCR
│       │   ├── bot_service.py   # Telegram bot
│       │   ├── export_service.py # Excel generation
│       │   └── email_service.py  # Email sender
│       └── routers/
│           ├── webhook.py       # Telegram webhook
│           └── bills.py         # Bill endpoints
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🔒 Security Notes

- Store sensitive keys in `.env` (never commit!)
- Use HTTPS for webhook URLs
- Set proper file permissions for volumes
- Use app-specific passwords for email

## 📈 Deployment Options

- **Railway** - Easiest, ~$5/month
- **Render** - Free tier available
- **DigitalOcean** - App Platform or Droplet
- **Any VPS** - Ubuntu + Docker

## 🤝 Contributing

Contributions welcome! Future features:
- WhatsApp integration
- Multi-language support
- Receipt categorization
- Budget tracking
- Mobile app

## 📄 License

MIT License - Free to use and modify

## 🐛 Troubleshooting

**Bot not responding?**
- Check webhook is set correctly
- Verify `TELEGRAM_WEBHOOK_URL` is accessible
- Check Docker logs: `docker-compose logs backend`

**OCR not working?**
- Verify `GEMINI_API_KEY` is valid
- Check image quality (min 800x600px recommended)

**Database connection failed?**
- Ensure PostgreSQL container is running
- Check `DATABASE_URL` format
