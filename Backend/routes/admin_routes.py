# routes/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import math
from models.models import (
    session,
    User,
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
from auth.security import is_admin

admin_router = APIRouter()


@admin_router.get("/admin/users/all", response_model=PaginatedResponse[UserOut])
def get_all_users(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de la página"),
    admin_user: dict = Depends(is_admin),
):
    """
    Obtiene una lista paginada de todos los usuarios del sistema.
    """
    try:
        # 1. Calcular el offset para la consulta
        offset = (page - 1) * size

        # 2. Obtener el total de usuarios para calcular las páginas
        total_items = session.query(User).count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=1, items=[]
            )

        # 3. Realizar la consulta paginada
        users_query = (
            session.query(User)
            .options(joinedload(User.userdetail))
            .offset(offset)
            .limit(size)
            .all()
        )

        # 4. Calcular el total de páginas
        total_pages = math.ceil(total_items / size)

        # 5. Formatear la respuesta
        # Aquí transformamos los objetos User/UserDetail a un formato limpio
        # similar al modelo InputUser para no exponer la contraseña.
        items_list = []
        for user in users_query:
            if user.userdetail:
                items_list.append(
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
                )

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    finally:
        session.close()


@admin_router.get(
    "/admin/subscriptions/all", response_model=PaginatedResponse[SubscriptionOut]
)
def get_all_subscriptions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(is_admin),
):
    """Obtiene una lista paginada de TODAS las suscripciones en el sistema."""
    try:
        offset = (page - 1) * size
        total_items = session.query(Subscription).count()

        # Usamos joinedload para cargar los datos del usuario y del plan en una sola consulta
        subscriptions_query = (
            session.query(Subscription)
            .options(
                joinedload(Subscription.user).joinedload(User.userdetail),
                joinedload(Subscription.plan),
            )
            .offset(offset)
            .limit(size)
            .all()
        )

        total_pages = math.ceil(total_items / size)

        # Formateamos la respuesta para que coincida con el modelo SubscriptionOut
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
    finally:
        session.close()


@admin_router.get("/admin/payments/all", response_model=PaginatedResponse[PaymentOut])
def get_all_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(is_admin),
):
    """Obtiene una lista paginada de TODOS los pagos en el sistema."""
    try:
        offset = (page - 1) * size
        total_items = session.query(Payment).count()

        payments_query = session.query(Payment).offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=payments_query,
        )
    finally:
        session.close()


@admin_router.put("/admin/users/{user_id}/details")
def update_user_details(
    user_id: int, user_data: UpdateUserDetail, admin_user: dict = Depends(is_admin)
):
    """
    Endpoint para que un administrador actualice los detalles de un cliente.
    """
    try:
        # 1. Buscar al usuario que se quiere modificar
        user_to_update = session.query(User).filter(User.id == user_id).first()

        if not user_to_update or not user_to_update.userdetail:
            return JSONResponse(
                status_code=404,
                content={"message": "Usuario o sus detalles no encontrados"},
            )

        # 2. Actualizar solo los campos que se enviaron en la petición
        if user_data.firstname is not None:
            user_to_update.userdetail.firstname = user_data.firstname
        if user_data.lastname is not None:
            user_to_update.userdetail.lastname = user_data.lastname
        if user_data.address is not None:
            user_to_update.userdetail.address = user_data.address
        if user_data.phone is not None:
            user_to_update.userdetail.phone = user_data.phone

        # 3. Guardar los cambios en la base de datos
        session.commit()

        return {
            "message": f"Detalles del usuario con ID {user_id} actualizados exitosamente."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@admin_router.put("/admin/subscriptions/{subscription_id}/status")
def update_subscription_status(
    subscription_id: int,
    sub_data: UpdateSubscriptionStatus,
    admin_user: dict = Depends(is_admin),  # Protegido por rol de admin
):
    """
    Endpoint para que un administrador actualice el estado de una suscripción.
    """
    try:
        # 1. Buscar la suscripción por su ID
        subscription_to_update = (
            session.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )

        if not subscription_to_update:
            return JSONResponse(
                status_code=404, content={"message": "Suscripción no encontrada"}
            )

        # 2. Actualizar el estado y guardar los cambios
        subscription_to_update.status = sub_data.status
        session.commit()

        return {
            "message": f"Estado de la suscripción {subscription_id} actualizado a '{sub_data.status}'."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@admin_router.put("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int, role_data: UpdateUserRole, admin_user: dict = Depends(is_admin)
):
    """
    Endpoint para que un administrador cambie el rol de otro usuario.
    """
    # Validación para que un administrador no pueda quitarse su propio rol por accidente
    token_user_id = admin_user.get("user_id")
    if token_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede cambiar su propio rol.",
        )

    try:
        user_to_update = session.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        # Actualizamos el rol y guardamos
        user_to_update.role = role_data.role
        session.commit()

        return {
            "message": f"Rol del usuario {user_id} actualizado a '{role_data.role}'."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@admin_router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, admin_user: dict = Depends(is_admin)):
    """
    Endpoint para que un administrador elimine a un usuario y todos sus datos.
    """
    # Un administrador no puede eliminarse a sí mismo
    token_user_id = admin_user.get("user_id")
    if token_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede eliminarse a sí mismo.",
        )

    try:
        user_to_delete = session.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        # Gracias a la configuración de cascada, solo necesitamos borrar el objeto User
        session.delete(user_to_delete)
        session.commit()

        return {
            "message": f"Usuario con ID {user_id} y todos sus datos han sido eliminados."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()
