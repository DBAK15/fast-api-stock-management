from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routers import categories, auth, roles, users, admin, products, orders, orderItems, deliveries, permissions
from .logger import logger

Base.metadata.create_all(bind=engine)

app = FastAPI()
logger.info('Starting StockManagement App')

# app.middleware("http")(log_request_response)
# app.add_middleware(log_request_response)
# app.add_middleware(
#     LoggingMiddleware,
#     get_db=get_db,
#     get_user=get_current_user,
# )


@app.get("/")
def read_root():
    return {"message": "Stock Management System API is running"}


@app.get('/healthy')
async def healthy():
    return {'status': 'Healthy'}


app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(orderItems.router)
app.include_router(deliveries.router)

