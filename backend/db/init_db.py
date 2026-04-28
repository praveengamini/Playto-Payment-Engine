"""
Run once to create all tables and seed demo data.

Usage:
    uv run python -m db.init_db
"""
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from db.base import Base
from db.session import engine, AsyncSessionLocal


from merchant.model import Merchant
from ledger.model import LedgerEntry
from payout.model import Payout
from idempotency.model import IdempotencyRecord
from core.constants import LedgerEntryType


SEED_MERCHANTS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Arjun Designs",
        "email": "arjun@arjundesigns.in",
        "bank_account_id": "BANK-ARJUN-001",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Priya Dev Studio",
        "email": "priya@priyadev.in",
        "bank_account_id": "BANK-PRIYA-001",
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "Coastal Exports Co",
        "email": "ops@coastalexports.in",
        "bank_account_id": "BANK-COASTAL-001",
    },
]


SEED_CREDITS = [

    ("11111111-1111-1111-1111-111111111111", 500_000, "Client payment - Acme Corp"),
    ("11111111-1111-1111-1111-111111111111", 250_000, "Client payment - Beta Ltd"),
    ("22222222-2222-2222-2222-222222222222", 1_000_000, "Invoice
    ("22222222-2222-2222-2222-222222222222", 300_000, "Invoice
    ("33333333-3333-3333-3333-333333333333", 750_000, "Shipment payment Q1"),
    ("33333333-3333-3333-3333-333333333333", 400_000, "Shipment payment Q2"),
]


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created.")


async def seed_data() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():

            result = await session.execute(text("SELECT COUNT(*) FROM merchants"))
            count = result.scalar()
            if count > 0:
                print("⚠️  Seed data already exists. Skipping.")
                return


            for m in SEED_MERCHANTS:
                await session.execute(
                    text(
                        """
                        INSERT INTO merchants (id, name, email, bank_account_id, created_at)
                        VALUES (:id, :name, :email, :bank_account_id, :created_at)
                        """
                    ),
                    {**m, "created_at": datetime.now(timezone.utc)},
                )


            for merchant_id, amount_paise, note in SEED_CREDITS:
                await session.execute(
                    text(
                        """
                        INSERT INTO ledger_entries
                            (id, merchant_id, entry_type, amount_paise, note, created_at)
                        VALUES
                            (:id, :merchant_id, :entry_type, :amount_paise, :note, :created_at)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "merchant_id": merchant_id,
                        "entry_type": LedgerEntryType.CREDIT.value,
                        "amount_paise": amount_paise,
                        "note": note,
                        "created_at": datetime.now(timezone.utc),
                    },
                )

    print("✅ Seed data inserted.")


async def main() -> None:
    await create_tables()
    await seed_data()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())