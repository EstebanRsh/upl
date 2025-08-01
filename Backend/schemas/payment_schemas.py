# schemas/payment_schemas.py
from pydantic import BaseModel, ConfigDict
import datetime


class PaymentOut(BaseModel):
    """Schema de respuesta para un pago (vista de cliente)."""

    id: int
    user_id: int
    amount: float
    payment_date: datetime.datetime
    invoice_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


# 1. Creamos un schema pequeño para la información del usuario
class UserInfo(BaseModel):
    """Un schema simple para mostrar la información básica del cliente."""

    firstname: str
    lastname: str
    dni: int

    model_config = ConfigDict(from_attributes=True)


# 2. Creamos el nuevo schema para la vista del administrador
class PaymentAdminOut(BaseModel):
    """
    Define la estructura de un pago cuando es consultado por un administrador.
    Incluye los detalles del pago y la información del cliente que lo realizó.
    """

    id: int
    payment_date: datetime.datetime
    amount: float
    payment_method: str | None = None
    invoice_id: int
    user: UserInfo

    model_config = ConfigDict(from_attributes=True)
