from sqlmodel import Field, Relationship
from typing import Optional
from .base import CamelModel
from .role import Role

class User(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
    created_at: Optional[str] = None

    role_id: int = Field(foreign_key="role.id")
    role: Role = Relationship()