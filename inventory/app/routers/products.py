"""Product API routes"""
from typing import List, Annotated
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from inventory.app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from inventory.app.database import get_db
from inventory.app.repositories import product as product_repo
from inventory.app.auth.oauth2 import admin_required, authenticated_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductResponse], dependencies=[Depends(authenticated_user)])
def get_all_products(
    db: Annotated[Session, Depends(get_db)]
):
    """Get all products"""
    products = product_repo.get_all_products(db)
    return products


@router.get("/{product_id}", response_model=ProductResponse, dependencies=[Depends(authenticated_user)])
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Get a product by ID"""
    product = product_repo.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_product(
    product_data: ProductCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """Create a new product"""
    product = product_repo.create_product(db, product_data)
    return product


@router.put("/{product_id}", response_model=ProductResponse, dependencies=[Depends(admin_required)])
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """Update a product"""
    product = product_repo.update_product(db, product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.delete("/{product_id}", dependencies=[Depends(admin_required)])
def delete_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Delete a product"""
    success = product_repo.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return {"message": "Product deleted successfully"}

