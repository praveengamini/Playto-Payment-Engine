from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from merchant.controller import get_merchant, list_merchants, get_balance
from merchant.schema import MerchantResponse, MerchantBalanceResponse

router = APIRouter(prefix="/api/v1/merchants", tags=["merchants"])


@router.get("", response_model=list[MerchantResponse])
async def list_all_merchants(session: AsyncSession = Depends(get_db)):
    try:
        return await list_merchants(session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "merchant_list_failed", "message": str(e)},
        )


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_one_merchant(merchant_id: str, session: AsyncSession = Depends(get_db)):
    try:
        return await get_merchant(session, merchant_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "merchant_fetch_failed", "message": str(e)},
        )


@router.get("/{merchant_id}/balance", response_model=MerchantBalanceResponse)
async def get_merchant_balance(
    merchant_id: str, session: AsyncSession = Depends(get_db)
):
    try:
        return await get_balance(session, merchant_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "merchant_balance_failed", "message": str(e)},
        )