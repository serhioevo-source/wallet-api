import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WalletBalanceResult:
    wallet_id: uuid.UUID
    balance: int
