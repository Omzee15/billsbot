"""
Email Service for sending bill reports and images via email using SendGrid
"""
import os
import base64
import logging
from typing import List, Optional
from pathlib import Path

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

logger = logging.getLogger(__name__)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "omzee.codes@gmail.com")


class EmailService:
    """
    Service for sending bills and Excel reports via email using SendGrid
    """
    
    def __init__(self):
        self.from_email = SENDGRID_FROM_EMAIL
        self.api_key = SENDGRID_API_KEY
        
        if not self.api_key:
            logger.error("SENDGRID_API_KEY not set in environment")
        else:
            logger.info("SendGrid email service initialized")
    
    def send_bills_email(
        self,
        to_email: str,
        excel_path: Optional[str] = None,
        bill_images: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bool:
        """
        Send bills and Excel report via email using SendGrid
        
        Args:
            to_email: Recipient email address
            excel_path: Path to Excel file (optional)
            bill_images: List of bill image paths (optional)
            start_date: Start date for report (for email body)
            end_date: End date for report (for email body)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("SendGrid API key not configured")
                return False
            
            # Email body
            date_range = f" from {start_date} to {end_date}" if start_date and end_date else ""
            subject = f"Your Bill Report - {start_date} to {end_date}" if start_date else "Your Bill Report"
            
            body = f"""
Hello!

Please find attached your bill report{date_range}.

This email contains:
- Excel report with all bills and summary
- Individual bill images

If you have any questions, please reply to this email.

Best regards,
BillBot Team
            """
            
            # Create SendGrid message
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            
            # Attach Excel file
            if excel_path and os.path.exists(excel_path):
                self._add_attachment(message, excel_path, "bills_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # Attach bill images
            if bill_images:
                for i, image_path in enumerate(bill_images):
                    if os.path.exists(image_path):
                        filename = f"bill_{i+1}{Path(image_path).suffix}"
                        mime_type = "image/jpeg" if Path(image_path).suffix.lower() in [".jpg", ".jpeg"] else "image/png"
                        self._add_attachment(message, image_path, filename, mime_type)
            
            # Send email via SendGrid
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            logger.info(f"Email sent successfully to {to_email}. Status: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _add_attachment(self, message: Mail, file_path: str, filename: str, mime_type: str):
        """
        Add attachment to SendGrid message
        
        Args:
            message: SendGrid Mail object
            file_path: Path to file to attach
            filename: Name to give the attachment
            mime_type: MIME type of the file
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            encoded_file = base64.b64encode(file_data).decode()
            
            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(filename),
                FileType(mime_type),
                Disposition('attachment')
            )
            
            message.add_attachment(attached_file)
            
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {str(e)}")
    
    def send_simple_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Send a simple text email using SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("SendGrid API key not configured")
                return False
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            logger.info(f"Simple email sent to {to_email}. Status: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending simple email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
