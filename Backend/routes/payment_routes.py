# routes/payment_routes.py
import logging
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session, joinedload

from models.models import Payment, Invoice
from schemas.payment_schemas import PaymentOut
from schemas.common_schemas import PaginatedResponse
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
# Cambiamos el prefijo para que todas las rutas aquí empiecen con /api/payments
payment_router = APIRouter(prefix="/payments", tags=["Pagos"])


@payment_router.get(
    "/user/{user_id}",
    response_model=PaginatedResponse[PaymentOut],
    summary="Obtener los pagos de un usuario específico",
)
def get_user_payments(
    user_id: int,
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Endpoint para que un administrador o el propio usuario puedan ver un historial de pagos.
    """
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    requesting_user_id = token_data.get("user_id")
    requesting_user_role = token_data.get("role")

    # Solo el admin o el propio usuario pueden ver los pagos
    if requesting_user_role != "administrador" and requesting_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estos pagos.",
        )

    query = (
        db.query(Payment)
        .filter_by(user_id=user_id)
        .order_by(Payment.payment_date.desc())
    )

    total_items = query.count()
    payments = (
        query.options(joinedload(Payment.invoice).joinedload(Invoice.subscription))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return PaginatedResponse(
        total_items=total_items,
        total_pages=math.ceil(total_items / size),
        current_page=page,
        items=payments,
    )
