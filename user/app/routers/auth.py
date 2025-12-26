"""User API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from user.app.database import get_db
from user.app.repositories import user as user_repo
from user.app.schemas.user import UserCreate, UserLogin, UserToken, User, TokenData
from user.app.auth.jwt import create_access_token, verify_token
from user.app.auth.hashing import Hash
from user.app.auth.oauth2 import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if user_repo.is_user_exists(db, payload.email):
        raise HTTPException(status_code=400, detail="User already exists")

    user = user_repo.create_user(db, payload)
    return user

@router.post("/login", response_model=UserToken)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> UserToken:
    """Login endpoint that accepts email and password"""
    user = user_repo.get_user_by_email(db, payload.email)
    if not user or not Hash.verify(user.password, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    })

    return UserToken(access_token=token, token_type="bearer")

@router.get("/user", response_model=User)
def get_user(
    current_user_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    user = user_repo.get_user(db, current_user_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user