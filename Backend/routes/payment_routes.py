# routes/payment_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PAGOS
# -----------------------------------------------------------------------------
# Este módulo define los endpoints para procesar pagos y consultar historiales.
# 1. Registrar un nuevo pago, lo que implica actualizar una factura y generar un recibo.
# 2. Consultar el historial de pagos de un usuario de forma paginada.
# -----------------------------------------------------------------------------
import random
from PIL import Image, ImageDraw, ImageFont
import locale
import traceback
from num2words import num2words
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
import math
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
from datetime import datetime

# Creación de un router específico para las rutas de pagos.
payment_router = APIRouter()


@payment_router.post(
    "/payments/add",
    summary="Registrar un nuevo pago",
    description="**Permisos requeridos: `administrador`**.<br>Registra un pago para la factura pendiente más antigua de un usuario, la marca como pagada y genera un recibo en PDF con un sello de agua de imagen.",
)
def add_payment(
    payment_data: InputPayment,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    try:
        # Esta parte para buscar la factura correcta ya está bien, no la toques.
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == payment_data.user_id,
                Subscription.plan_id == payment_data.plan_id,
            )
            .first()
        )
        if not subscription:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No se encontró una suscripción para este usuario y plan."
                },
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
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No se encontró una factura pendiente para esta suscripción."
                },
            )

        # Esta parte para crear el pago también está bien.
        invoice_to_pay.status = "paid"
        new_payment = Payment(
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            invoice_id=invoice_to_pay.id,
        )
        db.add(new_payment)
        db.flush()
        db.refresh(new_payment)

        # --- INICIO DE LA MODIFICACIÓN ---
        #
        # Reemplazamos todo el bloque de código que preparaba el PDF
        # con estas dos líneas mucho más limpias.
        #
        receipt_url = generate_payment_receipt(new_payment, invoice_to_pay)
        invoice_to_pay.receipt_pdf_url = receipt_url
        #
        # --- FIN DE LA MODIFICACIÓN ---

        # Confirmar y responder
        db.commit()

        return JSONResponse(
            status_code=201,
            content={
                "message": "Pago registrado exitosamente.",
                "receipt_number": f"F{new_payment.payment_date.year}-{invoice_to_pay.id:03d}",
                "pdf_filename": os.path.basename(
                    receipt_url
                ),  # Obtenemos el nombre del archivo
                "total_paid": new_payment.amount,
            },
        )

    except Exception as e:
        db.rollback()
        print(f"Error en /payments/add: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "Ocurrió un error interno al procesar el pago."},
        )


@payment_router.get(
    "/users/{user_id}/payments",
    response_model=PaginatedResponse[PaymentOut],
    summary="Consultar historial de pagos de un usuario",
    description="""
Obtiene el historial de pagos de un usuario de forma paginada.

**Permisos:**
- **Cliente**: Puede consultar **únicamente su propio** historial de pagos.
- **Administrador**: Puede consultar el historial de pagos de **cualquier** usuario.
""",
)
def get_user_payments(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene el historial de pagos de un usuario de forma paginada.
    Un usuario solo puede ver sus propios pagos, un administrador puede ver los de cualquiera.
    """
    token_user_id = current_user.get("user_id")
    token_user_role = current_user.get("role")

    if token_user_role != "administrador" and token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver los pagos de otro usuario.",
        )

    try:
        offset = (page - 1) * size

        # 1. Hacemos un JOIN para poder acceder a los datos relacionados
        payments_query = (
            db.query(Payment)
            .join(Payment.invoice)
            .join(Invoice.subscription)
            .filter(Payment.user_id == user_id)
        )

        total_items = payments_query.count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=1, items=[]
            )

        # 2. Usamos joinedload para cargar eficientemente los datos relacionados
        payments = (
            payments_query.options(
                joinedload(Payment.invoice).joinedload(Invoice.subscription)
            )
            .offset(offset)
            .limit(size)
            .all()
        )

        total_pages = math.ceil(total_items / size)

        # 3. Construimos la lista de respuesta manualmente para que coincida con PaymentOut
        items_list = [
            PaymentOut(
                id=p.id,
                # Obtenemos el plan_id a través de la relación
                plan_id=p.invoice.subscription.plan_id,
                user_id=p.user_id,
                amount=p.amount,
                payment_date=p.payment_date,
            )
            for p in payments
            if p.invoice and p.invoice.subscription
        ]

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,  # Devolvemos la lista que construimos
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
