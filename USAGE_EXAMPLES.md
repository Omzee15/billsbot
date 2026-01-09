# 📱 Usage Examples

## User Interactions via Telegram

### 1. Start the Bot

```
User: /start
Bot: 🧾 Welcome to BillBot!
     I help you manage your bills automatically...
```

### 2. Send a Bill Image

```
User: [Sends bill photo]
Bot: 📸 Received! Processing your bill...
     
     ✅ Bill Processed Successfully!
     
     🏪 Shop: Starbucks Coffee
     📍 Location: 123 Main St, New York
     💰 Total: USD 15.50
     🏷️ Type: Restaurant
     
     📝 Description: Coffee and pastry
     
     Use /export to download your bills as Excel!
```

### 3. Export Bills to Excel

```
User: /export 2026-01-01 2026-01-31
Bot: 📊 Generating your Excel report...
     [Sends Excel file]
     📊 Your bills from 2026-01-01 to 2026-01-31
```

### 4. Email Bills

```
User: /email john@example.com 2026-01-01 2026-01-31
Bot: 📧 Sending bills to john@example.com...
     ✅ Bills sent successfully to john@example.com!
```

---

## API Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": ["telegram", "ocr", "export", "email"]
}
```

### 2. Get User Bills

```bash
curl http://localhost:8000/bills/user/123456
```

Response:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "123456",
    "shop_name": "Starbucks",
    "shop_type": "Restaurant",
    "location": "123 Main St",
    "total_price": 15.50,
    "currency": "USD",
    "tax_amount": 1.25,
    "menu": [
      {"item": "Latte", "quantity": 1, "price": 5.50},
      {"item": "Croissant", "quantity": 2, "price": 5.00}
    ],
    "description": "Morning coffee",
    "image_path": "/app/bills/123456/bill_abc123.jpg",
    "status": "processed",
    "created_at": "2026-01-15T10:30:00"
  }
]
```

### 3. Export Bills with Date Filter

```bash
curl -O "http://localhost:8000/bills/export/123456?start_date=2026-01-01&end_date=2026-01-31"
```

Downloads: `bills_2026-01-01_to_2026-01-31.xlsx`

### 4. Send Email

```bash
curl -X POST http://localhost:8000/bills/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123456",
    "email": "john@example.com",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Bills sent to john@example.com",
  "bills_count": 15
}
```

### 5. Process Bill Manually

```bash
curl -X POST http://localhost:8000/bills/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123456",
    "image_path": "/app/bills/123456/bill_xyz.jpg"
  }'
```

---

## Python SDK Examples

### Using the Services Directly

```python
from services.ocr_service import ocr_service
from services.export_service import export_service
from services.email_service import email_service
from database import SessionLocal
from models import Bill

# 1. Parse a bill
parsed_data = ocr_service.parse_bill("/path/to/bill.jpg")
print(f"Shop: {parsed_data['shop_name']}")
print(f"Total: {parsed_data['total_price']}")

# 2. Save to database
db = SessionLocal()
bill = Bill(
    user_id="123456",
    shop_name=parsed_data['shop_name'],
    total_price=parsed_data['total_price'],
    # ... other fields
)
db.add(bill)
db.commit()

# 3. Export to Excel
bills = db.query(Bill).filter(Bill.user_id == "123456").all()
excel_path = export_service.generate_excel(bills, "123456")
print(f"Excel saved to: {excel_path}")

# 4. Send email
email_service.send_bills_email(
    to_email="user@example.com",
    excel_path=excel_path,
    bill_images=[bill.image_path for bill in bills],
    start_date="2026-01-01",
    end_date="2026-01-31"
)
```

---

## Database Queries

### PostgreSQL Direct Queries

```sql
-- View all bills for a user
SELECT * FROM bills 
WHERE user_id = '123456' 
ORDER BY created_at DESC;

-- Get total spending per shop type
SELECT 
    shop_type,
    COUNT(*) as bill_count,
    SUM(total_price) as total_spent,
    AVG(total_price) as avg_bill
FROM bills
GROUP BY shop_type
ORDER BY total_spent DESC;

-- Get monthly spending
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as bills,
    SUM(total_price) as total
FROM bills
WHERE user_id = '123456'
GROUP BY month
ORDER BY month DESC;

-- Find bills with specific items
SELECT * FROM bills
WHERE menu @> '[{"item": "Coffee"}]'::jsonb;

-- Get bills above certain amount
SELECT * FROM bills
WHERE total_price > 50
ORDER BY total_price DESC;
```

