"""
Bills router for bill management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
import logging
import os
from pathlib import Path

from database import get_db
from models import Bill
from services.ocr_service import ocr_service
from services.export_service import export_service
from services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("/list/{user_id}")
async def list_user_bills(
    user_id: str,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get recent bills for a user (for /list command)
    """
    try:
        bills = db.query(Bill).filter(
            Bill.user_id == user_id
        ).order_by(
            Bill.created_at.desc()
        ).limit(limit).all()
        
        return [bill.to_dict() for bill in bills]
        
    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching bills")


@router.post("/parse-only")
async def parse_bill_only(
    user_id: str,
    image_path: str
):
    """
    Parse a bill image without saving to database (for preview)
    """
    try:
        # Parse the bill
        parsed_data = ocr_service.parse_bill(image_path)
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing bill: {str(e)}")
        raise HTTPException(status_code=500, detail="Error parsing bill")


@router.post("/generate-description")
async def generate_description(
    image_path: str,
    bill_data: dict
):
    """
    Generate a short, concise description for a bill using Gemini
    """
    try:
        description = ocr_service.generate_bill_description(image_path, bill_data)
        return {"description": description}
        
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating description")


@router.post("/save")
async def save_bill(
    user_id: str,
    bill_data: dict,
    image_path: str,
    db: Session = Depends(get_db)
):
    """
    Save a parsed bill to database
    """
    try:
        bill = Bill(
            user_id=user_id,
            shop_name=bill_data.get("shop_name"),
            shop_type=bill_data.get("shop_type"),
            location=bill_data.get("location"),
            total_price=bill_data.get("total_price"),
            currency=bill_data.get("currency", "USD"),
            tax_amount=bill_data.get("tax_amount"),
            menu=bill_data.get("menu"),
            description=bill_data.get("description"),
            image_path=image_path,
            status="processed",
            created_at=datetime.utcnow()
        )
        
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        return bill.to_dict()
        
    except Exception as e:
        logger.error(f"Error saving bill: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving bill")


@router.post("/process")
async def process_bill(
    user_id: str,
    image_path: str,
    db: Session = Depends(get_db)
):
    """
    Process a bill image and store parsed data
    """
    try:
        # Parse the bill
        parsed_data = ocr_service.parse_bill(image_path)
        
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
            image_path=image_path,
            status="processed",
            created_at=datetime.utcnow()
        )
        
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        return bill.to_dict()
        
    except Exception as e:
        logger.error(f"Error processing bill: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing bill")


@router.get("/user/{user_id}")
async def get_user_bills(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all bills for a specific user with optional date filtering
    """
    try:
        query = db.query(Bill).filter(Bill.user_id == user_id)
        
        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Bill.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Bill.created_at <= end_dt)
        
        bills = query.order_by(Bill.created_at.desc()).all()
        
        return [bill.to_dict() for bill in bills]
        
    except Exception as e:
        logger.error(f"Error fetching bills: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching bills")


@router.get("/export/{user_id}")
async def export_bills(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Export bills to Excel with date range filtering
    """
    try:
        # Get bills
        query = db.query(Bill).filter(Bill.user_id == user_id)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Bill.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Bill.created_at <= end_dt)
        
        bills = query.order_by(Bill.created_at.desc()).all()
        
        if not bills:
            raise HTTPException(status_code=404, detail="No bills found for this date range")
        
        # Generate Excel
        excel_path = export_service.generate_excel(
            bills=bills,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Return file
        filename = f"bills_{start_date or 'all'}_to_{end_date or 'now'}.xlsx"
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting bills: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating export")


@router.post("/email/send")
async def send_bills_email(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Send bills and Excel report via email
    """
    try:
        user_id = request.get("user_id")
        email = request.get("email")
        start_date = request.get("start_date")
        end_date = request.get("end_date")
        
        # Get bills
        query = db.query(Bill).filter(Bill.user_id == user_id)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Bill.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Bill.created_at <= end_dt)
        
        bills = query.order_by(Bill.created_at.desc()).all()
        
        if not bills:
            raise HTTPException(status_code=404, detail="No bills found for this date range")
        
        # Generate Excel
        excel_path = export_service.generate_excel(
            bills=bills,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Get bill image paths
        bill_images = [bill.image_path for bill in bills if os.path.exists(bill.image_path)]
        
        # Send email
        success = email_service.send_bills_email(
            to_email=email,
            excel_path=excel_path,
            bill_images=bill_images,
            start_date=start_date,
            end_date=end_date
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Error sending email")
        
        return {
            "status": "success",
            "message": f"Bills sent to {email}",
            "bills_count": len(bills)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending email")


@router.delete("/{bill_id}")
async def delete_bill(
    bill_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific bill
    """
    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # Delete image file
        if os.path.exists(bill.image_path):
            os.remove(bill.image_path)
        
        # Delete from database
        db.delete(bill)
        db.commit()
        
        return {"status": "success", "message": "Bill deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bill: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting bill")
