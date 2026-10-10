from sqlmodel import Field
from .base import CamelModel

class Role(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # 'admin', 'manager', 'user'
    description: str | None = None