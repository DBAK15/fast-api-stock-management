from typing import Annotated, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session, selectinload
from starlette import status

from app.database import SessionLocal
from app.models import Orders, Products, OrderItems
from app.routers.auth import get_current_user
from app.schemas import OrderRead, OrderUpdate, OrderCreate
from app.utils import OrderStatus
from ..logging_config import setup_logger  # Import the setup_logger function

# Configure logging
logger = setup_logger("orderManagementLogger")

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


def get_order_by_id(db: Session, order_id: int, include_relations: bool = True):
    """Retrieve order by ID with optional relation loading."""
    query = db.query(Orders)

    if include_relations:
        query = query.options(
            selectinload(Orders.items),
            selectinload(Orders.delivery)
        )

    order = query.filter(
        Orders.id == order_id,
        Orders.is_deleted == False
    ).first()

    if not order:
        logger.warning(f"Order with ID {order_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


def verify_order_ownership(order: Orders, user_id: int):
    """Verify if user owns the order."""
    if order.user_id != user_id:
        logger.warning(f"User {user_id} is not authorized to access order {order.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )


def calculate_order_total(db: Session, items: list, user_id: int):
    """Calculate order total and create order items."""
    total_price = 0
    order_items = []

    for item in items:
        product = db.query(Products).filter(Products.id == item.product_id).first()
        if not product:
            logger.warning(f"Product with ID {item.product_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found"
            )

        # Verify stock availability
        if product.stock_quantity < item.quantity:
            logger.warning(f"Insufficient stock for product {product.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.id}"
            )

        order_item = OrderItems(
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_unit=product.price,
            created_by=user_id
        )

        total_price += product.price * item.quantity
        order_items.append(order_item)

    return total_price, order_items


# Endpoints
@router.get("/", response_model=List[OrderRead])
async def read_all_orders(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all orders with pagination.
    """
    verify_user(user)
    logger.info(f"Fetching all orders for user_id: {user.get('id')}, skip={skip}, limit={limit}")

    orders = db.query(Orders) \
        .filter(Orders.is_deleted == False) \
        .offset(skip) \
        .limit(limit) \
        .all()

    return orders


@router.get("/order/{order_id}", response_model=OrderRead)
async def read_order(
        user: user_dependency,
        db: db_dependency,
        order_id: int = Path(gt=0)
):
    """
    Retrieve a specific order by ID.
    """
    verify_user(user)
    order = get_order_by_id(db, order_id)
    verify_order_ownership(order, user.get('id'))

    logger.info(f"Retrieved order {order_id} for user {user.get('id')}")
    return OrderRead.from_orm(order)


@router.get("/orders/by_user", response_model=List[OrderRead])
async def read_all_by_user(
        user: user_dependency,
        db: db_dependency,
        user_id: int = Query(gt=0),
        status: OrderStatus = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all orders for a specific user with optional status filter and pagination.
    """
    verify_user(user)
    logger.info(f"Fetching orders for user_id: {user_id}, status: {status}, skip={skip}, limit={limit}")

    query = db.query(Orders) \
        .options(
        selectinload(Orders.items),
        selectinload(Orders.delivery)
    ) \
        .filter(Orders.user_id == user_id, Orders.is_deleted == False)

    if status:
        query = query.filter(Orders.status == status)

    orders = query.offset(skip).limit(limit).all()

    if not orders:
        logger.warning(f"No orders found for user with ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No orders found for user with ID: {user_id}"
        )

    return orders


@router.post("/order", status_code=status.HTTP_201_CREATED, response_model=OrderRead)
async def create_order(
        user: user_dependency,
        db: db_dependency,
        order_request: OrderCreate
):
    """
    Create a new order with items.
    """
    verify_user(user)
    user_id = user.get('id')

    # Create order
    order_model = Orders(**order_request.dict(), created_by=user_id)

    db.add(order_model)
    db.flush()  # Get order ID without committing

    # Calculate total and create order items
    total_price, order_items = calculate_order_total(db, order_request.items, user_id)

    # Associate items with order
    for item in order_items:
        item.order_id = order_model.id

    # Update order total and save everything
    order_model.total_price = total_price
    db.add_all(order_items)
    db.commit()

    logger.info(f"Created order {order_model.id} for user {user_id}")
    return OrderRead.from_orm(order_model)


@router.put("/order/{order_id}", response_model=OrderRead)
async def update_order(
        user: user_dependency,
        db: db_dependency,
        order_id: int,
        order_request: OrderUpdate
):
    """
    Update an existing order.
    """
    verify_user(user)
    order_model = get_order_by_id(db, order_id, include_relations=False)
    verify_order_ownership(order_model, user.get('id'))

    # Update fields if provided
    if order_request.status:
        order_model.status = order_request.status
    if order_request.total_price and order_model.total_price <= 0:
        order_model.total_price = order_request.total_price

    order_model.updated_by = user.get('id')
    db.commit()

    logger.info(f"Updated order {order_id}")
    return OrderRead.from_orm(order_model)


@router.delete("/order/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
        user: user_dependency,
        db: db_dependency,
        order_id: int = Path(gt=0)
):
    """
    Soft delete an order.
    """
    verify_user(user)
    order_model = get_order_by_id(db, order_id, include_relations=False)
    verify_order_ownership(order_model, user.get('id'))

    order_model.is_deleted = True
    order_model.updated_by = user.get('id')
    db.commit()

    logger.info(f"Deleted order {order_id}")
