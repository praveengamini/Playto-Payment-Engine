from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from ledger.service import list_ledger_entries
from ledger.schema import LedgerEntryResponse

router = APIRouter(prefix="/api/v1/merchants", tags=["ledger"])


@router.get("/{merchant_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_merchant_ledger(
    merchant_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
):
    return await list_ledger_entries(session, merchant_id, limit)