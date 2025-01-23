from typing import Annotated, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from app.database import SessionLocal
from app.models import OrderItems, Products, Orders
from app.routers.auth import get_current_user
from app.schemas import OrderItemRead, OrderItemCreate, OrderItemUpdate

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/orderItems",
    tags=["OrderItems"],
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


def get_order_item(db: Session, item_id: int):
    """Retrieve order item by ID."""
    item = db.query(OrderItems).filter(
        OrderItems.id == item_id,
        OrderItems.is_deleted == False
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    return item


def verify_product(db: Session, product_id: int):
    """Verify product exists and return it."""
    product = db.query(Products).filter(Products.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


def verify_order(db: Session, order_id: int):
    """Verify order exists and return it."""
    order = db.query(Orders).filter(Orders.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


def verify_order_ownership(db: Session, order_id: int, user_id: int):
    """Verify if user owns the order."""
    order = verify_order(db, order_id)
    if order.user_id != user_id:
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

    items = db.query(OrderItems) \
        .filter(
        OrderItems.order_id == order_id,
        OrderItems.is_deleted == False
    ) \
        .offset(skip) \
        .limit(limit) \
        .all()

    if not items:
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        item.quantity = order_item_request.quantity

    if order_item_request.price_per_unit is not None:
        if order_item_request.price_per_unit <= 0:
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







# from typing import Annotated, List
#
# from fastapi import APIRouter, Depends, HTTPException, Path, Query
# from sqlalchemy.orm import Session
# from starlette import status
#
# from app.database import SessionLocal
# from app.models import OrderItems, Products, Orders
# from app.routers.auth import get_current_user
# from app.schemas import OrderItemRead, OrderItemCreate, OrderItemUpdate
#
# router = APIRouter(
#     prefix="/orderItems",
#     tags=["OrderItems"],
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
#
# @router.get("/", status_code=status.HTTP_200_OK)
# async def read_all(user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#     return db.query(OrderItems).filter(OrderItems.is_deleted == False).all()
#
#
# @router.get("/orderItem/{order_item_id}", status_code=status.HTTP_200_OK, response_model=OrderItemRead)
# async def read_order_item(order_item_id: int, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).filter(
#         OrderItems.is_deleted == False).first()
#     if order_item_model is not None:
#         return order_item_model
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                         detail="OrderItem not found")
#
#
# # @router.get("/orderItem/by_order/{order_id}", response_model=OrderItemRead)
# # async def read_all_by_order(order_id: int, user: user_dependency, db: db_dependency):
# #     if user is None:
# #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
# #                             detail="Authorization failed")
# #     order_items_to_return =[]
# #     for item in db.query(OrderItems).filter(OrderItems.order_id == order_id).filter(OrderItems.is_deleted == False).all():
# #         order_items_to_return.append({item})
# #
# #     if order_items_to_return:
# #         return order_items_to_return
# #
# #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
# #                         detail=f"No items found for order with ID: `{order_id}`")
#
# @router.get("/orderItems/by_order", response_model=List[OrderItemRead])
# async def read_all_by_order(user: user_dependency, db: db_dependency, order_id: int = Query(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#
#     order_items = (
#         db.query(OrderItems)
#         .filter(OrderItems.order_id == order_id, OrderItems.is_deleted == False)
#         .all()
#     )
#
#     if not order_items:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"No items found for order with ID: `{order_id}`")
#     return order_items
#
#
# # @router.post("/orderItem", status_code=status.HTTP_201_CREATED, response_model=OrderItemRead)
# # async def create_order_item(order_item_request: OrderItemCreate, user: user_dependency, db: db_dependency):
# #     if user is None:
# #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
# #                             detail="Authorization failed")
# #     order_item_model = OrderItems(**order_item_request.dict(), created_by=user.get('id'))
# #
# #     db.add(order_item_model)
# #     db.commit()
# #
# #     return OrderItemRead.from_orm(order_item_model)
#
# @router.post("/orderItem", status_code=status.HTTP_201_CREATED, response_model=OrderItemRead)
# async def create_order_items(order_item_request: OrderItemCreate, user: user_dependency, db: db_dependency,
#                              order_id: int = Query(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     # Récupérer le produit depuis la table 'Products' en fonction de product_id
#     product = db.query(Products).filter(Products.id == order_item_request.product_id).first()
#     if product is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#
#     # Vérification de l'existence de la commande dans la base de données
#     order = db.query(Orders).filter(Orders.id == order_id).first()
#     if order is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
#
#     # Assigner le prix du produit au price_per_unit
#     price_per_unit = product.price  # Assurez-vous que 'price' existe dans le modèle Product
#
#     # Créer l'élément de commande avec les informations nécessaires
#     order_item_model = OrderItems(
#         product_id=order_item_request.product_id,
#         order_id=order_id,
#         quantity=order_item_request.quantity,
#         price_per_unit=price_per_unit,  # Utiliser le prix récupéré
#         created_by=user.get('id')
#     )
#
#     # Ajouter l'élément de commande à la base de données
#     db.add(order_item_model)
#     db.commit()
#
#     # Retourner le modèle de lecture avec toutes les informations nécessaires
#     return OrderItemRead.from_orm(order_item_model)
#
#
# @router.put("/orderItem/{order_item_id}", status_code=status.HTTP_200_OK, response_model=OrderItemRead)
# async def update_order_item(order_item_request: OrderItemUpdate, user: user_dependency, db: db_dependency,
#                             order_item_id: int = Path(gt=0), ):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).filter(
#         OrderItems.is_deleted == False).first()
#     if order_item_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail="OrderItem not found")
#
#     # Mise à jour des champs non vides
#     if order_item_request.quantity and order_item_request.quantity <= 0:
#         order_item_model.quantity = order_item_request.quantity
#     if order_item_request.price_per_unit and order_item_request.price_per_unit <= 0:
#         order_item_model.price_per_unit = order_item_request.price_per_unit
#     if order_item_request.quantity or order_item_request.price_per_unit:
#         order_item_model.updated_by = user.get('id')
#
#     db.add(order_item_model)
#     db.commit()
#
#     return OrderItemRead.from_orm(order_item_model)
#
#
# @router.delete("/orderItem/{order_item_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_order_item(order_item_id: int, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#
#     order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).first()
#     if order_item_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail="OrderItem not found")
#
#     order_item_model.is_deleted = True
#     db.add(order_item_model)
#     db.commit()
