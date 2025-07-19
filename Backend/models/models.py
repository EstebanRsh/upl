# models/models.py
# -----------------------------------------------------------------------------
# DEFINICIÓN DE MODELOS DE DATOS
# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

# Importaciones necesarias de SQLAlchemy, Pydantic y tipos de Python.
from config.db import engine, Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, EmailStr, Field
import datetime
from typing import List, TypeVar, Generic
from core.constants import (
    USER_ROLE_CLIENT,
    SUBSCRIPTION_STATUS_ACTIVE,
    INVOICE_STATUS_PENDING,
)

# ... (El resto de las importaciones y la variable T no cambian) ...
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
    role = Column("role", String, default="cliente", nullable=False)
    refresh_token = Column("refresh_token", String, nullable=True)

    # ... (las relaciones no cambian) ...
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

    # --- MODIFICADO ---
    def __init__(self, username, password, email=None, role=USER_ROLE_CLIENT):
        """Constructor para crear una instancia de User."""
        self.username = username
        self.password = password
        self.email = email
        self.role = role


# ... (La clase UserDetail no cambia) ...
class UserDetail(Base):
    """Modelo de la tabla 'userdetails'. Almacena datos personales."""

    __tablename__ = "userdetails"
    id = Column("id", Integer, primary_key=True)
    dni = Column("dni", Integer, unique=True, nullable=False)
    firstname = Column("firstname", String, nullable=False)
    lastname = Column("lastname", String, nullable=False)
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
        address=None,
        phone=None,
        city=None,
        barrio=None,
        phone2=None,
    ):
        self.dni = dni
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.phone = phone
        self.city = city
        self.barrio = barrio
        self.phone2 = phone2


# ... (La clase InternetPlan no cambia) ...
class InternetPlan(Base):
    """Modelo de la tabla 'internet_plans'. Define los planes ofrecidos."""

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


# ... (La clase Payment no cambia) ...
class Payment(Base):
    """Modelo de la tabla 'payments'. Registra cada pago."""

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
    """Modelo de la tabla 'subscriptions'. Tabla pivote que une usuarios y planes."""

    __tablename__ = "subscriptions"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("internet_plans.id"))
    subscription_date = Column(DateTime, default=datetime.datetime.now)
    # --- MODIFICADO ---
    status = Column(String, default=SUBSCRIPTION_STATUS_ACTIVE)
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("InternetPlan", back_populates="subscriptions")

    def __init__(self, user_id, plan_id):
        """Constructor para crear una instancia de Subscription."""
        self.user_id = user_id
        self.plan_id = plan_id


# ... (La clase BusinessSettings no cambia) ...
class BusinessSettings(Base):
    """Modelo de la tabla 'business_settings'. Almacena reglas de negocio configurables."""

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
    """Modelo de la tabla 'invoices'. Representa una factura mensual."""

    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.now)
    due_date = Column(DateTime, nullable=False)
    base_amount = Column(Float, nullable=False)
    late_fee = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    # --- MODIFICADO ---
    status = Column(String, default=INVOICE_STATUS_PENDING)
    receipt_pdf_url = Column(String, nullable=True)

    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription")
    payments = relationship("Payment", back_populates="invoice")

    def __init__(self, user_id, subscription_id, due_date, base_amount, total_amount):
        """Constructor para crear una instancia de Invoice."""
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.due_date = due_date
        self.base_amount = base_amount
        self.total_amount = total_amount


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


class InputLogin(BaseModel):
    username: str
    password: str


class InputPlan(BaseModel):
    name: str = Field(
        ..., description="El nombre comercial del plan. Ej: 'Fibra Óptica 100 Mega'"
    )
    speed_mbps: int = Field(
        ..., description="La velocidad de descarga del plan en Megabits por segundo."
    )
    price: float = Field(
        ..., gt=0, description="El precio mensual del plan. Debe ser mayor que cero."
    )


class InputPayment(BaseModel):
    plan_id: int
    user_id: int
    amount: float


class InputSubscription(BaseModel):
    user_id: int
    plan_id: int


# --- Modelos de Actualización (Pydantic) ---
# ... (Las clases UpdatePlan, UpdateUserDetail, UpdateSubscriptionStatus, UpdateUserRole no cambian) ...
class UpdatePlan(BaseModel):
    name: str | None = None
    speed_mbps: int | None = None
    price: float | None = Field(
        default=None,
        gt=0,
        description="El nuevo precio mensual del plan. Debe ser mayor que cero.",
    )


class UpdateUserDetail(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    phone: str | None = None


class UpdateSubscriptionStatus(BaseModel):
    status: str


class UpdateUserRole(BaseModel):
    role: str


class UpdateMyDetails(BaseModel):
    """Schema para que un usuario actualice sus propios detalles (no el DNI)."""

    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    barrio: str | None = None
    city: str | None = None
    phone: str | None = None
    phone2: str | None = None


class UpdateMyPassword(BaseModel):
    """Schema para que un usuario cambie su contraseña."""

    current_password: str
    new_password: str = Field(..., min_length=8)


# --- Modelos de Respuesta (Pydantic) ---
class PaginatedResponse(BaseModel, Generic[T]):
    total_items: int
    total_pages: int
    current_page: int
    items: List[T]


class UserOut(BaseModel):
    username: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str
    phone: str
    phone2: str | None = None
    role: str


class PlanOut(BaseModel):
    id: int
    name: str
    speed_mbps: int
    price: float


class PaymentOut(BaseModel):
    id: int
    plan_id: int
    user_id: int
    amount: float
    payment_date: datetime.datetime


class SubscriptionOut(BaseModel):
    id: int
    status: str
    subscription_date: datetime.datetime
    user: UserOut
    plan: PlanOut


class Setting(BaseModel):
    setting_name: str
    setting_value: str
    description: str | None = None


class InvoiceOut(BaseModel):
    """Schema de respuesta para una factura, sin datos del usuario."""

    id: int
    issue_date: datetime.datetime
    due_date: datetime.datetime
    base_amount: float
    late_fee: float
    total_amount: float
    status: str
    receipt_pdf_url: str | None = None

    class Config:
        # Esto permite que Pydantic lea los datos desde un objeto de SQLAlchemy
        from_attributes = True  # En Pydantic v1 era orm_mode = True
