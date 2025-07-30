# Backend/auth/security.py
import datetime
import pytz
import jwt
import logging
from passlib.context import CryptContext
from models.models import User

logger = logging.getLogger(__name__)

# --- Configuración de Seguridad Simplificada ---
SECRET_KEY = "tu_clave_secreta_aqui_deberia_ser_mas_larga_y_compleja"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas

# Contexto para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Security:
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera el hash encriptado de una contraseña."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña plana contra su versión encriptada."""
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def hoy(cls):
        """Devuelve la fecha y hora actual."""
        return datetime.datetime.now(pytz.utc)

    @classmethod
    def generate_token(cls, authUser: User) -> str | None:
        """
        Genera un token JWT que incluye el rol del usuario desde userdetail.
        """
        expire = cls.hoy() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Asegurarse de que userdetail y su tipo existen
        role = "cliente"  # Rol por defecto
        if authUser.userdetail and authUser.userdetail.type:
            role = authUser.userdetail.type.lower()

        payload = {
            "exp": expire,
            "iat": cls.hoy(),
            "sub": authUser.username,  # 'subject' del token, comúnmente el username
            "user_id": authUser.id,
            "role": role,
        }
        try:
            return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        except Exception as e:
            logger.error(f"Error al generar el token: {e}")
            return None

    @classmethod
    def verify_token(cls, headers: dict) -> dict:
        """
        Verifica un token JWT desde las cabeceras de la petición.
        Devuelve el payload si es válido, o un diccionario de error si no lo es.
        """
        auth_header = headers.get("authorization")
        if not auth_header:
            return {"success": False, "message": "Falta la cabecera de autorización"}

        try:
            # Asume el formato "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            payload["success"] = True
            return payload
        except jwt.ExpiredSignatureError:
            return {"success": False, "message": "El token ha expirado"}
        except (jwt.InvalidTokenError, IndexError):
            return {"success": False, "message": "Token inválido o malformado"}
        except Exception as e:
            logger.error(f"Error desconocido al validar el token: {e}")
            return {"success": False, "message": "Error al validar el token"}
