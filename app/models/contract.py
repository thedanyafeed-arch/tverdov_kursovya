from sqlmodel import Field, Relationship
from typing import Optional
from .base import CamelModel
from .real_estate_object import RealEstateObject
from .user import User

class Contract(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    real_estate_object_id: int = Field(foreign_key="realestateobject.id")
    user_id: int = Field(foreign_key="user.id")      # покупатель
    manager_id: int = Field(foreign_key="user.id")   # менеджер
    contract_date: str
    status: str  # 'создан', 'подписан'
    generated_file_path: str | None = None
    created_at: Optional[str] = None

    real_estate_object: RealEstateObject = Relationship(back_populates="contracts")
    user: User = Relationship(sa_relationship_kwargs={"foreign_keys": "Contract.user_id"})
    manager: User = Relationship(sa_relationship_kwargs={"foreign_keys": "Contract.manager_id"})