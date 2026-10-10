from fastapi import APIRouter, Depends, Response, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from app.controllers.auth_controller import AuthController
from app.schemas.user_schema import UserLoginSchema, UserRegisterSchema, UserUpdateSchema
from app.db.session import get_session
from sqlmodel import Session
from app.models.user import User
from app.core.security import get_current_user, admin_required

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", summary="Аутентификация")
def login_route(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    login_data = UserLoginSchema(email=form_data.username, password=form_data.password)
    return AuthController.login(response, login_data, session)

@router.post("/logout", summary="Выход из аккаунта")
def logout_route(response: Response):
    return AuthController.logout(response)

@router.get("/me", response_model=User, summary="Информация о текущем пользователе")
def get_user_info_route(current_user: User = Depends(get_current_user)):
    return AuthController.get_user_info(current_user)

@router.post("/register", summary="Регистрация нового пользователя")
def register_user_route(
    data: UserRegisterSchema,
    session: Session = Depends(get_session)
):
    return AuthController.register_user(data, session)

@router.patch("/users/{user_id}/role", summary="Назначение роли пользователю (только для админа)")
def assign_role_route(
    user_id: int,
    role_name: str = Query(..., description="Название роли: user, manager или admin"),
    session: Session = Depends(get_session),
    _ = Depends(admin_required)
):
    return AuthController.assign_role(user_id, role_name, session)

@router.patch("/me", summary="Обновление профиля (email/пароль)", response_model=dict)
def update_profile_route(
    data: UserUpdateSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return AuthController.update_profile(data, session, current_user)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление пользователя (только для админа)")
def delete_user_route(
    user_id: int,
    session: Session = Depends(get_session),
    _ = Depends(admin_required)
):
    return AuthController.delete_user(user_id, session)