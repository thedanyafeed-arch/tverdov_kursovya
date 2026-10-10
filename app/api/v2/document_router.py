from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.controllers.document_controller import DocumentController
from app.core.security import manager_required
from app.db.session import get_session
from app.models.user import User
from app.schemas.document_schema import DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents-v2"])


@router.post(
    "/upload/{property_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ (менеджер/админ)",
)
def upload_document(
    property_id: int,
    file: UploadFile = File(...),
    doc_type: str = Query(..., min_length=1, max_length=128, description="Тип документа"),
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return DocumentController.upload_document(property_id, file, doc_type, session)


@router.get("", response_model=list[DocumentResponse], summary="Список всех документов (менеджер/админ)")
def list_all_documents(
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return DocumentController.get_all_documents(session)


@router.get("/download/{doc_id}", response_class=FileResponse, summary="Скачать документ")
def download_document(
    doc_id: int,
    session: Session = Depends(get_session),
):
    return DocumentController.download_document(doc_id, session)


@router.get("/{property_id}", response_model=list[DocumentResponse], summary="Публичный просмотр документов объекта")
def get_documents(property_id: int, session: Session = Depends(get_session)):
    return DocumentController.get_documents(property_id, session)


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа (менеджер/админ)",
)
def delete_document(
    doc_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    DocumentController.delete_document(doc_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{doc_id}", response_model=DocumentResponse, summary="Обновление документа (менеджер/админ)")
def update_document(
    doc_id: int,
    file: UploadFile = File(...),
    doc_type: str = Query(..., min_length=1, max_length=128, description="Тип документа"),
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return DocumentController.update_document(doc_id, file, doc_type, session)
