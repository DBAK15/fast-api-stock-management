from enum import Enum
from enum import Enum as PyEnum
from typing import List

from fastapi import HTTPException
from starlette import status
from .logging_config import setup_logger  # Import the setup_logger function

# Configure logger
logger = setup_logger("categoryManagementLogger")

settings_required_permissions = ["MANAGE_SETTINGS"]
logs_required_permissions = ["VIEW_LOGS"]


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class DeliveryStatus(Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"
    IN_PROGRESS = "IN_PROGRESS"


class MovementType(PyEnum):
    IN = "IN"
    OUT = "OUT"


class NotificationType(PyEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


def generate_order_number(order_id: int, user_id: int) -> str:
    """
    Génère un numéro de commande unique en utilisant l'ID de l'ordre et l'ID de l'utilisateur.

    Format : ORD-{user_id}-{order_id}, où :
        - {user_id} est l'ID de l'utilisateur, zéro-paddé à 4 chiffres
        - {order_id} est l'ID de la commande, zéro-paddé à 6 chiffres
    """
    return f"ORD-{str(user_id).zfill(4)}-{str(order_id).zfill(6)}"


def check_permissions(user: dict, required_permissions: List[str]) -> None:
    """
    Vérifie si l'utilisateur possède toutes les permissions nécessaires.
    Lève une exception HTTP 403 si les permissions sont insuffisantes.
    """
    user_permissions = set(user.get('permissions', []))
    missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]

    if missing_permissions:
        logger.warning(
            f"Permission check failed for user {user.get('username')}. "
            f"Missing permissions: {missing_permissions}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Missing: {missing_permissions}"
        )
    logger.info(f"User {user.get('username')} has the required permissions: {required_permissions}")


def verify_user(user: dict) -> None:
    if user is None:
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")