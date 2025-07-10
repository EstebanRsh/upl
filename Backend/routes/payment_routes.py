# routes/payment_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import math
from fastapi.responses import JSONResponse
from models.models import (
    session,
    Payment,
    InputPayment,
    User,
    Invoice,
    PaginatedResponse,
    PaymentOut,
)
from auth.security import get_current_user, is_admin
from utils.pdf_generator import create_invoice_pdf

payment_router = APIRouter()


@payment_router.post("/payments/add")
def add_payment(payment_data: InputPayment, admin_user: dict = Depends(is_admin)):
    try:
        # 1. Buscamos la factura pendiente más antigua para este usuario
        invoice_to_pay = (
            session.query(Invoice)
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

        # 2. Creamos el nuevo registro de pago
        new_payment = Payment(
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            invoice_id=invoice_to_pay.id,
        )
        session.add(new_payment)
        session.flush()

        # 3. Actualizamos la factura
        invoice_to_pay.status = "paid"
        invoice_to_pay.payment_id = new_payment.id

        # 4. Generamos el recibo en PDF
        user_details = invoice_to_pay.user.userdetail
        plan_details = invoice_to_pay.subscription.plan

        pdf_data = {
            "invoice_id": invoice_to_pay.id,
            "client_name": f"{user_details.firstname} {user_details.lastname}",
            "payment_date": new_payment.payment_date.strftime("%d/%m/%Y"),
            "plan_name": plan_details.name,
            "amount_paid": new_payment.amount,
        }
        pdf_path = create_invoice_pdf(pdf_data)

        # 5. Guardamos la ruta del PDF en la factura
        invoice_to_pay.receipt_pdf_url = pdf_path

        session.commit()
        return JSONResponse(
            status_code=201,
            content={
                "message": "Pago registrado y recibo generado.",
                "pdf_path": pdf_path,
            },
        )

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@payment_router.get(
    "/users/{user_id}/payments", response_model=PaginatedResponse[PaymentOut]
)
def get_user_payments(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    token_user_id = current_user.get("user_id")
    token_user_role = current_user.get("role")

    if token_user_role != "administrador" and token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver los pagos de otro usuario.",
        )

    try:
        offset = (page - 1) * size

        # Contamos solo los pagos del usuario especificado
        total_items = session.query(Payment).filter(Payment.user_id == user_id).count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=1, items=[]
            )

        # Hacemos la consulta paginada para ese usuario
        payments_query = (
            session.query(Payment)
            .filter(Payment.user_id == user_id)
            .offset(offset)
            .limit(size)
            .all()
        )

        total_pages = math.ceil(total_items / size)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=payments_query,
        )
    finally:
        session.close()
