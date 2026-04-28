import uuid
from fastapi import Header, HTTPException


def validate_idempotency_key(idempotency_key: str = Header(...)) -> str:
    """
    FastAPI dependency — extracts and validates the Idempotency-Key header.
    Must be a valid UUID v4.
    """
    try:
        parsed = uuid.UUID(idempotency_key, version=4)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail="Idempotency-Key must be a valid UUID v4.",
        )
    return str(parsed)