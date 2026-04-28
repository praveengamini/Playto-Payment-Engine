"""
All balance arithmetic happens here — inside the database, not in Python.

WHY DATABASE AGGREGATION?
--------------------------
If we did:
    entries = await session.execute(select(LedgerEntry).where(...))
    balance = sum(e.amount_paise for e in entries.scalars())

…we'd load potentially thousands of rows into Python memory, and the sum
would be computed by the Python interpreter. This is both slow AND unsafe
under concurrency — two transactions reading the "same" rows can each
compute an outdated balance before either commits.

Instead we push SUM() into PostgreSQL where it is atomic within a transaction
and benefits from index-only scans on (merchant_id, entry_type).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text

from ledger.model import LedgerEntry
from merchant.schema import MerchantBalanceResponse
from core.constants import LedgerEntryType


async def get_balance_breakdown(
    session: AsyncSession, merchant_id: str
) -> MerchantBalanceResponse:
    """
    Single aggregation query that computes all balance components at once.

    available = SUM(credits) - SUM(debits) - SUM(holds) + SUM(hold_releases)
    held      = SUM(holds)   - SUM(hold_releases)

    Using conditional aggregation (CASE WHEN) so we hit the table once.
    """
    result = await session.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.entry_type == LedgerEntryType.CREDIT.value,
                         LedgerEntry.amount_paise),
                        else_=0,
                    )
                ),
                0,
            ).label("total_credit"),
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.entry_type == LedgerEntryType.DEBIT.value,
                         LedgerEntry.amount_paise),
                        else_=0,
                    )
                ),
                0,
            ).label("total_debit"),
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.entry_type == LedgerEntryType.HOLD.value,
                         LedgerEntry.amount_paise),
                        else_=0,
                    )
                ),
                0,
            ).label("total_hold"),
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.entry_type == LedgerEntryType.HOLD_RELEASE.value,
                         LedgerEntry.amount_paise),
                        else_=0,
                    )
                ),
                0,
            ).label("total_hold_release"),
        ).where(LedgerEntry.merchant_id == merchant_id)
    )

    row = result.one()
    total_credit: int = row.total_credit
    total_debit: int = row.total_debit
    total_hold: int = row.total_hold
    total_hold_release: int = row.total_hold_release

    held_paise = total_hold - total_hold_release
    available_paise = total_credit - total_debit - held_paise

    return MerchantBalanceResponse(
        merchant_id=merchant_id,
        available_paise=available_paise,
        held_paise=held_paise,
        total_credited_paise=total_credit,
        total_debited_paise=total_debit,
    )


async def get_available_balance_for_update(
    session: AsyncSession, merchant_id: str
) -> int:
    """
    Compute available balance INSIDE a SELECT FOR UPDATE transaction.

    This is called from payout/service.py after the merchant row is
    locked with SELECT FOR UPDATE. By computing the balance in the same
    transaction, we guarantee no other transaction can interleave a
    competing payout between our balance read and our hold write.

    Returns available balance in paise.
    """
    result = await session.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.entry_type == LedgerEntryType.CREDIT.value,
                         LedgerEntry.amount_paise),
                        (LedgerEntry.entry_type == LedgerEntryType.HOLD_RELEASE.value,
                         LedgerEntry.amount_paise),
                        (LedgerEntry.entry_type == LedgerEntryType.DEBIT.value,
                         -LedgerEntry.amount_paise),
                        (LedgerEntry.entry_type == LedgerEntryType.HOLD.value,
                         -LedgerEntry.amount_paise),
                        else_=0,
                    )
                ),
                0,
            )
        ).where(LedgerEntry.merchant_id == merchant_id)
    )
    return int(result.scalar())


async def insert_ledger_entry(
    session: AsyncSession,
    merchant_id: str,
    entry_type: LedgerEntryType,
    amount_paise: int,
    payout_id: str | None = None,
    note: str | None = None,
) -> LedgerEntry:
    entry = LedgerEntry(
        id=str(uuid.uuid4()),
        merchant_id=merchant_id,
        entry_type=entry_type.value,
        amount_paise=amount_paise,
        payout_id=payout_id,
        note=note,
        created_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    return entry


async def get_ledger_entries(
    session: AsyncSession,
    merchant_id: str,
    limit: int = 50,
) -> list[LedgerEntry]:
    result = await session.execute(
        select(LedgerEntry)
        .where(LedgerEntry.merchant_id == merchant_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())