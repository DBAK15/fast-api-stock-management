from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app import crud, models
from app.schemas import ProductCreate, ProductRead, ProductUpdate
from app.database import SessionLocal
from typing import Annotated

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


def get_db():
    db = SessionLocal()
    print("Connexion réussie à la base de données.")
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/product", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: db_dependency):
    return crud.create_product(db=db, product=product)


@router.get("/", response_model=list[ProductRead], status_code=status.HTTP_200_OK)
def list_products(db: db_dependency, skip: int = 0, limit: int = 10):
    return crud.get_products(db=db, skip=skip, limit=limit)
