from typing import Annotated

from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Categories

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/categories/", status_code=status.HTTP_200_OK)
async def read_all_categories(user: user_dependency, db: db_dependency):
    if user is None or user.get('user_role') != 'admin':
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")
    return db.query(Categories).filter(Categories.is_deleted == False).all()


@router.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    category_model = db.query(Categories).filter(Categories.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category_model.is_deleted = True
    db.add(category_model)
    db.commit()
