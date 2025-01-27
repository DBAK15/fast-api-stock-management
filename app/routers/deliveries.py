from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.models import Deliveries
from app.schemas import DeliveryRead, DeliveryCreate, DeliveryUpdate
from ..dependencies import db_dependency, user_dependency
from ..logging_config import setup_logger  # Import the setup_logger function
from ..utils import check_permissions, verify_user

# Configure logging
logger = setup_logger("deliveryManagementLogger")

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

# Permissions required for delivery actions
required_permissions = [
    "VIEW_DELIVERIES", "CREATE_DELIVERIES", "EDIT_DELIVERIES",
    "DELETE_DELIVERIES", "MANAGE_DELIVERIES", "VALIDATE_DELIVERIES",
    "TRACK_DELIVERIES", "ASSIGN_DELIVERIES"
]

# Helpers functions
# def verify_user(user: dict) -> None:
#     """Verify if the user is authenticated."""
#     if user is None:
#         logger.warning("Authorization failed: No user provided")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")


def get_delivery(db: Session, delivery_id: int):
    """Retrieve delivery by ID."""
    delivery = db.query(Deliveries).filter(
        Deliveries.id == delivery_id,
        Deliveries.is_deleted == False
    ).first()

    if delivery is None:
        logger.warning(f"Delivery with ID {delivery_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


# Endpoints
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all_deliveries(user: user_dependency, db: db_dependency):
    """Fetch all deliveries."""
    verify_user(user)
    check_permissions(user, required_permissions)

    logger.info(f"Fetching all deliveries for user_id: {user.get('id')}")
    return db.query(Deliveries).filter(Deliveries.is_deleted == False).all()


@router.get("/delivery/{delivery_id}", response_model=DeliveryRead, status_code=status.HTTP_200_OK)
async def read_delivery(delivery_id: int, db: db_dependency, user: user_dependency):
    """Fetch a single delivery by ID."""
    verify_user(user)
    check_permissions(user, required_permissions)

    delivery = get_delivery(db, delivery_id)
    logger.info(f"Retrieved delivery {delivery_id} for user_id: {user.get('id')}")
    return DeliveryRead.from_orm(delivery)


@router.post("/delivery", response_model=DeliveryRead, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    delivery_request: DeliveryCreate,
    db: db_dependency,
    user: user_dependency,
) -> DeliveryRead:
    """Create a new delivery."""
    verify_user(user)
    check_permissions(user, required_permissions)

    try:
        delivery_data = delivery_request.dict()
        delivery_data["created_by"] = user.get("id")

        delivery_model = Deliveries(**delivery_data)
        db.add(delivery_model)
        db.commit()

        logger.info(f"Created delivery {delivery_model.id} for user_id: {user.get('id')}")
        return DeliveryRead.from_orm(delivery_model)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create delivery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create delivery: {str(e)}"
        )


@router.put("/delivery/{delivery_id}", response_model=DeliveryRead, status_code=status.HTTP_200_OK)
async def update_delivery(
    delivery_id: int,
    delivery_update: DeliveryUpdate,
    db: db_dependency,
    user: user_dependency,
) -> DeliveryRead:
    """Update an existing delivery."""
    verify_user(user)
    check_permissions(user, required_permissions)

    delivery = get_delivery(db, delivery_id)

    try:
        update_data = delivery_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(delivery, field, value)

        # Add audit information
        delivery.updated_by = user.get("id")

        db.commit()
        db.refresh(delivery)
        logger.info(f"Updated delivery {delivery_id} for user_id: {user.get('id')}")
        return DeliveryRead.from_orm(delivery)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update delivery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update delivery: {str(e)}"
        )


@router.delete("/delivery/{delivery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery(
    delivery_id: int,
    db: db_dependency,
    user: user_dependency,
):
    """Delete (soft delete) a delivery."""
    verify_user(user)
    check_permissions(user, required_permissions)

    delivery = get_delivery(db, delivery_id)

    try:
        delivery.is_deleted = True

        db.commit()
        logger.info(f"Deleted delivery {delivery_id} for user_id: {user.get('id')}")
        return None

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete delivery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete delivery: {str(e)}"
        )
