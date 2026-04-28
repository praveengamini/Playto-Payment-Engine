from datetime import datetime
from pydantic import BaseModel, EmailStr


class MerchantResponse(BaseModel):
    id: str
    name: str
    email: str
    bank_account_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MerchantBalanceResponse(BaseModel):
    merchant_id: str
    available_paise: int
    held_paise: int
    total_credited_paise: int
    total_debited_paise: int