import uuid

import pytest
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import Wallet, WalletOperation


@pytest.fixture
async def wallet_id():
    wallet_uuid = uuid.uuid4()

    async with async_session_factory() as session:
        async with session.begin():
            session.add(
                Wallet(
                    id=wallet_uuid,
                    balance=10_000,
                )
            )

    yield wallet_uuid

    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(
                delete(WalletOperation).where(WalletOperation.wallet_id == wallet_uuid)
            )
            await session.execute(delete(Wallet).where(Wallet.id == wallet_uuid))
