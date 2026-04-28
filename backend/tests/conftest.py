import uuid
from datetime import datetime, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from db.base import Base
from db.session import AsyncSessionLocal, engine
from ledger.model import LedgerEntry
from main import app
from merchant.model import Merchant
from payout.model import Payout
from idempotency.model import IdempotencyRecord


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture()
async def clean_db():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(IdempotencyRecord))
            await session.execute(delete(LedgerEntry))
            await session.execute(delete(Payout))
            await session.execute(delete(Merchant))
    yield


@pytest_asyncio.fixture()
async def api_client(clean_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture()
async def seeded_merchant(clean_db):
    merchant_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(
                Merchant(
                    id=merchant_id,
                    name="Concurrency Merchant",
                    email=f"{merchant_id[:8]}@example.com",
                    bank_account_id="BANK-TEST-001",
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                LedgerEntry(
                    id=str(uuid.uuid4()),
                    merchant_id=merchant_id,
                    entry_type="credit",
                    amount_paise=10_000,
                    created_at=datetime.now(timezone.utc),
                )
            )
    return merchant_id
