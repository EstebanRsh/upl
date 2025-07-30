# schemas/invoice_schemas.py
from pydantic import BaseModel, ConfigDict
import datetime


class UserBasicInfo(BaseModel):
    """Schema para devolver información básica de un usuario anidado."""

    username: str
    firstname: str
    lastname: str
    model_config = ConfigDict(from_attributes=True)


class InvoiceOut(BaseModel):
    """Schema base de respuesta para una factura."""

    id: int
    issue_date: datetime.datetime
    due_date: datetime.datetime
    base_amount: float
    late_fee: float
    total_amount: float
    status: str
    receipt_pdf_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class InvoiceAdminOut(InvoiceOut):
    """Schema de respuesta para facturas en el panel de admin, incluye datos del usuario."""

    user: UserBasicInfo
    model_config = ConfigDict(from_attributes=True)


class UpdateInvoiceStatus(BaseModel):
    """Schema para recibir el nuevo estado de una factura."""

    status: str
