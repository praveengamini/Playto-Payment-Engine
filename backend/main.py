from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from core.config import settings
from db.session import engine
from merchant.routes import router as merchant_router
from ledger.routes import router as ledger_router
from payout.routes import router as payout_router

app = FastAPI()

allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def verify_postgres_connection() -> None:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"PostgreSQL connection check failed at startup: {e}") from e


app.include_router(merchant_router)
app.include_router(ledger_router)
app.include_router(payout_router)