# models/models.py
# -----------------------------------------------------------------------------
# DEFINICIÓN DE MODELOS DE DATOS (VERSIÓN SIMPLIFICADA)
# -----------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from config.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
import datetime
from typing import List, TypeVar, Generic
from core.constants import (
    SUBSCRIPTION_STATUS_ACTIVE,
    INVOICE_STATUS_PENDING,
)

T = TypeVar("T")

# --- Modelos de la Base de Datos (SQLAlchemy) ---


class User(Base):
    """Modelo de la tabla 'users'. Almacena credenciales y datos básicos."""

    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column("password", String, nullable=False)
    email = Column("email", String(80), unique=True, nullable=True)
    id_userdetail = Column(Integer, ForeignKey("userdetails.id"))
    refresh_token = Column("refresh_token", String, nullable=True)

    userdetail = relationship(
        "UserDetail",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    payments = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    invoices = relationship(
        "Invoice", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, username, password, email=None):
        self.username = username
        self.password = password
        self.email = email


class UserDetail(Base):
    """Modelo de la tabla 'userdetails'. Almacena datos personales y el rol."""

    __tablename__ = "userdetails"
    id = Column("id", Integer, primary_key=True)
    dni = Column("dni", Integer, unique=True, nullable=False)
    firstname = Column("firstname", String, nullable=False)
    lastname = Column("lastname", String, nullable=False)

    # --- CAMBIO CLAVE: Campo de rol simplificado, como en appescuela ---
    type = Column("type", String(50), default="cliente", nullable=False)

    address = Column("address", String, nullable=True)
    barrio = Column("barrio", String, nullable=True)
    city = Column("city", String, nullable=True)
    phone = Column("phone", String, nullable=True)
    phone2 = Column("phone2", String, nullable=True)
    user = relationship("User", back_populates="userdetail")

    def __init__(
        self,
        dni,
        firstname,
        lastname,
        type="cliente",  # Agregamos 'type' al constructor
        address=None,
        phone=None,
        city=None,
        barrio=None,
        phone2=None,
    ):
        self.dni = dni
        self.firstname = firstname
        self.lastname = lastname
        self.type = type
        self.address = address
        self.phone = phone
        self.city = city
        self.barrio = barrio
        self.phone2 = phone2


# --- MODELOS ELIMINADOS ---
# Ya no se necesitan las clases Role, Permission ni la tabla role_permissions.

# --- OTROS MODELOS (Permanecen igual) ---


class InternetPlan(Base):
    __tablename__ = "internet_plans"
    id = Column("id", Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    speed_mbps = Column(Integer)
    price = Column(Float)
    subscriptions = relationship("Subscription", back_populates="plan")

    def __init__(self, name, speed_mbps, price):
        self.name = name
        self.speed_mbps = speed_mbps
        self.price = price


class Payment(Base):
    __tablename__ = "payments"
    id = Column("id", Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.datetime.now())
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    user = relationship("User", uselist=False, back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")

    def __init__(self, user_id, amount, invoice_id=None):
        self.user_id = user_id
        self.amount = amount
        self.invoice_id = invoice_id


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("internet_plans.id"))
    subscription_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(String, default=SUBSCRIPTION_STATUS_ACTIVE)
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("InternetPlan", back_populates="subscriptions")

    def __init__(self, user_id, plan_id):
        self.user_id = user_id
        self.plan_id = plan_id


class BusinessSettings(Base):
    __tablename__ = "business_settings"
    id = Column(Integer, primary_key=True)
    setting_name = Column(String, unique=True, nullable=False, index=True)
    setting_value = Column(String, nullable=False)
    description = Column(String, nullable=True)

    def __init__(self, setting_name, setting_value, description=None):
        self.setting_name = setting_name
        self.setting_value = setting_value
        self.description = description


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.now)
    due_date = Column(DateTime, nullable=False)
    base_amount = Column(Float, nullable=False)
    late_fee = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default=INVOICE_STATUS_PENDING)
    receipt_pdf_url = Column(String, nullable=True)
    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription")
    payments = relationship("Payment", back_populates="invoice")

    def __init__(self, user_id, subscription_id, due_date, base_amount, total_amount):
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.due_date = due_date
        self.base_amount = base_amount
        self.total_amount = total_amount


# --- Modelos Pydantic (para validación en las rutas) ---


class InputUser(BaseModel):
    username: str
    password: str
    dni: int
    firstname: str
    lastname: str
    email: EmailStr | None = None
    address: str | None = None
    phone: str | None = None
    city: str | None = None
    barrio: str | None = None
    phone2: str | None = None
    type: str = "cliente"


class InputLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str | None = None
    barrio: str | None = None
    city: str | None = None
    phone: str | None = None
    phone2: str | None = None
    role: str  # Simplificado de 'role_obj' a 'role'
    model_config = ConfigDict(from_attributes=True)


class UpdateMyDetails(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    barrio: str | None = None
    city: str | None = None
    phone: str | None = None
    phone2: str | None = None


class UpdateMyPassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PaginatedResponse(BaseModel, Generic[T]):
    total_items: int
    total_pages: int
    current_page: int
    items: List[T]


class UpdateUserDetail(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    phone: str | None = None
    city: str | None = None
    barrio: str | None = None
    phone2: str | None = None


# ... (Otros modelos Pydantic que no dependen de Role/Permission pueden permanecer)
class ClientStatusSummary(BaseModel):
    active_clients: int
    suspended_clients: int
    total_clients: int


class InvoiceStatusSummary(BaseModel):
    pending: int
    paid: int
    overdue: int
    total: int


class DashboardStats(BaseModel):
    client_summary: ClientStatusSummary
    invoice_summary: InvoiceStatusSummary
    monthly_revenue: float
    new_subscriptions_this_month: int


class Setting(BaseModel):
    setting_name: str
    setting_value: str
    description: str | None = None


class SettingsUpdate(BaseModel):
    settings: List[Setting]
