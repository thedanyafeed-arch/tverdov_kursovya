from sqlmodel import Field
from .base import CamelModel

class PropertyType(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)  # 'квартира', 'дом', 'коммерческая недвижимость'