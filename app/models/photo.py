from sqlmodel import Field, Relationship
from typing import Optional
from .base import CamelModel
from .real_estate_object import RealEstateObject

class Photo(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    real_estate_object_id: int = Field(foreign_key="realestateobject.id")
    file_path: str
    filename: str
    uploaded_at: Optional[str] = None

    real_estate_object: RealEstateObject = Relationship(back_populates="photos")