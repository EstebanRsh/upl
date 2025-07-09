# routes/payment_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from models.models import session, Payment, InputPayment, User

payment_router = APIRouter()

@payment_router.post("/payments/add")
def add_payment(payment_data: InputPayment, req: Request):
    # La protección con token es crucial aquí
    # has_access = Security.verify_token(req.headers)
    # if not "iat" in has_access:
    #     return JSONResponse(status_code=401, content=has_access)
    
    try:
        # Verificamos si el usuario existe
        user_exists = session.query(User).filter(User.id == payment_data.user_id).first()
        if not user_exists:
            return JSONResponse(status_code=404, content={"message": "El usuario especificado no existe"})
        
        new_payment = Payment(
            plan_id=payment_data.plan_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount
        )
        session.add(new_payment)
        session.commit()
        return JSONResponse(status_code=201, content={"message": "Pago registrado exitosamente"})
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()

@payment_router.get("/users/{user_id}/payments")
def get_user_payments(user_id: int, req: Request):
    # descomentar estas lineas
    # has_access = Security.verify_token(req.headers)
    # if not "iat" in has_access:
    #     return JSONResponse(status_code=401, content=has_access)
    
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            # Gracias a la relación 'payments' en el modelo User, esto es muy sencillo
            return user.payments
        return JSONResponse(status_code=404, content={"message": "Usuario no encontrado"})
    finally:
        session.close()