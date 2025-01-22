from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator, validator, root_validator, EmailStr

from app.models import Roles
from app.utils import OrderStatus, DeliveryStatus


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int

    class Config:
        from_attributes = True


#  Product Schemas
class ProductBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3, max_length=100)
    price: float = Field(gt=0)
    quantity: int = Field(gt=0)
    stock_minimum: int = Field(gt=0)
    category_id: Optional[int] = None
    is_deleted: bool = False
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    stock_minimum: Optional[int] = None


class ProductRead(ProductBase):
    id: int
    category_id: Optional[int]

    class Config:
        from_attributes = True


# User Schemas

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    password: str
    is_active: Optional[bool] = True
    role_id: Optional[int] = None


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str

    class Config:
        from_attributes = True

    # Utilisation du validateur de champ
    @validator('role', pre=True, always=True)
    def set_role_name(cls, v, values):
        # Si 'role' est un objet de type 'Roles', on le transforme en son nom
        if isinstance(v, Roles):
            return v.name
        return v


class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str


# Role Schema

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleRead(RoleBase):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# Permissions Schemas

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(PermissionBase):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionRead(PermissionBase):
    id: int

    class Config:
        from_attributes = True


# OrderItem Schemas

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None
    price_per_unit: Optional[float] = None


class OrderItemRead(OrderItemBase):
    id: int
    order_id: Optional[int]

    class Config:
        from_attributes = True  # Cela permet de convertir les objets SQLAlchemy en modèles Pydantic


# Delivery Schemas
class DeliveryBase(BaseModel):
    delivery_address: str
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING


class DeliveryCreate(DeliveryBase):
    order_id: int


class DeliveryUpdate(DeliveryBase):
    delivery_address: Optional[str] = None
    delivery_status: Optional[DeliveryStatus] = None


class DeliveryRead(DeliveryBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True


# Order Schemas

class OrderBase(BaseModel):
    user_id: int
    status: OrderStatus = OrderStatus.PENDING  # Statut par défaut


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    total_price: Optional[float] = None


class OrderRead(OrderBase):
    id: int
    order_number: str
    status: OrderStatus
    created_at: datetime
    total_price: float
    items: List[OrderItemRead] = []
    delivery: Optional[DeliveryRead] = None

    class Config:
        from_attributes = True

# # Report Schemas
#
# class ReportBase(BaseModel):
#     title: str
#     description: Optional[str] = None
#
#
# class ReportCreate(ReportBase):
#     pass
#
#
# class ReportRead(ReportBase):
#     id: int
#     generated_at: datetime
#     generated_by: Optional[int]
#
#     class Config:
#         from_attributes = True
#
#
# # Notifications Schemas
#
# class NotificationBase(BaseModel):
#     message: str
#     is_read: Optional[bool] = False
#     notification_type: Optional[NotificationType] = NotificationType.INFO
#
#
# class NotificationCreate(NotificationBase):
#     pass
#
#
# class NotificationRead(NotificationBase):
#     id: int
#     created_at: datetime
#     user_id: Optional[int]
#
#     class Config:
#         from_attributes = True
#
#
# # Stock Movement Schemas
#
# class StockMovementBase(BaseModel):
#     product_id: int
#     quantity: float = Field(gt=0)
#     movement_type: str  # IN or OUT
#
#
# class StockMovementCreate(StockMovementBase):
#     pass
#
#
# class StockMovementRead(StockMovementBase):
#     id: int
#     created_at: datetime
#     created_by: Optional[int]
#
#     class Config:
#         from_attributes = True
#
#
# # AuditLog Schema
# class AuditLogBase(BaseModel):
#     action: str
#     user_id: int
#     timestamp: datetime
#     ip_address: Optional[str] = None
#     endpoint: Optional[str] = None
#     action_details: Optional[str] = None
#
#
# class AuditLogCreate(AuditLogBase):
#     pass
#
#
# class AuditLogRead(AuditLogBase):
#     id: int
#
#     class Config:
#         from_attributes = True
