import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_concurrent_deposits(wallet_id):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        async def deposit(index: int):
            return await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                headers={
                    "Idempotency-Key": f"deposit-{index}",
                },
                json={
                    "operation_type": "DEPOSIT",
                    "amount": 100,
                },
            )

        responses = await asyncio.gather(*(deposit(i) for i in range(20)))

        final_response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert all(response.status_code == 200 for response in responses)
    assert final_response.status_code == 200
    assert final_response.json()["balance"] == 12_000


async def test_concurrent_withdrawals_do_not_overdraw(wallet_id):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        async def withdraw(index: int):
            return await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                headers={
                    "Idempotency-Key": f"withdraw-{index}",
                },
                json={
                    "operation_type": "WITHDRAW",
                    "amount": 7000,
                },
            )

        first, second = await asyncio.gather(
            withdraw(1),
            withdraw(2),
        )

        final_response = await client.get(f"/api/v1/wallets/{wallet_id}")

    status_codes = sorted(
        [
            first.status_code,
            second.status_code,
        ]
    )

    assert status_codes == [200, 409]
    assert final_response.status_code == 200
    assert final_response.json()["balance"] == 3000
