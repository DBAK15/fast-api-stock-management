from typing import Annotated
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Path, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from app.models import Categories
from app.database import SessionLocal
from app.routers.auth import get_current_user
from app.schemas import CategoryCreate, CategoryUpdate, CategoryRead

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
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


def has_permission(required_permission: str, user_permissions: list):
    if required_permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permission"
        )


def get_category(db: Session, category_id: int) -> Categories:
    """Retrieve a category by ID."""
    category = db.query(Categories).filter(
        Categories.id == category_id,
        Categories.is_deleted == False
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


# Endpoints
@router.get("/", response_model=list[CategoryRead], status_code=status.HTTP_200_OK)
async def read_all_categories(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all categories with pagination.
    """
    verify_user(user)
    return db.query(Categories).filter(Categories.is_deleted == False).offset(skip).limit(limit).all()


@router.get("/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
async def read_category(
        user: user_dependency,
        db: db_dependency,
        category_id: int = Path(..., gt=0)
):
    """
    Retrieve a specific category by ID.
    """
    verify_user(user)
    return get_category(db, category_id)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_request: CategoryCreate,
        user: user_dependency,
        db: db_dependency
):
    """
    Create a new category.
    """
    verify_user(user)

    # Check if category already exists
    existing_category = db.query(Categories).filter(Categories.name == category_request.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category {category_request.name} already exists."
        )

    category = Categories(
        **category_request.dict(),
        created_by=user.get('id')
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    logger.info(f"Created category {category.id}")
    return category


@router.put("/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
async def update_category(
        user: user_dependency,
        db: db_dependency,
        category_request: CategoryUpdate,
        category_id: int = Path(gt=0)
):
    """
    Update an existing category.
    """
    verify_user(user)
    category = get_category(db, category_id)

    # Update fields if provided
    if category_request.name:
        category.name = category_request.name
    if category_request.description:
        category.description = category_request.description
    if category_request.name or category_request.description:
        category.updated_by = user.get('id')

    db.commit()
    db.refresh(category)

    logger.info(f"Updated category {category.id}")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
        user: user_dependency,
        db: db_dependency,
        category_id: int = Path(gt=0)
):
    """
    Soft delete a category by setting `is_deleted` to True.
    """
    verify_user(user)
    category = get_category(db, category_id)

    category.is_deleted = True
    category.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted category {category.id}")

# from typing import Annotated
#
# from fastapi import APIRouter, Depends, Path, HTTPException
# from sqlalchemy.orm import Session
# from starlette import status
# from app.models import Categories
# from pydantic import BaseModel, Field
# from app.database import SessionLocal
# from app.routers.auth import get_current_user
# from app.schemas import CategoryCreate, CategoryUpdate, CategoryRead
# from datetime import datetime
#
# router = APIRouter(
#     prefix="/categories",
#     tags=["Categories"],
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
# ## Endpoints ##
# @router.get("/", status_code=status.HTTP_200_OK)
# async def read_all(user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#     return db.query(Categories).filter(Categories.is_deleted == False).all()
#
#
# @router.get("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
# async def read_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     category_model = db.query(Categories).filter(Categories.id == category_id).filter(
#         Categories.is_deleted == False).first()
#
#     if category_model is not None:
#         return category_model
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
#
#
# @router.post("/category", status_code=status.HTTP_201_CREATED, response_model=CategoryRead)
# async def create_category(user: user_dependency, db: db_dependency, category_request: CategoryCreate):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     existing_category = db.query(Categories).filter(Categories.name == category_request.name).first()
#     if existing_category:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail=f"Category {category_request.name} already exists.")
#     category_model = Categories(**category_request.dict(), created_by=user.get('id'))
#
#     db.add(category_model)
#     db.commit()
#     return CategoryRead.from_orm(category_model)
#
#
# @router.put("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=CategoryRead)
# async def update_category(user: user_dependency, db: db_dependency, category_request: CategoryUpdate,
#                           category_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     category_model = db.query(Categories).filter(Categories.id == category_id).filter(
#         Categories.is_deleted == False).first()
#
#     if category_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
#
#     # Mise à jour des champs non vides
#     if category_request.name:
#         category_model.name = category_request.name
#     if category_request.description:
#         category_model.description = category_request.description
#     if category_request.name or category_request.description:
#         category_model.updated_by = user.get('id')
#
#     db.add(category_model)
#     db.commit()
#
#     return CategoryRead.from_orm(category_model)
#
#
# @router.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
# async def delete_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     category_model = db.query(Categories).filter(Categories.id == category_id).first()
#     if category_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
#     category_model.is_deleted = True
#     db.add(category_model)
#     db.commit()
#     # db.query(Categories).filter(Categories.id == category_id).delete()
#     # db.commit()
