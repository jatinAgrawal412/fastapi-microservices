"""Order repository for database operations"""
from sqlalchemy.orm import Session
from typing import Optional
from payment.app.models.order import Order, OrderStatus


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    """Get order by ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def create_order(
    db: Session,
    product_id: int,
    price: float,
    fee: float,
    total: float,
    quantity: int,
    status: OrderStatus = OrderStatus.PENDING
) -> Order:
    """Create a new order"""
    order = Order(
        product_id=product_id,
        price=price,
        fee=fee,
        total=total,
        quantity=quantity,
        status=status
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Optional[Order]:
    """Update order status"""
    order = get_order_by_id(db, order_id)
    if not order:
        return None
    
    order.status = status
    db.commit()
    db.refresh(order)
    return order

