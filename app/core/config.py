from dotenv import load_dotenv
import os
from pathlib import Path

# Загружаем .env из папки app
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Безопасный парсинг ACCESS_TOKEN_EXPIRE_MINUTES
_access_token_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30").strip()
# Удаляем все нецифровые символы (на случай лишних символов в .env)
_access_token_expire = ''.join(filter(str.isdigit, _access_token_expire))
ACCESS_TOKEN_EXPIRE_MINUTES = int(_access_token_expire) if _access_token_expire else 30

DATABASE_URL = os.getenv("DATABASE_URL")

if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY не найден в переменных окружения. "
        "Пожалуйста, создайте файл .env и укажите SECRET_KEY."
    )