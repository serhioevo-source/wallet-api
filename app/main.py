from fastapi import FastAPI

from app.api.wallets import router as wallets_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Wallet API",
    version="1.0.0",
)

app.include_router(wallets_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