---

## Excel Export Format

The generated Excel file contains 3 sheets:

### Sheet 1: Bills
| Date | Shop Name | Shop Type | Location | Total Price | Currency | Tax Amount | Description | Status | Items Count |
|------|-----------|-----------|----------|-------------|----------|------------|-------------|--------|-------------|
| 2026-01-15 | Starbucks | Restaurant | Main St | 15.50 | USD | 1.25 | Coffee | processed | 2 |

### Sheet 2: Menu Items
| Date | Shop Name | Item Name | Quantity | Price |
|------|-----------|-----------|----------|-------|
| 2026-01-15 | Starbucks | Latte | 1 | 5.50 |
| 2026-01-15 | Starbucks | Croissant | 2 | 5.00 |

### Sheet 3: Summary
```
Bills Summary Report

Total Bills: 15
Total Amount: 450.75
Total Tax: 36.50

Bills by Shop Type
Restaurant: 8
Grocery: 5
Retail: 2
```

---

## Common Use Cases

### 1. Monthly Expense Report

```python
from datetime import datetime, timedelta
from database import SessionLocal
from models import Bill
from services.export_service import export_service

db = SessionLocal()

# Get last month's bills
now = datetime.now()
start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
end_of_month = start_of_month + timedelta(days=32)
end_of_month = end_of_month.replace(day=1) - timedelta(seconds=1)

bills = db.query(Bill).filter(
    Bill.user_id == "123456",
    Bill.created_at >= start_of_month,
    Bill.created_at <= end_of_month
).all()

# Generate report
excel_path = export_service.generate_excel(
    bills, "123456", start_of_month, end_of_month
)
print(f"Monthly report: {excel_path}")
```

### 2. Spending by Category

```python
from collections import defaultdict

bills = db.query(Bill).filter(Bill.user_id == "123456").all()

spending_by_type = defaultdict(float)
for bill in bills:
    if bill.total_price:
        spending_by_type[bill.shop_type or "Unknown"] += float(bill.total_price)

for shop_type, total in spending_by_type.items():
    print(f"{shop_type}: ${total:.2f}")
```

### 3. Weekly Email Digest

```python
from datetime import datetime, timedelta

# Get last week's bills
week_ago = datetime.now() - timedelta(days=7)
bills = db.query(Bill).filter(
    Bill.user_id == "123456",
    Bill.created_at >= week_ago
).all()

# Generate and email
excel_path = export_service.generate_excel(bills, "123456")
email_service.send_bills_email(
    to_email="user@example.com",
    excel_path=excel_path,
    bill_images=[b.image_path for b in bills[:5]],  # First 5 images
    start_date=week_ago.strftime("%Y-%m-%d"),
    end_date=datetime.now().strftime("%Y-%m-%d")
)
```

---

## Testing Examples

### Test with Sample Bill

Create a test bill image or use a sample:

```bash
# Download a sample bill (for testing)
curl -o test_bill.jpg https://example.com/sample-receipt.jpg

# Process it
curl -X POST http://localhost:8000/bills/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "image_path": "/app/bills/test_user/test_bill.jpg"
  }'
```

---

## Integration Examples

### WhatsApp Integration (Future)

```python
# Placeholder for future WhatsApp integration
from twilio.rest import Client

def send_whatsapp_message(to_number, message):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to=f'whatsapp:{to_number}'
    )
```

### Slack Integration (Future)

```python
from slack_sdk import WebClient

def send_slack_notification(channel, bill_data):
    client = WebClient(token=slack_token)
    client.chat_postMessage(
        channel=channel,
        text=f"New bill from {bill_data['shop_name']}: ${bill_data['total_price']}"
    )
```

---

Need more examples? Check the code or ask in issues!
