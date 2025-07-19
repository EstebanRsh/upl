# routes/payment_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PAGOS
# -----------------------------------------------------------------------------
# routes/payment_routes.py
import logging
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from models.models import Payment, InputPayment, Invoice, PaginatedResponse, PaymentOut
from auth.security import get_current_user, has_permission
from config.db import get_db
from services.payment_service import process_new_payment, PaymentException

logger = logging.getLogger(__name__)
payment_router = APIRouter()


@payment_router.post(
    "/payments/add",
    summary="Registrar un nuevo pago",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission("payments:create"))],
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
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en la ruta add_payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error interno.")


@payment_router.get(
    "/users/{user_id}/payments", response_model=PaginatedResponse[PaymentOut]
)
def get_user_payments(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Esta ruta no cambia
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando pagos para el usuario ID: {user_id}."
    )
    try:
        user_has_permission = (
            "users:read_all" in current_user.get("permissions", set())
            or current_user.get("user_id") == user_id
        )
        if not user_has_permission:
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

        items_list = [PaymentOut.model_validate(p) for p in payments]
        return PaginatedResponse(
            total_items=total_items,
            total_pages=math.ceil(total_items / size),
            current_page=page,
            items=items_list,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en get_user_payments (ID: {user_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
