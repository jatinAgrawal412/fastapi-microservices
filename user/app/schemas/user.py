"""User Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from user.app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = Field(default=UserRole.USER, description="User role: USER or ADMIN")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserToken(BaseModel):
    access_token: str
    token_type: str
    
class User(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

class TokenData(BaseModel):
    sub: int
    email: EmailStr
    role: UserRole