# app/schemas/user_schema.py

from pydantic import BaseModel, EmailStr, Field
from fastapi import Form

from app.models.base import CamelModel

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

    @classmethod
    def as_form(cls, email: EmailStr = Form(...), password: str = Form(...)):
        return cls(email=email, password=password)


# СХЕМА — для регистрации (роль всегда "user" по умолчанию)
class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

# СХЕМА — для обновления профиля
class UserUpdateSchema(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)

    model_config = {"extra": "forbid"}

# СХЕМА — для назначения роли
class AssignRoleSchema(BaseModel):
    role: str = Field(pattern="^(user|manager|admin)$")


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: str | None = None
    role_id: int


class UserRegisterResponse(BaseModel):
    message: str
    user_id: int


class ProfileUpdateResponse(BaseModel):
    message: str
    user_id: int
    email: EmailStr


class UserAdminSummary(CamelModel):
    """Пользователь без чувствительных полей (для админской выдачи списка)."""

    id: int
    email: str
    is_active: bool
    created_at: str | None = None
    role_id: int
    role_name: str