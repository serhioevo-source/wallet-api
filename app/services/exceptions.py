class WalletError(Exception):
    """Base exception for wallet business logic."""


class WalletNotFoundError(WalletError):
    """Raised when a wallet does not exist."""


class InsufficientFundsError(WalletError):
    """Raised when a wallet has insufficient funds."""


class IdempotencyConflictError(WalletError):
    """Raised when an idempotency key is reused with another request."""
