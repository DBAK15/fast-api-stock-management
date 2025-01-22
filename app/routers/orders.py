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

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


def verify_order_ownership(order: Orders, user_id: int):
    """Verify if user owns the order."""
    if order.user_id != user_id:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found"
            )

        # Verify stock availability
        if product.stock_quantity < item.quantity:
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
async def read_all(
        user: user_dependency,
        db: db_dependency,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100)
):
    """
    Retrieve all orders with pagination.
    """
    verify_user(user)

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

    logger.debug(f"Retrieved order {order_id} for user {user.get('id')}")
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
    order_model = Orders(
        user_id=user_id,
        status=OrderStatus.PENDING,
        created_by=user_id
    )
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









# from typing import Annotated, List
#
# from fastapi import APIRouter, Depends, HTTPException, Path, Query
# from sqlalchemy.orm import Session, joinedload, selectinload
# from starlette import status
#
# from app.database import SessionLocal
# from app.models import Orders, Products, OrderItems
# from app.routers.auth import get_current_user
# from app.schemas import OrderRead, OrderUpdate, OrderCreate
# from app.utils import OrderStatus
#
# router = APIRouter(
#     prefix="/orders",
#     tags=["Orders"],
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
# @router.get("/", status_code=status.HTTP_200_OK, response_model=List[OrderRead])
# async def read_all(user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#     return db.query(Orders).filter(Orders.is_deleted == False).all()
#
#
# @router.get("/order/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderRead)
# async def read_order(user: user_dependency, db: db_dependency, order_id: int = Path(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
#
#     # Requête avec chargement des relations
#     # order_model = db.query(Orders) \
#     #     .options(joinedload(Orders.order_item), joinedload(Orders.delivery)) \
#     #     .filter(Orders.id == order_id, Orders.is_deleted == False) \
#     #     .first()
#     order_model = (
#         db.query(Orders)
#         .options(
#             selectinload(Orders.items),  # Charge les items associés
#             selectinload(Orders.delivery)  # Charge la livraison associée
#         )
#         .filter(Orders.id == order_id, Orders.is_deleted == False)
#         .first()
#     )
#
#     if not order_model:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
#
#     # Debug: Vérifiez ce qui est chargé
#     print("Order:", order_model)
#     print("Items:", order_model.items)
#     print("Delivery:", order_model.delivery)
#
#     return OrderRead.from_orm(order_model)
#
#
# @router.get("/orders/by_user", status_code=status.HTTP_200_OK, response_model=List[OrderRead])
# async def read_all_by_user(user: user_dependency, db: db_dependency, user_id: int = Query(gt=0)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#
#     orders = (
#         db.query(Orders)
#         .options(
#             selectinload(Orders.items),
#             selectinload(Orders.delivery)
#         )
#         .filter(Orders.user_id == user_id, Orders.is_deleted == False)
#         .all()
#     )
#
#     if not orders:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No orders found for user with ID: {user_id}"
#         )
#
#     return orders
#
#
# @router.post("/order", status_code=status.HTTP_201_CREATED, response_model=OrderRead)
# async def create_order(user: user_dependency, db: db_dependency, order_request: OrderCreate):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#
#     # Création de la commande
#     order_model = Orders(
#         user_id=user.get('id'),
#         status=OrderStatus.PENDING,  # statut initial
#         created_by=user.get('id'),
#     )
#
#     # Ajouter la commande à la session DB
#     db.add(order_model)
#     db.commit()  # Commiter pour que l'ID de la commande soit généré
#
#     # Calculer le prix total de la commande
#     total_price = 0
#     for item in order_request.items:  # `items` est une liste d'articles dans la requête
#         product = db.query(Products).filter(Products.id == item.product_id).first()
#         if not product:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                                 detail=f"Product with ID {item.product_id} not found.")
#
#         # Créer l'item de commande
#         order_item = OrderItems(
#             order_id=order_model.id,
#             product_id=item.product_id,
#             quantity=item.quantity,
#             price_per_unit=product.price,  # Utiliser le prix du produit
#             created_by=user.get('id'),
#         )
#
#         # Ajouter l'item à la session DB
#         db.add(order_item)
#         db.commit()  # Commit chaque item après l'ajout
#
#         # Calculer le prix total de la commande
#         total_price += product.price * item.quantity
#
#     # Mise à jour du total de la commande
#     order_model.total_price = total_price
#     db.commit()  # Commit la mise à jour du total dans la commande
#
#     return OrderRead.from_orm(order_model)
#
#
# @router.put("/order/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderRead)
# async def update_order(user: user_dependency, db: db_dependency, order_id: int, order_request: OrderUpdate):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_model = db.query(Orders).filter(Orders.id == order_id).filter(Orders.is_deleted == False).first()
#     if order_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
#
#     # Mise à jour des champs non vides
#     if order_request.status:
#         order_model.status = order_request.status
#     if order_request.total_price and order_model.total_price <= 0:
#         order_model.total_price = order_request.total_price
#     if order_request.status or order_request.total_price:
#         order_model.updated_by = user.get('id')
#
#     db.add(order_model)
#     db.commit()
#
#     return OrderRead.from_orm(order_model)
#
#
# @router.delete("/order/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_order(user: user_dependency, db: db_dependency, order_id: int):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_model = db.query(Orders).filter(Orders.id == order_id).first()
#     if order_model is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
#     order_model.is_deleted = True
#
#     db.add(order_model)
#     db.commit()
