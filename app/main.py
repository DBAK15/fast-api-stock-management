from fastapi import FastAPI
from app.routers import products
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(products.router, prefix="/api/v1/products", tags=["products"])

@app.get("/")
def read_root():
    return {"message": "Stock Management System API is running"}
