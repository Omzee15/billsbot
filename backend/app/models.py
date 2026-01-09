"""
Database models for bill management
"""
from sqlalchemy import Column, String, Numeric, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base


class Bill(Base):
    """
    Bill model for storing parsed bill information
    """
    __tablename__ = "bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    shop_name = Column(String, nullable=True)
    shop_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    total_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="USD")
    tax_amount = Column(Numeric(10, 2), nullable=True)
    menu = Column(JSON, nullable=True)  # Array of {item, quantity, price}
    description = Column(Text, nullable=True)
    image_path = Column(String, nullable=False)
    status = Column(String(20), default="processed")  # processed, failed, pending
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """
        Convert model to dictionary for JSON serialization
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "shop_name": self.shop_name,
            "shop_type": self.shop_type,
            "location": self.location,
            "total_price": float(self.total_price) if self.total_price else None,
            "currency": self.currency,
            "tax_amount": float(self.tax_amount) if self.tax_amount else None,
            "menu": self.menu,
            "description": self.description,
            "image_path": self.image_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
