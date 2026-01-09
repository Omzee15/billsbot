"""
OCR Service using Google Gemini 2.5 Flash for bill parsing
"""
from google import genai
import os
from PIL import Image
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class OCRService:
    """
    Service for parsing bill images using Google Gemini 2.5 Flash
    """
    
    def __init__(self):
        # Initialize client with API key
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        
    def parse_bill(self, image_path: str) -> Dict[str, Any]:
        """
        Parse a bill image and extract structured data
        
        Args:
            image_path: Path to the bill image file
            
        Returns:
            Dictionary containing parsed bill data
        """
        try:
            # Load the image
            image = Image.open(image_path)
            
            # Create the prompt for Gemini (optimized for Indian bills)
            prompt = """
            Analyze this bill/receipt image and extract the following information in JSON format:
            
            {
                "shop_name": "name of the shop/restaurant",
                "shop_type": "type of business (e.g., restaurant, grocery, pharmacy, retail)",
                "location": "address or location if visible",
                "total_price": numeric value only (e.g., 450.50),
                "currency": "currency code (INR for Indian bills, USD, EUR, etc.)",
                "tax_amount": numeric tax value if shown (CGST + SGST for Indian bills),
                "menu": [
                    {
                        "item": "item name",
                        "quantity": numeric quantity,
                        "price": numeric price per item
                    }
                ],
                "description": "brief summary or any additional notes about the bill"
            }
            
            Rules:
            - Extract only what's visible in the image
            - Use null for missing fields
            - Ensure all prices are numeric (no currency symbols, no ₹ or $ signs)
            - Parse menu items as accurately as possible
            - For Indian bills, currency should be "INR"
            - For description, include date, payment method, or other relevant details
            - Return ONLY valid JSON, no markdown or extra text
            """
            
            # Generate content with Gemini (using gemini-2.5-flash like the working example)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            
            # Parse the response
            result_text = response.text.strip()
            logger.info(f"Raw Gemini response: {result_text[:200]}...")
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(result_text)
            
            # Default currency to INR if not set (for Indian users)
            if not parsed_data.get('currency'):
                parsed_data['currency'] = 'INR'
            
            logger.info(f"Successfully parsed bill from {image_path}")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {result_text if 'result_text' in locals() else 'No response'}")
            return self._get_default_structure()
            
        except Exception as e:
            logger.error(f"Error parsing bill: {str(e)}", exc_info=True)
            return self._get_default_structure()
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """
        Return default structure when parsing fails
        """
        return {
            "shop_name": None,
            "shop_type": None,
            "location": None,
            "total_price": None,
            "currency": "INR",  # Default to INR for Indian users
            "tax_amount": None,
            "menu": [],
            "description": "Failed to parse bill automatically"
        }
    
    def generate_bill_description(self, image_path: str, bill_data: Dict[str, Any]) -> str:
        """
        Generate a short, concise description for a bill using Gemini
        
        Args:
            image_path: Path to the bill image
            bill_data: Already parsed bill data
            
        Returns:
            Short description string (max 50 characters)
        """
        try:
            image = Image.open(image_path)
            
            shop_name = bill_data.get('shop_name', 'Unknown')
            shop_type = bill_data.get('shop_type', 'shop')
            total = bill_data.get('total_price', 0)
            
            prompt = f"""
            Looking at this receipt from {shop_name} ({shop_type}) totaling {total}, 
            generate a very short, concise description (maximum 8 words).
            
            Examples:
            - "Coffee and breakfast at Starbucks"
            - "Weekly groceries from Walmart"
            - "Biryani and drinks at restaurant"
            - "Medicines from pharmacy"
            
            Return ONLY the description text, nothing else.
            Keep it natural and brief.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            description = response.text.strip()
            
            # Ensure it's concise (max 100 chars)
            if len(description) > 100:
                description = description[:97] + "..."
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            # Fallback to simple description
            shop = bill_data.get('shop_name', 'Unknown')
            return f"Purchase from {shop}"


# Singleton instance
ocr_service = OCRService()
