# Backend/auth/security.py
import datetime
import jwt
import logging
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.models import User
from config.db import get_db
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

# --- Configuración de Seguridad ---
SECRET_KEY = "tu_clave_secreta_aqui_deberia_ser_mas_larga_y_compleja"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 días

# Contexto para encriptar contraseñas usando el método seguro bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


class Security:
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera el hash encriptado de una contraseña."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña plana contra su versión encriptada."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def _create_token(data: dict, expires_delta: datetime.timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def generate_access_token(user: User) -> str:
        """Genera un nuevo token de acceso para un usuario."""
        permissions = (
            {perm.name for perm in user.role_obj.permissions}
            if user.role_obj
            else set()
        )
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role_obj.name if user.role_obj else None,
            "permissions": list(permissions),
        }
        return Security._create_token(payload, access_token_expires)

    @staticmethod
    def generate_refresh_token(user: User) -> str:
        """Genera un nuevo refresh token para un usuario."""
        refresh_token_expires = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {"sub": user.username}
        return Security._create_token(payload, refresh_token_expires)


# --- Dependencias para Rutas ---
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except jwt.PyJWTError:
        raise credentials_exception


def has_permission(required_permission: str):
    def permission_checker(current_user: dict = Depends(get_current_user)) -> bool:
        user_permissions = current_user.get("permissions", [])
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los permisos necesarios.",
            )
        return True

    return permission_checker
