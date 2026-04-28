import asyncio
import random

from core.config import settings
from core.constants import PayoutStatus
from db.session import AsyncSessionLocal
from payout.repository import (
    get_pending_payouts,
    get_payout_by_id,
    get_stuck_processing_payouts,
)
from payout.service import complete_payout, fail_payout, transition_status
from workers.celery_app import celery_app
from workers.retry_handler import next_retry_delay_seconds, processing_deadline


def _simulate_bank_outcome() -> str:
    x = random.random()
    if x < settings.PAYOUT_SUCCESS_RATE:
        return "success"
    if x < settings.PAYOUT_SUCCESS_RATE + settings.PAYOUT_FAIL_RATE:
        return "failed"
    return "hang"


async def _process_pending_once() -> int:

    async with AsyncSessionLocal() as read_session:
        pending = await get_pending_payouts(read_session)
        pending_ids = [p.id for p in pending]


    for payout_id in pending_ids:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                current = await get_payout_by_id(session, payout_id)
                if current is None or current.status != PayoutStatus.PENDING.value:
                    continue
                await transition_status(
                    session=session,
                    payout_id=payout_id,
                    new_status=PayoutStatus.PROCESSING,
                    increment_attempt=True,
                )

        outcome = _simulate_bank_outcome()
        if outcome == "hang":
            continue

        async with AsyncSessionLocal() as session:
            async with session.begin():
                current = await get_payout_by_id(session, payout_id)
                if current is None or current.status != PayoutStatus.PROCESSING.value:
                    continue
                if outcome == "success":
                    await complete_payout(session, payout_id)
                else:
                    await fail_payout(session, payout_id)

    return len(pending_ids)


async def _retry_stuck_processing_once() -> int:
    async with AsyncSessionLocal() as read_session:
        stuck = await get_stuck_processing_payouts(read_session, processing_deadline())
        stuck_rows = [(p.id, p.attempt_count) for p in stuck]

    for payout_id, attempt_count in stuck_rows:
        if attempt_count >= settings.PAYOUT_MAX_RETRIES:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    current = await get_payout_by_id(session, payout_id)
                    if current is None or current.status != PayoutStatus.PROCESSING.value:
                        continue
                    await fail_payout(session, payout_id)
            continue

        countdown = next_retry_delay_seconds(attempt_count)
        process_pending_payouts.apply_async(countdown=countdown)

    return len(stuck_rows)


@celery_app.task(name="payouts.process_pending")
def process_pending_payouts() -> int:
    return asyncio.run(_process_pending_once())


@celery_app.task(name="payouts.retry_stuck")
def retry_stuck_processing_payouts() -> int:
    return asyncio.run(_retry_stuck_processing_once())
