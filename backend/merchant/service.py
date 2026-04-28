from sqlalchemy.ext.asyncio import AsyncSession

from merchant.model import Merchant
from merchant.repository import get_merchant_by_id, get_all_merchants
from merchant.exceptions import MerchantNotFoundError
from merchant.schema import MerchantBalanceResponse
from ledger.repository import get_balance_breakdown


async def fetch_merchant(session: AsyncSession, merchant_id: str) -> Merchant:
    merchant = await get_merchant_by_id(session, merchant_id)
    if not merchant:
        raise MerchantNotFoundError(merchant_id)
    return merchant


async def fetch_all_merchants(session: AsyncSession) -> list[Merchant]:
    return await get_all_merchants(session)


async def fetch_merchant_balance(
    session: AsyncSession, merchant_id: str
) -> MerchantBalanceResponse:
    await fetch_merchant(session, merchant_id)
    return await get_balance_breakdown(session, merchant_id)