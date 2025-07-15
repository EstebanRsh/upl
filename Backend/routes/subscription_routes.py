# routes/subscription_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE SUSCRIPCIONES
# -----------------------------------------------------------------------------
# Este módulo se encarga de la lógica relacionada con las suscripciones de los
# clientes a los planes de internet.
# 1. Asignar un plan a un usuario (acción administrativa).
# 2. Consultar las suscripciones de un usuario específico.
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.models import session, Subscription, InputSubscription, User
from auth.security import Security
from sqlalchemy.orm import joinedload
from auth.security import is_admin, get_current_user

# Creación de un router específico para las rutas de suscripciones.
subscription_router = APIRouter()


@subscription_router.post("admin/subscriptions/assign")
def assign_plan_to_user(
    sub_data: InputSubscription, admin_user: dict = Depends(is_admin)
):
    """Endpoint para que un administrador asigne un plan a un cliente."""
    try:
        new_subscription = Subscription(
            user_id=sub_data.user_id, plan_id=sub_data.plan_id
        )
        session.add(new_subscription)
        session.commit()
        return {"message": "Plan asignado al cliente exitosamente."}
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@subscription_router.get("/users/{user_id}/subscriptions")
def get_user_subscriptions(
    user_id: int, current_user: dict = Depends(get_current_user)
):
    """
    Obtiene las suscripciones de un usuario, incluyendo detalles del plan.
    NOTA: La verificación del token en esta ruta es manual. Podría refactorizarse
    para usar 'Depends(get_current_user)' para mayor consistencia y seguridad,
    y para definir mejor quién puede acceder a esta información.
    """
    token_user_id = current_user.get("user_id")
    token_user_role = current_user.get("role")
    if token_user_role != "administrador" and token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver las suscripciones de otro usuario.",
        )
    try:
        # 'joinedload' se usa para cargar eficientemente las suscripciones y los planes
        # asociados en una sola consulta, evitando el problema de N+1 queries.
        user = (
            session.query(User)
            .filter(User.id == user_id)
            .options(joinedload(User.subscriptions).joinedload(Subscription.plan))
            .first()
        )
        if not user:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        # Se mapean los resultados a una lista de diccionarios para una respuesta JSON limpia.
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
        return subscriptions_list
    finally:
        session.close()
