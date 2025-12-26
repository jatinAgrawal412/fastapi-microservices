
from jose import JWTError, jwt
from inventory.app.config import settings

def verify_token(token: str, credentials_exception) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        sub = payload.get("sub")
        role = payload.get("role")
        
        if sub is None or role is None:
            raise credentials_exception
        
        return payload
    except (JWTError, ValueError, TypeError):
        raise credentials_exception