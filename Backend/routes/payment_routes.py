# routes/payment_routes.py
from fastapi import APIRouter, Depends
from models.models import session, Payment, InputPayment, User
from auth.security import Security # Para proteger rutas

payment_router = APIRouter()

@payment_router.post("/payments/add")
def add_payment(payment_data: InputPayment):
    # Aquí iría la lógica para agregar un pago, similar a la del 
    # archivo original 'payment.py' pero usando los nuevos modelos.
    pass

@payment_router.get("/users/{user_id}/payments")
def get_user_payments(user_id: int):
    # Gracias a las relaciones ORM, obtener los pagos de un usuario es sencillo
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user.payments
        return {"message": "Usuario no encontrado"}
    finally:
        session.close()