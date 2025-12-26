"""Product model"""
from sqlalchemy import Column, Integer, String, Float
from inventory.app.database import Base


class Product(Base):
    """Product database model"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)

