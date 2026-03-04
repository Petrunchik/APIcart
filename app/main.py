from fastapi import FastAPI
from app.routers import categories, products, users, reviews, cart, orders

app = FastAPI(
    title="APIcart",
    version="0.0.1"
)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)