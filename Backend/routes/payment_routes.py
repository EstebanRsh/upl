# routes/payment_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PAGOS
# -----------------------------------------------------------------------------
# Este módulo define los endpoints para procesar pagos y consultar historiales.
# 1. Registrar un nuevo pago, lo que implica actualizar una factura y generar un recibo.
# 2. Consultar el historial de pagos de un usuario de forma paginada.
# -----------------------------------------------------------------------------

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
)
from auth.security import get_current_user, is_admin
from utils.pdf_generator import create_invoice_pdf
from config.db import get_db

# Creación de un router específico para las rutas de pagos.
payment_router = APIRouter()


@payment_router.post(
    "/payments/add",
    summary="Registrar un nuevo pago",
    description="**Permisos requeridos: `administrador`**.<br>Registra un pago para la factura pendiente más antigua de un usuario. Si el pago es exitoso, actualiza el estado de la factura a 'pagada' y genera un recibo en PDF.",
)
def add_payment(
    payment_data: InputPayment,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """
    Registra un pago para un usuario.
    AÑADIDA LA VALIDACIÓN DEL MONTO DEL PAGO.
    """
    try:
        # 1. Busca la factura pendiente más antigua del usuario.
        invoice_to_pay = (
            db.query(Invoice)
            .filter(
                Invoice.user_id == payment_data.user_id, Invoice.status == "pending"
            )
            .order_by(Invoice.issue_date.asc())
            .first()
        )
        if not invoice_to_pay:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No se encontró una factura pendiente para este usuario."
                },
            )

        # --- VALIDACIÓN DEL MONTO ---
        # Comprueba si el monto del pago coincide con el total de la factura.
        if payment_data.amount != invoice_to_pay.total_amount:
            return JSONResponse(
                status_code=400,  # Bad Request
                content={
                    "message": "El monto del pago no coincide con el total de la factura.",
                    "monto_requerido": invoice_to_pay.total_amount,
                    "monto_recibido": payment_data.amount,
                },
            )

        # 2. Crea el nuevo registro del pago en la tabla 'payments'.
        new_payment = Payment(
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            invoice_id=invoice_to_pay.id,  # Asocia el pago a la factura encontrada.
        )
        db.add(new_payment)
        db.flush()  # 'flush' envía los cambios a la BD sin hacer commit, útil para obtener el ID del nuevo pago.

        # 3. Actualiza el estado de la factura a 'paid'.
        invoice_to_pay.status = "paid"
        # La línea 'invoice_to_pay.payment_id = new_payment.id' parece estar ausente en tu código original,
        # pero sería una buena adición para relacionar la factura con el pago directamente.

        # 4. Prepara los datos para generar el recibo en PDF.
        user_details = invoice_to_pay.user.userdetail
        plan_details = invoice_to_pay.subscription.plan
        pdf_data = {
            "invoice_id": invoice_to_pay.id,
            "client_name": f"{user_details.firstname} {user_details.lastname}",
            "payment_date": new_payment.payment_date.strftime("%d/%m/%Y"),
            "plan_name": plan_details.name,
            "amount_paid": new_payment.amount,
        }
        # Llama a la función de utilidad para crear el PDF.
        pdf_path = create_invoice_pdf(pdf_data)

        # 5. Guarda la ruta relativa del PDF generado en el registro de la factura.
        invoice_to_pay.receipt_pdf_url = pdf_path

        db.commit()
        return JSONResponse(
            status_code=201,
            content={
                "message": "Pago registrado y recibo generado.",
                "pdf_path": pdf_path,
            },
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


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
