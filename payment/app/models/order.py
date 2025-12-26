"""Order model"""
from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum
import enum
from payment.app.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class Order(Base):
    """Order database model"""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)

