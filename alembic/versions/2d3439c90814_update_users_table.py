"""update Users Table

Revision ID: 2d3439c90814
Revises: 
Create Date: 2025-01-14 15:35:43.677540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2d3439c90814'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_notification_type', table_name='notifications')
    op.drop_index('idx_user_id_notifications', table_name='notifications')
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_permissions_id', table_name='permissions')
    op.drop_table('permissions')
    op.drop_index('ix_reports_id', table_name='reports')
    op.drop_table('reports')
    op.drop_index('ix_categories_id', table_name='categories')
    op.drop_table('categories')
    op.drop_index('idx_user_id', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_order_items_id', table_name='order_items')
    op.drop_table('order_items')
    op.drop_index('idx_product_id', table_name='products')
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')
    op.drop_index('idx_product_id_stock_movements', table_name='stock_movements')
    op.drop_index('ix_stock_movements_id', table_name='stock_movements')
    op.drop_table('stock_movements')
    op.drop_index('ix_roles_id', table_name='roles')
    op.drop_table('roles')
    op.drop_index('ix_orders_id', table_name='orders')
    op.drop_table('orders')
    op.drop_index('idx_action_auditlog', table_name='audit_logs')
    op.drop_index('idx_user_id_auditlog', table_name='audit_logs')
    op.drop_index('ix_audit_logs_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('audit_logs',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('action', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('timestamp', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('details', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ip_address', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('endpoint', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('action_details', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='audit_logs_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='audit_logs_pkey'),
    sa.UniqueConstraint('action', name='audit_logs_action_key')
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'], unique=False)
    op.create_index('idx_user_id_auditlog', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_action_auditlog', 'audit_logs', ['action'], unique=False)
    op.create_table('orders',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('orders_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='orders_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='orders_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_orders_id', 'orders', ['id'], unique=False)
    op.create_table('roles',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('roles_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='roles_pkey'),
    sa.UniqueConstraint('name', name='roles_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_roles_id', 'roles', ['id'], unique=False)
    op.create_table('stock_movements',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('quantity', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('movement_type', postgresql.ENUM('IN', 'OUT', name='movementtype'), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='stock_movements_product_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='stock_movements_pkey')
    )
    op.create_index('ix_stock_movements_id', 'stock_movements', ['id'], unique=False)
    op.create_index('idx_product_id_stock_movements', 'stock_movements', ['product_id'], unique=False)
    op.create_table('products',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('products_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('stock_minimum', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('category_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='products_category_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='products_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('idx_product_id', 'products', ['id'], unique=False)
    op.create_table('order_items',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('order_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('price_per_unit', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='order_items_order_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='order_items_product_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='order_items_pkey')
    )
    op.create_index('ix_order_items_id', 'order_items', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('users_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='users_role_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='users_pkey'),
    sa.UniqueConstraint('email', name='users_email_key'),
    sa.UniqueConstraint('username', name='users_username_key'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('idx_user_id', 'users', ['id'], unique=False)
    op.create_table('categories',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='categories_pkey'),
    sa.UniqueConstraint('name', name='categories_name_key')
    )
    op.create_index('ix_categories_id', 'categories', ['id'], unique=False)
    op.create_table('reports',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('generated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('generated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['generated_by'], ['users.id'], name='reports_generated_by_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='reports_pkey')
    )
    op.create_index('ix_reports_id', 'reports', ['id'], unique=False)
    op.create_table('permissions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='permissions_role_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='permissions_pkey'),
    sa.UniqueConstraint('name', name='permissions_name_key')
    )
    op.create_index('ix_permissions_id', 'permissions', ['id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('message', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_read', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('notification_type', postgresql.ENUM('INFO', 'WARNING', 'ERROR', name='notificationtype'), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='notifications_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='notifications_pkey')
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    op.create_index('idx_user_id_notifications', 'notifications', ['user_id'], unique=False)
    op.create_index('idx_notification_type', 'notifications', ['notification_type'], unique=False)
    # ### end Alembic commands ###
