from enum import Enum
from enum import Enum as PyEnum


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

