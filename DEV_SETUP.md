# 📝 Development Setup Guide

## Local Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Git

### Setup Steps

#### 1. Clone Repository

```bash
git clone <your-repo>
cd billbot
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your local credentials:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bills_db
TELEGRAM_BOT_TOKEN=your_dev_bot_token
GEMINI_API_KEY=your_gemini_key
# ... other variables
```

#### 5. Start PostgreSQL (using Docker)

```bash
docker run -d \
  --name billbot-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=bills_db \
  -p 5432:5432 \
  postgres:15
```

#### 6. Run the Application

```bash
cd backend/app
uvicorn main:app --reload --port 8000
```

#### 7. Setup ngrok for Telegram Webhook (Development)

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000
```

Copy the HTTPS URL and set webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-ngrok-url.ngrok.io/webhook/telegram"
```

---

## Project Structure Explained

```
billbot/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI application entry point
│       ├── database.py          # Database connection & session
│       ├── models.py            # SQLAlchemy models (Bill)
│       │
│       ├── services/            # Business logic layer
│       │   ├── __init__.py
│       │   ├── ocr_service.py   # Gemini OCR integration
│       │   ├── bot_service.py   # Telegram bot handlers
│       │   ├── export_service.py # Excel generation
│       │   └── email_service.py  # Email sending
│       │
│       └── routers/             # API endpoints
│           ├── __init__.py
│           ├── webhook.py       # Telegram webhook receiver
│           └── bills.py         # Bill management APIs
│
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Container image definition
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # Main documentation
├── DEPLOYMENT.md                # Deployment guide
└── DEV_SETUP.md                 # This file
```

---

## API Endpoints

### Health Check

```bash
GET /
GET /health
```

### Telegram Webhook

```bash
POST /webhook/telegram
# Receives updates from Telegram
```

### Bill Management

```bash
# Process a bill manually
POST /bills/process
{
  "user_id": "123456",
  "image_path": "/path/to/bill.jpg"
}

# Get user's bills
GET /bills/user/{user_id}?start_date=2026-01-01&end_date=2026-01-31

# Export to Excel
GET /bills/export/{user_id}?start_date=2026-01-01&end_date=2026-01-31

# Send email
POST /bills/email/send
{
  "user_id": "123456",
  "email": "user@example.com",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31"
}

# Delete bill
DELETE /bills/{bill_id}
```

---

## Database Schema

### Bills Table

```sql
CREATE TABLE bills (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    shop_name TEXT,
    shop_type TEXT,
    location TEXT,
    total_price NUMERIC(10, 2),
    currency TEXT DEFAULT 'USD',
    tax_amount NUMERIC(10, 2),
    menu JSONB,
    description TEXT,
    image_path TEXT NOT NULL,
    status TEXT DEFAULT 'processed',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bills_user_id ON bills(user_id);
CREATE INDEX idx_bills_created_at ON bills(created_at);
```

---

## Testing

### Manual Testing

1. **Test OCR Service**

```python
from services.ocr_service import ocr_service

result = ocr_service.parse_bill("/path/to/bill.jpg")
print(result)
```

2. **Test Excel Export**

```python
from services.export_service import export_service
from database import SessionLocal
from models import Bill

db = SessionLocal()
bills = db.query(Bill).filter(Bill.user_id == "test_user").all()
excel_path = export_service.generate_excel(bills, "test_user")
print(f"Excel generated: {excel_path}")
```

3. **Test Email**

```python
from services.email_service import email_service

success = email_service.send_simple_email(
    to_email="test@example.com",
    subject="Test Email",
    body="This is a test"
)
print(f"Email sent: {success}")
```

### API Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# Get bills
curl http://localhost:8000/bills/user/123456

# Export bills
curl -O http://localhost:8000/bills/export/123456?start_date=2026-01-01&end_date=2026-01-31
```

---

## Docker Development

### Build and Run

```bash
docker-compose up --build
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f db
```

### Access Database

```bash
docker exec -it bill-postgres psql -U postgres -d bills_db
```

### Stop Services

```bash
docker-compose down
```

### Clean Rebuild

```bash
docker-compose down -v  # Remove volumes
docker-compose up --build
```

---

## Debugging Tips

### Enable Debug Logging

In `main.py`, change logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Check Telegram Webhook

```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

### Test Gemini API Directly

```python
import google.generativeai as genai
from PIL import Image

genai.configure(api_key="your_key")
model = genai.GenerativeModel('gemini-2.0-flash-exp')
image = Image.open("bill.jpg")
response = model.generate_content(["What's in this image?", image])
print(response.text)
```

### Database Queries

```sql
-- View all bills
SELECT * FROM bills ORDER BY created_at DESC LIMIT 10;

-- Count bills by user
SELECT user_id, COUNT(*) FROM bills GROUP BY user_id;

-- Total spending by user
SELECT user_id, SUM(total_price) FROM bills GROUP BY user_id;
```

---

## Common Issues

### Import Errors

Make sure you're in the correct directory:

```bash
cd backend/app
python -c "import main"
```

### Database Connection Failed

Check PostgreSQL is running:

```bash
docker ps
# Should see bill-postgres container
```

### Telegram Webhook Not Working

1. Check ngrok is running
2. Verify webhook URL is set correctly
3. Check bot token is valid

### Gemini API Errors

1. Verify API key is correct
2. Check quota limits
3. Ensure image file exists and is valid

---

## Code Style

### Python Style Guide

We follow PEP 8. Use tools:

```bash
# Install
pip install black flake8 mypy

# Format code
black backend/app

# Lint
flake8 backend/app

# Type check
mypy backend/app
```

### Commit Messages

Follow conventional commits:

```
feat: add email functionality
fix: resolve OCR parsing issue
docs: update deployment guide
refactor: improve export service
```

---

## Environment Variables for Development

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bills_db

# Telegram (use a test bot for development)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF-test-bot-token
TELEGRAM_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhook/telegram

# Google Gemini
GEMINI_API_KEY=AIzaSy...your-dev-key

# Email (optional for development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-test-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-test-email@gmail.com

# App
APP_HOST=0.0.0.0
APP_PORT=8000
ENVIRONMENT=development
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Gemini API](https://ai.google.dev/docs)
- [Docker Compose](https://docs.docker.com/compose/)

---

Happy coding! 🚀
