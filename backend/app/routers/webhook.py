"""
Webhook router for Telegram bot integration
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from telegram import Update
import logging
import os
from pathlib import Path
import uuid
from datetime import datetime

from database import get_db
from models import Bill
from services.ocr_service import ocr_service
from services.bot_service import telegram_service
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

BILLS_FOLDER = "/app/bills"


@router.post("/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive webhook updates from Telegram
    """
    try:
        # Get the update data
        data = await request.json()
        logger.info(f"Received webhook data: {data}")
        
        update = Update.de_json(data, telegram_service.bot)
        logger.info(f"Update parsed successfully. Message: {bool(update.message)}, Callback: {bool(update.callback_query)}")
        
        # Handle different update types
        if update.message:
            logger.info(f"Processing message. Has photo: {bool(update.message.photo)}, Has document: {bool(update.message.document)}, Has text: {bool(update.message.text)}")
            if update.message.photo:
                await handle_photo_message(update, db)
            elif update.message.document:
                # Handle document uploads (images sent as files)
                await handle_document_message(update, db)
            elif update.message.text:
                await handle_text_message(update, db)
        elif update.callback_query:
            logger.info("Processing callback query")
            callback_data = update.callback_query.data
            
            # Route to appropriate callback handler
            if callback_data.startswith("desc_"):
                await telegram_service.handle_description_callback(update, None)
            elif callback_data.startswith("export_"):
                await telegram_service.handle_export_callback(update, None)
            elif callback_data.startswith("email_"):
                await telegram_service.handle_email_callback(update, None)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing update")


async def handle_photo_message(update: Update, db: Session):
    """
    Handle photo messages (bill images)
    """
    try:
        user_id = str(update.message.from_user.id)
        
        # Send processing message
        await update.message.reply_text("📸 Received! Processing your bill...")
        
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await telegram_service.bot.get_file(photo.file_id)
        
        # Create user folder
        user_folder = Path(BILLS_FOLDER) / user_id
        user_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        bill_id = str(uuid.uuid4())
        file_path = user_folder / f"bill_{bill_id}.jpg"
        
        # Download the file
        await file.download_to_drive(str(file_path))
        
        # Parse the bill with OCR
        parsed_data = ocr_service.parse_bill(str(file_path))
        
        # Save to database
        bill = Bill(
            user_id=user_id,
            shop_name=parsed_data.get("shop_name"),
            shop_type=parsed_data.get("shop_type"),
            location=parsed_data.get("location"),
            total_price=parsed_data.get("total_price"),
            currency=parsed_data.get("currency", "USD"),
            tax_amount=parsed_data.get("tax_amount"),
            menu=parsed_data.get("menu"),
            description=parsed_data.get("description"),
            image_path=str(file_path),
            status="processed",
            created_at=datetime.utcnow()
        )
        
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        # Format response
        message = f"""
✅ **Bill Processed Successfully!**

🏪 Shop: {bill.shop_name or 'N/A'}
📍 Location: {bill.location or 'N/A'}
💰 Total: {bill.currency} {bill.total_price or 'N/A'}
🏷️ Type: {bill.shop_type or 'N/A'}

📝 Description: {bill.description or 'N/A'}

Use /export to download your bills as Excel!
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error handling photo: {str(e)}")
        await update.message.reply_text("❌ Error processing your bill. Please try again.")


async def handle_document_message(update: Update, db: Session):
    """
    Handle document messages (images sent as files via drag-drop)
    """
    try:
        document = update.message.document
        
        # Check if it's an image file
        if document.mime_type and document.mime_type.startswith('image/'):
            user_id = str(update.message.from_user.id)
            
            # Send processing message
            await update.message.reply_text("📸 Received! Processing your bill...")
            
            # Get the document file
            file = await telegram_service.bot.get_file(document.file_id)
            
            # Create user folder
            user_folder = Path(BILLS_FOLDER) / user_id
            user_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            bill_id = str(uuid.uuid4())
            # Get extension from mime type or filename
            ext = document.file_name.split('.')[-1] if '.' in document.file_name else 'jpg'
            file_path = user_folder / f"bill_{bill_id}.{ext}"
            
            # Download the file
            await file.download_to_drive(str(file_path))
            
            # Parse the bill with OCR using backend API
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
                    
                    # Use the bot service to show parsed data with inline keyboard
                    from services.bot_service import pending_bills
                    
                    # Store pending bill data
                    pending_bills[user_id] = {
                        "bill_data": result,
                        "image_path": str(file_path),
                        "bill_id": bill_id
                    }
                    
                    # Format menu items
                    menu_text = ""
                    if result.get('menu') and len(result['menu']) > 0:
                        menu_text = "\n\n📋 **Items:**\n"
                        for item in result['menu'][:5]:
                            item_name = item.get('item', 'Unknown')
                            qty = item.get('quantity', 1)
                            price = item.get('price', 0)
                            menu_text += f"  • {item_name} x{qty} - {result.get('currency', '₹')}{price}\n"
                        if len(result['menu']) > 5:
                            menu_text += f"  ... and {len(result['menu']) - 5} more items\n"
                    
                    # Format tax info
                    tax_text = ""
                    if result.get('tax_amount'):
                        tax_text = f"\n💳 Tax: {result.get('currency', '₹')} {result.get('tax_amount', 0)}"
                    
                    message = f"""
