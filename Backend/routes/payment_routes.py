# routes/payment_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PAGOS
# -----------------------------------------------------------------------------
import logging
import os
import math
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
from utils.pdf_generator import generate_payment_receipt
from config.db import get_db

logger = logging.getLogger(__name__)
payment_router = APIRouter()


@payment_router.post("/payments/add", status_code=status.HTTP_201_CREATED)
def add_payment(
    payment_data: InputPayment,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' registrando pago para usuario ID: {payment_data.user_id}."
    )
    try:
        # ... (lógica sin cambios) ...
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == payment_data.user_id,
                Subscription.plan_id == payment_data.plan_id,
            )
            .first()
        )
        if not subscription:
            logger.warning(
                f"No se encontró suscripción para usuario {payment_data.user_id} y plan {payment_data.plan_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una suscripción para este usuario y plan.",
            )
        invoice_to_pay = (
            db.query(Invoice)
            .filter(
                Invoice.subscription_id == subscription.id, Invoice.status == "pending"
            )
            .options(
                joinedload(Invoice.user).joinedload(User.userdetail),
                joinedload(Invoice.subscription).joinedload(Subscription.plan),
            )
            .order_by(Invoice.issue_date)
            .first()
        )
        if not invoice_to_pay:
            logger.warning(
                f"No se encontró factura pendiente para la suscripción ID: {subscription.id}."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una factura pendiente para esta suscripción.",
            )
        invoice_to_pay.status = "paid"
        new_payment = Payment(
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            invoice_id=invoice_to_pay.id,
        )
        db.add(new_payment)
        db.flush()
        db.refresh(new_payment)
        receipt_url = generate_payment_receipt(new_payment, invoice_to_pay, db)
        invoice_to_pay.receipt_pdf_url = receipt_url
        db.commit()
        logger.info(
            f"Pago para factura ID {invoice_to_pay.id} confirmado exitosamente."
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Pago registrado exitosamente.",
                "receipt_number": f"F{new_payment.payment_date.year}-{invoice_to_pay.id:03d}",
                "pdf_filename": os.path.basename(receipt_url),
                "total_paid": new_payment.amount,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en add_payment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar el pago.",
        )


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
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando historial de pagos para el usuario ID: {user_id}."
    )
    try:
        # ... (lógica de permisos sin cambios) ...
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")
        if token_user_role != "administrador" and token_user_id != user_id:
            logger.warning(f"Acceso no autorizado a pagos del usuario ID {user_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de otro usuario.",
            )
        # ... (lógica de consulta sin cambios) ...
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
