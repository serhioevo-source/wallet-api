import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.operation import OperationType


class WalletOperationRequest(BaseModel):
    operation_type: OperationType
    amount: int = Field(gt=0)


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    wallet_uuid: uuid.UUID
    balance: int
