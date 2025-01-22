from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.database import SessionLocal
from app.models import Deliveries
from app.routers.auth import get_current_user
from app.schemas import DeliveryRead, DeliveryCreate, DeliveryUpdate

router = APIRouter(
    prefix="/deliveries",
    tags=["Deliveries"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


## Endpoints ##


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return db.query(Deliveries).filter(Deliveries.is_deleted == False).all()


@router.get("/delivery/{delivery_id}", status_code=status.HTTP_200_OK)
async def read_delivery(delivery_id: int, db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    delivery = db.query(Deliveries).filter(Deliveries.id == delivery_id).first()
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


@router.post("/delivery", status_code=status.HTTP_201_CREATED)
async def create_delivery(
        delivery_request: DeliveryCreate,
        db: db_dependency,
        user: user_dependency,
) -> DeliveryRead:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        # Convert Pydantic model to dict and add created_by field
        delivery_data = delivery_request.dict()
        delivery_data["created_by"] = user.get("id")

        # Create and save the delivery
        delivery_model = Deliveries(**delivery_data)
        db.add(delivery_model)
        db.commit()
        return DeliveryRead.from_orm(delivery_model)

    except Exception as e:
        db.rollback()  # Rollback on any error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create delivery: {str(e)}"
        )


@router.put("/delivery/{delivery_id}", response_model=DeliveryRead)
async def update_delivery(
        delivery_id: int,
        delivery_update: DeliveryUpdate,
        db: db_dependency,
        user: user_dependency,
) -> DeliveryRead:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        delivery = db.query(Deliveries).filter(
            Deliveries.id == delivery_id,
            Deliveries.is_deleted == False
        ).first()

        if delivery is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery not found"
            )

        # Update only provided fields
        update_data = delivery_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(delivery, field, value)

        # Add audit information
        delivery.updated_by = user.get("id")

        db.commit()
        db.refresh(delivery)

        return DeliveryRead.from_orm(delivery)

    except Exception as e:
        db.rollback()
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
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        delivery = db.query(Deliveries).filter(
            Deliveries.id == delivery_id,
            Deliveries.is_deleted == False
        ).first()

        if delivery is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery not found"
            )

        # Soft delete
        delivery.is_deleted = True

        db.commit()

        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete delivery: {str(e)}"
        )
