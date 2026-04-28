class InsufficientBalanceError(Exception):
    def __init__(self, available: int, requested: int):
        super().__init__(
            f"Insufficient balance. Available: {available} paise, Requested: {requested} paise"
        )
        self.available = available
        self.requested = requested