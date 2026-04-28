from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from payout.model import Payout
from core.constants import PayoutStatus


async def create_payout(
    session: AsyncSession,
    merchant_id: str,
    amount_paise: int,
    bank_account_id: str,
    idempotency_key: str,
) -> Payout:
    payout = Payout(
        merchant_id=merchant_id,
        amount_paise=amount_paise,
        bank_account_id=bank_account_id,
        idempotency_key=idempotency_key,
        status=PayoutStatus.PENDING.value,
    )
    session.add(payout)
    await session.flush()
    return payout


async def get_payout_by_id(session: AsyncSession, payout_id: str) -> Payout | None:
    result = await session.execute(
        select(Payout).where(Payout.id == payout_id)
    )
    return result.scalar_one_or_none()


async def get_payouts_by_merchant(
    session: AsyncSession,
    merchant_id: str,
    limit: int = 50,
) -> list[Payout]:
    result = await session.execute(
        select(Payout)
        .where(Payout.merchant_id == merchant_id)
        .order_by(Payout.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_pending_payouts(session: AsyncSession) -> list[Payout]:
    result = await session.execute(
        select(Payout).where(Payout.status == PayoutStatus.PENDING.value)
    )
    return list(result.scalars().all())


async def get_stuck_processing_payouts(
    session: AsyncSession, stuck_since: datetime
) -> list[Payout]:
    """
    Return payouts stuck in PROCESSING state since before `stuck_since`.
    These are candidates for retry.
    """
    result = await session.execute(
        select(Payout).where(
            Payout.status == PayoutStatus.PROCESSING.value,
            Payout.last_attempted_at <= stuck_since,
        )
    )
    return list(result.scalars().all())


async def transition_payout_status(
    session: AsyncSession,
    payout_id: str,
    new_status: PayoutStatus,
    increment_attempt: bool = False,
) -> Payout | None:
    """
    Update payout status. Optionally increment attempt_count.
    Returns updated payout or None if not found.
    """
    values: dict = {
        "status": new_status.value,
        "updated_at": datetime.now(timezone.utc),
    }
    if increment_attempt:

        values["attempt_count"] = Payout.attempt_count + 1
        values["last_attempted_at"] = datetime.now(timezone.utc)
    if new_status in (PayoutStatus.COMPLETED, PayoutStatus.FAILED):
        values["completed_at"] = datetime.now(timezone.utc)

    await session.execute(
        update(Payout).where(Payout.id == payout_id).values(**values)
    )
    return await get_payout_by_id(session, payout_id)