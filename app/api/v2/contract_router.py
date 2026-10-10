from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.controllers.contract_controller import ContractController
from app.core.security import get_current_user, manager_required
from app.db.session import get_session
from app.models.contract import Contract
from app.models.role import Role
from app.models.user import User
from app.schemas.contract_schema import ContractFullUpdate, ContractResponse, ContractUpdate

router = APIRouter(prefix="/contracts", tags=["contracts-v2"])


@router.post(
    "/generate/{property_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание договора (авторизованный пользователь)",
)
def generate_contract(
    property_id: int,
    manager_id: int | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    manager_query = (
        select(User)
        .join(Role)
        .where(Role.name.in_(["manager", "admin"]))
        .order_by(User.id)
    )
    if manager_id is not None:
        manager_query = manager_query.where(User.id == manager_id)

    manager = session.exec(manager_query).first()
    if not manager:
        if manager_id is not None:
            raise HTTPException(status_code=404, detail="Менеджер с указанным id не найден")
        raise HTTPException(status_code=500, detail="Менеджер не найден в системе")
    return ContractController.generate_contract(property_id, current_user.id, manager.id, session)


@router.get("", response_model=list[ContractResponse], summary="Договоры текущего пользователя")
def get_user_contracts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contracts = session.exec(
        select(Contract).where(Contract.user_id == current_user.id)
    ).all()
    return contracts


@router.get("/all", response_model=list[ContractResponse], summary="Список всех договоров (менеджер/админ)")
def list_all_contracts(
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return session.exec(select(Contract)).all()


@router.get("/{contract_id}", response_model=ContractResponse, summary="Просмотр договора")
def get_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")

    if current_user.role.name not in ["manager", "admin"] and contract.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этому договору")

    return contract


@router.get("/{contract_id}/download", response_class=FileResponse, summary="Скачать договор")
def download_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return ContractController.download_contract(contract_id, current_user, session)


@router.patch("/{contract_id}", response_model=ContractResponse, summary="Частичное обновление договора (менеджер/админ)")
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return ContractController.update_contract(contract_id, data, session, current_user)


@router.put("/{contract_id}", response_model=ContractResponse, summary="Полное обновление договора (менеджер/админ)")
def update_contract_full(
    contract_id: int,
    data: ContractFullUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return ContractController.update_contract_full(contract_id, data, session, current_user)


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить договор (менеджер/админ)",
)
def delete_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ContractController.delete_contract(contract_id, session, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
