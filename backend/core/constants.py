from enum import Enum


class LedgerEntryType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    HOLD = "hold"
    HOLD_RELEASE = "hold_release"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"





LEGAL_TRANSITIONS: dict[PayoutStatus, set[PayoutStatus]] = {
    PayoutStatus.PENDING:     {PayoutStatus.PROCESSING},
    PayoutStatus.PROCESSING:  {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
    PayoutStatus.COMPLETED:   set(),
    PayoutStatus.FAILED:      set(),
}


def is_legal_transition(from_status: PayoutStatus, to_status: PayoutStatus) -> bool:
    """Return True if the state transition is allowed."""
    return to_status in LEGAL_TRANSITIONS.get(from_status, set())