# routes/admin_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from config.db import get_db
import math
from typing import Optional
from models.models import (
    User,
    UserDetail,
    InputUser,
    Payment,
    UpdateUserDetail,
    Subscription,
    UpdateSubscriptionStatus,
    PaginatedResponse,
    UserOut,
    SubscriptionOut,
    PaymentOut,
    PlanOut,
    UpdateUserRole,
)
from sqlalchemy.orm import joinedload
from auth.security import is_admin, Security
from sqlalchemy.exc import IntegrityError

admin_router = APIRouter()

# --- RUTAS DE ADMINISTRACIÓN DE USUARIOS ---


@admin_router.post(
    "/users/add",
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    description="**Permisos requeridos: `administrador`**.<br>Registra un nuevo usuario (cliente) y sus detalles personales en el sistema.",
)
def add_user(user_data: InputUser, db: Session = Depends(get_db)):
    """Registra un nuevo usuario (cliente) y sus detalles personales."""
    try:
        new_user_detail = UserDetail(
            dni=user_data.dni,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            address=user_data.address,
            phone=user_data.phone,
        )
        hashed_password = Security.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            password=hashed_password,
            email=user_data.email,
            role="cliente",
        )
        new_user.userdetail = new_user_detail
        db.add(new_user)
        db.commit()
        return {"message": "Cliente agregado exitosamente"}
    except IntegrityError:
        db.rollback()  # Es importante revertir la transacción fallida
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{user_data.username}' o el email '{user_data.email}' ya existen.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get(
    "/users/all",
    response_model=PaginatedResponse[UserOut],
    summary="Obtener todos los usuarios",
    description="**Permisos requeridos: `administrador`**.<br>Obtiene una lista paginada y opcionalmente filtrada por nombre de todos los usuarios del sistema.",
)
def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    username: Optional[str] = Query(None),
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Obtiene una lista paginada y filtrada de todos los usuarios del sistema."""
    query = db.query(User).join(User.userdetail)
    if username:
        query = query.filter(User.username.ilike(f"{username}%"))

    total_items = query.count()
    offset = (page - 1) * size
    users_query = (
        query.options(joinedload(User.userdetail)).offset(offset).limit(size).all()
    )
    total_pages = math.ceil(total_items / size)

    # --- INICIO DE LA CORRECCIÓN ---
    # Se construye manualmente la lista de respuesta para que coincida con el modelo UserOut.
    items_list = [
        UserOut(
            username=user.username,
            email=user.email,
            dni=user.userdetail.dni,
            firstname=user.userdetail.firstname,
            lastname=user.userdetail.lastname,
            address=user.userdetail.address,
            phone=user.userdetail.phone,
            role=user.role,
        )
        for user in users_query
        if user.userdetail  # Nos aseguramos de que el usuario tenga detalles
    ]
    # --- FIN DE LA CORRECCIÓN ---

    return PaginatedResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        items=items_list,
    )


@admin_router.put(
    "/users/{user_id}/details",
    summary="Actualizar detalles de un usuario",
    description="**Permisos requeridos: `administrador`**.<br>Permite a un administrador actualizar los detalles personales de cualquier cliente.",
)
def update_user_details(
    user_id: int,
    user_data: UpdateUserDetail,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Endpoint para que un administrador actualice los detalles de un cliente."""
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update or not user_to_update.userdetail:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_to_update.userdetail, key, value)

    db.commit()
    return {
        "message": f"Detalles del usuario con ID {user_id} actualizados exitosamente."
    }


@admin_router.delete(
    "/users/{user_id}",
    summary="Eliminar un usuario",
    description="**Permisos requeridos: `administrador`**.<br>Elimina a un usuario y todos sus datos asociados en cascada. Un administrador no puede eliminarse a sí mismo.",
)
def delete_user(
    user_id: int, admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    """Endpoint para que un administrador elimine a un usuario y todos sus datos en cascada."""
    token_user_id = admin_user.get("user_id")
    if token_user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Un administrador no puede eliminarse a sí mismo."
        )

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user_to_delete)
    db.commit()
    return {
        "message": f"Usuario con ID {user_id} y todos sus datos han sido eliminados."
    }
