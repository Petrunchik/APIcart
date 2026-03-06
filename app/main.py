from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import categories, products, users, reviews, cart, orders
from .log import log_middleware

app = FastAPI(
    title="APIcart",
    version="0.0.1"
)
app.middleware("http")(log_middleware)


app.mount("/media", StaticFiles(directory="media"), name="media")
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)