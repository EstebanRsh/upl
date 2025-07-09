# routes/admin_routes.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from models.models import (
    session,
    User,
    UpdateUserDetail,
    Subscription,
    UpdateSubscriptionStatus,
)
from auth.security import is_admin

admin_router = APIRouter()


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
