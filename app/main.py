from fastapi import FastAPI
from app.routers import categories, auth, roles, users, admin, products
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Stock Management System API is running"}


@app.get('/healthy')
async def healthy():
    return {'status': 'Healthy'}


app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
