"""Order API routes"""
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Request
from sqlalchemy.orm import Session
import requests
import time
from payment.app.schemas.order import OrderCreate, OrderResponse
from payment.app.database import get_db, SessionLocal
from payment.app.repositories import order as order_repo
from payment.app.models.order import OrderStatus
from payment.app.config import settings
from payment.app.auth.oauth2 import user_required

router = APIRouter(prefix="/orders", tags=["orders"])


def order_completed(order_id: int, order_data: dict) -> None:
    """Background task to complete order after delay"""
    # Lazy import to avoid circular import issues
    from payment.app.main import app
    
    time.sleep(settings.order_completion_delay)
    
    # Update order status in database
    db = SessionLocal()
    try:
        order = order_repo.update_order_status(db, order_id, OrderStatus.COMPLETED)
        
        if order:
            # Update order_data with latest values from database
            order_data['status'] = OrderStatus.COMPLETED.value
            order_data['pk'] = str(order.id)
            order_data['product_id'] = str(order.product_id)
            order_data['quantity'] = str(order.quantity)
            
            # Send to Redis stream for inventory service using global connection
            redis_client = app.state.redis
            redis_client.xadd('order_completed', order_data, '*')
    finally:
        db.close()


@router.get("/{order_id}", response_model=OrderResponse, dependencies=[Depends(user_required)])
def get_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Get an order by ID"""
    order = order_repo.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(user_required)])
def create_order(
    request: Request,
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new order"""
    # Fetch product from inventory service
    try:
        auth_header = request.headers.get('Authorization')
        response = requests.get(
            f"{settings.inventory_service_url}/products/{order_data.id}",
            headers={
                "Authorization": auth_header
            },
            timeout=10.0
        )
        response.raise_for_status()
        product = response.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {e.response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Inventory service unavailable: {str(e)}"
        )
    
    # Calculate order details
    price = float(product['price'])
    fee = 0.2 * price
    total = 1.2 * price
    
    # Create order
    order = order_repo.create_order(
        db=db,
        product_id=order_data.id,
        price=price,
        fee=fee,
        total=total,
        quantity=order_data.quantity,
        status=OrderStatus.PENDING
    )
    
    # Prepare order data for background task and Redis
    order_dict = {
        'pk': str(order.id),
        'product_id': str(order.product_id),
        'price': str(order.price),
        'fee': str(order.fee),
        'total': str(order.total),
        'quantity': str(order.quantity),
        'status': order.status.value
    }
    
    # Schedule background task to complete order
    # Use imported app instance directly (no need to pass request)
    background_tasks.add_task(order_completed, order.id, order_dict)
    
    return order

