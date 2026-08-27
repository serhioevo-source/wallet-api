from fastapi import FastAPI

app = FastAPI(
    title="Wallet API",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
