from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from merchant.service import fetch_merchant, fetch_all_merchants, fetch_merchant_balance
from merchant.exceptions import MerchantNotFoundError
from merchant.schema import MerchantResponse, MerchantBalanceResponse


async def get_merchant(session: AsyncSession, merchant_id: str) -> MerchantResponse:
    try:
        merchant = await fetch_merchant(session, merchant_id)
        return MerchantResponse.model_validate(merchant)
    except MerchantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


async def list_merchants(session: AsyncSession) -> list[MerchantResponse]:
    merchants = await fetch_all_merchants(session)
    return [MerchantResponse.model_validate(m) for m in merchants]


async def get_balance(
    session: AsyncSession, merchant_id: str
) -> MerchantBalanceResponse:
    try:
        return await fetch_merchant_balance(session, merchant_id)
    except MerchantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))