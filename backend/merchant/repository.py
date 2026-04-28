import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from merchant.model import Merchant

logger = logging.getLogger(__name__)


async def get_merchant_by_id(
    session: AsyncSession, merchant_id: str
) -> Merchant | None:
    try:
        result = await session.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        return result.scalar_one_or_none()

    except Exception as e:
        logger.exception(f"Error fetching merchant with id: {merchant_id}")
        raise


async def get_all_merchants(session: AsyncSession) -> list[Merchant]:
    try:
        result = await session.execute(
            select(Merchant).order_by(Merchant.created_at)
        )
        return list(result.scalars().all())

    except Exception as e:
        logger.exception("Error fetching all merchants")
        raise