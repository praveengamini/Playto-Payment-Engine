from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import validate_idempotency_key
from db.session import get_db
from payout.controller import create_payout_request, get_merchant_payouts, get_one_payout
from payout.schema import PayoutCreateRequest, PayoutResponse

router = APIRouter(prefix="/api/v1/payouts", tags=["payouts"])


@router.post("", response_model=PayoutResponse)
async def request_new_payout(
    merchant_id: str,
    payload: PayoutCreateRequest,
    idempotency_key: str = Depends(validate_idempotency_key),
    session: AsyncSession = Depends(get_db),
):
    return await create_payout_request(session, merchant_id, payload, idempotency_key)


@router.get("", response_model=list[PayoutResponse])
async def list_payouts(
    merchant_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
):
    return await get_merchant_payouts(session, merchant_id, limit)


@router.get("/{payout_id}", response_model=PayoutResponse)
async def get_payout_by_id(payout_id: str, session: AsyncSession = Depends(get_db)):
    return await get_one_payout(session, payout_id)
