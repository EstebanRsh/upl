# auth/security.py
import logging
import os
from dotenv import load_dotenv
import datetime
import pytz
import jwt
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from config.db import get_db
from models.models import User, Role  # Importamos los modelos necesarios

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")
logger = logging.getLogger(__name__)


class Security:
    """Clase que encapsula toda la lógica de seguridad."""

    secret = os.getenv("JWT_SECRET_KEY")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def generate_access_token(cls, authUser: User) -> str:
        """Genera un TOKEN DE ACCESO de corta duración."""
        hoy = datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))

        # --- CORREGIDO: Usamos la relación para obtener el nombre del rol ---
        role_name = authUser.role_obj.name if authUser.role_obj else None

        payload = {
            "exp": hoy + datetime.timedelta(minutes=30),
            "iat": hoy,
            "sub": authUser.username,
            "user_id": authUser.id,
            "role": role_name,  # <-- Se usa la variable corregida
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, cls.secret, algorithm="HS256")

    @classmethod
    def generate_refresh_token(cls, authUser: User) -> str:
        """Genera un TOKEN DE ACTUALIZACIÓN de larga duración."""
        hoy = datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))
        payload = {
            "exp": hoy + datetime.timedelta(days=1),
            "iat": hoy,
            "sub": authUser.username,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, cls.secret, algorithm="HS256")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Decodifica el token JWT, obtiene el usuario de la BD y sus permisos.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Security.secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        user = (
            db.query(User)
            .options(joinedload(User.role_obj).joinedload(Role.permissions))
            .filter(User.username == username)
            .first()
        )
        if user is None:
            raise credentials_exception

        user_permissions = (
            {p.name for p in user.role_obj.permissions} if user.role_obj else set()
        )

        return {
            "user_id": user.id,
            "sub": user.username,
            "role": user.role_obj.name if user.role_obj else None,
            "permissions": user_permissions,
        }
    except jwt.PyJWTError:
        raise credentials_exception


def is_admin(current_user: dict = Depends(get_current_user)):
    """[DEPRECADO] Reemplazar por has_permission."""
    if current_user.get("role") != "Super Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes."
        )
    return current_user


def has_permission(required_permission: str):
    """
    Crea una dependencia que verifica si el usuario tiene un permiso específico.
    """

    def permission_checker(current_user: dict = Depends(get_current_user)):
        if required_permission not in current_user.get("permissions", set()):
            logger.warning(
                f"Acceso denegado para '{current_user.get('sub')}'. Permiso requerido: '{required_permission}'."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para realizar esta acción.",
            )
        return current_user

    return permission_checker
