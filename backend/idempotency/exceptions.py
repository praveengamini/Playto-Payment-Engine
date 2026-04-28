class DuplicateIdempotencyKeyError(Exception):
    def __init__(self, merchant_id: str, key: str):
        super().__init__(
            f"Idempotency key already used for merchant {merchant_id}: {key}"
        )


class InvalidIdempotencyRecordError(Exception):
    def __init__(self, merchant_id: str, key: str):
        super().__init__(f"Corrupt idempotency record for merchant {merchant_id}: {key}")
