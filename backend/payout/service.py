"""
payout/service.py — The most critical file in the engine.

Key guarantees enforced here:
1. SELECT FOR UPDATE on the merchant row prevents concurrent overdrafts.
2. Balance is computed INSIDE the locked transaction — never outside.
3. Idempotency check happens before the lock to avoid holding the lock
   longer than necessary, but the payout creation is inside the lock.
4. State machine transitions validated before every status update.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from merchant.model import Merchant
from merchant.exceptions import MerchantNotFoundError
from payout.model import Payout
from payout.repository import (
    create_payout,
    get_payout_by_id,
    get_payouts_by_merchant,
    transition_payout_status,
)
from payout.schema import PayoutResponse
from payout.exceptions import InvalidStateTransitionError, PayoutNotFoundError
from ledger.repository import get_available_balance_for_update
from ledger.service import record_hold, record_hold_release, record_debit
from ledger.exceptions import InsufficientBalanceError
from idempotency.service import check_idempotency, store_idempotency
from core.constants import PayoutStatus, is_legal_transition


async def request_payout(
    session: AsyncSession,
    merchant_id: str,
    amount_paise: int,
    bank_account_id: str,
    idempotency_key: str,
) -> PayoutResponse:
    """
    Create a payout request with full safety guarantees.

    CONCURRENCY SAFETY APPROACH:
    -----------------------------
    We lock the merchant row using SELECT ... FOR UPDATE.
    PostgreSQL will block any competing transaction that tries to lock
    the same row until we commit. This means:

        T1: locks merchant row, reads balance=10000, checks 6000 < 10000 → OK
        T2: blocks on lock (waiting for T1 to commit)
        T1: inserts HOLD for 6000, commits → balance now 4000
        T2: unblocks, reads balance=4000, checks 6000 > 4000 → REJECTED

    Without the lock, T2 could read stale balance=10000 before T1 commits
    and both would succeed, overdrawing the account.
    """


    existing = await check_idempotency(session, merchant_id, idempotency_key)
    if existing is not None:
        return existing






    result = await session.execute(
        select(Merchant)
        .where(Merchant.id == merchant_id)
        .with_for_update()
    )
    merchant = result.scalar_one_or_none()
    if merchant is None:
        raise MerchantNotFoundError(merchant_id)


    existing_after_lock = await check_idempotency(session, merchant_id, idempotency_key)
    if existing_after_lock is not None:
        return existing_after_lock




    available = await get_available_balance_for_update(session, merchant_id)
    if available < amount_paise:
        raise InsufficientBalanceError(available, amount_paise)


    payout = await create_payout(
        session,
        merchant_id=merchant_id,
        amount_paise=amount_paise,
        bank_account_id=bank_account_id,
        idempotency_key=idempotency_key,
    )


    await record_hold(
        session,
        merchant_id=merchant_id,
        amount_paise=amount_paise,
        payout_id=payout.id,
    )


    response = PayoutResponse.model_validate(payout)
    await store_idempotency(session, merchant_id, idempotency_key, response)

    return response


async def transition_status(
    session: AsyncSession,
    payout_id: str,
    new_status: PayoutStatus,
    increment_attempt: bool = False,
) -> PayoutResponse:
    """
    Advance payout through the state machine.

    ILLEGAL TRANSITIONS ARE BLOCKED HERE.
    The state machine is enforced at the application layer.
    PostgreSQL constraints enforce at DB layer via a CHECK constraint would be
    ideal too, but application enforcement is sufficient given all writes go
    through this function.
    """
    payout = await get_payout_by_id(session, payout_id)
    if payout is None:
        raise PayoutNotFoundError(payout_id)

    current = PayoutStatus(payout.status)




    if not is_legal_transition(current, new_status):
        raise InvalidStateTransitionError(payout_id, current.value, new_status.value)

    updated = await transition_payout_status(
        session,
        payout_id=payout_id,
        new_status=new_status,
        increment_attempt=increment_attempt,
    )
    return PayoutResponse.model_validate(updated)


async def complete_payout(session: AsyncSession, payout_id: str) -> PayoutResponse:
    """
    Mark payout as COMPLETED and convert HOLD → DEBIT atomically.
    Both the status update and the ledger debit happen in the same transaction.
    """
    payout = await get_payout_by_id(session, payout_id)
    if payout is None:
        raise PayoutNotFoundError(payout_id)

    response = await transition_status(session, payout_id, PayoutStatus.COMPLETED)


    await record_debit(
        session,
        merchant_id=payout.merchant_id,
        amount_paise=payout.amount_paise,
        payout_id=payout_id,
    )

    return response


async def fail_payout(session: AsyncSession, payout_id: str) -> PayoutResponse:
    """
    Mark payout as FAILED and release the held funds — atomically.

    ATOMICITY GUARANTEE:
    The hold release and the status update happen in the same database
    transaction. If either fails, both are rolled back. This means we
    can never end up in a state where funds are held but the payout
    shows as failed (or vice versa).
    """
    payout = await get_payout_by_id(session, payout_id)
    if payout is None:
        raise PayoutNotFoundError(payout_id)


    response = await transition_status(session, payout_id, PayoutStatus.FAILED)


    await record_hold_release(
        session,
        merchant_id=payout.merchant_id,
        amount_paise=payout.amount_paise,
        payout_id=payout_id,
    )

    return response


async def list_merchant_payouts(
    session: AsyncSession, merchant_id: str, limit: int = 50
) -> list[PayoutResponse]:
    payouts = await get_payouts_by_merchant(session, merchant_id, limit)
    return [PayoutResponse.model_validate(p) for p in payouts]


async def get_payout(session: AsyncSession, payout_id: str) -> PayoutResponse:
    payout = await get_payout_by_id(session, payout_id)
    if payout is None:
        raise PayoutNotFoundError(payout_id)
    return PayoutResponse.model_validate(payout)