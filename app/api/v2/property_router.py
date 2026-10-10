from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi_pagination import Page
from fastapi_pagination import paginate as manual_paginate
from fastapi_pagination.ext.sqlmodel import paginate
from sqlmodel import Session

from app.controllers.property_controller import PropertyController
from app.core.security import get_current_user, manager_required
from app.db.session import get_session
from app.models.real_estate_object import RealEstateObject
from app.models.user import User
from app.schemas.property_schema import (
    ALLOWED_STATUSES,
    RealEstateObjectCreate,
    RealEstateObjectReplace,
    RealEstateObjectUpdate,
)

router = APIRouter(prefix="/properties", tags=["properties-v2"])


def _validate_range(min_value, max_value, field_name: str) -> None:
    if min_value is not None and max_value is not None and min_value > max_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Некорректный диапазон {field_name}: минимум больше максимума",
        )


@router.post(
    "",
    response_model=RealEstateObject,
    status_code=status.HTTP_201_CREATED,
    summary="Создать объект недвижимости (менеджер/админ)",
)
def create_property(
    data: RealEstateObjectCreate,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return PropertyController.create_property(data, session)


@router.get("", response_model=Page[RealEstateObject], summary="Вывод объектов недвижимости")
def get_properties(
    property_type_id: int | None = Query(None, description="Фильтр по типу недвижимости"),
    status_filter: str | None = Query(None, description=f"Статус: {', '.join(ALLOWED_STATUSES)}"),
    min_price: Decimal | None = Query(None, description="Минимальная цена"),
    max_price: Decimal | None = Query(None, description="Максимальная цена"),
    min_area: float | None = Query(None, description="Минимальная площадь"),
    max_area: float | None = Query(None, description="Максимальная площадь"),
    session: Session = Depends(get_session),
):
    if status_filter is not None and status_filter not in ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Недопустимый статус")

    _validate_range(min_price, max_price, "цены")
    _validate_range(min_area, max_area, "площади")

    has_filters = any(
        value is not None
        for value in [property_type_id, status_filter, min_price, max_price, min_area, max_area]
    )
    if not has_filters:
        return paginate(session, RealEstateObject)

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


@router.patch("/{property_id}/status", response_model=RealEstateObject, summary="Изменение статуса (менеджер/админ)")
def update_property_status(
    property_id: int,
    new_status: str = Query(..., pattern="^(в продаже|продан|забронирован)$"),
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return PropertyController.update_property_status(property_id, new_status, session)


@router.post("/{property_id}/reserve", response_model=RealEstateObject, summary="Бронирование объекта (авторизованный)")
def reserve_property(
    property_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    property_obj = PropertyController.get_property_by_id(property_id, session)
    if property_obj.status == "продан":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Нельзя забронировать уже проданный объект")
    if property_obj.status == "забронирован":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Объект уже забронирован")

    return PropertyController.update_property_status(property_id, "забронирован", session)


@router.put(
    "/{property_id}",
    response_model=RealEstateObject,
    summary="Редактирование информации об объекте недвижимости (менеджер/админ)",
)
def update_property(
    property_id: int,
    data: RealEstateObjectReplace,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return PropertyController.replace_property(property_id, data, session)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление объекта недвижимости (менеджер/админ)",
)
def delete_property(
    property_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    PropertyController.delete_property(property_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
