import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class LedgerEntry(Base):
    """
    Immutable append-only ledger. Balance is NEVER stored — always derived.

    entry_type values:
        credit       — customer payment in (positive)
        debit        — payout settled (positive amount, subtracted in query)
        hold         — funds reserved on payout request (positive)
        hold_release — held funds returned on payout failure (positive)

    payout_id is nullable: credits have no linked payout.
    """

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)

    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payout_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("payouts.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant", back_populates="ledger_entries"
    )

    __table_args__ = (

        Index("ix_ledger_merchant_id", "merchant_id"),

        Index("ix_ledger_payout_id", "payout_id"),
    )