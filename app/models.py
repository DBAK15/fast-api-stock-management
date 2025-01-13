from datetime import datetime
from sqlalchemy.types import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.utils import MovementType, NotificationType
from sqlalchemy import Index
from sqlalchemy import JSON


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_by = Column(Integer)
    created_by = Column(Integer)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    stock_minimum = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_by = Column(Integer)
    created_by = Column(Integer)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    orders = relationship("Order", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    reports = relationship("Report", back_populates="generated_by_user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="created_by_user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec User
    users = relationship("User", back_populates="role")

    # Relation avec Permission
    permissions = relationship("Permission", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec Role
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="permissions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(String)  # Détails généraux de l'action
    ip_address = Column(String)  # IP de l'utilisateur
    endpoint = Column(String)  # Nom de l'endpoint ou méthode appelée
    action_details = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec User
    user = relationship("User", back_populates="audit_logs")

    # Indexation sur `user_id` et `action`
    __table_args__ = (
        Index('idx_user_id_auditlog', 'user_id'),
        Index('idx_action_auditlog', 'action'),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec User
    user = relationship("User", back_populates="orders")

    # Relation avec OrderItem
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec Order
    order = relationship("Order", back_populates="items")

    # Relation avec Product
    product = relationship("Product", back_populates="order_items")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec l'utilisateur qui a généré le rapport
    generated_by_user = relationship("User", back_populates="reports")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(Enum(NotificationType), nullable=False,
                               default=NotificationType.INFO)  # Nouveau champ pour le type de notification
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec l'utilisateur
    user = relationship("User", back_populates="notifications")

    # Indexation sur `user_id` et `notification_type`
    __table_args__ = (
        Index('idx_user_id_notifications', 'user_id'),
        Index('idx_notification_type', 'notification_type'),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relations
    product = relationship("Product", back_populates="stock_movements")
    created_by_user = relationship("User", back_populates="stock_movements")


# Ajouter un index sur les colonnes 'user_id' et 'product_id'
Index('idx_user_id', User.id)  # Exemple sur le modèle User
Index('idx_product_id', Product.id)  # Exemple sur le modèle Product
Index('idx_user_id_notifications', Notification.user_id)  # Exemple sur le modèle Notification
Index('idx_product_id_stock_movements', StockMovement.product_id)  # Exemple sur le modèle StockMovement
