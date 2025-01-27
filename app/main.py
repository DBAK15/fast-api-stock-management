from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routers import categories, auth, roles, users, admin, products, orders, orderItems, deliveries, permissions, \
    stockMovements, reports, notifications
from .logging_config import setup_logger
from .middlewares import register_middleware

version = "v1.0.0"

description = """
Une API REST conçue pour la gestion des stocks 
avec des fonctionnalités telles que la gestion des utilisateurs, 
des rôles, des produits, des commandes, et bien plus
"""
version_prefix = f"/api/{version}"

app = FastAPI(
    title="Stock Management API",
    description=description,
    version=version,
    license_info={"name": "MIT License", "url": "https://opensource.org/license/mit"},
    contact={
        "name": "Bakarim Diomandé",
        "url": "https://github.com/DBAK15/fast-api-stock-management.git",
        "email": "bakarimdiomande05@gmail.com",
    },
    terms_of_service="httpS://example.com/tos",
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}/docs",
    redoc_url=f"{version_prefix}/redoc"
)
Base.metadata.create_all(bind=engine)
register_middleware(app)
# Configure the logger
logger = setup_logger("stockManagementLogger")
logger.info('Starting StockManagement App')


@app.on_event("startup")
async def startup_event():
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")


@app.get("/")
def read_root():
    return {"message": "Stock Management System API is running"}


@app.get('/healthy')
async def healthy():
    return {'status': 'Healthy'}


app.include_router(auth.router, prefix=f"{version_prefix}/auth", tags=["Auth"])
app.include_router(roles.router, prefix=f"{version_prefix}/roles", tags=["Roles"])
app.include_router(permissions.router, prefix=f"{version_prefix}/permissions", tags=["Permissions"])
app.include_router(users.router, prefix=f"{version_prefix}/users", tags=["Users"])
# app.include_router(admin.router, prefix=f"{version_prefix}/admin", tags=["Admin"])
app.include_router(auth.router, prefix=f"{version_prefix}/auth", tags=["Auth"])
app.include_router(categories.router, prefix=f"{version_prefix}/categories", tags=["Categories"])
app.include_router(products.router, prefix=f"{version_prefix}/products", tags=["Products"])
app.include_router(orders.router, prefix=f"{version_prefix}/orders", tags=["Orders"])
app.include_router(orderItems.router, prefix=f"{version_prefix}/orderItems", tags=["OrderItems"])
app.include_router(deliveries.router, prefix=f"{version_prefix}/deliveries", tags=["Deliveries"])
app.include_router(stockMovements.router, prefix=f"{version_prefix}/stockMovements", tags=["StockMovements"])
app.include_router(reports.router, prefix=f"{version_prefix}/reports", tags=["Reports"])
app.include_router(notifications.router, prefix=f"{version_prefix}/notifications", tags=["Notifications"])
