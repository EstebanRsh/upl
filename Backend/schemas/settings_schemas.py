# schemas/settings_schemas.py
from pydantic import BaseModel
from typing import List


class Setting(BaseModel):
    setting_name: str
    setting_value: str
    description: str | None = None


class SettingsUpdate(BaseModel):
    settings: List[Setting]


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
