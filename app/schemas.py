from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.utils import OrderStatus, NotificationType


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
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


#
# # Product Schemas
# class ProductBase(BaseModel):
#     name: str = Field(min_length=3, max_length=100)
#     description: str = Field(min_length=3, max_length=100)
#     price: float = Field(gt=0)
#     quantity: int = Field(gt=0)
#     stock_minimum: Optional[int] = Field(gt=0)
#     is_deleted: bool = False
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_by: Optional[str] = None
#     created_by: Optional[str] = None
#
#
# class ProductCreate(ProductBase):
#     pass
#
#
# class ProductUpdate(ProductBase):
#     name: Optional[str] = None
#     description: Optional[str] = None
#     price: Optional[float] = None
#     quantity: Optional[int] = None
#     stock_minimum: Optional[int] = None
#     is_deleted: Optional[bool] = None
#     updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
#
#
# class ProductRead(ProductBase):
#     id: int
#     category_id: Optional[int]
#
#     class Config:
#         from_attributes = True
#
#
# User Schemas

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str
    username: str
    first_name: str
    last_name: str
    phone_number: str
    password: str
    is_active: Optional[bool] = True
    role_id: Optional[int] = None


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


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

# # Permissions Schemas
#
# class PermissionBase(BaseModel):
#     name: str
#     description: Optional[str] = None
#
#
# class PermissionCreate(PermissionBase):
#     pass
#
#
# class PermissionUpdate(PermissionBase):
#     name: Optional[str] = None
#     description: Optional[str] = None
#
#
# class PermissionRead(PermissionBase):
#     id: int
#
#     class Config:
#         from_attributes = True
#
#
# # Order Schemas
#
# class OrderBase(BaseModel):
#     customer_name: str
#     status: OrderStatus = OrderStatus.PENDING  # Statut par défaut
#
#
# class OrderCreate(OrderBase):
#     pass
#
#
# class OrderUpdate(BaseModel):
#     customer_name: Optional[str] = None
#     status: Optional[str] = None
#
#
# class OrderRead(OrderBase):
#     id: int
#     created_at: Optional[str] = None
#
#     class Config:
#         from_attributes = True
#
#
# # OrderItem Schemas
#
# class OrderItemBase(BaseModel):
#     product_id: int
#     quantity: int
#
#
# class OrderItemCreate(OrderItemBase):
#     pass
#
#
# class OrderItemUpdate(BaseModel):
#     product_id: Optional[int] = None
#     quantity: Optional[int] = None
#
#
# class OrderItemRead(OrderItemBase):
#     id: int
#     order_id: int
#
#     class Config:
#         from_attributes = True
#
#
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
