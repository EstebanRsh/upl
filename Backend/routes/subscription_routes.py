# routes/subscription_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE SUSCRIPCIONES
# -----------------------------------------------------------------------------
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.models import Subscription, InputSubscription, User
from auth.security import is_admin, get_current_user
from config.db import get_db

logger = logging.getLogger(__name__)
subscription_router = APIRouter()


@subscription_router.post(
    "/admin/subscriptions/assign", status_code=status.HTTP_201_CREATED
)
def assign_plan_to_user(
    sub_data: InputSubscription,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' asignando plan ID {sub_data.plan_id} a usuario ID {sub_data.user_id}."
    )
    try:
        user = db.query(User).filter(User.id == sub_data.user_id).first()
        if not user:
            logger.warning(
                f"Intento de asignar plan a usuario no existente (ID: {sub_data.user_id})."
            )
            raise HTTPException(
                status_code=404,
                detail=f"Usuario con ID {sub_data.user_id} no encontrado.",
            )
        new_subscription = Subscription(
            user_id=sub_data.user_id, plan_id=sub_data.plan_id
        )
        db.add(new_subscription)
        db.commit()
        logger.info(
            f"Plan ID {sub_data.plan_id} asignado exitosamente a usuario ID {sub_data.user_id}."
        )
        return {"message": "Plan asignado al cliente exitosamente."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en assign_plan_to_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@subscription_router.get("/users/{user_id}/subscriptions")
def get_user_subscriptions(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando suscripciones del usuario ID: {user_id}."
    )
    try:
        # ... (lógica de permisos y consulta sin cambios) ...
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")
        if token_user_role != "administrador" and token_user_id != user_id:
            logger.warning(
                f"Acceso no autorizado a suscripciones del usuario ID {user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver las suscripciones de otro usuario.",
            )
        user = (
            db.query(User)
            .options(joinedload(User.subscriptions).joinedload(Subscription.plan))
            .filter(User.id == user_id)
            .first()
        )
        if not user:
            logger.warning(
                f"Usuario no encontrado al buscar suscripciones (ID: {user_id})."
            )
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        subscriptions_list = [
            {
                "subscription_id": sub.id,
                "status": sub.status,
                "subscription_date": sub.subscription_date.isoformat(),
                "plan_details": {
                    "id": sub.plan.id,
                    "name": sub.plan.name,
                    "speed_mbps": sub.plan.speed_mbps,
                    "price": sub.plan.price,
                },
            }
            for sub in user.subscriptions
        ]
        logger.info(
            f"Devolviendo {len(subscriptions_list)} suscripciones para el usuario ID: {user_id}."
        )
        return subscriptions_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado en get_user_subscriptions (ID: {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
