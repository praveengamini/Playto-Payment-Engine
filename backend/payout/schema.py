from datetime import datetime
from pydantic import BaseModel, field_validator


class PayoutCreateRequest(BaseModel):
    amount_paise: int
    bank_account_id: str

    @field_validator("amount_paise")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount_paise must be a positive integer")
        return v


class PayoutResponse(BaseModel):
    id: str
    merchant_id: str
    amount_paise: int
    bank_account_id: str
    status: str
    idempotency_key: str
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}