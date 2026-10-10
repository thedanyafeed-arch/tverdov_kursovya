from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.core.security import admin_required, manager_required
from app.models.property_type import PropertyType

router = APIRouter(prefix="/property-types", tags=["property-types"])


@router.get("", response_model=list[PropertyType], summary="Список типов недвижимости (публично)")
def list_property_types(session: Session = Depends(get_session)):
    return session.exec(select(PropertyType)).all()


@router.post("", response_model=PropertyType, status_code=status.HTTP_201_CREATED, summary="Создать тип (менеджер/админ)")
def create_property_type(
    data: PropertyType,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    existing = session.exec(select(PropertyType).where(PropertyType.name == data.name)).first()
    if existing:
        return existing
    session.add(data)
    session.commit()
    session.refresh(data)
    return data


@router.put("/{type_id}", response_model=PropertyType, summary="Обновить тип (менеджер/админ)")
def update_property_type(
    type_id: int,
    data: PropertyType,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    pt = session.get(PropertyType, type_id)
    if not pt:
        return {"detail": "Тип недвижимости не найден"}
    pt.name = data.name
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return pt


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить тип (менеджер/админ)")
def delete_property_type(
    type_id: int,
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    pt = session.get(PropertyType, type_id)
    if not pt:
        return {"detail": "Тип недвижимости не найден"}
    session.delete(pt)
    session.commit()
    return {"message": "Тип недвижимости удален"}


