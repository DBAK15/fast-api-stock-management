from typing import List

from fastapi import APIRouter, HTTPException, Query, Path
from sqlalchemy.orm import Session
from starlette import status

from app.models import Products
from app.schemas import ProductRead, ProductCreate, ProductUpdate
from ..dependencies import db_dependency, user_dependency
from ..logging_config import setup_logger  # Import the setup_logger function
from ..utils import check_permissions, verify_user

# Configure logging
logger = setup_logger("stockManagementLogger")

router = APIRouter()


# # Dependencies
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
required_permissions = ["VIEW_PRODUCTS", "CREATE_PRODUCTS", "EDIT_PRODUCTS", "DELETE_PRODUCTS", "ARCHIVE_PRODUCTS"]


# # Helper functions
# def verify_user(user: dict) -> None:
#     """Verify if user is authenticated."""
#     if user is None:
#         logger.error("Authorization failed")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization failed"
#         )


def get_product(db: Session, product_id: int):
    """Retrieve product by ID."""
    product = db.query(Products).filter(
        Products.id == product_id,
        Products.is_deleted == False
    ).first()

    if not product:
        logger.error(f"Product with ID {product_id} not found")
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
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)
    logger.info(f"Reading all products with skip={skip} and limit={limit}")
    return db.query(Products) \
        .filter(Products.is_deleted == False) \
        .offset(skip) \
        .limit(limit) \
        .all()


@router.get("/product/{product_id}", response_model=ProductRead)
async def read_product(
        user: user_dependency,
        db: db_dependency,
        product_id: int = Path(gt=0),
):
    """
    Retrieve a specific product by ID.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)
    logger.info(f"Reading product with ID: {product_id}")
    return get_product(db, product_id)


@router.post("/product", status_code=status.HTTP_201_CREATED, response_model=ProductRead)
async def create_product(
        product_request: ProductCreate,
        user: user_dependency,
        db: db_dependency
):
    """
    Create a new product.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    product = Products(**product_request.dict(), created_by=user.get('id'))

    db.add(product)
    db.commit()
    db.refresh(product)

    logger.info(f"Created product {product.name}")
    return product


@router.put("/product/{product_id}", response_model=ProductRead)
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
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    product = get_product(db, product_id)

    if product_request.name is not None:
        product.name = product_request.name
    if product_request.description is not None:
        product.description = product_request.description
    if product_request.price is not None:
        if product_request.price <= 0:
            logger.error(f"Invalid price {product_request.price} for product {product_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0"
            )
        product.price = product_request.price
    if product_request.stock_quantity is not None:
        if product_request.stock_quantity < 0:
            logger.error(f"Invalid stock quantity {product_request.stock_quantity} for product {product_id}")
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


@router.delete("/product/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
        user: user_dependency,
        db: db_dependency,
        product_id: int = Path(gt=0)
):
    """
    Soft delete a product.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)
    product = get_product(db, product_id)

    product.is_deleted = True
    product.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted product {product.id}")
