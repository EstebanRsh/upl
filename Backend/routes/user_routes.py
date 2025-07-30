# Backend/routes/user_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from models.models import User, InputLogin, UserOut, UpdateMyDetails, UpdateMyPassword
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
user_router = APIRouter()


@user_router.post("/users/login", summary="Iniciar sesión")
def login(user_credentials: InputLogin, db: Session = Depends(get_db)):
    username = user_credentials.username
    logger.info(f"Intento de inicio de sesión para: '{username}'.")
    try:
        user_in_db = (
            db.query(User)
            .options(joinedload(User.userdetail))
            .filter(User.username == username)
            .first()
        )

        if not user_in_db or not Security.verify_password(
            user_credentials.password, user_in_db.password
        ):
            logger.warning(f"Credenciales incorrectas para: '{username}'.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )

        if not user_in_db.userdetail:
            logger.error(
                f"¡CRÍTICO! El usuario '{username}' no tiene un UserDetail asociado."
            )
            raise HTTPException(
                status_code=500,
                detail="Error de configuración de la cuenta de usuario.",
            )

        logger.info(
            f"Usuario '{username}' autenticado. Rol: '{user_in_db.userdetail.type}'. Generando token."
        )

        access_token = Security.generate_token(user_in_db)
        if not access_token:
            raise HTTPException(
                status_code=500, detail="No se pudo generar el token de acceso."
            )

        user_info_for_frontend = {
            "username": user_in_db.username,
            "first_name": user_in_db.userdetail.firstname,
            "role": user_in_db.userdetail.type,
        }

        return JSONResponse(
            content={
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_info_for_frontend,
            }
        )
    except HTTPException as http_exc:
        raise http_exc
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


@user_router.get("/users/me", response_model=UserOut, tags=["Cliente"])
def get_my_profile(authorization: str = Header(...), db: Session = Depends(get_db)):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido, no contiene ID de usuario.",
        )

    logger.info(f"Usuario ID {user_id} solicitando su perfil.")
    user = (
        db.query(User)
        .options(joinedload(User.userdetail))
        .filter(User.id == user_id)
        .first()
    )

    if not user or not user.userdetail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado."
        )

    user_response = UserOut(
        username=user.username,
        email=user.email,
        dni=user.userdetail.dni,
        firstname=user.userdetail.firstname,
        lastname=user.userdetail.lastname,
        address=user.userdetail.address,
        barrio=user.userdetail.barrio,
        city=user.userdetail.city,
        phone=user.userdetail.phone,
        phone2=user.userdetail.phone2,
        role=user.userdetail.type,
    )
    return user_response


@user_router.put("/users/me", summary="Actualizar mis datos", tags=["Cliente"])
def update_my_details(
    user_data: UpdateMyDetails,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    user_id = token_data.get("user_id")
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update or not user_to_update.userdetail:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_to_update.userdetail, key, value)

    db.commit()
    return {"message": "Tus datos han sido actualizados exitosamente."}


@user_router.put(
    "/users/me/password", summary="Cambiar mi contraseña", tags=["Cliente"]
)
def update_my_password(
    password_data: UpdateMyPassword,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    user_id = token_data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not Security.verify_password(password_data.current_password, user.password):
        raise HTTPException(
            status_code=400, detail="La contraseña actual es incorrecta."
        )

    user.password = Security.get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada exitosamente."}
