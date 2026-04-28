from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from merchant.routes import router as merchant_router
from ledger.routes import router as ledger_router
from payout.routes import router as payout_router

app = FastAPI()

allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchant_router)
app.include_router(ledger_router)
app.include_router(payout_router)