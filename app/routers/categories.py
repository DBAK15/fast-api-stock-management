from typing import Annotated

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.models import Categories
from pydantic import BaseModel, Field
from app.database import SessionLocal
from app.routers.auth import get_current_user
from app.schemas import CategoryCreate, CategoryUpdate, CategoryRead
from datetime import datetime

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class CategoryRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3, max_length=100)

    class Config:
        from_attributes = True


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    return db.query(Categories).filter(Categories.is_deleted == False).all()


@router.get("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
async def read_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization failed")
    category_model = db.query(Categories).filter(Categories.id == category_id).filter(
        Categories.is_deleted == False).first()

    if category_model is not None:
        return category_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@router.post("/category", status_code=status.HTTP_201_CREATED, response_model=CategoryRead)
async def create_category(user: user_dependency, db: db_dependency, category_request: CategoryCreate):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")

    existing_category = db.query(Categories).filter(Categories.name == category_request.name).first()
    if existing_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Category {category_request.name} already exists.")
    category_model = Categories(**category_request.dict(), created_by=user.get('id'))

    db.add(category_model)
    db.commit()
    return CategoryRead.from_orm(category_model)


@router.put("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
async def update_category(user: user_dependency, db: db_dependency, category_request: CategoryUpdate,
                          category_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")

    category_model = db.query(Categories).filter(Categories.id == category_id).filter(
        Categories.is_deleted == False).first()

    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Mise à jour des champs non vides
    if category_request.name:
        category_model.name = category_request.name
    if category_request.description:
        category_model.description = category_request.description
    if category_request.name or category_request.description:
        category_model.updated_by = user.get('id')

    db.add(category_model)
    db.commit()

    return CategoryRead.from_orm(category_model)


@router.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")

    category_model = db.query(Categories).filter(Categories.id == category_id).filter(
        Categories.is_deleted == False).first()
    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category_model.is_deleted = True
    db.add(category_model)
    db.commit()
    # db.query(Categories).filter(Categories.id == category_id).delete()
    # db.commit()
