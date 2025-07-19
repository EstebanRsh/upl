# routes/token_routes.py
# -----------------------------------------------------------------------------
# RUTA DE ACTUALIZACIÓN DE TOKEN (REFRESH TOKEN)
# -----------------------------------------------------------------------------
import logging
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import User
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
token_router = APIRouter()


@token_router.post("/token/refresh")
def refresh_access_token(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    logger.info("Recibida solicitud para renovar token de acceso.")
    try:
        refresh_token_from_cookie = request.cookies.get("refresh_token")
        if not refresh_token_from_cookie:
            logger.warning("Intento de refrescar token sin la cookie 'refresh_token'.")
            raise HTTPException(
                status_code=401, detail="No se encontró el refresh token"
            )
        payload = jwt.decode(
            refresh_token_from_cookie, Security.secret, algorithms=["HS256"]
        )
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user or user.refresh_token != refresh_token_from_cookie:
            logger.warning(
                f"Refresh token inválido o revocado para el usuario '{username}'."
            )
            if user:
                user.refresh_token = None
                db.commit()
            raise HTTPException(
                status_code=401, detail="Refresh token inválido o revocado"
            )
        new_access_token = Security.generate_access_token(user)
        new_refresh_token = Security.generate_refresh_token(user)
        user.refresh_token = new_refresh_token
        db.commit()
        response_body = {"access_token": new_access_token, "token_type": "bearer"}
        json_response = JSONResponse(content=response_body)
        json_response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="strict",
            secure=True,
        )
        logger.info(f"Nuevos tokens generados para el usuario '{username}'.")
        return json_response
    except jwt.ExpiredSignatureError:
        logger.warning("Intento de usar un refresh token expirado.")
        raise HTTPException(status_code=401, detail="Refresh token ha expirado")
    except jwt.InvalidTokenError:
        logger.warning("Intento de usar un refresh token inválido.")
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en refresh_access_token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
