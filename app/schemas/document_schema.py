from pydantic import BaseModel
from app.models.base import CamelModel

class DocumentCreate(CamelModel):
    doc_type: str

class DocumentResponse(CamelModel):
    id: int
    real_estate_object_id: int
    file_path: str
    filename: str
    doc_type: str
    uploaded_at: str | None = None