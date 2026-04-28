import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from idempotency.exceptions import InvalidIdempotencyRecordError
from idempotency.repository import create_idempotency_record, get_idempotency_record
from payout.schema import PayoutResponse


async def check_idempotency(
    session: AsyncSession, merchant_id: str, idempotency_key: str
) -> PayoutResponse | None:
    record = await get_idempotency_record(session, merchant_id, idempotency_key)
    if record is None:
        return None
    try:
        payload = json.loads(record.response_json)
        return PayoutResponse.model_validate(payload)
    except Exception as exc:
        raise InvalidIdempotencyRecordError(merchant_id, idempotency_key) from exc


async def store_idempotency(
    session: AsyncSession,
    merchant_id: str,
    idempotency_key: str,
    response: PayoutResponse,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.IDEMPOTENCY_TTL_SECONDS
    )
    await create_idempotency_record(
        session=session,
        merchant_id=merchant_id,
        idempotency_key=idempotency_key,
        response_json=response.model_dump_json(),
        expires_at=expires_at,
    )
