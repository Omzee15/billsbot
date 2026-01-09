"""
Email Service for sending bill reports and images via email
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")


class EmailService:
    """
    Service for sending bills and Excel reports via email
    """
    
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
    
    def send_bills_email(
        self,
        to_email: str,
        excel_path: Optional[str] = None,
        bill_images: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bool:
        """
        Send bills and Excel report via email
        
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
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"Your Bill Report - {start_date} to {end_date}" if start_date else "Your Bill Report"
            
            # Email body
            date_range = f" from {start_date} to {end_date}" if start_date and end_date else ""
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
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach Excel file
            if excel_path and os.path.exists(excel_path):
                self._attach_file(msg, excel_path, "bills_report.xlsx")
            
            # Attach bill images
            if bill_images:
                for i, image_path in enumerate(bill_images):
                    if os.path.exists(image_path):
                        filename = f"bill_{i+1}{Path(image_path).suffix}"
                        self._attach_file(msg, image_path, filename)
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str, filename: str):
        """
        Attach a file to the email message
        
        Args:
            msg: Email message object
            file_path: Path to file to attach
            filename: Name to give the attachment
        """
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {str(e)}")
    
    def send_simple_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Send a simple text email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Simple email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending simple email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
