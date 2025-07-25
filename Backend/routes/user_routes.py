# routes/user_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE USUARIOS (REGISTRO Y LOGIN)
# -----------------------------------------------------------------------------
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import User, InputLogin, UpdateMyDetails, UpdateMyPassword, UserOut
from auth.security import Security, get_current_user
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

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado durante el login del usuario '{username}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor.",
        )


@user_router.get(
    "/users/me",
    response_model=UserOut,
    summary="Consultar mi perfil",
    description="**Permisos requeridos: `autenticado`**.<br>Devuelve la información del perfil del usuario que realiza la petición.",
    tags=["Cliente"],
)
def get_my_profile(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")
    logger.info(f"Usuario ID {user_id} solicitando su perfil.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.userdetail:
        logger.error(
            f"No se encontró el perfil para el usuario ID {user_id} que está autenticado."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado."
        )

    user_data_for_response = {
        **user.userdetail.__dict__,  # Copia todos los campos de userdetail
        "username": user.username,  # Añade el username desde user
        "email": user.email,  # Añade el email desde user
        "role": user.role_obj.name,  # Añade el nombre del rol desde la relación
    }

    return UserOut.model_validate(user_data_for_response)


@user_router.put(
    "/users/me",
    summary="Actualizar mis datos",
    description="**Permisos requeridos: `autenticado`**.<br>Permite al usuario actualizar su información de contacto.",
    tags=["Cliente"],
)
def update_my_details(
    user_data: UpdateMyDetails,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    logger.info(f"Usuario ID {user_id} está actualizando sus datos personales.")
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update or not user_to_update.userdetail:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_data = user_data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=400, detail="No se proporcionaron datos para actualizar."
            )

        for key, value in update_data.items():
            setattr(user_to_update.userdetail, key, value)

        db.commit()
        logger.info(f"Datos del usuario ID {user_id} actualizados correctamente.")
        return {"message": "Tus datos han sido actualizados exitosamente."}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error actualizando detalles para usuario ID {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error interno al actualizar tus datos."
        )


@user_router.put(
    "/users/me/password",
    summary="Cambiar mi contraseña",
    description="**Permisos requeridos: `autenticado`**.<br>Permite al usuario cambiar su propia contraseña.",
    tags=["Cliente"],
)
def update_my_password(
    password_data: UpdateMyPassword,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    logger.info(f"Usuario ID {user_id} iniciando cambio de contraseña.")
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if not Security.verify_password(password_data.current_password, user.password):
            logger.warning(
                f"Intento fallido de cambio de contraseña para usuario ID {user_id}: contraseña actual incorrecta."
            )
            raise HTTPException(
                status_code=400, detail="La contraseña actual es incorrecta."
            )

        user.password = Security.get_password_hash(password_data.new_password)
        db.commit()

        logger.info(f"Contraseña del usuario ID {user_id} cambiada exitosamente.")
        return {"message": "Contraseña actualizada exitosamente."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error cambiando contraseña para usuario ID {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error interno al cambiar la contraseña."
        )
