from datetime import datetime
import logging
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, DECIMAL, UniqueConstraint, event
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum

from app.database import Base
from app.utils import MovementType, NotificationType, DeliveryStatus, OrderStatus, generate_order_number

# Configure logging
logger = logging.getLogger(__name__)


class Categories(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer)
    created_by = Column(Integer)

    product = relationship("Products", back_populates="category")


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
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

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    category = relationship("Categories", back_populates="product")
    order_item = relationship("OrderItems", back_populates="product")
    stock_movement = relationship("StockMovements", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Products(name={self.name}, description={self.description})>"


#
# class Users(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     username = Column(String, unique=True, nullable=False)
#     first_name = Column(String, nullable=False)
#     last_name = Column(String, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     phone = Column(String, nullable=False)
#     hashed_password = Column(String, nullable=False)
#     is_active = Column(Boolean, default=True, nullable=False)
#     # role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     created_by = Column(Integer)
#     updated_by = Column(Integer)
#
#     order = relationship("Orders", back_populates="user")
#     audit_log = relationship("AuditLogs", back_populates="user")
#     report = relationship("Reports", back_populates="generated_by_user", cascade="all, delete-orphan")
#     notification = relationship("Notifications", back_populates="user", cascade="all, delete-orphan")
#     role = relationship("Roles", back_populates="user")
#     # stock_movement = relationship("StockMovements", back_populates="created_by_user", cascade="all, delete-orphan")
#     stock_movement = relationship(
#         "StockMovements",
#         back_populates="user",
#         primaryjoin="Users.id == StockMovements.user_id"
#     )
#     user_roles = relationship("UserRoles", back_populates="user", cascade="all, delete-orphan")
#
#     @property
#     def permissions(self):
#         return {perm.name for role in self.user_roles for perm in role.role_permissions}
#
#
# class UserRoles(Base):
#     __tablename__ = "user_roles"
#     __table_args__ = (
#         UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
#     )
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
#
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#
#     # Relations
#     user = relationship("Users", back_populates="user_roles")
#     role = relationship("Roles", back_populates="user_roles")
#
#
# class Roles(Base):
#     __tablename__ = "roles"
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     name = Column(String, unique=True, nullable=False)
#     description = Column(String)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     created_by = Column(Integer)
#     updated_by = Column(Integer)
#
#     # Relation avec Users
#     # user = relationship("Users", back_populates="role")
#     user_roles = relationship("UserRoles", back_populates="role", cascade="all, delete-orphan")
#     # Relation avec Permissions
#     # permission = relationship("Permissions", back_populates="role", cascade="all, delete-orphan")
#     role_permissions = relationship("RolePermissions", back_populates="role", cascade="all, delete-orphan")
#
#
# class Permissions(Base):
#     __tablename__ = "permissions"
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     name = Column(String, unique=True, nullable=False)
#     description = Column(String, nullable=True)
#     is_deleted = Column(Boolean, default=False, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     created_by = Column(Integer)
#     updated_by = Column(Integer)
#     # Relation avec Roles
#     # role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
#     # role = relationship("Roles", back_populates="permission")
#
#     role_permissions = relationship("RolePermissions", back_populates="permission", cascade="all, delete-orphan")
#
#
# class RolePermissions(Base):
#     __tablename__ = "role_permissions"
#     __table_args__ = (
#         UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
#     )
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
#     permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
#
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#
#     # Relations
#     role = relationship("Roles", back_populates="role_permissions")
#     permission = relationship("Permissions", back_populates="role_permissions")


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relations
    role = relationship("Roles", back_populates="users")
    audit_log = relationship('AuditLogs', back_populates='user')
    order = relationship("Orders", back_populates="user")
    report = relationship("Reports", back_populates="generated_by_user")
    notification = relationship("Notifications", back_populates="user", cascade="all, delete-orphan")
    stock_movement = relationship(
        "StockMovements",
        back_populates="user",
        primaryjoin="Users.id == StockMovements.user_id"
    )

    @property
    def permissions(self):
        """Accès aux permissions de l'utilisateur via son rôle en utilisant la table RolePermissions."""
        if not self.role:
            return set()

        permissions = set()

        # Effectuer une jointure entre RolePermissions et Permissions pour récupérer les noms de permissions
        for rp in self.role.role_permissions:
            permission = rp.permission
            if permission and permission.name:
                permissions.add(permission.name)
            else:
                logger.warning(f"Role '{self.role.name}' has an invalid permission entry (id: {rp.permission_id}).")

        return permissions


class Roles(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relations
    users = relationship("Users", back_populates="role")
    role_permissions = relationship("RolePermissions", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Roles(role_id={self.id}, name={self.name})>"


class Permissions(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relations
    role_permissions = relationship("RolePermissions", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permissions(name={self.name})>"


class RolePermissions(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    role = relationship("Roles", back_populates="role_permissions")
    permission = relationship("Permissions", back_populates="role_permissions")

    def __repr__(self):
        return f"<RolePermissions(role_id={self.id}, permission_id={self.permission_id})>"


class AuditLogs(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec Users
    user = relationship("Users", back_populates="audit_log")

    # Indexation sur `user_id` et `action`
    __table_args__ = (
        Index('idx_user_id_auditlog', 'user_id'),
        Index('idx_action_auditlog', 'action'),
    )


class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(20), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    total_price = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default=OrderStatus.PENDING, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec Users
    user = relationship("Users", back_populates="order")

    # Relation avec OrderItems
    items = relationship("OrderItems", back_populates="order", lazy="selectin")

    # Relation avec Deliveries
    delivery = relationship("Deliveries", back_populates="order", uselist=False, lazy="selectin")

    def __repr__(self):
        return f"<Orders(order_number={self.order_number}, total_price={self.total_price}, status={self.status})>"


@event.listens_for(Orders, "after_insert")
def generate_order_number_hook(mapper, connection, target):
    if not target.order_number:  # Si `order_number` n'est pas défini
        order_number = generate_order_number(target.id, target.user_id)
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(order_number=order_number)
        )


class OrderItems(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(DECIMAL(10, 2), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec Orders
    order = relationship("Orders", back_populates="items")

    # Relation avec Products
    product = relationship("Products", back_populates="order_item")

    def __repr__(self):
        return (f"<OrderItems(order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity}, "
                f"price_per_unit={self.price_per_unit})>")


class Deliveries(Base):
    __tablename__ = "deliveries"
    __table_args__ = (UniqueConstraint("order_id", name="uq_order_delivery"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    delivery_address = Column(String(255), nullable=False)
    delivery_status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relation avec Orders
    order = relationship("Orders", back_populates="delivery")

    def __repr__(self):
        return (f"<Deliveries(order_id={self.order_id}, delivery_address={self.delivery_address}, "
                f"delivery_status={self.delivery_status})>")


class Reports(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec l'utilisateur qui a généré le rapport
    generated_by_user = relationship("Users", back_populates="report")


class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    notification_type = Column(Enum(NotificationType), nullable=False,
                               default=NotificationType.INFO)  # Nouveau champ pour le type de notification
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relation avec l'utilisateur
    user = relationship("Users", back_populates="notification")

    # Indexation sur `user_id` et `notification_type`
    __table_args__ = (
        Index('idx_user_id_notifications', 'user_id'),
        Index('idx_notification_type', 'notification_type'),
    )


class StockMovements(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relations
    product = relationship("Products", back_populates="stock_movement")
    user = relationship("Users", back_populates="stock_movement")


# Ajouter un index sur les colonnes 'user_id' et 'product_id'
Index('idx_user_id', Users.id)  # Exemple sur le modèle Users
Index('idx_product_id', Products.id)  # Exemple sur le modèle Products
# Index('idx_user_id_notifications', Notifications.user_id)  # Exemple sur le modèle Notifications
Index('idx_product_id_stock_movements', StockMovements.product_id)  # Exemple sur le modèle StockMovements
