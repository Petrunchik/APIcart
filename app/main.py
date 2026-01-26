from fastapi import FastAPI
from app.routers import categories
from app.routers import products

app = FastAPI(
    title="APIcart",
    version="0.0.1"
)

app.include_router(categories.router)
app.include_router(products.router)