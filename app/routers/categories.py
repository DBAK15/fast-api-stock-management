from typing import Annotated

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.models import Categories
from pydantic import BaseModel, Field
from app.database import SessionLocal
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


class CategoryRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3, max_length=100)

    class Config:
        from_attributes = True


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Categories).all()


@router.get("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
async def read_category(db: db_dependency, category_id: int = Path(gt=0)):
    category_model = db.query(Categories).filter(Categories.id == category_id).first()

    if category_model is not None:
        return category_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@router.post("/category", status_code=status.HTTP_201_CREATED, response_model=CategoryRead)
async def create_category(db: db_dependency, category_request: CategoryCreate):
    category_model = Categories(**category_request.dict())

    db.add(category_model)
    db.commit()


@router.put("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
async def update_category(db: db_dependency, category_request: CategoryUpdate, category_id: int = Path(gt=0)):
    category_model = db.query(Categories).filter(Categories.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    category_model.name = category_request.name
    category_model.description = category_request.description

    db.add(category_model)
    db.commit()


@router.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(db: db_dependency, category_id: int = Path(gt=0)):
    category_model = db.query(Categories).filter(Categories.id == category_id).first()
    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category_model.is_deleted = True
    db.add(category_model)
    db.commit()
    # db.query(Categories).filter(Categories.id == category_id).delete()
    # db.commit()
