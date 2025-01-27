# app/dependencies.py
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.logging_config import setup_logger

# Configuration depuis l'environnement
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 20))

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# Configure logger
logger = setup_logger("DependencyLogger")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Decode JWT
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        permissions: list = payload.get('permissions', [])
        if not username or not user_id:
            logger.warning(f"Invalid JWT token: missing username or user_id")
            print('not user')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials 1'
            )
        logger.info(f"Token decoded successfully for user: {username} (ID: {user_id})")
        return {
            "id": user_id,
            "username": username,
            "user_role": user_role,
            "permissions": permissions
        }
    except JWTError as e:
        logger.error(f"JWT decoding failed: {e}")
        print('not token decoding')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials 2'
        )


user_dependency = Annotated[dict, Depends(get_current_user)]