✅ **Bill Parsed Successfully!**

🏪 Shop: {result.get('shop_name', 'N/A')}
📍 Location: {result.get('location', 'N/A')}
🏷️ Type: {result.get('shop_type', 'N/A')}
💰 Total: {result.get('currency', '₹')} {result.get('total_price', 'N/A')}{tax_text}{menu_text}

📝 How would you like to add a description?
                    """
                    
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
        else:
            await update.message.reply_text("Please send an image file (JPG, PNG, etc.)")
            
    except Exception as e:
        logger.error(f"Error handling document: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error processing your file. Please try again.")


async def handle_text_message(update: Update, db: Session):
    """
    Handle text messages and commands
    """
    try:
        text = update.message.text
        user_id = str(update.message.from_user.id)
        
        if text.startswith("/start"):
            await telegram_service.handle_start(update, None)
        elif text.startswith("/help"):
            await telegram_service.handle_start(update, None)
        elif text.startswith("/export"):
            await telegram_service.handle_export(update, None)
        elif text.startswith("/list"):
            await telegram_service.handle_list(update, None)
        elif text.startswith("/email"):
            await telegram_service.handle_email(update, None)
        else:
            # Check if user is in export/email flow or providing description
            from services.bot_service import pending_bills, export_state, email_state
            
            # Check if user is in email input flow
            if user_id in email_state:
                state = email_state[user_id]
                
                if state["step"] == "awaiting_email":
                    # Validate email format
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, text):
                        await update.message.reply_text(
                            "❌ Invalid email format. Please enter a valid email address.\n\n"
                            "Example: `john@example.com`"
                        )
                        return
                    
                    email = text.strip()
                    
                    if state["range_type"] == "all":
                        # Send all bills immediately
                        await update.message.reply_text(f"📧 Sending all bills to {email}...")
                        await telegram_service._send_email_report(user_id, email, None, None, update.message)
                    else:
                        # Ask for start date
                        email_state[user_id] = {
                            "step": "awaiting_start",
                            "email": email
                        }
                        await update.message.reply_text(
                            f"✅ Email: **{email}**\n\n"
                            "Now, please enter the **start date**.\n\n"
                            "You can use:\n"
                            "• Natural language: `12 jan`, `1 January 2026`\n"
                            "• Format: `YYYY-MM-DD` or `DD-MM-YYYY`\n"
                            "• Type `NA` to include all bills from the beginning\n\n"
                            "Example: `1 jan 2026`"
                        )
                
                elif state["step"] == "awaiting_start":
                    # Parse start date
                    await update.message.reply_text("🕒 Parsing your date...")
                    start_date = await telegram_service.parse_natural_date(text)
                    
                    if start_date is None and text.strip().upper() != "NA":
                        await update.message.reply_text(
                            "❌ Invalid date format. Please try again.\n\n"
                            "Examples: `12 jan`, `1 January 2026`, `2026-01-01`, or `NA`"
                        )
                        return
                    
                    # Store start date and ask for end date
                    email_state[user_id]["step"] = "awaiting_end"
                    email_state[user_id]["start_date"] = start_date
                    
                    start_text = start_date if start_date else "beginning"
                    await update.message.reply_text(
                        f"✅ Start date: **{start_text}**\n\n"
                        "Now, please enter the **end date**.\n\n"
                        "You can use:\n"
                        "• Natural language: `12 jan`, `31 December 2026`\n"
                        "• Format: `YYYY-MM-DD` or `DD-MM-YYYY`\n"
                        "• Type `NA` to include all bills after start date\n\n"
                        "Example: `31 dec 2026`"
                    )
                
                elif state["step"] == "awaiting_end":
                    # Parse end date
                    await update.message.reply_text("🕒 Parsing your date...")
                    end_date = await telegram_service.parse_natural_date(text)
                    
                    if end_date is None and text.strip().upper() != "NA":
                        await update.message.reply_text(
                            "❌ Invalid date format. Please try again.\n\n"
                            "Examples: `31 dec`, `31 December 2026`, `2026-12-31`, or `NA`"
                        )
                        return
                    
                    # Send email with date range
                    email = state.get("email")
                    start_date = state.get("start_date")
                    await update.message.reply_text(f"📧 Sending bills to {email}...")
                    await telegram_service._send_email_report(user_id, email, start_date, end_date, update.message)
            
            # Check if user is in export date input flow
            elif user_id in export_state:
                state = export_state[user_id]
                
                if state["step"] == "awaiting_start":
                    # Parse start date
                    await update.message.reply_text("\ud83d\udd52 Parsing your date...")
                    start_date = await telegram_service.parse_natural_date(text)
                    
                    if start_date is None and text.strip().upper() != "NA":
                        await update.message.reply_text(
                            "\u274c Invalid date format. Please try again.\\n\\n"
                            "Examples: `12 jan`, `1 January 2026`, `2026-01-01`, or `NA`"
                        )
                        return
                    
                    # Store start date and ask for end date
                    export_state[user_id] = {
                        "step": "awaiting_end",
                        "start_date": start_date
                    }
                    
                    start_text = start_date if start_date else "beginning"
                    await update.message.reply_text(
                        f"\u2705 Start date: **{start_text}**\\n\\n"
                        "Now, please enter the **end date**.\\n\\n"
                        "You can use:\\n"
                        "\u2022 Natural language: `12 jan`, `31 December 2026`\\n"
                        "\u2022 Format: `YYYY-MM-DD` or `DD-MM-YYYY`\\n"
                        "\u2022 Type `NA` to include all bills after start date\\n\\n"
                        "Example: `31 dec 2026`"
                    )
                    
                elif state["step"] == "awaiting_end":
                    # Parse end date
                    await update.message.reply_text("\ud83d\udd52 Parsing your date...")
                    end_date = await telegram_service.parse_natural_date(text)
                    
                    if end_date is None and text.strip().upper() != "NA":
                        await update.message.reply_text(
                            "\u274c Invalid date format. Please try again.\\n\\n"
                            "Examples: `31 dec`, `31 December 2026`, `2026-12-31`, or `NA`"
                        )
                        return
                    
                    # Generate export
                    start_date = state.get("start_date")
                    await telegram_service._generate_export(user_id, start_date, end_date, update.message)
                    
            elif user_id in pending_bills:
                # This is a description for a pending bill
                pending_bill = pending_bills[user_id]
                pending_bill['bill_data']['description'] = text
                
                await update.message.reply_text("💾 Saving your bill...")
                
                # Save the bill
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
                            await update.message.reply_text(message)
                            
                            # Clean up
                            del pending_bills[user_id]
                        else:
                            await update.message.reply_text("❌ Failed to save bill.")
                            
                except Exception as e:
                    logger.error(f"Error saving bill with description: {str(e)}")
                    await update.message.reply_text("❌ Error saving bill.")
            else:
                await update.message.reply_text(
                    "Please send me a bill image to process. Use /start to see available commands."
                )
            
    except Exception as e:
        logger.error(f"Error handling text: {str(e)}")
