import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.main import app
from app.models import WalletOperation


async def test_idempotent_operation(wallet_id):
    headers = {
        "Idempotency-Key": "test-key-001",
    }

    payload = {
        "operation_type": "DEPOSIT",
        "amount": 1000,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            headers=headers,
            json=payload,
        )

        second = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            headers=headers,
            json=payload,
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["balance"] == 11_000
    assert second.json()["balance"] == 11_000


async def test_idempotency_conflict(wallet_id):
    headers = {
        "Idempotency-Key": "conflict-key",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            headers=headers,
            json={
                "operation_type": "DEPOSIT",
                "amount": 1000,
            },
        )

        second = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            headers=headers,
            json={
                "operation_type": "WITHDRAW",
                "amount": 500,
            },
        )

    assert first.status_code == 200
    assert second.status_code == 409


async def test_concurrent_idempotent_operation(wallet_id):
    headers = {
        "Idempotency-Key": "concurrent-same-key",
    }

    payload = {
        "operation_type": "DEPOSIT",
        "amount": 1000,
    }

    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        async def send_operation():
            return await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                headers=headers,
                json=payload,
            )

        first, second = await asyncio.gather(
            send_operation(),
            send_operation(),
        )

        final_response = await client.get(f"/api/v1/wallets/{wallet_id}")

    async with async_session_factory() as session:
        operations_count = await session.scalar(
            select(func.count())
            .select_from(WalletOperation)
            .where(
                WalletOperation.wallet_id == wallet_id,
                WalletOperation.idempotency_key == "concurrent-same-key",
            )
        )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["balance"] == 11_000
    assert second.json()["balance"] == 11_000

    assert final_response.status_code == 200
    assert final_response.json()["balance"] == 11_000

    assert operations_count == 1
