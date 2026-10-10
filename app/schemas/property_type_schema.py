from pydantic import Field
from app.models.base import CamelModel


class PropertyTypeCreate(CamelModel):
    name: str = Field(min_length=1, max_length=120)


class PropertyTypeUpdate(CamelModel):
    name: str = Field(min_length=1, max_length=120)

    model_config = {"extra": "forbid"}
