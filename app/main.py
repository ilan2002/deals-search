from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Deals Search",
    version="0.1.0",
    description="Deals from Amazon, Flipkart, Myntra and AJIO in one search.",
    lifespan=lifespan,
)
app.include_router(router)
