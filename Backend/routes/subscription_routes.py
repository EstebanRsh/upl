# routes/subscription_routes.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from models.models import session, Subscription, InputSubscription, User
from auth.security import Security
from sqlalchemy.orm import joinedload  # Para cargas eficientes
from auth.security import is_admin

subscription_router = APIRouter()


@subscription_router.post("/subscriptions/assign")
# La firma de la función ahora usa la dependencia 'is_admin'
def assign_plan_to_user(
    sub_data: InputSubscription, admin_user: dict = Depends(is_admin)
):
    """
    Endpoint para que un administrador asigne un plan a un cliente.
    Protegido por el rol de administrador.
    """
    try:
        # La lógica de la función ya es correcta
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
def get_user_subscriptions(user_id: int, req: Request):
    # Verificar token
    has_access = Security.verify_token(req.headers)
    if not "iat" in has_access:
        return JSONResponse(status_code=401, content=has_access)

    try:
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

        # Mapear los resultados a un formato limpio para el frontend
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
