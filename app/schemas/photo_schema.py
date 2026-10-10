from pydantic import BaseModel
from app.models.base import CamelModel

class PhotoResponse(CamelModel):
    id: int
    real_estate_object_id: int
    file_path: str
    filename: str
    uploaded_at: str | None = None