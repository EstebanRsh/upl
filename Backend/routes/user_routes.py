# routes/user_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE USUARIOS (REGISTRO Y LOGIN)
# -----------------------------------------------------------------------------
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import User, InputLogin
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
user_router = APIRouter()


@user_router.post(
    "/users/login",
    summary="Iniciar sesión",
)
def login(user_credentials: InputLogin, db: Session = Depends(get_db)):
    username = user_credentials.username
    logger.info(f"Intento de inicio de sesión para el usuario: '{username}'.")
    try:
        user_in_db = db.query(User).filter(User.username == username).first()

        if not user_in_db or not Security.verify_password(
            user_credentials.password, user_in_db.password
        ):
            logger.warning(f"Credenciales incorrectas para el usuario: '{username}'.")
            # Lanzamos la excepción de forma normal. FastAPI la manejará.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )

        # Si todo va bien, continuamos...
        logger.info(
            f"Usuario '{username}' autenticado correctamente. Generando tokens."
        )
        access_token = Security.generate_access_token(user_in_db)
        refresh_token = Security.generate_refresh_token(user_in_db)

        user_in_db.refresh_token = refresh_token
        db.commit()

        response_body = {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
        }
        response = JSONResponse(content=response_body)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=True,
        )
        logger.info(
            f"Tokens enviados y cookie de refresco establecida para '{username}'."
        )
        return response

    # --- CAMBIO IMPORTANTE AQUÍ ---
    # Atrapamos primero la HTTPException y la volvemos a lanzar sin registrarla como error.
    except HTTPException:
        raise

    # Atrapamos cualquier otra excepción que SÍ es un error inesperado.
    except Exception as e:
        db.rollback()  # Es importante hacer rollback en caso de error de BD.
        logger.error(
            f"Error inesperado durante el login del usuario '{username}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor.",
        )
