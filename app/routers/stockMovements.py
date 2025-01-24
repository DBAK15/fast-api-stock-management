from typing import List, Annotated
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .auth import get_current_user
from ..database import SessionLocal
from ..models import StockMovements
from ..schemas import StockMovementCreate, StockMovementRead, StockMovementUpdate
from ..logging_config import setup_logger  # Import the setup_logger function

# Configure logging
logger = setup_logger("stockMovementLogger")

router = APIRouter()


# Dépendance pour récupérer la session de la base de données
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
    """
    Vérifie si l'utilisateur est authentifié.
    Lève une exception HTTP 401 si ce n'est pas le cas.
    """
    if user is None:
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )


### Endpoints ###

@router.get("/", response_model=List[StockMovementRead])
async def read_all_stock_movements(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de tous les mouvements de stock non supprimés.
    """
    verify_user(user)
    logger.info(f"Fetching all stock movements for user_id: {user.get('id')}")
    movements = db.query(StockMovements).filter(StockMovements.is_deleted == False).all()
    return movements


@router.get("/stock_movement/{stock_movements_id}", response_model=StockMovementRead)
async def read_stock_movement(stock_movements_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer un mouvement de stock spécifique par son ID.
    """
    verify_user(user)
    movement = db.query(StockMovements).filter(
        StockMovements.id == stock_movements_id, StockMovements.is_deleted == False
    ).first()
    if not movement:
        logger.warning(f"Stock movement with ID {stock_movements_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StockMovement not found")
    logger.info(f"Retrieved stock movement {stock_movements_id} for user_id: {user.get('id')}")
    return movement


@router.post("/stock_movement", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(movement: StockMovementCreate, db: db_dependency, user: user_dependency):
    """
    Créer un nouveau mouvement de stock.
    """
    verify_user(user)

    # Créer un nouvel objet StockMovement à partir des données reçues
    new_movement = StockMovements(**movement.dict(), created_by=user.get('id'))

    try:
        db.add(new_movement)
        db.commit()
        db.refresh(new_movement)  # Récupérer l'objet mis à jour avec son ID généré
        logger.info(f"Created stock movement {new_movement.id} for user_id: {user.get('id')}")
        return new_movement
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create stock movement: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create stock movement")


@router.put("/stock_movement/{stock_movements_id}", response_model=StockMovementRead)
async def update_stock_movement(stock_movements_id: int, movement: StockMovementUpdate, db: db_dependency,
                                user: user_dependency):
    """
    Mettre à jour un mouvement de stock existant par son ID.
    """
    verify_user(user)

    # Récupérer le mouvement de stock
    existing_movement = db.query(StockMovements).filter(StockMovements.id == stock_movements_id,
                                                        StockMovements.is_deleted == False).first()

    if not existing_movement:
        logger.warning(f"Stock movement with ID {stock_movements_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StockMovement not found")

    # Mettre à jour les attributs du mouvement de stock
    for key, value in movement.dict().items():
        setattr(existing_movement, key, value)

    existing_movement.updated_by = user.get('id')

    try:
        db.commit()
        db.refresh(existing_movement)
        logger.info(f"Updated stock movement {stock_movements_id} for user_id: {user.get('id')}")
        return existing_movement
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update stock movement: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update stock movement")


@router.delete("/stock_movement/{stock_movements_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_movement(stock_movements_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer (marquer comme supprimé) un mouvement de stock par son ID.
    """
    verify_user(user)

    # Récupérer le mouvement de stock
    movement = db.query(StockMovements).filter(StockMovements.id == stock_movements_id).first()

    if not movement:
        logger.warning(f"Stock movement with ID {stock_movements_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StockMovement not found")

    # Marquer le mouvement de stock comme supprimé
    movement.is_deleted = True
    try:
        db.commit()
        logger.info(f"Deleted stock movement {stock_movements_id} for user_id: {user.get('id')}")
        return {"detail": "Stock movement deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete stock movement: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete stock movement")
