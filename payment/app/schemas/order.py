"""Order Pydantic schemas"""
from pydantic import BaseModel, Field
from payment.app.models.order import OrderStatus


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    id: int = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity to order")


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: int
    product_id: int
    price: float
    fee: float
    total: float
    quantity: int
    status: OrderStatus
    
    model_config = {"from_attributes": True}

