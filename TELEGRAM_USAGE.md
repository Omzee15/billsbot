# 📱 Telegram Bot Usage Guide

## Bot: @biillss_bot

---

## 🎯 Available Commands

### 1. `/start`
Start the bot and see the welcome message with all available features.

```
/start
```

### 2. Upload Bill Image
Simply send any bill/receipt image to the bot. The bot will:
1. ✅ Parse the bill automatically
2. 📝 Ask you for a description with 3 options:
   - **✍️ Give Description** - Type your own description
   - **🤖 Auto Generate** - Let AI create a description
   - **❌ Skip Description** - Save without description

### 3. Export Bills to Excel
Export all bills within a date range to an Excel file.

```
/export 2026-01-01 2026-01-31
```

The Excel file will include:
- All bills with details
- Menu items breakdown
- Summary statistics

### 4. Email Bills
Send bills and Excel report to any email address.

```
/email your@example.com 2026-01-01 2026-01-31
```

---

## 💬 Complete User Flow Example

### Scenario: Uploading a Coffee Shop Bill

**Step 1:** User sends bill image

```
[User uploads photo of Starbucks receipt]
```

**Step 2:** Bot processes and shows parsed data

```
Bot: 📸 Received! Processing your bill...

✅ Bill Parsed Successfully!

🏪 Shop: Starbucks Coffee
📍 Location: 123 Main St, New York, NY
💰 Total: USD 15.50
🏷️ Type: Restaurant

📝 How would you like to add a description?

[✍️ Give Description] [🤖 Auto Generate]
         [❌ Skip Description]
```

**Step 3a:** If user clicks "✍️ Give Description"

```
Bot: ✍️ Please type your description for this bill:
     (Keep it short and concise)

User: Morning coffee before work

Bot: 💾 Saving your bill...

✅ Bill Saved Successfully!

🏪 Shop: Starbucks Coffee
📍 Location: 123 Main St, New York, NY
💰 Total: USD 15.50
📝 Description: Morning coffee before work

Use /export 2026-01-01 2026-12-31 to download your bills!
```

**Step 3b:** If user clicks "🤖 Auto Generate"

```
Bot: 🤖 Generating description...

✅ Bill Saved Successfully!

🏪 Shop: Starbucks Coffee
📍 Location: 123 Main St, New York, NY
💰 Total: USD 15.50
📝 Description: Coffee and pastry at Starbucks

Use /export 2026-01-01 2026-12-31 to download your bills!
```

**Step 3c:** If user clicks "❌ Skip Description"

```
Bot: ✅ Bill Saved Successfully!

🏪 Shop: Starbucks Coffee
📍 Location: 123 Main St, New York, NY
💰 Total: USD 15.50
📝 Description: None

Use /export 2026-01-01 2026-12-31 to download your bills!
```

---

## 📊 Export Examples

### Export Current Month
```
/export 2026-01-01 2026-01-31
```

Bot will send an Excel file: `bills_2026-01-01_to_2026-01-31.xlsx`

### Export Year to Date
```
/export 2026-01-01 2026-12-31
```

---

## 📧 Email Examples

### Send to Your Email
```
/email john@example.com 2026-01-01 2026-01-31
```

Bot will:
1. Generate Excel report
2. Attach all bill images
3. Send email to john@example.com

```
Bot: 📧 Sending bills to john@example.com...
     ✅ Bills sent successfully to john@example.com!
```

---

## 🎨 Interactive Features

### Description Options Explained

1. **✍️ Give Description** (Manual)
   - You type your own description
   - Best for: Personal notes, specific details
   - Example: "Team lunch with clients", "Birthday gift for mom"

2. **🤖 Auto Generate** (AI-powered)
   - Gemini AI analyzes the bill and creates a description
   - Best for: Quick processing, standard purchases
   - Example: "Groceries from Walmart", "Gas station fuel"

3. **❌ Skip Description**
   - Save bill without description
   - Best for: When you're in a hurry
   - You can always add notes later

---

## ⚡ Quick Tips

### Tip 1: Best Image Quality
- Take clear, well-lit photos
- Avoid blurry or dark images
- Ensure text is readable
- Full receipt in frame

### Tip 2: Batch Processing
- You can upload multiple bills in a row
- Each bill will be processed separately
- Each gets its own description prompt

### Tip 3: Date Format
Always use `YYYY-MM-DD` format:
- ✅ `2026-01-15`
- ❌ `01/15/2026`
- ❌ `15-01-2026`

### Tip 4: Regular Exports
Export your bills monthly for better tracking:
```
# End of January
/export 2026-01-01 2026-01-31

# End of February
/export 2026-02-01 2026-02-28
```

---

## 🔍 What the Bot Can Extract

From each bill, the bot extracts:

✅ **Basic Info:**
- Shop name
- Shop type (Restaurant, Grocery, etc.)
- Location/Address

✅ **Financial Details:**
- Total amount
- Currency
- Tax amount

✅ **Items:**
- Item names
- Quantities
- Individual prices

✅ **Metadata:**
- Date & time
- Description (manual or AI-generated)

---

## 🐛 Troubleshooting

### Bot not responding?
1. Send `/start` to wake it up
2. Check your internet connection
3. Wait a few seconds and try again

### Can't see buttons?
Update your Telegram app to the latest version

### Wrong information parsed?
- Retake the photo with better lighting
- Ensure receipt is fully visible
- Upload a clearer image

### Export command not working?
- Check date format: `YYYY-MM-DD`
- Ensure you have bills in that date range
- Try a wider date range

---

## 📈 Future Features (Coming Soon)

- 🔄 Edit bill details
- 📊 Spending analytics
- 🏷️ Custom categories
- 🔔 Budget alerts
- 📱 WhatsApp integration
- 🌍 Multi-language support

---

## 💡 Use Cases

### Personal Finance
- Track daily expenses
- Monthly budget reports
- Tax preparation

### Small Business
- Record business expenses
- Vendor tracking
- Expense reports for clients

### Shared Expenses
- Split bills with roommates
- Family expense tracking
- Group trip expenses

---

**Need help? Just send /start to see all commands!** 🚀
