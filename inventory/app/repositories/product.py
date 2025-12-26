"""Product repository for database operations"""
from sqlalchemy.orm import Session
from typing import List, Optional
from inventory.app.models.product import Product
from inventory.app.schemas.product import ProductCreate, ProductUpdate


def get_all_products(db: Session) -> List[Product]:
    """Get all products"""
    return db.query(Product).all()


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Get product by ID"""
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, product_data: ProductCreate) -> Product:
    """Create a new product"""
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
    """Update a product"""
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """Delete a product"""
    product = get_product_by_id(db, product_id)
    if not product:
        return False
    
    db.delete(product)
    db.commit()
    return True


def update_product_quantity(db: Session, product_id: int, quantity_change: int) -> Optional[Product]:
    """Update product quantity (for order processing)"""
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    
    product.quantity += quantity_change
    db.commit()
    db.refresh(product)
    return product

