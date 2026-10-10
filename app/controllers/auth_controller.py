from fastapi import HTTPException, status, Response
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from app.models.user import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.role import Role
from app.schemas.user_schema import UserAdminSummary, UserLoginSchema, UserRegisterSchema, UserUpdateSchema

class AuthController:
    @staticmethod
    def login(response: Response, data: UserLoginSchema, session: Session):
        user = session.exec(select(User).where(User.email == data.email)).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
        token = create_access_token(data={"sub": user.email, "role": user.role.name})
        return {"access_token": token, "token_type": "bearer"}

    @staticmethod
    def logout(response: Response):
        response.delete_cookie(key="access_token")
        return {"message": "Выход выполнен"}

    @staticmethod
    def get_user_info(current_user: User):
        return current_user

    @staticmethod
    def list_users_for_admin(session: Session) -> list[UserAdminSummary]:
        stmt = select(User).options(selectinload(User.role)).order_by(User.id)
        rows = list(session.exec(stmt).all())
        return [
            UserAdminSummary(
                id=u.id,
                email=u.email,
                is_active=u.is_active,
                created_at=u.created_at,
                role_id=u.role_id,
                role_name=u.role.name if u.role else "—",
            )
            for u in rows
        ]

    @staticmethod
    def register_user(data: UserRegisterSchema, session: Session):
        # Проверка: email уже существует?
        existing = session.exec(select(User).where(User.email == data.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

        # Получаем роль "user" по умолчанию
        role = session.exec(select(Role).where(Role.name == "user")).first()
        if not role:
            raise HTTPException(status_code=500, detail="Роль 'user' не найдена в системе")

        # Создаём нового пользователя с ролью "user"
        from datetime import datetime
        new_user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            role_id=role.id,
            is_active=True,
            created_at=datetime.now().isoformat()
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return {"message": "Пользователь успешно зарегистрирован", "user_id": new_user.id}

    @staticmethod
    def assign_role(user_id: int, role_name: str, session: Session):
        # Проверяем, существует ли пользователь
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Проверяем, существует ли роль
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Роль '{role_name}' не найдена")

        # Назначаем роль
        user.role_id = role.id
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"message": f"Роль '{role_name}' успешно назначена пользователю", "user_id": user.id, "new_role": role_name}

    @staticmethod
    def update_profile(data: UserUpdateSchema, session: Session, current_user: User):
        # Проверяем уникальность email, если задан
        if data.email and data.email != current_user.email:
            exists = session.exec(select(User).where(User.email == data.email)).first()
            if exists:
                raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
            current_user.email = data.email

        # Обновляем пароль, если задан
        if data.password:
            current_user.hashed_password = get_password_hash(data.password)

        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return {"message": "Профиль обновлен", "user_id": current_user.id, "email": current_user.email}

    @staticmethod
    def delete_user(user_id: int, session: Session):
        # Проверяем, существует ли пользователь
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Удаляем пользователя
        session.delete(user)
        session.commit()
        return {"message": "Пользователь успешно удален", "user_id": user_id}