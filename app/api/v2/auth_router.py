from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.controllers.auth_controller import AuthController
from app.core.security import admin_required, get_current_user, manager_required
from app.db.session import get_session
from app.models.user import User
from app.schemas.user_schema import (
    ProfileUpdateResponse,
    UserAdminSummary,
    UserLoginSchema,
    UserPublic,
    UserRegisterResponse,
    UserRegisterSchema,
    UserUpdateSchema,
)

router = APIRouter(prefix="/auth", tags=["auth-v2"])


@router.post(
    "/login",
    summary="Аутентификация пользователя",
    description="Проверяет email и пароль, возвращает JWT access token.",
    include_in_schema=False,
)
def login_route(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    login_data = UserLoginSchema(email=form_data.username, password=form_data.password)
    return AuthController.login(response, login_data, session)


@router.post(
    "/logout",
    summary="Выход из аккаунта",
    description="Удаляет cookie access_token. Выданный JWT остается валидным до истечения срока действия.",
)
def logout_route(response: Response):
    return AuthController.logout(response)


@router.get("/me", response_model=UserPublic, summary="Информация о текущем пользователе")
def get_user_info_route(current_user: User = Depends(get_current_user)):
    return AuthController.get_user_info(current_user)


@router.get(
    "/users",
    response_model=list[UserAdminSummary],
    summary="Список пользователей (менеджер и администратор; без пароля)",
)
def list_users_route(
    session: Session = Depends(get_session),
    _: User = Depends(manager_required),
):
    return AuthController.list_users_for_admin(session)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegisterResponse,
    summary="Регистрация нового пользователя",
)
def register_user_route(
    data: UserRegisterSchema,
    session: Session = Depends(get_session),
):
    return AuthController.register_user(data, session)


@router.patch(
    "/users/{user_id}/role",
    summary="Назначение роли пользователю (только для админа)",
)
def assign_role_route(
    user_id: int,
    role_name: str = Query(..., pattern="^(user|manager|admin)$"),
    session: Session = Depends(get_session),
    _: User = Depends(admin_required),
):
    return AuthController.assign_role(user_id, role_name, session)


@router.patch(
    "/me",
    response_model=ProfileUpdateResponse,
    summary="Обновление профиля (email/пароль)",
)
def update_profile_route(
    data: UserUpdateSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return AuthController.update_profile(data, session, current_user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя (только для админа)",
)
def delete_user_route(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(admin_required),
):
    AuthController.delete_user(user_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
