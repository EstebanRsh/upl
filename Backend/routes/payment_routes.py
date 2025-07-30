# routes/payment_routes.py
import logging
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

# --- INICIO DE LA CORRECCIÓN DE IMPORTACIONES ---
from models.models import Payment, InputPayment, Invoice
from schemas.payment_schemas import PaymentOut
from schemas.common_schemas import PaginatedResponse

# --- FIN DE LA CORRECCIÓN DE IMPORTACIONES ---

from auth.security import Security
from config.db import get_db
from services.payment_service import process_new_payment, PaymentException

logger = logging.getLogger(__name__)
payment_router = APIRouter()


def verify_admin_permission(authorization: str = Header(...)):
    """Verifica que el token en la cabecera pertenezca a un administrador."""
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success") or token_data.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción.",
        )
    return token_data


@payment_router.post(
    "/admin/payments/add",
    summary="Registrar un nuevo pago",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def add_payment(payment_data: InputPayment, db: Session = Depends(get_db)):
    logger.info(
        f"Iniciando el registro de un pago para el usuario ID {payment_data.user_id}."
    )
    try:
        result = process_new_payment(payment_data, db)
        db.commit()
        logger.info(
            f"Pago para usuario ID {payment_data.user_id} procesado y confirmado."
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=result)
    except PaymentException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en la ruta add_payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error interno.")


@payment_router.get(
    "/users/{user_id}/payments",
    response_model=PaginatedResponse[PaymentOut],
    tags=["Pagos"],
)
def get_user_payments(
    user_id: int,
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    requesting_user_id = token_data.get("user_id")
    requesting_user_role = token_data.get("role")

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
