# routes/token_routes.py
# -----------------------------------------------------------------------------
# RUTA DE ACTUALIZACIÓN DE TOKEN (REFRESH TOKEN)
# -----------------------------------------------------------------------------
# Este módulo contiene el endpoint crucial para el sistema de autenticación:
# la rotación de tokens. Permite al frontend obtener un nuevo token de acceso
# de corta duración usando un token de actualización de larga duración, sin que
# el usuario tenga que volver a iniciar sesión.
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import User
from auth.security import Security
import jwt
from config.db import get_db

# Creación de un router específico para la ruta de token.
token_router = APIRouter()


@token_router.post("/token/refresh")
def refresh_access_token(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    """
    Refresca el token de acceso usando el 'refresh_token' almacenado en una cookie.
    Implementa la rotación de refresh tokens para mayor seguridad.
    """
    try:
        # 1. Lee el 'refresh_token' desde una cookie 'httpOnly' en la petición.
        #    'httpOnly' significa que la cookie no es accesible por JavaScript en el navegador.
        refresh_token_from_cookie = request.cookies.get("refresh_token")
        if not refresh_token_from_cookie:
            raise HTTPException(
                status_code=401, detail="No se encontró el refresh token"
            )

        # Se decodifica el token para obtener el nombre de usuario ('sub').
        payload = jwt.decode(
            refresh_token_from_cookie, Security.secret, algorithms=["HS256"]
        )
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()

        # 2. Medida de seguridad CRÍTICA: se valida que el token de la cookie
        #    coincida con el último refresh token guardado en la base de datos para ese usuario.
        if not user or user.refresh_token != refresh_token_from_cookie:
            # Si no coincide, podría ser una señal de un token robado. Se invalida el token
            # en la base de datos para prevenir su uso futuro.
            if user:
                user.refresh_token = None
                db.commit()
            raise HTTPException(
                status_code=401, detail="Refresh token inválido o revocado"
            )

        # 3. ROTACIÓN DE TOKENS: Si el refresh token es válido, se generan un
        #    NUEVO token de acceso y un NUEVO token de actualización.
        new_access_token = Security.generate_access_token(user)
        new_refresh_token = Security.generate_refresh_token(user)

        # 4. Se guarda el NUEVO refresh token en la base de datos, reemplazando el antiguo.
        user.refresh_token = new_refresh_token
        db.commit()

        # 5. Se devuelve el nuevo token de acceso en el cuerpo de la respuesta y
        #    el nuevo refresh token se establece en una nueva cookie 'httpOnly'.
        response_body = {"access_token": new_access_token, "token_type": "bearer"}
        response = JSONResponse(content=response_body)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,  # Impide el acceso desde JavaScript (protección XSS).
            samesite="strict",  # Ayuda a proteger contra ataques CSRF.
            secure=True,  # La cookie solo se enviará a través de HTTPS.
        )
        return response
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token ha expirado")
    except (jwt.InvalidTokenError, Exception) as e:
        raise HTTPException(status_code=401, detail=f"Refresh token inválido: {e}")
