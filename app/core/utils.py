import os
import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    folder_path = UPLOADS_DIR / folder
    folder_path.mkdir(exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{upload_file.filename.replace(' ', '_')}"
    file_path = folder_path / safe_filename
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())
    return str(file_path).replace("\\", "/")