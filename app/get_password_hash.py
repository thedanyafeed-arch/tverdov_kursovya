# hash_password.py
from app.core.security import get_password_hash

password = "admin"
print("Хеш для пароля 'admin123':")
print(get_password_hash(password))