from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )
    # Убеждаемся, что роль загружена (SQLModel должен загрузить автоматически, но на всякий случай)
    if user.role is None:
        from app.models.role import Role
        user.role = session.get(Role, user.role_id)
    return user

def admin_required(user: User = Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")
    return user

def manager_required(user: User = Depends(get_current_user)):
    if user.role.name not in ["manager", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права менеджера")
    return user