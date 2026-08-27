import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(Base):
    __tablename__ = "wallet_operations"

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_wallet_operations_amount_positive",
        ),
        CheckConstraint(
            "balance_after >= 0",
            name="ck_wallet_operations_balance_non_negative",
        ),
        CheckConstraint(
            "operation_type IN ('DEPOSIT', 'WITHDRAW')",
            name="ck_wallet_operations_type",
        ),
        UniqueConstraint(
            "wallet_id",
            "idempotency_key",
            name="uq_wallet_operations_wallet_idempotency_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    operation_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    balance_after: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
