from typing import Annotated, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from app.database import SessionLocal
from app.models import OrderItems, Products, Orders
from app.routers.auth import get_current_user
from app.schemas import OrderItemRead, OrderItemCreate, OrderItemUpdate
from ..logging_config import setup_logger  # Import the setup_logger function

# Configure logging
logger = setup_logger("orderItemManagementLogger")

router = APIRouter()


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
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )


def get_order_item(db: Session, item_id: int):
    """Retrieve order item by ID."""
    item = db.query(OrderItems).filter(
        OrderItems.id == item_id,
        OrderItems.is_deleted == False
    ).first()

    if not item:
        logger.warning(f"Order item with ID {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    return item


def verify_product(db: Session, product_id: int):
    """Verify product exists and return it."""
    product = db.query(Products).filter(Products.id == product_id).first()
    if not product:
        logger.warning(f"Product with ID {product_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


def verify_order(db: Session, order_id: int):
    """Verify order exists and return it."""
    order = db.query(Orders).filter(Orders.id == order_id).first()
    if not order:
        logger.warning(f"Order with ID {order_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


def verify_order_ownership(db: Session, order_id: int, user_id: int):
    """Verify if user owns the order."""
    order = verify_order(db, order_id)
    if order.user_id != user_id:
        logger.warning(f"User {user_id} is not authorized to access order {order_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )


# Endpoints
@router.get("/", response_model=List[OrderItemRead])
async def read_all_orders_items(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all order items with pagination.
    """
    verify_user(user)
    logger.info(f"Fetching all order items for user_id: {user.get('id')}, skip={skip}, limit={limit}")

    return db.query(OrderItems) \
        .filter(OrderItems.is_deleted == False) \
        .offset(skip) \
        .limit(limit) \
        .all()


@router.get("/orderItem/{order_item_id}", response_model=OrderItemRead)
async def read_order_item(
        order_item_id: int,
        user: user_dependency,
        db: db_dependency
):
    """
    Retrieve a specific order item by ID.
    """
    verify_user(user)
    item = get_order_item(db, order_item_id)
    verify_order_ownership(db, item.order_id, user.get('id'))

    logger.info(f"Retrieved order item {order_item_id} for user {user.get('id')}")
    return item


@router.get("/orderItems/by_order", response_model=List[OrderItemRead])
async def read_all_by_order(
        user: user_dependency,
        db: db_dependency,
        order_id: int = Query(gt=0),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all items for a specific order with pagination.
    """
    verify_user(user)
    verify_order_ownership(db, order_id, user.get('id'))

    logger.info(f"Fetching order items for order_id: {order_id}, skip={skip}, limit={limit}")

    items = db.query(OrderItems) \
        .filter(
        OrderItems.order_id == order_id,
        OrderItems.is_deleted == False
    ) \
        .offset(skip) \
        .limit(limit) \
        .all()

    if not items:
        logger.warning(f"No items found for order with ID: {order_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found for order with ID: {order_id}"
        )
    return items


@router.post("/orderItem", status_code=status.HTTP_201_CREATED, response_model=OrderItemRead)
async def create_order_item(
        order_item_request: OrderItemCreate,
        user: user_dependency,
        db: db_dependency,
        order_id: int = Query(gt=0)
):
    """
    Create a new order item for a specific order.
    """
    verify_user(user)
    verify_order_ownership(db, order_id, user.get('id'))

    # Verify product and get its price
    product = verify_product(db, order_item_request.product_id)

    # Verify stock availability
    if product.stock_quantity < order_item_request.quantity:
        logger.warning(f"Insufficient stock for product {product.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock for product"
        )

    # Create order item
    order_item = OrderItems(
        product_id=order_item_request.product_id,
        order_id=order_id,
        quantity=order_item_request.quantity,
        price_per_unit=product.price,
        created_by=user.get('id')
    )

    db.add(order_item)
    db.commit()
    db.refresh(order_item)

    logger.info(f"Created order item {order_item.id} for order {order_id}")
    return order_item


@router.put("/orderItem/{order_item_id}", response_model=OrderItemRead)
async def update_order_item(
        order_item_request: OrderItemUpdate,
        user: user_dependency,
        db: db_dependency,
        order_item_id: int = Path(gt=0)
):
    """
    Update an existing order item.
    """
    verify_user(user)
    item = get_order_item(db, order_item_id)
    verify_order_ownership(db, item.order_id, user.get('id'))

    if order_item_request.quantity is not None:
        if order_item_request.quantity <= 0:
            logger.warning(f"Invalid quantity {order_item_request.quantity} for order item {order_item_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        item.quantity = order_item_request.quantity

    if order_item_request.price_per_unit is not None:
        if order_item_request.price_per_unit <= 0:
            logger.warning(f"Invalid price {order_item_request.price_per_unit} for order item {order_item_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0"
            )
        item.price_per_unit = order_item_request.price_per_unit

    item.updated_by = user.get('id')
    db.commit()
    db.refresh(item)

    logger.info(f"Updated order item {order_item_id}")
    return item


@router.delete("/orderItem/{order_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_item(
        order_item_id: int,
        user: user_dependency,
        db: db_dependency
):
    """
    Soft delete an order item.
    """
    verify_user(user)
    item = get_order_item(db, order_item_id)
    verify_order_ownership(db, item.order_id, user.get('id'))

    item.is_deleted = True
    item.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted order item {order_item_id}")
