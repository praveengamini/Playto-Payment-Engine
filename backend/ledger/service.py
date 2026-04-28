from sqlalchemy.ext.asyncio import AsyncSession

from ledger.repository import insert_ledger_entry, get_ledger_entries
from ledger.schema import LedgerEntryResponse
from core.constants import LedgerEntryType


async def record_hold(
    session: AsyncSession,
    merchant_id: str,
    amount_paise: int,
    payout_id: str,
) -> None:
    await insert_ledger_entry(
        session,
        merchant_id=merchant_id,
        entry_type=LedgerEntryType.HOLD,
        amount_paise=amount_paise,
        payout_id=payout_id,
        note=f"Funds held for payout {payout_id}",
    )


async def record_hold_release(
    session: AsyncSession,
    merchant_id: str,
    amount_paise: int,
    payout_id: str,
) -> None:
    await insert_ledger_entry(
        session,
        merchant_id=merchant_id,
        entry_type=LedgerEntryType.HOLD_RELEASE,
        amount_paise=amount_paise,
        payout_id=payout_id,
        note=f"Hold released — payout {payout_id} failed",
    )


async def record_debit(
    session: AsyncSession,
    merchant_id: str,
    amount_paise: int,
    payout_id: str,
) -> None:
    await insert_ledger_entry(
        session,
        merchant_id=merchant_id,
        entry_type=LedgerEntryType.DEBIT,
        amount_paise=amount_paise,
        payout_id=payout_id,
        note=f"Payout settled: {payout_id}",
    )


async def list_ledger_entries(
    session: AsyncSession, merchant_id: str, limit: int = 50
) -> list[LedgerEntryResponse]:
    entries = await get_ledger_entries(session, merchant_id, limit)
    return [LedgerEntryResponse.model_validate(e) for e in entries]