from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.core.security import manager_required
from app.db.session import get_session
from app.models.property_type import PropertyType
from app.models.user import User
from app.schemas.property_type_schema import PropertyTypeCreate, PropertyTypeUpdate

router = APIRouter(prefix="/property-types", tags=["property-types-v2"])


@router.get("", response_model=list[PropertyType], summary="Список типов недвижимости (публично)")
def list_property_types(session: Session = Depends(get_session)):
    return session.exec(select(PropertyType)).all()


@router.post(
    "",
    response_model=PropertyType,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тип недвижимости (менеджер/админ)",
)
def create_property_type(
    data: PropertyTypeCreate,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    existing = session.exec(select(PropertyType).where(PropertyType.name == data.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тип недвижимости уже существует")

    pt = PropertyType(name=data.name)
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return pt


@router.put("/{type_id}", response_model=PropertyType, summary="Обновить тип недвижимости (менеджер/админ)")
def update_property_type(
    type_id: int,
    data: PropertyTypeUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    pt = session.get(PropertyType, type_id)
    if not pt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип недвижимости не найден")

    duplicate = session.exec(
        select(PropertyType).where(PropertyType.name == data.name, PropertyType.id != type_id)
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тип недвижимости уже существует")

    pt.name = data.name
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return pt


@router.delete(
    "/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить тип недвижимости (менеджер/админ)",
)
def delete_property_type(
    type_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    pt = session.get(PropertyType, type_id)
    if not pt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип недвижимости не найден")

    session.delete(pt)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
