from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from app.database import SessionLocal
from app.models import OrderItems, Products, Orders
from app.routers.auth import get_current_user
from app.schemas import OrderItemRead, OrderItemCreate, OrderItemUpdate

router = APIRouter(
    prefix="/orderItems",
    tags=["OrderItems"],
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    return db.query(OrderItems).filter(OrderItems.is_deleted == False).all()


@router.get("/orderItem/{order_item_id}", status_code=status.HTTP_200_OK, response_model=OrderItemRead)
async def read_order_item(order_item_id: int, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization failed")
    order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).filter(
        OrderItems.is_deleted == False).first()
    if order_item_model is not None:
        return order_item_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="OrderItem not found")


# @router.get("/orderItem/by_order/{order_id}", response_model=OrderItemRead)
# async def read_all_by_order(order_id: int, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_items_to_return =[]
#     for item in db.query(OrderItems).filter(OrderItems.order_id == order_id).filter(OrderItems.is_deleted == False).all():
#         order_items_to_return.append({item})
#
#     if order_items_to_return:
#         return order_items_to_return
#
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"No items found for order with ID: `{order_id}`")

@router.get("/orderItems/by_order", response_model=List[OrderItemRead])
async def read_all_by_order(user: user_dependency, db: db_dependency, order_id: int = Query(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization failed")

    order_items = (
        db.query(OrderItems)
        .filter(OrderItems.order_id == order_id, OrderItems.is_deleted == False)
        .all()
    )

    if not order_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No items found for order with ID: `{order_id}`")
    return order_items


# @router.post("/orderItem", status_code=status.HTTP_201_CREATED, response_model=OrderItemRead)
# async def create_order_item(order_item_request: OrderItemCreate, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Authorization failed")
#     order_item_model = OrderItems(**order_item_request.dict(), created_by=user.get('id'))
#
#     db.add(order_item_model)
#     db.commit()
#
#     return OrderItemRead.from_orm(order_item_model)

@router.post("/orderItem", status_code=status.HTTP_201_CREATED, response_model=OrderItemRead)
async def create_order_items(order_item_request: OrderItemCreate, user: user_dependency, db: db_dependency,
                             order_id: int = Query(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")

    # Récupérer le produit depuis la table 'Products' en fonction de product_id
    product = db.query(Products).filter(Products.id == order_item_request.product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Vérification de l'existence de la commande dans la base de données
    order = db.query(Orders).filter(Orders.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Assigner le prix du produit au price_per_unit
    price_per_unit = product.price  # Assurez-vous que 'price' existe dans le modèle Product

    # Créer l'élément de commande avec les informations nécessaires
    order_item_model = OrderItems(
        product_id=order_item_request.product_id,
        order_id=order_id,
        quantity=order_item_request.quantity,
        price_per_unit=price_per_unit,  # Utiliser le prix récupéré
        created_by=user.get('id')
    )

    # Ajouter l'élément de commande à la base de données
    db.add(order_item_model)
    db.commit()

    # Retourner le modèle de lecture avec toutes les informations nécessaires
    return OrderItemRead.from_orm(order_item_model)


@router.put("/orderItem/{order_item_id}", status_code=status.HTTP_200_OK, response_model=OrderItemRead)
async def update_order_item(order_item_request: OrderItemUpdate, user: user_dependency, db: db_dependency,
                            order_item_id: int = Path(gt=0), ):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization failed")
    order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).filter(
        OrderItems.is_deleted == False).first()
    if order_item_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="OrderItem not found")

    # Mise à jour des champs non vides
    if order_item_request.quantity and order_item_request.quantity <= 0:
        order_item_model.quantity = order_item_request.quantity
    if order_item_request.price_per_unit and order_item_request.price_per_unit <= 0:
        order_item_model.price_per_unit = order_item_request.price_per_unit
    if order_item_request.quantity or order_item_request.price_per_unit:
        order_item_model.updated_by = user.get('id')

    db.add(order_item_model)
    db.commit()

    return OrderItemRead.from_orm(order_item_model)


@router.delete("/orderItem/{order_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_item(order_item_id: int, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization failed")

    order_item_model = db.query(OrderItems).filter(OrderItems.id == order_item_id).first()
    if order_item_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="OrderItem not found")

    order_item_model.is_deleted = True
    db.add(order_item_model)
    db.commit()
