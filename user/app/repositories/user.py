"""User repository for database operations"""
from sqlalchemy.orm import Session
from user.app.models.user import User
from user.app.schemas import UserCreate
from user.app.auth.hashing import Hash
from typing import Optional

def is_user_exists(db: Session, email: str) -> bool:
    """Check if user exists by email"""
    user = db.query(User).filter(User.email == email).first()
    return user is not None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password  = Hash.hash(user.password)
    user = User(email=user.email, password=hashed_password, role=user.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return None
    return user