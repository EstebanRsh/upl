# routes/payment_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
import math
from fastapi.responses import JSONResponse
from models.models import (
    session,
    Payment,
    InputPayment,
    User,
    PaginatedResponse,
    PaymentOut,
)
from auth.security import get_current_user, is_admin

payment_router = APIRouter()


@payment_router.post("/payments/add")
def add_payment(payment_data: InputPayment, admin_user: dict = Depends(is_admin)):
    try:
        user_exists = (
            session.query(User).filter(User.id == payment_data.user_id).first()
        )
        if not user_exists:
            return JSONResponse(
                status_code=404,
                content={"message": "El usuario especificado no existe"},
            )

        new_payment = Payment(
            plan_id=payment_data.plan_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount,
        )
        session.add(new_payment)
        session.commit()
        return JSONResponse(
            status_code=201, content={"message": "Pago registrado exitosamente"}
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
