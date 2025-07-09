# auth/security.py
import datetime
import pytz
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

class Security:
    """
    Clase para manejar la generación y verificación de tokens JWT.
    """
    secret = "hola"  # En un proyecto real, esto debería estar en una variable de entorno.
    
    @classmethod
    def generate_token(cls, authUser) -> str:
        """
        Genera un nuevo token JWT incluyendo el rol del usuario en el payload.
        """
        # Se obtiene la hora actual cada vez que se genera un token
        # para asegurar que la expiración sea siempre correcta.
        hoy = datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))
        

        payload = {
            "exp": hoy + datetime.timedelta(minutes=480), # Tiempo de vida del token (8 horas)
            "iat": hoy, # Tiempo en que fue creado el token
            "sub": authUser.username, # 'Subject', el identificador principal del token
            "user_id": authUser.id, 
            "role": authUser.role
        }
        try:
            return jwt.encode(payload, cls.secret, algorithm="HS256")
        except Exception:
            return None

# --- Dependencias de Seguridad de FastAPI ---

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia que decodifica el token, valida su firma y expiración,
    y devuelve el payload si todo es correcto. Si no, levanta un error HTTP.
    """
    try:
        payload = jwt.decode(token, Security.secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def is_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependencia "guardiana" que verifica si el usuario actual tiene el rol 'administrador'.
    Reutiliza la dependencia get_current_user. Si el rol no es el correcto,
    levanta un error HTTP 403 Forbidden.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción."
        )
    return current_user