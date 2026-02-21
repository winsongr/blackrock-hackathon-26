from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.state
from app.api.v1.routes import performance, returns, transactions
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/blackrock/challenge/v1"

app.include_router(transactions.router, prefix=PREFIX)
app.include_router(returns.router, prefix=PREFIX)
app.include_router(performance.router, prefix=PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy"}
