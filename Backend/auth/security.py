# auth/security.py
# -----------------------------------------------------------------------------
# MÓDULO DE SEGURIDAD Y AUTENTICACIÓN
# -----------------------------------------------------------------------------
# Este archivo es fundamental para la seguridad de la API. Sus responsabilidades son:
# 1. Hashear y verificar contraseñas de forma segura usando passlib.
# 2. Generar y decodificar JSON Web Tokens (JWT) para la autenticación y autorización.
# 3. Proveer dependencias de FastAPI ('Depends') para proteger las rutas,
#    verificando que el usuario esté autenticado y tenga los permisos necesarios.
# -----------------------------------------------------------------------------

import datetime
import pytz  # Para manejar zonas horarias de forma correcta.
import jwt  # Para la creación y validación de JSON Web Tokens.
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext  # Para el hasheo de contraseñas.

# 1. Configuración del hasheo de contraseñas
# Se crea un contexto de 'passlib' que usará el algoritmo 'bcrypt', el estándar actual
# para el almacenamiento seguro de contraseñas.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Configuración del esquema de autenticación OAuth2
# 'OAuth2PasswordBearer' es una clase de FastAPI que facilita la obtención del token
# desde la cabecera 'Authorization: Bearer <token>'.
# 'tokenUrl' le indica a la documentación automática de la API cuál es el endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


class Security:
    """Clase que encapsula toda la lógica de seguridad."""

    # ¡IMPORTANTE! Esta clave secreta se usa para firmar los tokens JWT.
    # En producción, NUNCA debe estar escrita directamente en el código.
    # Debe cargarse desde una variable de entorno segura.
    secret = "hola"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña en texto plano coincide con su hash almacenado."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera el hash de una contraseña usando bcrypt."""
        return pwd_context.hash(password)

    @classmethod
    def generate_access_token(cls, authUser) -> str:
        """
        Genera un TOKEN DE ACCESO de corta duración (30 minutos).
        Se usa para autorizar al usuario en cada petición a las rutas protegidas.
        """
        # Se establece la zona horaria para que las fechas de expiración sean consistentes.
        hoy = datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))

        # El 'payload' es la información que se almacena dentro del token.
        payload = {
            "exp": hoy + datetime.timedelta(minutes=30),  # Tiempo de expiración.
            "iat": hoy,  # Tiempo de emisión ('issued at').
            "sub": authUser.username,  # 'Subject' o sujeto, identifica al usuario.
            "user_id": authUser.id,  # ID del usuario, útil en las rutas.
            "role": authUser.role,  # Rol, para el control de acceso (autorización).
        }
        # Se codifica el payload junto con la clave secreta para generar el token.
        return jwt.encode(payload, cls.secret, algorithm="HS256")

    @classmethod
    def generate_refresh_token(cls, authUser) -> str:
        """
        Genera un TOKEN DE ACTUALIZACIÓN de larga duración (1 día).
        Su única finalidad es obtener un nuevo token de acceso cuando el anterior expira.
        """
        hoy = datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))

        # El payload del refresh token es más simple, solo necesita identificar al usuario.
        payload = {
            "exp": hoy + datetime.timedelta(days=1),  # Duración más larga.
            "iat": hoy,
            "sub": authUser.username,
        }
        return jwt.encode(payload, cls.secret, algorithm="HS256")


# --- Dependencias de Seguridad de FastAPI ---


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia que valida el token de acceso y devuelve su contenido.
    FastAPI inyectará esta dependencia en las rutas que la requieran.
    """
    try:
        # Intenta decodificar el token usando la misma clave secreta.
        # jwt.decode verifica automáticamente la firma y la fecha de expiración.
        payload = jwt.decode(token, Security.secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        # Si el token ha expirado, lanza una excepción HTTP 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        # Si el token es inválido por cualquier otra razón (firma incorrecta, etc.),
        # lanza una excepción HTTP 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependencia "guardiana" que restringe el acceso solo a administradores.
    Reutiliza la dependencia 'get_current_user' para obtener primero al usuario.
    """
    # Verifica si el rol extraído del token es 'administrador'.
    if current_user.get("role") != "administrador":
        # Si no lo es, lanza una excepción HTTP 403 Forbidden.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción.",
        )
    # Si es administrador, devuelve los datos del usuario para que la ruta los pueda usar.
    return current_user
