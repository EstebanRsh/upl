# models/models.py
from config.db import engine, Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, EmailStr
import datetime
from typing import List, TypeVar, Generic


T = TypeVar("T")

# --- Modelos de la Base de Datos (SQLAlchemy) ---


class User(Base):
    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column("password", String)
    email = Column("email", String(80), nullable=False, unique=True)
    id_userdetail = Column(Integer, ForeignKey("userdetails.id"))
    role = Column("role", String, default="cliente")
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
    subscriptions = relationship("Subscription", cascade="all, delete-orphan")
    invoices = relationship(
        "Invoice", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, username, password, email, role="cliente"):
        self.username = username
        self.password = password
        self.email = email
        self.role = role


class UserDetail(Base):
    __tablename__ = "userdetails"
    id = Column("id", Integer, primary_key=True)
    dni = Column("dni", Integer, unique=True)
    firstname = Column("firstname", String)
    lastname = Column("lastname", String)
    address = Column("address", String)
    phone = Column("phone", String)
    user = relationship("User", back_populates="userdetail")

    def __init__(self, dni, firstname, lastname, address, phone):
        self.dni = dni
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.phone = phone


class InternetPlan(Base):
    __tablename__ = "internet_plans"
    id = Column("id", Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    speed_mbps = Column(Integer)
    price = Column(Float)
    subscriptions = relationship("Subscription")

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


# tabla pivote relacionando usuarios con planes de internet
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("internet_plans.id"))
    subscription_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(String, default="active")
    user = relationship("User")
    plan = relationship("InternetPlan")

    def __init__(self, user_id, plan_id):
        self.user_id = user_id
        self.plan_id = plan_id


class BusinessSettings(Base):
    """
    Almacena las reglas de negocio configurables para la facturación.
    """

    __tablename__ = "business_settings"
    id = Column(Integer, primary_key=True)
    setting_name = Column(String, unique=True, nullable=False)
    setting_value = Column(String, nullable=False)
    description = Column(String, nullable=True)

    def __init__(self, setting_name, setting_value, description=None):
        self.setting_name = setting_name
        self.setting_value = setting_value
        self.description = description


class Invoice(Base):
    """
    Representa una factura mensual generada para un cliente.
    """

    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    issue_date = Column(DateTime, default=datetime.datetime.now)  # Fecha de emisión
    due_date = Column(DateTime, nullable=False)  # Fecha de vencimiento

    base_amount = Column(Float, nullable=False)
    late_fee = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    status = Column(
        String, default="pending"
    )  # Estados: pending, paid, overdue, cancelled
    receipt_pdf_url = Column(String, nullable=True)  # Ruta al PDF del recibo

    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription")
    payments = relationship("Payment", back_populates="invoice")

    def __init__(self, user_id, subscription_id, due_date, base_amount, total_amount):
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.due_date = due_date
        self.base_amount = base_amount
        self.total_amount = total_amount


# --- Modelos de Entrada (Pydantic) ---
class InputUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str
    phone: str


class InputLogin(BaseModel):
    username: str
    password: str


class InputPlan(BaseModel):
    name: str
    speed_mbps: int
    price: float


class InputPayment(BaseModel):
    plan_id: int
    user_id: int
    amount: float


class InputSubscription(BaseModel):
    user_id: int
    plan_id: int


# --- Modelos de Actualización (Pydantic) ---
class UpdatePlan(BaseModel):
    name: str | None = None
    speed_mbps: int | None = None
    price: float | None = None


# --- Modelo de Actualización (Pydantic) ---
class UpdateUserDetail(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    phone: str | None = None


class UpdateSubscriptionStatus(BaseModel):
    status: str  # Recibirá el nuevo estado, ej: "cancelled", "suspended"


class UpdateUserRole(BaseModel):
    role: str


# --- Modelo de Respuesta Paginada (Pydantic) ---
class PaginatedResponse(BaseModel, Generic[T]):
    total_items: int
    total_pages: int
    current_page: int
    items: List[T]


# --- Modelo de Respuesta paginacion (Pydantic) ---
class UserOut(BaseModel):
    """
    Modelo de respuesta para el usuario, sin exponer datos sensibles.
    """

    username: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str
    phone: str
    role: str


class PlanOut(BaseModel):
    """Modelo de respuesta para los planes de internet."""

    id: int
    name: str
    speed_mbps: int
    price: float


class PaymentOut(BaseModel):
    """Modelo de respuesta para los pagos."""

    id: int
    plan_id: int
    user_id: int
    amount: float
    payment_date: datetime.datetime


class SubscriptionOut(BaseModel):
    """Modelo de respuesta para las suscripciones, incluyendo detalles."""

    id: int
    status: str
    subscription_date: datetime.datetime
    user: UserOut  # Anidamos el modelo del usuario
    plan: PlanOut  # Anidamos el modelo del plan


# --- Modelo de configuración de negocio (Pydantic) ---


class Setting(BaseModel):
    setting_name: str
    setting_value: str
    description: str | None = None


# --- Creación de Tablas y Sesión ---
Base.metadata.create_all(engine)
Session = sessionmaker(engine)
session = Session()
