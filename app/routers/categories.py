from typing import Annotated

from fastapi import APIRouter, Path, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.models import Categories
from app.schemas import CategoryCreate, CategoryUpdate, CategoryRead
from ..database import SessionLocal
# from .auth import get_current_user
from ..dependencies import db_dependency, user_dependency
from ..logging_config import setup_logger  # Import the setup_logger function
from ..utils import check_permissions, verify_user

# Configure logger
logger = setup_logger("categoryManagementLogger")

router = APIRouter()

#
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
required_permissions = ["VIEW_CATEGORIES", "CREATE_CATEGORIES", "EDIT_CATEGORIES", "MANAGE_CATEGORIES"]


# def verify_user(user: dict) -> None:
#     if user is None:
#         logger.warning("Authorization failed: No user provided")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")


def get_category(db: db_dependency, category_id: int) -> Categories:
    category = db.query(Categories).filter(
        Categories.id == category_id,
        Categories.is_deleted == False
    ).first()

    if not category:
        logger.warning(f"Category with ID {category_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("/", response_model=list[CategoryRead], status_code=status.HTTP_200_OK)
async def read_all_categories(user: user_dependency, db: db_dependency, skip: int = Query(default=0, ge=0),
                              limit: int = Query(default=100, le=100)):
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    # check_permissions(user, required_permissions)

    logger.info(f"Fetching all categories for user_id: {user.get('id')}, skip={skip}, limit={limit}")
    return db.query(Categories).filter(Categories.is_deleted == False).offset(skip).limit(limit).all()


@router.get("/category/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
async def read_category(user: user_dependency, db: db_dependency, category_id: int = Path(..., gt=0)):
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    logger.info(f"Fetching category with ID: {category_id} for user_id: {user.get('id')}")
    return get_category(db, category_id)


@router.post("/category", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(category_request: CategoryCreate, user: user_dependency, db: db_dependency):
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    logger.info(f"Attempting to create category: {category_request.name}")

    existing_category = db.query(Categories).filter(Categories.name == category_request.name).first()
    if existing_category:
        logger.warning(f"Category {category_request.name} already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Category {category_request.name} already exists.")

    category = Categories(
        **category_request.dict(),
        created_by=user.get('id')
    )

    db.add(category)
    db.commit()
    db.refresh(category)
    logger.info(f"Created category {category.name} by user_id: {user.get('id')}")
    return category


@router.put("/category/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
async def update_category(user: user_dependency, db: db_dependency, category_request: CategoryUpdate,
                          category_id: int = Path(gt=0)):
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    category = get_category(db, category_id)

    if category_request.name:
        logger.info(f"Updating category name to {category_request.name} for category_id: {category_id}")
        category.name = category_request.name
    if category_request.description:
        logger.info(f"Updating category description for category_id: {category_id}")
        category.description = category_request.description
    if category_request.name or category_request.description:
        category.updated_by = user.get('id')

    db.commit()
    db.refresh(category)
    logger.info(f"Updated category {category.name} by user_id: {user.get('id')}")
    return category


@router.delete("/category/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    category = get_category(db, category_id)

    category.is_deleted = True
    category.updated_by = user.get('id')
    db.commit()
    logger.info(f"Deleted category {category.name} by user_id: {user.get('id')}")
