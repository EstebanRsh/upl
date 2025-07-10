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

    userdetail = relationship("UserDetail", uselist=False)
    payments = relationship("Payment", back_populates="user")
    subscriptions = relationship("Subscription")

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
    speed_mbps = Column(Integer)  # Velocidad del plan
    price = Column(Float)  # Precio del plan

    subscriptions = relationship("Subscription")

    def __init__(self, name, speed_mbps, price):
        self.name = name
        self.speed_mbps = speed_mbps
        self.price = price


class Payment(Base):
    __tablename__ = "payments"
    id = Column("id", Integer, primary_key=True)
    plan_id = Column(ForeignKey("internet_plans.id"))
    user_id = Column(ForeignKey("users.id"))
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.datetime.now())

    user = relationship("User", uselist=False, back_populates="payments")
    plan = relationship("InternetPlan", uselist=False)

    def __init__(self, plan_id, user_id, amount):
        self.plan_id = plan_id
        self.user_id = user_id
        self.amount = amount


# tabla pivote relacionando usuarios con planes de internet
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("internet_plans.id"))
    subscription_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(String, default="active")  # Puede ser 'active', 'cancelled', etc.

    # Relaciones para acceder desde una suscripción a su usuario y plan
    user = relationship("User")
    plan = relationship("InternetPlan")

    def __init__(self, user_id, plan_id):
        self.user_id = user_id
        self.plan_id = plan_id


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


# --- Creación de Tablas y Sesión ---
Base.metadata.create_all(engine)
Session = sessionmaker(engine)
session = Session()
