from typing import List

from fastapi import APIRouter, HTTPException, Query, Path
from starlette import status

from app.models import Permissions
from app.schemas import PermissionRead, PermissionCreate, PermissionUpdate
from ..dependencies import db_dependency, user_dependency
from ..logging_config import setup_logger  # Import the setup_logger function
from ..utils import check_permissions, verify_user

# Configure logging
logger = setup_logger("permissionManagementLogger")

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
required_permissions = [
    "VIEW_PERMISSIONS",
    "CREATE_PERMISSIONS",
    "EDIT_PERMISSIONS",
    "DELETE_PERMISSIONS"
]


# Helper functions
# def verify_user(user: dict) -> None:
#     """Verify if user is authenticated."""
#     if user is None:
#         logger.warning("Authorization failed: No user provided")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization failed"
#         )


def get_permission(db: db_dependency, permission_id: int) -> Permissions:
    """Retrieve a permission by ID."""
    permission = db.query(Permissions).filter(
        Permissions.id == permission_id,
        Permissions.is_deleted == False
    ).first()

    if not permission:
        logger.warning(f"Permission with ID {permission_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


# Endpoints
@router.get("/", response_model=List[PermissionRead])
async def read_all_permissions(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all permissions with pagination.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    # check_permissions(user, required_permissions)
    logger.info(f"Fetching all permissions for user_id: {user.get('id')}, skip={skip}, limit={limit}")

    permissions = db.query(Permissions) \
        .filter(Permissions.is_deleted == False) \
        .offset(skip) \
        .limit(limit) \
        .all()

    return permissions


@router.get("/permission/{permission_id}", response_model=PermissionRead)
async def read_permission(
        user: user_dependency,
        db: db_dependency,
        permission_id: int = Path(gt=0)
):
    """
    Retrieve a specific permission by ID.
    """
    verify_user(user)
    check_permissions(user, required_permissions)
    logger.info(f"Fetching permission with ID: {permission_id} for user_id: {user.get('id')}")
    return get_permission(db, permission_id)


@router.post("/permission", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
        permission_request: PermissionCreate,
        user: user_dependency,
        db: db_dependency
):
    """
    Create a new permission.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    # check_permissions(user, required_permissions)

    # Check for duplicates
    existing_permission = db.query(Permissions).filter(
        Permissions.name == permission_request.name
    ).first()

    if existing_permission:
        logger.warning(f"Permission '{permission_request.name}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission '{permission_request.name}' already exists."
        )

    permission = Permissions(
        **permission_request.dict(),
        created_by=user.get('id')
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    logger.info(f"Created permission {permission.id}")
    return permission


@router.put("/permission/{permission_id}", response_model=PermissionRead, status_code=status.HTTP_200_OK)
async def update_permission(
        permission_request: PermissionUpdate,
        user: user_dependency,
        db: db_dependency,
        permission_id: int = Path(gt=0),
):
    """
    Update an existing permission.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)
    permission = get_permission(db, permission_id)

    # Update fields if provided
    if permission_request.name:
        permission.name = permission_request.name
    if permission_request.description:
        permission.description = permission_request.description
    if permission_request.name or permission_request.description:
        permission.updated_by = user.get('id')

    db.commit()
    db.refresh(permission)

    logger.info(f"Updated permission {permission.id}")
    return permission


@router.delete("/permission/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
        user: user_dependency,
        db: db_dependency,
        permission_id: int = Path(gt=0)
):
    """
    Soft delete a permission by setting `is_deleted` to True.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    permission = get_permission(db, permission_id)

    permission.is_deleted = True
    permission.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted permission {permission.id}")
