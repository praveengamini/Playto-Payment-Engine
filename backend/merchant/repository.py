from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from merchant.model import Merchant


async def get_merchant_by_id(session: AsyncSession, merchant_id: str) -> Merchant | None:
    result = await session.execute(
        select(Merchant).where(Merchant.id == merchant_id)
    )
    return result.scalar_one_or_none()


async def get_all_merchants(session: AsyncSession) -> list[Merchant]:
    result = await session.execute(select(Merchant).order_by(Merchant.created_at))
    return list(result.scalars().all())