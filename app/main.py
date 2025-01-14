from fastapi import FastAPI
from app.routers import products, categories
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


app.include_router(categories.router)
# app.include_router(products.router)
