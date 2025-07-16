# routes/admin_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# -----------------------------------------------------------------------------
# Este archivo define todos los endpoints que son exclusivos para usuarios
# con el rol de 'administrador'. Todas las rutas aquí están protegidas por la
# dependencia 'is_admin'.
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from config.db import get_db
import math
from typing import Optional
from models.models import (
    User,
    UserDetail,
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
from auth.security import is_admin

# Creación de un router específico para las rutas de administración.
admin_router = APIRouter()


@admin_router.get("/admin/users/all", response_model=PaginatedResponse[UserOut])
def get_all_users(
    # 'Query' permite definir validaciones y metadatos para los parámetros de la URL.
    page: int = Query(1, ge=1, description="Número de página"),  # ge = greater or equal
    size: int = Query(
        10, ge=1, le=100, description="Tamaño de la página"
    ),  # le = less or equal
    # Parámetros de filtrado opcionales.
    username: Optional[str] = Query(
        None, description="Filtrar por nombre de usuario (empieza con...)"
    ),
    email: Optional[str] = Query(
        None, description="Filtrar por email (empieza con...)"
    ),
    dni: Optional[int] = Query(None, description="Filtrar por DNI exacto"),
    firstname: Optional[str] = Query(
        None, description="Filtrar por nombre (contiene...)"
    ),
    lastname: Optional[str] = Query(
        None, description="Filtrar por apellido (contiene...)"
    ),
    # La dependencia 'is_admin' se ejecuta antes que esta función. Si el usuario no es admin,
    # la petición se detiene y se devuelve un error 403.
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Obtiene una lista paginada y filtrada de todos los usuarios del sistema."""
    try:
        # Consulta base que une las tablas de usuarios y detalles para poder filtrar por ambas.
        query = db.query(User).join(User.userdetail)

        # Construcción dinámica de filtros basada en los parámetros de la query.
        filters = []
        if username:
            filters.append(
                User.username.ilike(f"{username}%")
            )  # ilike es case-insensitive LIKE.
        if email:
            filters.append(User.email.ilike(f"{email}%"))
        if dni:
            filters.append(UserDetail.dni == dni)
        if firstname:
            filters.append(UserDetail.firstname.ilike(f"{firstname}%"))
        if lastname:
            filters.append(UserDetail.lastname.ilike(f"{lastname}%"))

        # Si hay filtros, se aplican a la consulta.
        if filters:
            query = query.filter(
                *filters
            )  # El operador '*' desempaqueta la lista de filtros.

        # Se cuenta el total de resultados después de filtrar para la paginación.
        total_items = query.count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=1, items=[]
            )

        # Se calcula el 'offset' para la paginación y se ejecuta la consulta.
        offset = (page - 1) * size
        users_query = (
            query.options(joinedload(User.userdetail)).offset(offset).limit(size).all()
        )
        total_pages = math.ceil(total_items / size)

        # Se transforma la lista de objetos SQLAlchemy a una lista de objetos Pydantic 'UserOut'.
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
            if user.userdetail
        ]

        # Se devuelve la respuesta paginada.
        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        db.rollback()


@admin_router.get(
    "/admin/subscriptions/all", response_model=PaginatedResponse[SubscriptionOut]
)
def get_all_subscriptions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Obtiene una lista paginada de TODAS las suscripciones en el sistema."""
    try:
        offset = (page - 1) * size
        total_items = db.query(Subscription).count()

        # Usamos 'joinedload' anidado para cargar eficientemente todos los datos relacionados
        # (Suscripción -> Usuario -> Detalles de Usuario y Suscripción -> Plan) en una sola consulta.
        subscriptions_query = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.user).joinedload(User.userdetail),
                joinedload(Subscription.plan),
            )
            .offset(offset)
            .limit(size)
            .all()
        )
        total_pages = math.ceil(total_items / size)

        # Se formatea la respuesta para que coincida con el modelo 'SubscriptionOut',
        # que espera objetos anidados 'UserOut' y 'PlanOut'.
        items_list = [
            SubscriptionOut(
                id=sub.id,
                status=sub.status,
                subscription_date=sub.subscription_date,
                user=UserOut(
                    username=sub.user.username,
                    email=sub.user.email,
                    dni=sub.user.userdetail.dni,
                    firstname=sub.user.userdetail.firstname,
                    lastname=sub.user.userdetail.lastname,
                    address=sub.user.userdetail.address,
                    phone=sub.user.userdetail.phone,
                    role=sub.user.role,
                ),
                plan=PlanOut(
                    id=sub.plan.id,
                    name=sub.plan.name,
                    speed_mbps=sub.plan.speed_mbps,
                    price=sub.plan.price,
                ),
            )
            for sub in subscriptions_query
        ]

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@admin_router.get("/admin/payments/all", response_model=PaginatedResponse[PaymentOut])
def get_all_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Obtiene una lista paginada de TODOS los pagos en el sistema."""
    try:
        offset = (page - 1) * size
        total_items = db.query(Payment).count()
        payments_query = db.query(Payment).offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=payments_query,
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@admin_router.put("/admin/users/{user_id}/details")
def update_user_details(
    user_id: int,
    user_data: UpdateUserDetail,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Endpoint para que un administrador actualice los detalles de un cliente."""
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update or not user_to_update.userdetail:
            return JSONResponse(
                status_code=404,
                content={"message": "Usuario o sus detalles no encontrados"},
            )

        # Actualización parcial: solo se modifican los campos que vienen en el request.
        if user_data.firstname is not None:
            user_to_update.userdetail.firstname = user_data.firstname
        if user_data.lastname is not None:
            user_to_update.userdetail.lastname = user_data.lastname
        if user_data.address is not None:
            user_to_update.userdetail.address = user_data.address
        if user_data.phone is not None:
            user_to_update.userdetail.phone = user_data.phone

        db.commit()
        return {
            "message": f"Detalles del usuario con ID {user_id} actualizados exitosamente."
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@admin_router.put("/admin/subscriptions/{subscription_id}/status")
def update_subscription_status(
    subscription_id: int,
    sub_data: UpdateSubscriptionStatus,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Endpoint para que un administrador actualice el estado de una suscripción."""
    try:
        subscription_to_update = (
            db.query(Subscription).filter(Subscription.id == subscription_id).first()
        )
        if not subscription_to_update:
            return JSONResponse(
                status_code=404, content={"message": "Suscripción no encontrada"}
            )

        subscription_to_update.status = sub_data.status
        db.commit()
        return {
            "message": f"Estado de la suscripción {subscription_id} actualizado a '{sub_data.status}'."
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@admin_router.put("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: UpdateUserRole,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Endpoint para que un administrador cambie el rol de otro usuario."""
    token_user_id = admin_user.get("user_id")
    # Regla de negocio: un administrador no puede cambiar su propio rol.
    if token_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede cambiar su propio rol.",
        )

    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        user_to_update.role = role_data.role
        db.commit()
        return {
            "message": f"Rol del usuario {user_id} actualizado a '{role_data.role}'."
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@admin_router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int, admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    """Endpoint para que un administrador elimine a un usuario y todos sus datos en cascada."""
    token_user_id = admin_user.get("user_id")
    # Regla de negocio: un administrador no puede eliminarse a sí mismo.
    if token_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede eliminarse a sí mismo.",
        )

    try:
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        # Gracias a la configuración 'cascade="all, delete-orphan"' en el modelo User,
        # al borrar el usuario se borrarán también sus detalles, pagos, suscripciones y facturas.
        db.delete(user_to_delete)
        db.commit()
        return {
            "message": f"Usuario con ID {user_id} y todos sus datos han sido eliminados."
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
