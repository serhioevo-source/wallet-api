import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.wallet import WalletOperationRequest, WalletResponse
from app.services.exceptions import (
    IdempotencyConflictError,
    InsufficientFundsError,
    WalletNotFoundError,
)
from app.services.wallet import get_wallet, perform_operation

router = APIRouter(
    prefix="/api/v1/wallets",
    tags=["wallets"],
)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        max_length=128,
    ),
]


def make_wallet_response(
    wallet_uuid: uuid.UUID,
    balance: int,
) -> WalletResponse:
    return WalletResponse(
        wallet_uuid=wallet_uuid,
        balance=balance,
    )


@router.get(
    "/{wallet_uuid}",
    response_model=WalletResponse,
)
async def read_wallet(
    wallet_uuid: uuid.UUID,
    session: DbSession,
) -> WalletResponse:
    try:
        wallet = await get_wallet(session, wallet_uuid)
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        ) from exc

    return make_wallet_response(
        wallet_uuid=wallet.id,
        balance=wallet.balance,
    )


@router.post(
    "/{wallet_uuid}/operation",
    response_model=WalletResponse,
)
async def change_wallet_balance(
    wallet_uuid: uuid.UUID,
    operation: WalletOperationRequest,
    session: DbSession,
    idempotency_key: IdempotencyKey = None,
) -> WalletResponse:
    try:
        result = await perform_operation(
            session=session,
            wallet_id=wallet_uuid,
            operation_type=operation.operation_type,
            amount=operation.amount,
            idempotency_key=idempotency_key,
        )
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        ) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient funds",
        ) from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key already used for another operation",
        ) from exc

    return make_wallet_response(
        wallet_uuid=result.wallet_id,
        balance=result.balance,
    )
