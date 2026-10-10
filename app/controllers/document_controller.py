from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from app.models.document import Document
from app.core.utils import save_upload_file
import os

class DocumentController:
    @staticmethod
    def upload_document(property_id: int, file, doc_type: str, session: Session):
        # Проверяем, существует ли объект недвижимости
        from app.models.real_estate_object import RealEstateObject
        property_obj = session.get(RealEstateObject, property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Объект недвижимости с id={property_id} не найден"
            )
        
        file_path = save_upload_file(file, "documents")
        doc = Document(
            real_estate_object_id=property_id,
            file_path=file_path,
            filename=file.filename,
            doc_type=doc_type
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc

    @staticmethod
    def get_documents(property_id: int, session: Session):
        return session.exec(
            select(Document).where(Document.real_estate_object_id == property_id)
        ).all()

    @staticmethod
    def get_all_documents(session: Session):
        return session.exec(select(Document)).all()

    @staticmethod
    def delete_document(doc_id: int, session: Session):
        doc = session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Документ не найден")
        # Удаляем файл
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        session.delete(doc)
        session.commit()
        return {"message": "Документ удалён"}

    @staticmethod
    def update_document(doc_id: int, file, doc_type: str, session: Session):
        doc = session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Документ не найден")

        old_file_path = doc.file_path
        file_path = save_upload_file(file, "documents")
        doc.file_path = file_path
        doc.filename = file.filename
        doc.doc_type = doc_type

        session.add(doc)
        session.commit()
        session.refresh(doc)

        # Удаляем старый файл только после успешной замены в БД
        if old_file_path and old_file_path != file_path and os.path.exists(old_file_path):
            os.remove(old_file_path)
        return doc

    @staticmethod
    def download_document(doc_id: int, session: Session):
        doc = session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Документ не найден")
        if not doc.file_path or not os.path.exists(doc.file_path):
            raise HTTPException(status_code=404, detail="Файл документа не найден")
        return FileResponse(path=doc.file_path, filename=doc.filename, media_type="application/octet-stream")