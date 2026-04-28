from datetime import datetime, timedelta, timezone

from core.config import settings


def next_retry_delay_seconds(attempt_count: int) -> int:
    """
    Exponential backoff in seconds: 2, 4, 8.
    attempt_count is the number of attempts already made.
    """
    return 2 ** max(1, attempt_count)


def processing_deadline() -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        seconds=settings.PAYOUT_PROCESSING_TIMEOUT_SECONDS
    )
