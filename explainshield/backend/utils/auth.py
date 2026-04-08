from jose import jwt, JWTError
import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from config import settings
import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict):
    """
    Creates a JWT access token for a specific company or user.
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_company(token: str = Depends(oauth2_scheme)):
    """
    FastAPI dependency to validate JWT and return company information.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        company_id: str = payload.get("company_id")
        if company_id is None:
            raise credentials_exception
        return {"company_id": company_id, "email": payload.get("sub")}
    except JWTError:
        raise credentials_exception

if __name__ == "__main__":
    # Test Block
    token = create_access_token({"company_id": "comp_123", "sub": "admin@example.com"})
    print(f"Generated Token: {token}")
