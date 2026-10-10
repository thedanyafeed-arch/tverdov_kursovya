from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.real_estate_object import RealEstateObject
from app.schemas.property_schema import (
    RealEstateObjectCreate,
    RealEstateObjectUpdate,
    RealEstateObjectReplace,
    ALLOWED_STATUSES,
)
from app.models.photo import Photo
from app.models.document import Document
from app.models.contract import Contract

class PropertyController:
    @staticmethod
    def _validate_business_rules(
        *,
        floor: int | None,
        floors_total: int | None,
        price: float | None,
        discount_price: float | None,
    ):
        if floor is not None and floors_total is not None and floor > floors_total:
            raise HTTPException(status_code=422, detail="Этаж не может быть выше этажности здания")

        if discount_price is not None and price is not None and discount_price > price:
            raise HTTPException(status_code=422, detail="Скидочная цена не может быть выше базовой")

    @staticmethod
    def create_property(data: RealEstateObjectCreate, session: Session):
        # Проверяем, существует ли тип недвижимости
        from app.models.property_type import PropertyType
        property_type = session.get(PropertyType, data.property_type_id)
        if not property_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Тип недвижимости с id={data.property_type_id} не найден"
            )
        # Проверяем допустимый статус
        if data.status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Недопустимый статус объекта")
        PropertyController._validate_business_rules(
            floor=data.floor,
            floors_total=data.floors_total,
            price=data.price,
            discount_price=data.discount_price,
        )

        obj = RealEstateObject(**data.model_dump())
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @staticmethod
    def get_properties(
        session: Session,
        property_type_id: int | None = None,
        status_filter: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_area: float | None = None,
        max_area: float | None = None,
    ):
        query = select(RealEstateObject)
        if property_type_id:
            query = query.where(RealEstateObject.property_type_id == property_type_id)
        if status_filter:
            query = query.where(RealEstateObject.status == status_filter)
        if min_price is not None:
            query = query.where(RealEstateObject.price >= min_price)
        if max_price is not None:
            query = query.where(RealEstateObject.price <= max_price)
        if min_area is not None:
            query = query.where(RealEstateObject.total_area >= min_area)
        if max_area is not None:
            query = query.where(RealEstateObject.total_area <= max_area)
        return session.exec(query).all()

    @staticmethod
    def get_property_by_id(property_id: int, session: Session):
        obj = session.get(RealEstateObject, property_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект недвижимости не найден")
        return obj

    @staticmethod
    def update_property_status(property_id: int, new_status: str, session: Session):
        obj = session.get(RealEstateObject, property_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект не найден")
        if new_status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Недопустимый статус объекта")
        obj.status = new_status
        from datetime import datetime
        obj.updated_at = datetime.now().isoformat()
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @staticmethod
    def update_property(property_id: int, data: RealEstateObjectUpdate, session: Session):
        obj = session.get(RealEstateObject, property_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект недвижимости не найден")

        # Проверяем тип недвижимости, если он указан
        if data.property_type_id is not None:
            from app.models.property_type import PropertyType
            property_type = session.get(PropertyType, data.property_type_id)
            if not property_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тип недвижимости с id={data.property_type_id} не найден"
                )

        # Проверяем статус, если передан
        if data.status is not None and data.status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Недопустимый статус объекта")

        next_floor = data.floor if data.floor is not None else obj.floor
        next_floors_total = data.floors_total if data.floors_total is not None else obj.floors_total
        next_price = data.price if data.price is not None else obj.price
        next_discount = data.discount_price if data.discount_price is not None else obj.discount_price
        PropertyController._validate_business_rules(
            floor=next_floor,
            floors_total=next_floors_total,
            price=next_price,
            discount_price=next_discount,
        )

        # Обновляем только указанные поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)

        from datetime import datetime
        obj.updated_at = datetime.now().isoformat()

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @staticmethod
    def replace_property(property_id: int, data: RealEstateObjectReplace, session: Session):
        obj = session.get(RealEstateObject, property_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект недвижимости не найден")

        from app.models.property_type import PropertyType
        property_type = session.get(PropertyType, data.property_type_id)
        if not property_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Тип недвижимости с id={data.property_type_id} не найден"
            )
        if data.status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Недопустимый статус объекта")

        PropertyController._validate_business_rules(
            floor=data.floor,
            floors_total=data.floors_total,
            price=data.price,
            discount_price=data.discount_price,
        )

        replace_data = data.model_dump()
        for field, value in replace_data.items():
            setattr(obj, field, value)

        from datetime import datetime
        obj.updated_at = datetime.now().isoformat()
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @staticmethod
    def delete_property(property_id: int, session: Session):
        obj = session.get(RealEstateObject, property_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект недвижимости не найден")

        # Удаляем связанные фото и документы
        # SQLAlchemy должен удалить их автоматически благодаря каскадному удалению,
        # но на всякий случай удалим вручную
        import os

        # Удаляем фото
        photos = session.exec(select(Photo).where(Photo.real_estate_object_id == property_id)).all()
        for photo in photos:
            # Удаляем файл
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            session.delete(photo)

        # Удаляем документы
        documents = session.exec(select(Document).where(Document.real_estate_object_id == property_id)).all()
        for doc in documents:
            # Удаляем файл
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            session.delete(doc)

        # Удаляем договоры
        contracts = session.exec(select(Contract).where(Contract.real_estate_object_id == property_id)).all()
        for contract in contracts:
            # Удаляем файл договора, если он существует
            if contract.generated_file_path and os.path.exists(contract.generated_file_path):
                os.remove(contract.generated_file_path)
            session.delete(contract)

        # Удаляем объект недвижимости
        session.delete(obj)
        session.commit()
        return {"message": "Объект недвижимости успешно удален", "property_id": property_id}