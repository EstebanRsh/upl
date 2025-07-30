# routes/subscription_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session, joinedload

# --- INICIO DE LA CORRECCIÓN DE IMPORTACIONES ---
from models.models import Subscription, InputSubscription, User

# No se necesitan schemas de respuesta específicos para este archivo por ahora
# --- FIN DE LA CORRECCIÓN DE IMPORTACIONES ---

from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
subscription_router = APIRouter()


def verify_admin_permission(authorization: str = Header(...)):
    """Verifica que el token en la cabecera pertenezca a un administrador."""
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success") or token_data.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción.",
        )
    return token_data


@subscription_router.post(
    "/admin/subscriptions/assign",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
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
    except Exception as e:
        db.rollback()
        logger.error(f"Error en assign_plan_to_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@subscription_router.get("/users/{user_id}/subscriptions", tags=["Suscripciones"])
def get_user_subscriptions(
    user_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    requesting_user_id = token_data.get("user_id")
    requesting_user_role = token_data.get("role")

    logger.info(
        f"Usuario ID {requesting_user_id} solicitando suscripciones del usuario ID: {user_id}."
    )

    if requesting_user_role != "administrador" and requesting_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
