from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session, select
from fastapi_pagination import Page, add_pagination, Params
from fastapi_pagination.ext.sqlmodel import paginate
from app.db.session import get_session
from app.controllers.property_controller import PropertyController
from app.schemas.property_schema import RealEstateObjectCreate, RealEstateObjectUpdate
from app.models.real_estate_object import RealEstateObject
from app.core.security import admin_required, manager_required, get_current_user

router = APIRouter(prefix="/properties", tags=["properties"])

@router.post("", response_model=RealEstateObject, status_code=status.HTTP_201_CREATED, summary="Создать объект недвижимости (менеджер/админ)")
def create_property(
    data: RealEstateObjectCreate,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PropertyController.create_property(data, session)

@router.get("", response_model=Page[RealEstateObject], summary="Вывод всей недвижимости ")
def get_properties(
    property_type_id: int | None = Query(None, description="Фильтр по типу недвижимости (опционально)"),
    status_filter: str | None = Query(None, description="Фильтр по статусу"),
    min_price: float | None = Query(None, description="Минимальная цена"),
    max_price: float | None = Query(None, description="Максимальная цена"),
    min_area: float | None = Query(None, description="Минимальная площадь"),
    max_area: float | None = Query(None, description="Максимальная площадь"),
    session: Session = Depends(get_session)
):
    # Если фильтры не указаны, можно использовать paginate напрямую
    if not any([property_type_id, status_filter, min_price, max_price, min_area, max_area]):
        return paginate(session, RealEstateObject)

    # Иначе получаем отфильтрованные данные и пагинируем в памяти
    from fastapi_pagination import paginate as manual_paginate

    filtered_objects = PropertyController.get_properties(
        session,
        property_type_id=property_type_id,
        status_filter=status_filter,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
    )
    return manual_paginate(filtered_objects)

@router.get("/{property_id}", response_model=RealEstateObject, summary="Вывод недвижимости по id")
def get_property(property_id: int, session: Session = Depends(get_session)):
    return PropertyController.get_property_by_id(property_id, session)

@router.patch("/{property_id}/status", response_model=RealEstateObject, summary="Изменение статуса (менеджер)")
def update_property_status(
    property_id: int,
    new_status: str,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PropertyController.update_property_status(property_id, new_status, session)

@router.post("/{property_id}/reserve", response_model=RealEstateObject, summary="Бронирование объекта (только авторизованные)")
def reserve_property(
    property_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Устанавливаем статус "забронирован"
    return PropertyController.update_property_status(property_id, "забронирован", session)

@router.put("/{property_id}", response_model=RealEstateObject, summary="Редактирование информации об объекте недвижимости (менеджер/админ)")
def update_property(
    property_id: int,
    data: RealEstateObjectUpdate,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PropertyController.update_property(property_id, data, session)

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление объекта недвижимости (менеджер/админ)")
def delete_property(
    property_id: int,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return PropertyController.delete_property(property_id, session)