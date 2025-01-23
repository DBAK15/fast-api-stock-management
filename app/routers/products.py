from typing import Annotated, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from starlette import status

from app.database import SessionLocal
from app.models import Products
from app.schemas import ProductRead, ProductCreate, ProductUpdate
from app.routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Helper functions
def verify_user(user: dict) -> None:
    """Verify if user is authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )


def get_product(db: Session, product_id: int):
    """Retrieve product by ID."""
    product = db.query(Products).filter(
        Products.id == product_id,
        Products.is_deleted == False
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


# Endpoints
@router.get("/", response_model=List[ProductRead])
async def read_all_products(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all products with pagination.
    """
    verify_user(user)
    return db.query(Products) \
        .filter(Products.is_deleted == False) \
        .offset(skip) \
        .limit(limit) \
        .all()


@router.get("/{product_id}", response_model=ProductRead)
async def read_product(
        user: user_dependency,
        db: db_dependency,
        product_id: int = Path(gt=0),
):
    """
    Retrieve a specific product by ID.
    """
    verify_user(user)
    return get_product(db, product_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductRead)
async def create_product(
        product_request: ProductCreate,
        user: user_dependency,
        db: db_dependency
):
    """
    Create a new product.
    """
    verify_user(user)

    product = Products(**product_request.dict(), created_by=user.get('id'))

    # product = Products(
    #     name=product_request.name,
    #     description=product_request.description,
    #     price=product_request.price,
    #     stock_quantity=product_request.stock_quantity,
    #     created_by=user.get('id')
    # )

    db.add(product)
    db.commit()
    db.refresh(product)

    logger.info(f"Created product {product.name}")
    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
        user: user_dependency,
        db: db_dependency,
        product_request: ProductUpdate,
        product_id: int = Path(gt=0)

):
    """
    Update an existing product.
    """
    verify_user(user)
    product = get_product(db, product_id)

    if product_request.name is not None:
        product.name = product_request.name
    if product_request.description is not None:
        product.description = product_request.description
    if product_request.price is not None:
        if product_request.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0"
            )
        product.price = product_request.price
    if product_request.stock_quantity is not None:
        if product_request.stock_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock quantity cannot be negative"
            )
        product.stock_quantity = product_request.stock_quantity

    product.updated_by = user.get('id')
    db.commit()
    db.refresh(product)

    logger.info(f"Updated product {product.id}")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
        user: user_dependency,
        db: db_dependency,
        product_id: int = Path(gt=0)
):
    """
    Soft delete a product.
    """
    verify_user(user)
    product = get_product(db, product_id)

    product.is_deleted = True
    product.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted product {product.id}")

# from typing import Annotated
#
# from fastapi import APIRouter, Depends, HTTPException, Path
# from sqlalchemy.orm import Session
# from starlette import status
#
# from app.database import SessionLocal
# from app.models import Products
# from app.routers.auth import get_current_user
# from app.schemas import ProductCreate, ProductRead, ProductUpdate
#
# router = APIRouter(
#     prefix="/products",
#     tags=["Products"]
# )
#
#
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# db_dependency = Annotated[Session, Depends(get_db)]
# user_dependency = Annotated[dict, Depends(get_current_user)]
#
#
# @router.get("/", response_model=list[ProductRead], status_code=status.HTTP_200_OK)
# async def read_all(user: user_dependency, db: db_dependency, skip: int = 0, limit: int = 10):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#     return db.query(Products).offset(skip).limit(limit).all()
#
#     # return crud.get_products(db=db, skip=skip, limit=limit)
#
#
# @router.get("/products/{category_id}", response_model=list[ProductRead], status_code=status.HTTP_200_OK)
# async def read_all_by_category(user: user_dependency, db: db_dependency, skip: int = 0, limit: int = 10,
#                                category_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#
#     products_to_return = []
#     for product in db.query(Products).filter(Products.category_id == category_id).offset(skip).limit(limit).all():
#         products_to_return.append(product)
#
#     if products_to_return:
#         return products_to_return
#
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"No product found for category `{category_id}`")
#
#
# @router.get("/product/{product_id}", response_model=ProductRead, status_code=status.HTTP_200_OK)
# async def read_product(product_id: int, db: db_dependency, user: user_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     product_model = db.query(Products).filter(Products.id == product_id).first()
#
#     if product_model is not None:
#         return product_model
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#
#
# @router.post("/product", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
# async def create_product(product_request: ProductCreate, db: db_dependency, user: user_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#     existing_product = db.query(Products).filter(Products.name == product_request.name).first()
#     if existing_product:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail=f"Product `{product_request.name}` already exists.")
#     product_model = Products(**product_request.dict(), created_by=user.get('id'))
#
#     db.add(product_model)
#     db.commit()
#     return ProductRead.from_orm(product_model)
#
#
# @router.put('/product/{product_id}', response_model=ProductRead, status_code=status.HTTP_200_OK)
# async def update_product(product_request: ProductUpdate, db: db_dependency, user: user_dependency,
#                          product_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Authorization failed")
#     product_model = db.query(Products).filter(Products.id == product_id).filter(Products.is_deleted == False).first()
#     if product_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#
#     # Mise à jour des champs non vides
#     if product_request.name:
#         product_model.name = product_request.name
#     if product_request.price and product_request.price <= 0:
#         product_model.price = product_request.price
#     if product_request.stock_minimum:
#         product_model.stock_minimum = product_request.stock_minimum
#     if product_request.quantity and product_request.quantity <= 0:
#         product_model.quantity = product_request.quantity
#     if product_request.description:
#         product_model.description = product_request.description
#     if product_request.name or product_request.price or product_request.stock_minimum or product_request.quantity or product_request.description:
#         product_model.updated_by = user.get('id')
#
#     db.add(product_model)
#     db.commit()
#
#     return ProductRead.from_orm(product_model)
#
#
# @router.delete("/product/{product_id}", status_code=status.HTTP_200_OK)
# async def delete_product(db: db_dependency, user: user_dependency, product_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Authorization failed")
#     product_model = db.query(Products).filter(Products.id == product_id).first()
#     if product_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#     product_model.is_deleted = True
#
#     db.add(product_model)
#     db.commit()
