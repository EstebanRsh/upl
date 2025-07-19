# routes/subscription_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.models import Subscription, InputSubscription, User
from auth.security import has_permission, get_current_user
from config.db import get_db

logger = logging.getLogger(__name__)
subscription_router = APIRouter()


@subscription_router.post(
    "/admin/subscriptions/assign",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission("users:update"))],
)
def assign_plan_to_user(sub_data: InputSubscription, db: Session = Depends(get_db)):
    logger.info(
        f"Asignando plan ID {sub_data.plan_id} a usuario ID {sub_data.user_id}."
    )
    try:
        if not db.query(User).filter_by(id=sub_data.user_id).first():
            raise HTTPException(
                status_code=404,
                detail=f"Usuario con ID {sub_data.user_id} no encontrado.",
            )

        new_subscription = Subscription(
            user_id=sub_data.user_id, plan_id=sub_data.plan_id
        )
        db.add(new_subscription)
        db.commit()
        return {"message": "Plan asignado al cliente exitosamente."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en assign_plan_to_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@subscription_router.get("/users/{user_id}/subscriptions")
def get_user_subscriptions(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Esta ruta no cambia, su lógica de permisos es correcta
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando suscripciones del usuario ID: {user_id}."
    )
    try:
        user_has_permission = (
            "users:read_all" in current_user.get("permissions", set())
            or current_user.get("user_id") == user_id
        )
        if not user_has_permission:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver estas suscripciones.",
            )

        user = (
            db.query(User)
            .options(joinedload(User.subscriptions).joinedload(Subscription.plan))
            .filter_by(id=user_id)
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return user.subscriptions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error en get_user_subscriptions (ID: {user_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
