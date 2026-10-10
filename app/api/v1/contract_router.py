from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.controllers.contract_controller import ContractController
from app.core.security import get_current_user, manager_required
from app.models.user import User
from app.models.contract import Contract
from app.schemas.contract_schema import ContractResponse, ContractUpdate, ContractFullUpdate
from app.models.role import Role
from fastapi.responses import FileResponse
router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/generate/{property_id}", response_model=ContractResponse,
             summary="Создание договора (только для авторизованных)")
def generate_contract(
        property_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # Для упрощения: менеджер — любой пользователь с ролью manager или admin
    manager = session.exec(
        select(User)
        .join(Role)
        .where(Role.name.in_(["manager", "admin"]))
    ).first()
    if not manager:
        raise HTTPException(status_code=500, detail="Менеджер не найден в системе")

    return ContractController.generate_contract(property_id, current_user.id, manager.id, session)


@router.get("", response_model=list[ContractResponse], summary="Просмотр всех договоров текущего пользователя (только для авторизованных)")
def get_user_contracts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Получить все договоры текущего пользователя"""
    contracts = session.exec(
        select(Contract).where(Contract.user_id == current_user.id)
    ).all()
    return contracts

@router.get("/all", response_model=list[ContractResponse], summary="Список всех договоров (менеджер/админ)")
def list_all_contracts(
    session: Session = Depends(get_session),
    _ = Depends(manager_required)
):
    return session.exec(select(Contract)).all()

@router.get("/{contract_id}", response_model=ContractResponse, summary="Просмотр договора (только для авторизованных)")
def get_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Просмотр договора. Пользователь может видеть только свои договоры, менеджер/админ - все"""
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    # Проверяем права доступа: пользователь может видеть только свои договоры
    # Менеджер и админ могут видеть все договоры
    if current_user.role.name not in ["manager", "admin"]:
        if contract.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="У вас нет доступа к этому договору"
            )
    
    return contract

@router.get("/{contract_id}/download", response_class=FileResponse, summary="Скачать договор (только для авторизованных)")
def download_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return ContractController.download_contract(contract_id, current_user, session)

@router.patch("/{contract_id}", response_model=ContractResponse, summary="Обновить договор (статус/дата) (менеджер/админ)")
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Доступ проверяется в контроллере
    return ContractController.update_contract(contract_id, data, session, current_user)

@router.put("/{contract_id}", response_model=ContractResponse, summary="Полное обновление договора (менеджер/админ)")
def update_contract_full(
    contract_id: int,
    data: ContractFullUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Доступ проверяется в контроллере
    return ContractController.update_contract_full(contract_id, data, session, current_user)

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить договор (менеджер/админ)")
def delete_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return ContractController.delete_contract(contract_id, session, current_user)