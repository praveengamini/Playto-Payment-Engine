import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from core.constants import PayoutStatus


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bank_account_id: Mapped[str] = mapped_column(String(100), nullable=False)


    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PayoutStatus.PENDING.value,
        server_default=PayoutStatus.PENDING.value,
    )


    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)


    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant", back_populates="payouts"
    )

    __table_args__ = (

        Index("ix_payouts_status", "status"),
        Index("ix_payouts_merchant_id", "merchant_id"),

        Index("ix_payouts_merchant_status", "merchant_id", "status"),
    )