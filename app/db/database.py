from sqlmodel import SQLModel, Session, select
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

# Загружаем .env из папки app
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL не найден в переменных окружения. "
        "Пожалуйста, создайте файл .env и укажите DATABASE_URL. "
        "Пример: DATABASE_URL=postgresql://user:password@localhost:5432/real_estate_api_db"
    )

# Создаём движок с psycopg2 (синхронный, как в шаблоне)
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Создание таблиц и инициализация базовых данных"""
    SQLModel.metadata.create_all(engine)
    init_roles()
    init_property_types()

def init_roles():
    """Инициализация ролей в базе данных"""
    from app.models.role import Role
    
    with Session(engine) as session:
        # Список ролей для создания
        roles = [
            {"name": "admin", "description": "Администратор - полный доступ"},
            {"name": "manager", "description": "Менеджер - управление объектами и статусами"},
            {"name": "user", "description": "Пользователь - просмотр и создание договоров"}
        ]
        
        for role_data in roles:
            # Проверяем, существует ли роль
            existing_role = session.exec(
                select(Role).where(Role.name == role_data["name"])
            ).first()
            
            if not existing_role:
                # Создаём роль, если её нет
                new_role = Role(**role_data)
                session.add(new_role)
                session.commit()
                print(f"Создана роль: {role_data['name']}")

def init_property_types():
    """Инициализация типов недвижимости в базе данных"""
    from app.models.property_type import PropertyType
    
    with Session(engine) as session:
        # Список типов недвижимости для создания
        property_types = [
            {"name": "квартира"},
            {"name": "дом"},
            {"name": "коммерческая недвижимость"}
        ]
        
        for prop_type_data in property_types:
            # Проверяем, существует ли тип
            existing_type = session.exec(
                select(PropertyType).where(PropertyType.name == prop_type_data["name"])
            ).first()
            
            if not existing_type:
                # Создаём тип, если его нет
                new_type = PropertyType(**prop_type_data)
                session.add(new_type)
                session.commit()
                print(f"Создан тип недвижимости: {prop_type_data['name']}")

def close_db():
    engine.dispose()

def get_engine():
    """Получение engine для миграций (Alembic)"""
    return engine