from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.photo import Photo
from app.core.utils import save_upload_file

class PhotoController:
    @staticmethod
    def upload_photo(property_id: int, file, session: Session):
        # Проверяем, существует ли объект недвижимости
        from app.models.real_estate_object import RealEstateObject
        property_obj = session.get(RealEstateObject, property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Объект недвижимости с id={property_id} не найден"
            )
        
        file_path = save_upload_file(file, "photos")
        photo = Photo(
            real_estate_object_id=property_id,
            file_path=file_path,
            filename=file.filename
        )
        session.add(photo)
        session.commit()
        session.refresh(photo)
        return photo

    @staticmethod
    def get_photos(property_id: int, session: Session):
        return session.exec(
            select(Photo).where(Photo.real_estate_object_id == property_id)
        ).all()

    @staticmethod
    def get_all_photos(session: Session):
        return session.exec(select(Photo)).all()

    @staticmethod
    def delete_photo(photo_id: int, session: Session):
        photo = session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        
        # Удаляем файл
        import os
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        session.delete(photo)
        session.commit()
        return {"message": "Фото удалено"}

    @staticmethod
    def update_photo(photo_id: int, file, session: Session):
        # Находим существующее фото
        photo = session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Фото не найдено")

        import os
        old_file_path = photo.file_path
        file_path = save_upload_file(file, "photos")
        photo.file_path = file_path
        photo.filename = file.filename

        session.add(photo)
        session.commit()
        session.refresh(photo)

        # Удаляем старый файл после успешного обновления записи
        if old_file_path and old_file_path != file_path and os.path.exists(old_file_path):
            os.remove(old_file_path)
        return photo