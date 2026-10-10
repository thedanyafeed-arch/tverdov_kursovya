from fastapi import APIRouter, File, UploadFile, Depends, status
from sqlmodel import Session
from app.db.session import get_session
from app.controllers.photo_controller import PhotoController
from app.core.security import admin_required, manager_required
from app.schemas.photo_schema import PhotoResponse

router = APIRouter(prefix="/photos", tags=["photos"])

@router.get("", response_model=list[PhotoResponse], summary="Список всех фото всех объектов (публично)")
def list_all_photos(
    session: Session = Depends(get_session),
):
    return PhotoController.get_all_photos(session)

@router.get("/{property_id}", response_model=list[PhotoResponse], summary="Публичный просмотр фото объекта")
def list_photos(
    property_id: int,
    session: Session = Depends(get_session),
):
    return PhotoController.get_photos(property_id, session)

@router.post("/upload/{property_id}", response_model=PhotoResponse, summary="Загрузить фото (менеджер/админ)")
def upload_photo(
    property_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PhotoController.upload_photo(property_id, file, session)

@router.put("/{photo_id}", response_model=PhotoResponse, summary="Изменение фото (замена существующего) (менеджер/админ)")
def update_photo(
    photo_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PhotoController.update_photo(photo_id, file, session)

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление фото (менеджер/админ)")
def delete_photo(
    photo_id: int,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PhotoController.delete_photo(photo_id, session)