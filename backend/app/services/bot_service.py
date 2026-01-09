"""
Telegram Bot Service for handling user interactions
"""
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import logging
from pathlib import Path
import uuid
from datetime import datetime
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)

# Store pending bills waiting for description (in-memory, consider Redis for production)
pending_bills: Dict[str, Dict] = {}

# Store export state for users (waiting for start/end dates)
export_state: Dict[str, Dict] = {}

# Store email state for users (waiting for email and dates)
email_state: Dict[str, Dict] = {}

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BILLS_FOLDER = "/app/bills"


class TelegramBotService:
    """
    Service for managing Telegram bot interactions
    """
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.token) if self.token else None
        
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command
        """
        welcome_message = """
🧾 Welcome to BillBot!

I help you manage your bills automatically. Here's what I can do:

📷 **Send Bill Image** - Just send me a photo of any bill/receipt
📊 **Export to Excel** - Use `/export YYYY-MM-DD YYYY-MM-DD`
📧 **Email Reports** - Use `/email your@email.com YYYY-MM-DD YYYY-MM-DD`
📋 **View Bills** - Use `/list` to see your recent bills

**Example:**
`/export 2026-01-01 2026-01-31`

Just send me a bill image to get started!
        """
        await update.message.reply_text(welcome_message)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle photo messages (bill images)
        """
        try:
            user_id = str(update.effective_user.id)
            
            # Send processing message
            processing_msg = await update.message.reply_text("📸 Received! Processing your bill...")
            
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Create user folder if not exists
            user_folder = Path(BILLS_FOLDER) / user_id
            user_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            bill_id = str(uuid.uuid4())
            file_extension = ".jpg"
            file_path = user_folder / f"bill_{bill_id}{file_extension}"
            
            # Download the file
            await file.download_to_drive(str(file_path))
            
            # Parse bill data (without saving to DB yet)
            backend_url = "http://localhost:8000/bills/parse-only"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    backend_url,
                    json={
                        "user_id": user_id,
                        "image_path": str(file_path)
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Store pending bill data
                    pending_bills[user_id] = {
                        "bill_data": result,
                        "image_path": str(file_path),
                        "bill_id": bill_id
                    }
                    
                    # Delete processing message
                    await processing_msg.delete()
                    
                    # Format menu items if available
                    menu_text = ""
                    if result.get('menu') and len(result['menu']) > 0:
                        menu_text = "\n\n📋 **Items:**\n"
                        for item in result['menu'][:5]:  # Show first 5 items
                            item_name = item.get('item', 'Unknown')
                            qty = item.get('quantity', 1)
                            price = item.get('price', 0)
                            menu_text += f"  • {item_name} x{qty} - ${price}\n"
                        if len(result['menu']) > 5:
                            menu_text += f"  ... and {len(result['menu']) - 5} more items\n"
                    
                    # Format tax info
                    tax_text = ""
                    if result.get('tax_amount'):
                        tax_text = f"\n💳 Tax: {result.get('currency', '$')} {result.get('tax_amount', 0)}"
                    
                    # Format response with parsed data
                    message = f"""
✅ **Bill Parsed Successfully!**

🏪 Shop: {result.get('shop_name', 'N/A')}
📍 Location: {result.get('location', 'N/A')}
🏷️ Type: {result.get('shop_type', 'N/A')}
💰 Total: {result.get('currency', '$')} {result.get('total_price', 'N/A')}{tax_text}{menu_text}

📝 How would you like to add a description?
                    """
                    
                    # Create inline keyboard with options
                    keyboard = [
                        [
                            InlineKeyboardButton("✍️ Give Description", callback_data=f"desc_manual_{user_id}"),
                            InlineKeyboardButton("🤖 Auto Generate", callback_data=f"desc_auto_{user_id}")
                        ],
                        [InlineKeyboardButton("❌ Skip Description", callback_data=f"desc_skip_{user_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(message, reply_markup=reply_markup)
                else:
                    await update.message.reply_text("❌ Failed to process bill. Please try again.")
                    
        except Exception as e:
            logger.error(f"Error handling photo: {str(e)}")
            await update.message.reply_text("❌ Error processing your bill. Please try again later.")
    
    async def handle_description_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline keyboard callbacks for description options
        """
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = str(update.effective_user.id)
        
        if user_id not in pending_bills:
            await query.edit_message_text("❌ Session expired. Please upload the bill again.")
            return
        
        pending_bill = pending_bills[user_id]
        
        if callback_data.startswith("desc_manual_"):
            # User wants to provide manual description
            await query.edit_message_text(
                "✍️ Please type your description for this bill:\n\n"
                "(Keep it short and concise)"
            )
            # Set a flag to expect description text
            context.user_data['awaiting_description'] = True
            
        elif callback_data.startswith("desc_auto_"):
            # Auto-generate description using Gemini
            await query.edit_message_text("🤖 Generating description...")
            
            try:
                # Call backend to auto-generate description
                backend_url = "http://localhost:8000/bills/generate-description"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        backend_url,
                        json={
                            "image_path": pending_bill['image_path'],
                            "bill_data": pending_bill['bill_data']
                        }
                    )
                    
                    if response.status_code == 200:
                        description = response.json().get('description', 'Bill processed')
                        pending_bill['bill_data']['description'] = description
                        
                        # Save the bill now
                        await self._save_bill_to_db(user_id, pending_bill, query)
                    else:
                        await query.edit_message_text("❌ Failed to generate description. Using default.")
                        pending_bill['bill_data']['description'] = "Bill processed"
                        await self._save_bill_to_db(user_id, pending_bill, query)
                        
            except Exception as e:
                logger.error(f"Error auto-generating description: {str(e)}")
                await query.edit_message_text("❌ Error generating description. Saving without it.")
                pending_bill['bill_data']['description'] = None
                await self._save_bill_to_db(user_id, pending_bill, query)
                
        elif callback_data.startswith("desc_skip_"):
            # Skip description
            pending_bill['bill_data']['description'] = None
            await self._save_bill_to_db(user_id, pending_bill, query)
    
    async def _save_bill_to_db(self, user_id: str, pending_bill: Dict, query):
        """
        Save bill to database
        """
        try:
            backend_url = "http://localhost:8000/bills/save"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    backend_url,
                    json={
                        "user_id": user_id,
                        "bill_data": pending_bill['bill_data'],
                        "image_path": pending_bill['image_path']
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    message = f"""
✅ **Bill Saved Successfully!**

🏪 Shop: {result.get('shop_name', 'N/A')}
📍 Location: {result.get('location', 'N/A')}
💰 Total: {result.get('currency', '')} {result.get('total_price', 'N/A')}
📝 Description: {result.get('description', 'None')}

Use `/export 2026-01-01 2026-12-31` to download your bills!
                    """
                    await query.edit_message_text(message)
                    
                    # Clean up pending bill
                    del pending_bills[user_id]
                else:
                    await query.edit_message_text("❌ Failed to save bill. Please try again.")
                    
        except Exception as e:
            logger.error(f"Error saving bill: {str(e)}")
            await query.edit_message_text("❌ Error saving bill. Please try again later.")
    
    async def handle_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /export command - Show export options
        """
        try:
            user_id = str(update.effective_user.id)
            
            # Show export options
            keyboard = [
                [InlineKeyboardButton("📊 Export All Bills", callback_data=f"export_all_{user_id}")],
                [InlineKeyboardButton("📅 Export Date Range", callback_data=f"export_range_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📊 **Export Bills to Excel**\n\n"
                "Choose an option:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error handling export: {str(e)}")
            await update.message.reply_text("❌ Error preparing export. Please try again.")
    
    async def handle_export_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle export option callbacks
        """
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = str(update.effective_user.id)
        
        if callback_data.startswith("export_all_"):
            # Export all bills
            await query.edit_message_text("📊 Generating Excel with all your bills...")
            await self._generate_export(user_id, None, None, query)
            
        elif callback_data.startswith("export_range_"):
            # Ask for start date
            export_state[user_id] = {"step": "awaiting_start"}
            await query.edit_message_text(
                "📅 **Date Range Export**\n\n"
                "Please enter the **start date**.\n\n"
                "You can use:\n"
                "• Natural language: `12 jan`, `1 January 2026`\n"
                "• Format: `YYYY-MM-DD` or `DD-MM-YYYY`\n"
                "• Type `NA` to include all bills from the beginning\n\n"
                "Example: `1 jan 2026`"
            )
    
    async def _generate_export(self, user_id: str, start_date: Optional[str], end_date: Optional[str], query_or_update):
        """
        Generate and send Excel export
        """
        try:
            # Determine if this is a query (callback) or message update
            is_query = hasattr(query_or_update, 'message')
            
            # Call backend API
            backend_url = f"http://localhost:8000/bills/export/{user_id}"
            params = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(backend_url, params=params)
                
                if response.status_code == 200:
                    # Save Excel file temporarily
                    temp_file = f"/tmp/bills_{user_id}.xlsx"
                    with open(temp_file, "wb") as f:
                        f.write(response.content)
                    
                    # Format filename and caption
                    if start_date and end_date:
                        filename = f"bills_{start_date}_to_{end_date}.xlsx"
                        caption = f"Your bills from {start_date} to {end_date}"
                    elif start_date:
                        filename = f"bills_from_{start_date}.xlsx"
                        caption = f"Your bills from {start_date} onwards"
                    elif end_date:
                        filename = f"bills_until_{end_date}.xlsx"
                        caption = f"Your bills until {end_date}"
                    else:
                        filename = "bills_all.xlsx"
                        caption = "All your bills exported successfully"
                    
                    # Send file
                    if is_query:
                        await query_or_update.message.reply_document(
                            document=open(temp_file, "rb"),
                            filename=filename,
                            caption=caption
                        )
                    else:
                        await query_or_update.reply_document(
                            document=open(temp_file, "rb"),
                            filename=filename,
                            caption=caption
                        )
                    
                    # Clean up export state
                    if user_id in export_state:
                        del export_state[user_id]
                else:
                    error_msg = "\u274c No bills found for this date range."
                    if is_query:
                        await query_or_update.message.reply_text(error_msg)
                    else:
                        await query_or_update.reply_text(error_msg)
                    
        except Exception as e:
            logger.error(f"Error generating export: {str(e)}", exc_info=True)
            error_msg = "\u274c Error generating export. Please try again."
            if hasattr(query_or_update, 'message'):
                await query_or_update.message.reply_text(error_msg)
            else:
                await query_or_update.reply_text(error_msg)
    
    async def handle_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /list command - show recent bills
        """
        try:
            user_id = str(update.effective_user.id)
            
            await update.message.reply_text("📋 Fetching your recent bills...")
            
            # Call backend API to get bills
            backend_url = f"http://localhost:8000/bills/list/{user_id}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(backend_url, params={"limit": 10})
                
                if response.status_code == 200:
                    bills = response.json()
                    
                    if not bills or len(bills) == 0:
                        await update.message.reply_text("📭 No bills found. Upload a bill image to get started!")
                        return
                    
                    # Format bills list
                    message = "📋 **Your Recent Bills:**\n\n"
                    
                    for i, bill in enumerate(bills, 1):
                        shop = bill.get('shop_name', 'Unknown')
                        total = bill.get('total_price', '0')
                        currency = bill.get('currency', 'INR')
                        date = bill.get('created_at', '')[:10]  # Get just the date part
                        desc = bill.get('description', 'No description')
                        
                        message += f"{i}. **{shop}** - {currency} {total}\n"
                        message += f"   📅 {date}\n"
                        message += f"   📝 {desc}\n\n"
                    
                    message += "\nUse `/export` to download all bills as Excel!"
                    
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("❌ Failed to fetch bills.")
                    
        except Exception as e:
            logger.error(f"Error handling list: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Error fetching bills. Please try again.")
    
    async def handle_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /email command - Show email options
        """
        try:
            user_id = str(update.effective_user.id)
            
            # Show email options
            keyboard = [
                [InlineKeyboardButton("📧 Email All Bills", callback_data=f"email_all_{user_id}")],
                [InlineKeyboardButton("📅 Email Date Range", callback_data=f"email_range_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📧 **Email Bills Report**\n\n"
                "Choose an option:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error handling email: {str(e)}")
            await update.message.reply_text("❌ Error preparing email. Please try again.")
    
    async def handle_email_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle email option callbacks
        """
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = str(update.effective_user.id)
        
        if callback_data.startswith("email_all_"):
            # Ask for email address for all bills
            email_state[user_id] = {"step": "awaiting_email", "range_type": "all"}
            await query.edit_message_text(
                "📧 **Email All Bills**\n\n"
                "Please enter your email address:\n\n"
                "Example: `john@example.com`"
            )
            
        elif callback_data.startswith("email_range_"):
            # Ask for email address for date range
            email_state[user_id] = {"step": "awaiting_email", "range_type": "range"}
            await query.edit_message_text(
                "📅 **Email Date Range**\n\n"
                "Please enter your email address:\n\n"
                "Example: `john@example.com`"
            )
    
    async def _send_email_report(self, user_id: str, email: str, start_date: Optional[str], end_date: Optional[str], query_or_update):
        """
        Send email report with bills
        """
        try:
            # Determine if this is a query (callback) or message update
            is_query = hasattr(query_or_update, 'message')
            
            # Call backend API
            backend_url = "http://localhost:8000/bills/email/send"
            payload = {
                "user_id": user_id,
                "email": email
            }
            if start_date:
                payload["start_date"] = start_date
            if end_date:
                payload["end_date"] = end_date
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(backend_url, json=payload)
                
                if response.status_code == 200:
                    success_msg = f"✅ Bills sent successfully to {email}!"
                    if is_query:
                        await query_or_update.message.reply_text(success_msg)
                    else:
                        await query_or_update.reply_text(success_msg)
                    
                    # Clean up email state
                    if user_id in email_state:
                        del email_state[user_id]
                else:
                    error_msg = "❌ Failed to send email. Please try again."
                    if is_query:
                        await query_or_update.message.reply_text(error_msg)
                    else:
                        await query_or_update.reply_text(error_msg)
                    
        except Exception as e:
            logger.error(f"Error sending email report: {str(e)}", exc_info=True)
            error_msg = "❌ Error sending email. Please try again."
            if hasattr(query_or_update, 'message'):
                await query_or_update.message.reply_text(error_msg)
            else:
                await query_or_update.reply_text(error_msg)
    
    async def parse_natural_date(self, date_text: str) -> Optional[str]:
        """
        Parse natural language date using Gemini and convert to YYYY-MM-DD format
        """
        try:
            # Handle NA case
            if date_text.strip().upper() == "NA":
                return None
            
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            prompt = f"""
Convert this date to YYYY-MM-DD format. Current date is 9 January 2026.

Date input: "{date_text}"

Rules:
- If year is not specified, assume 2026
- Return ONLY the date in YYYY-MM-DD format, nothing else
- If the date is invalid or unclear, return "INVALID"

Examples:
"12 jan" -> "2026-01-12"
"1 January 2026" -> "2026-01-01"
"01-01-2026" -> "2026-01-01"
"2026-01-01" -> "2026-01-01"
"yesterday" -> "2026-01-08"

Now convert: "{date_text}"
"""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
            
            result = response.text.strip()
            
            # Validate format
            if result == "INVALID" or len(result) != 10 or result.count("-") != 2:
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return None


# Singleton instance
telegram_service = TelegramBotService()
