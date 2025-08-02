# Backend/schemas/settings_schemas.py
from pydantic import BaseModel


# --- Schema para la página de Configuraciones ---
class CompanySettingsSchema(BaseModel):
    # Configuración General
    business_name: str
    business_cuit: str
    business_address: str
    businness_city: str
    business_phone: str

    # Facturación y Pagos
    payment_window_days: int
    late_fee_amount: float

    # Automatización
    auto_invoicing_enabled: bool
    days_for_suspension: int

    class Config:
        from_attributes = True


# --- Schemas para el Dashboard (que borramos por error) ---
class ClientStatusSummary(BaseModel):
    """Resume el número de clientes por estado."""

    active_clients: int
    suspended_clients: int
    total_clients: int


class InvoiceStatusSummary(BaseModel):
    """Resume el número de facturas por estado."""

    pending: int
    paid: int
    overdue: int
    total: int


class DashboardStats(BaseModel):
    """Schema principal para la respuesta del endpoint del panel de control."""

    client_summary: ClientStatusSummary
    invoice_summary: InvoiceStatusSummary
    monthly_revenue: float
    new_subscriptions_this_month: int
