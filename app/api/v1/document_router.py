from fastapi import APIRouter, File, UploadFile, Depends, Query, status
from sqlmodel import Session
from app.db.session import get_session
from app.controllers.document_controller import DocumentController
from app.core.security import admin_required, manager_required
from app.schemas.document_schema import DocumentResponse, DocumentCreate
from fastapi.responses import FileResponse

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload/{property_id}", response_model=DocumentResponse, summary="Загрузить документ (менеджер/админ)")
def upload_document(
    property_id: int,
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="Тип документа: схема, план застройки и т.д."),
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return DocumentController.upload_document(property_id, file, doc_type, session)

@router.get("/{property_id}", response_model=list[DocumentResponse], summary="Публичный просмотр документов")
def get_documents(property_id: int, session: Session = Depends(get_session)):
    return DocumentController.get_documents(property_id, session)

@router.get("", response_model=list[DocumentResponse], summary="Список всех документов (менеджер/админ)")
def list_all_documents(
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return DocumentController.get_all_documents(session)

@router.get("/download/{doc_id}", response_class=FileResponse, summary="Скачать документ")
def download_document(
    doc_id: int,
    session: Session = Depends(get_session)
):
    return DocumentController.download_document(doc_id, session)

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary = "Удаление документа (только менджер или админ)")
def delete_document(
    doc_id: int,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return DocumentController.delete_document(doc_id, session)

@router.put("/{doc_id}", response_model=DocumentResponse, summary="Обновление документа (менеджер/админ)")
def update_document(
    doc_id: int,
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="Тип документа"),
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return DocumentController.update_document(doc_id, file, doc_type, session)