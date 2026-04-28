from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from idempotency.model import IdempotencyRecord


async def get_idempotency_record(
    session: AsyncSession, merchant_id: str, idempotency_key: str
) -> IdempotencyRecord | None:
    result = await session.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.merchant_id == merchant_id,
            IdempotencyRecord.idempotency_key == idempotency_key,
            IdempotencyRecord.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


async def create_idempotency_record(
    session: AsyncSession,
    merchant_id: str,
    idempotency_key: str,
    response_json: str,
    expires_at: datetime,
) -> IdempotencyRecord:
    record = IdempotencyRecord(
        merchant_id=merchant_id,
        idempotency_key=idempotency_key,
        response_json=response_json,
        expires_at=expires_at,
    )
    session.add(record)
    await session.flush()
    return record
