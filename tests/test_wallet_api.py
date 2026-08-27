import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app


def get_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


async def test_get_wallet(wallet_id):
    async with get_client() as client:
        response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 200
    assert response.json() == {
        "wallet_uuid": str(wallet_id),
        "balance": 10_000,
    }


async def test_get_missing_wallet():
    wallet_id = uuid.uuid4()

    async with get_client() as client:
        response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


async def test_deposit(wallet_id):
    async with get_client() as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "DEPOSIT",
                "amount": 1000,
            },
        )

    assert response.status_code == 200
    assert response.json()["balance"] == 11_000


async def test_withdraw(wallet_id):
    async with get_client() as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "WITHDRAW",
                "amount": 500,
            },
        )

    assert response.status_code == 200
    assert response.json()["balance"] == 9_500


async def test_insufficient_funds(wallet_id):
    async with get_client() as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "WITHDRAW",
                "amount": 20_000,
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient funds"


async def test_negative_amount(wallet_id):
    async with get_client() as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "DEPOSIT",
                "amount": -1,
            },
        )

    assert response.status_code == 422


async def test_invalid_operation_type(wallet_id):
    async with get_client() as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={
                "operation_type": "INVALID",
                "amount": 100,
            },
        )

    assert response.status_code == 422
