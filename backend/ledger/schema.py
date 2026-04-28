from datetime import datetime
from pydantic import BaseModel


class LedgerEntryResponse(BaseModel):
    id: str
    merchant_id: str
    entry_type: str
    amount_paise: int
    payout_id: str | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}