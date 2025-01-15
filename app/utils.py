from enum import Enum
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Boolean, func


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MovementType(PyEnum):
    IN = "IN"
    OUT = "OUT"


class NotificationType(PyEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

