import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OperationType, Wallet, WalletOperation
from app.services.exceptions import (
    IdempotencyConflictError,
    InsufficientFundsError,
    WalletNotFoundError,
)
from app.services.types import WalletBalanceResult

logger = logging.getLogger(__name__)


async def get_wallet(
    session: AsyncSession,
    wallet_id: uuid.UUID,
) -> Wallet:
    wallet = await session.get(Wallet, wallet_id)

    if wallet is None:
        logger.warning(
            "wallet_not_found wallet_id=%s",
            wallet_id,
        )
        raise WalletNotFoundError

    return wallet


async def get_idempotent_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    idempotency_key: str,
) -> WalletOperation | None:
    result = await session.execute(
        select(WalletOperation).where(
            WalletOperation.wallet_id == wallet_id,
            WalletOperation.idempotency_key == idempotency_key,
        )
    )
    return result.scalar_one_or_none()


def validate_idempotent_operation(
    operation: WalletOperation,
    operation_type: OperationType,
    amount: int,
) -> None:
    if operation.operation_type != operation_type.value or operation.amount != amount:
        logger.warning(
            "idempotency_conflict wallet_id=%s key=%s",
            operation.wallet_id,
            operation.idempotency_key,
        )
        raise IdempotencyConflictError


async def perform_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: int,
    idempotency_key: str | None = None,
) -> WalletBalanceResult:
    async with session.begin():
        if idempotency_key is not None:
            existing_operation = await get_idempotent_operation(
                session,
                wallet_id,
                idempotency_key,
            )

            if existing_operation is not None:
                validate_idempotent_operation(
                    existing_operation,
                    operation_type,
                    amount,
                )

                logger.info(
                    "idempotent_operation_replayed wallet_id=%s operation=%s amount=%s",
                    wallet_id,
                    operation_type.value,
                    amount,
                )

                return WalletBalanceResult(
                    wallet_id=wallet_id,
                    balance=existing_operation.balance_after,
                )

        result = await session.execute(
            select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        )
        wallet = result.scalar_one_or_none()

        if wallet is None:
            logger.warning(
                "wallet_not_found wallet_id=%s",
                wallet_id,
            )
            raise WalletNotFoundError

        if idempotency_key is not None:
            existing_operation = await get_idempotent_operation(
                session,
                wallet_id,
                idempotency_key,
            )

            if existing_operation is not None:
                validate_idempotent_operation(
                    existing_operation,
                    operation_type,
                    amount,
                )

                logger.info(
                    "idempotent_operation_replayed wallet_id=%s operation=%s amount=%s",
                    wallet_id,
                    operation_type.value,
                    amount,
                )

                return WalletBalanceResult(
                    wallet_id=wallet_id,
                    balance=existing_operation.balance_after,
                )

        if operation_type == OperationType.WITHDRAW:
            if wallet.balance < amount:
                logger.warning(
                    "insufficient_funds wallet_id=%s amount=%s balance=%s",
                    wallet.id,
                    amount,
                    wallet.balance,
                )
                raise InsufficientFundsError

            wallet.balance -= amount
        else:
            wallet.balance += amount

        operation = WalletOperation(
            wallet_id=wallet.id,
            operation_type=operation_type.value,
            amount=amount,
            balance_after=wallet.balance,
            idempotency_key=idempotency_key,
        )

        session.add(operation)
        await session.flush()

        logger.info(
            "wallet_operation_completed "
            "wallet_id=%s operation=%s "
            "amount=%s balance_after=%s",
            wallet.id,
            operation_type.value,
            amount,
            wallet.balance,
        )

        return WalletBalanceResult(
            wallet_id=wallet.id,
            balance=wallet.balance,
        )
