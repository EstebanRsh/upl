# routes/payment_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PAGOS
# -----------------------------------------------------------------------------
import logging
import math
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from models.models import (
    Payment,
    InputPayment,
    User,
    Invoice,
    PaginatedResponse,
    PaymentOut,
    Subscription,
)
from auth.security import get_current_user, is_admin
from config.db import get_db

# ¡NUEVA IMPORTACIÓN! Importamos el servicio y la excepción personalizada.
from services.payment_service import process_new_payment, PaymentException

logger = logging.getLogger(__name__)
payment_router = APIRouter()


@payment_router.post(
    "/payments/add",
    summary="Registrar un nuevo pago",
    description="**Permisos requeridos: `administrador`**.",
    status_code=status.HTTP_201_CREATED,
)
def add_payment(
    payment_data: InputPayment,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """
    Ruta para registrar un nuevo pago. Delega la lógica de negocio al servicio de pagos.
    """
    logger.info(
        f"Admin '{admin_user.get('sub')}' ha iniciado el registro de un pago para el usuario ID {payment_data.user_id}."
    )
    try:
        # 1. La ruta ahora solo llama al servicio con los datos.
        result = process_new_payment(payment_data, db)

        # 2. Si el servicio se ejecuta sin errores, confirmamos la transacción.
        db.commit()

        logger.info(
            f"Pago para usuario ID {payment_data.user_id} procesado y confirmado exitosamente."
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=result)

    except PaymentException as e:
        # 3. Capturamos nuestros errores de negocio personalizados.
        db.rollback()
        # El logger ya registró el warning dentro del servicio, no necesitamos duplicarlo.
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except HTTPException:
        # Dejamos pasar otras HTTPExceptions sin registrarlas como error grave.
        raise

    except Exception as e:
        # 4. Capturamos cualquier otro error inesperado.
        db.rollback()
        logger.error(f"Error inesperado en la ruta add_payment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar el pago.",
        )


# La ruta get_user_payments no necesita refactorización por ahora,
# así que la dejamos como estaba, pero con el manejo de excepciones mejorado.
@payment_router.get(
    "/users/{user_id}/payments",
    response_model=PaginatedResponse[PaymentOut],
    summary="Consultar historial de pagos de un usuario",
)
def get_user_payments(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando historial de pagos para el usuario ID: {user_id}."
    )
    try:
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")
        if token_user_role != "administrador" and token_user_id != user_id:
            logger.warning(f"Acceso no autorizado a pagos del usuario ID {user_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de otro usuario.",
            )

        offset = (page - 1) * size
        payments_query = (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.payment_date.desc())
        )
        total_items = payments_query.count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=page, items=[]
            )

        payments = (
            payments_query.options(
                joinedload(Payment.invoice).joinedload(Invoice.subscription)
            )
            .offset(offset)
            .limit(size)
            .all()
        )
        total_pages = math.ceil(total_items / size)
        items_list = [
            PaymentOut(
                id=p.id,
                plan_id=(
                    p.invoice.subscription.plan_id
                    if p.invoice and p.invoice.subscription
                    else None
                ),
                user_id=p.user_id,
                amount=p.amount,
                payment_date=p.payment_date,
            )
            for p in payments
        ]

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado en get_user_payments (ID: {user_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
