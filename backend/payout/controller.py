from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ledger.exceptions import InsufficientBalanceError
from merchant.exceptions import MerchantNotFoundError
from payout.exceptions import InvalidStateTransitionError, PayoutNotFoundError
from payout.schema import PayoutCreateRequest, PayoutResponse
from payout.service import get_payout, list_merchant_payouts, request_payout
from workers.payout_tasks import process_pending_payouts


async def create_payout_request(
    session: AsyncSession,
    merchant_id: str,
    payload: PayoutCreateRequest,
    idempotency_key: str,
) -> PayoutResponse:
    try:
        payout_response: PayoutResponse
        async with session.begin():
            payout_response = await request_payout(
                session=session,
                merchant_id=merchant_id,
                amount_paise=payload.amount_paise,
                bank_account_id=payload.bank_account_id,
                idempotency_key=idempotency_key,
            )



        try:
            process_pending_payouts.delay()
        except Exception:
            pass
        return payout_response
    except MerchantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def get_merchant_payouts(
    session: AsyncSession, merchant_id: str, limit: int = 50
) -> list[PayoutResponse]:
    return await list_merchant_payouts(session=session, merchant_id=merchant_id, limit=limit)


async def get_one_payout(session: AsyncSession, payout_id: str) -> PayoutResponse:
    try:
        return await get_payout(session, payout_id)
    except PayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
