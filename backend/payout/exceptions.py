class InvalidStateTransitionError(Exception):
    """Raised when a payout state change violates the state machine."""
    def __init__(self, payout_id: str, from_status: str, to_status: str):
        super().__init__(
            f"Illegal transition for payout {payout_id}: {from_status} → {to_status}"
        )
        self.payout_id = payout_id
        self.from_status = from_status
        self.to_status = to_status


class PayoutNotFoundError(Exception):
    def __init__(self, payout_id: str):
        super().__init__(f"Payout not found: {payout_id}")