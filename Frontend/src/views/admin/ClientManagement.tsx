# routes/subscription_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from models.models import Subscription, InputSubscription, User, Plan # Aseguramos que Plan esté importado
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
subscription_router = APIRouter()


# Schema para recibir el nuevo estado en el body del PUT
class SubscriptionStatusUpdate(BaseModel):
    status: str


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
    logger.info(f"Asignando plan ID {sub_data.plan_id} a usuario ID {sub_data.user_id}.")
    
    # Verificamos que tanto el usuario como el plan existan
    if not db.query(User).filter_by(id=sub_data.user_id).first():
        raise HTTPException(status_code=404, detail=f"Usuario con ID {sub_data.user_id} no encontrado.")
    if not db.query(Plan).filter_by(id=sub_data.plan_id).first():
        raise HTTPException(status_code=404, detail=f"Plan con ID {sub_data.plan_id} no encontrado.")

    # Verificamos si ya existe una suscripción activa para evitar duplicados
    existing_active_sub = db.query(Subscription).filter_by(
        user_id=sub_data.user_id, status='active'
    ).first()
    if existing_active_sub:
        raise HTTPException(
            status_code=409, # Conflict
            detail="El cliente ya tiene una suscripción activa. Cancela la anterior antes de asignar una nueva."
        )

    new_subscription = Subscription(user_id=sub_data.user_id, plan_id=sub_data.plan_id)
    db.add(new_subscription)
    db.commit()
    return {"message": "Plan asignado al cliente exitosamente."}


# --- NUEVA FUNCIÓN AÑADIDA ---
@subscription_router.put(
    "/admin/subscriptions/{subscription_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def update_subscription_status(
    subscription_id: int,
    update_data: SubscriptionStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una suscripción (ej: 'active', 'suspended', 'cancelled').
    """
    logger.info(f"Cambiando estado de la suscripción ID {subscription_id} a '{update_data.status}'.")
    
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada.")

    valid_statuses = ["active", "suspended", "cancelled"]
    if update_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado '{update_data.status}' no es válido.")

    subscription.status = update_data.status
    db.commit()
    
    return {"message": f"El estado de la suscripción ha sido actualizado a '{update_data.status}'."}


@subscription_router.get(
    "/users/{user_id}/subscriptions", 
    tags=["Suscripciones"]
)
def get_user_subscriptions(
    user_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(status_code=401, detail=token_data.get("message"))

    requesting_user_id = token_data.get("user_id")
    requesting_user_role = token_data.get("role")

    if requesting_user_role != "administrador" and requesting_user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver estas suscripciones.")

    user = (
        db.query(User)
        .options(joinedload(User.subscriptions).joinedload(Subscription.plan))
        .filter_by(id=user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user.subscriptions