from datetime import datetime, timedelta
from jose import JWTError, jwt
from user.app.config import settings
from user.app.schemas.user import TokenData

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception) -> TokenData:
    """Verify JWT token and return TokenData"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        # Convert sub from string to int if needed
        if "sub" in payload and isinstance(payload["sub"], str):
            payload["sub"] = int(payload["sub"])
        token_data = TokenData(**payload)
        if token_data.sub is None:
            raise credentials_exception
        return token_data
    except (JWTError, ValueError, TypeError) as e:
        raise credentials_exception