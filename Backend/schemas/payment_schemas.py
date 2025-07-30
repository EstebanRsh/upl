# schemas/payment_schemas.py
from pydantic import BaseModel, ConfigDict
import datetime


class PaymentOut(BaseModel):
    """Schema de respuesta para un pago."""

    id: int
    user_id: int
    amount: float
    payment_date: datetime.datetime
    invoice_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
