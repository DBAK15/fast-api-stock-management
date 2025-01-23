from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Users
from ..schemas import UserVerification, UserRead, UserResponse

router = APIRouter(
    prefix="/user",
    tags=["User"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get('/', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    print(f"user_info: {user}")
    return db.query(Users).filter(Users.id == user.get('id')).first()


@router.put('/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail="Authorization failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    # if user_model is None:
    #     raise HTTPException(status_code=401, detail="User does not exist.")

    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="Error on password change.")

    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()


@router.put('/phonenumber/{phone_number}', status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(user: user_dependency, db: db_dependency, phone: str):
    if user is None:
        raise HTTPException(status_code=401, detail="Authorization failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    user_model.phone = phone
    db.add(user_model)
    db.commit()
