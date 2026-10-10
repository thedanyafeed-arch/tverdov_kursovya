from pydantic import BaseModel
from app.models.base import CamelModel

class ContractResponse(CamelModel):
    id: int
    real_estate_object_id: int
    user_id: int
    manager_id: int
    contract_date: str
    status: str
    generated_file_path: str | None = None
    created_at: str | None = None


class ContractUpdate(CamelModel):
    status: str | None = None
    contract_date: str | None = None

    model_config = {"extra": "forbid"}


class ContractFullUpdate(CamelModel):
    real_estate_object_id: int
    user_id: int
    manager_id: int
    contract_date: str
    status: str

    model_config = {"extra": "forbid"}