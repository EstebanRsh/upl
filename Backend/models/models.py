# models/models.py
# -----------------------------------------------------------------------------
# DEFINICIÓN DE MODELOS DE DATOS
# -----------------------------------------------------------------------------
# Este archivo centraliza dos tipos de modelos:
# 1. Modelos de Base de Datos (SQLAlchemy): Clases que representan las tablas
#    en la base de datos PostgreSQL. SQLAlchemy ORM las usa para interactuar
#    con los datos.
# 2. Modelos de API (Pydantic): Clases que definen la estructura (schema) de los
#    datos que entran y salen de la API. FastAPI los usa para validación,
#    conversión de tipos y documentación automática.
# -----------------------------------------------------------------------------

# Importaciones necesarias de SQLAlchemy, Pydantic y tipos de Python.
from config.db import engine, Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, EmailStr
import datetime
from typing import List, TypeVar, Generic

# 'TypeVar' y 'Generic' se usan para crear un modelo Pydantic genérico
# que pueda contener una lista de cualquier otro tipo de modelo (T).
T = TypeVar("T")

# --- Modelos de la Base de Datos (SQLAlchemy) ---


class User(Base):
    """Modelo de la tabla 'users'. Almacena credenciales y datos básicos."""

    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column("password", String)
    email = Column("email", String(80), nullable=False, unique=True)
    id_userdetail = Column(Integer, ForeignKey("userdetails.id"))
    role = Column("role", String, default="cliente")
    refresh_token = Column("refresh_token", String, nullable=True)

    # Relaciones ORM para conectar con otras tablas.
    # 'cascade="all, delete-orphan"' es crucial: si se elimina un User,
    # SQLAlchemy borrará automáticamente sus detalles, pagos, suscripciones y facturas.
    userdetail = relationship(
        "UserDetail",
        uselist=False,  # Indica una relación uno-a-uno.
        back_populates="user",  # Establece la relación inversa desde UserDetail.
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

    def __init__(self, username, password, email, role="cliente"):
        """Constructor para crear una instancia de User."""
        self.username = username
        self.password = password
        self.email = email
        self.role = role


class UserDetail(Base):
    """Modelo de la tabla 'userdetails'. Almacena datos personales."""

    __tablename__ = "userdetails"
    id = Column("id", Integer, primary_key=True)
    dni = Column("dni", Integer, unique=True)
    firstname = Column("firstname", String)
    lastname = Column("lastname", String)
    address = Column("address", String)
    phone = Column("phone", String)
    # Relación inversa para poder acceder al objeto User desde un UserDetail.
    user = relationship("User", back_populates="userdetail")

    def __init__(self, dni, firstname, lastname, address, phone):
        """Constructor para crear una instancia de UserDetail."""
        self.dni = dni
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.phone = phone


class InternetPlan(Base):
    """Modelo de la tabla 'internet_plans'. Define los planes ofrecidos."""

    __tablename__ = "internet_plans"
    id = Column("id", Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    speed_mbps = Column(Integer)
    price = Column(Float)
    subscriptions = relationship("Subscription", back_populates="plan")

    def __init__(self, name, speed_mbps, price):
        """Constructor para crear una instancia de InternetPlan."""
        self.name = name
        self.speed_mbps = speed_mbps
        self.price = price


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
        """Constructor para crear una instancia de Payment."""
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
    status = Column(String, default="active")
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("InternetPlan", back_populates="subscriptions")

    def __init__(self, user_id, plan_id):
        """Constructor para crear una instancia de Subscription."""
        self.user_id = user_id
        self.plan_id = plan_id


class BusinessSettings(Base):
    """Modelo de la tabla 'business_settings'. Almacena reglas de negocio configurables."""

    __tablename__ = "business_settings"
    id = Column(Integer, primary_key=True)
    setting_name = Column(String, unique=True, nullable=False)
    setting_value = Column(String, nullable=False)
    description = Column(String, nullable=True)

    def __init__(self, setting_name, setting_value, description=None):
        """Constructor para crear una instancia de BusinessSettings."""
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
    status = Column(String, default="pending")
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


# --- Modelos de Entrada (Pydantic) ---
# Definen la estructura (schema) de los datos que se esperan en el body de las peticiones POST y PUT.


class InputUser(BaseModel):
    """Schema para los datos de entrada al crear un usuario."""

    username: str
    password: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str
    phone: str


class InputLogin(BaseModel):
    """Schema para los datos de entrada del login."""

    username: str
    password: str


class InputPlan(BaseModel):
    """Schema para los datos de entrada al crear un plan."""

    name: str
    speed_mbps: int
    price: float


class InputPayment(BaseModel):
    """Schema para los datos de entrada al registrar un pago."""

    plan_id: int
    user_id: int
    amount: float


class InputSubscription(BaseModel):
    """Schema para los datos de entrada al asignar una suscripción."""

    user_id: int
    plan_id: int


# --- Modelos de Actualización (Pydantic) ---
# Similares a los de entrada, pero con todos los campos opcionales (usando `| None = None`)
# para permitir actualizaciones parciales (método PATCH o PUT).


class UpdatePlan(BaseModel):
    """Schema para actualizar un plan (campos opcionales)."""

    name: str | None = None
    speed_mbps: int | None = None
    price: float | None = None


class UpdateUserDetail(BaseModel):
    """Schema para actualizar los detalles de un usuario (campos opcionales)."""

    firstname: str | None = None
    lastname: str | None = None
    address: str | None = None
    phone: str | None = None


class UpdateSubscriptionStatus(BaseModel):
    """Schema para actualizar el estado de una suscripción."""

    status: str


class UpdateUserRole(BaseModel):
    """Schema para actualizar el rol de un usuario."""

    role: str


# --- Modelos de Respuesta (Pydantic) ---
# Definen la estructura de los datos que la API devuelve. Son útiles para:
# - Estandarizar las respuestas.
# - Filtrar campos sensibles (ej. no devolver el hash de la contraseña).
# - Documentar la API.


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico para respuestas paginadas."""

    total_items: int
    total_pages: int
    current_page: int
    items: List[T]


class UserOut(BaseModel):
    """Schema de respuesta para un usuario. Excluye datos sensibles como la contraseña."""

    username: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str
    phone: str
    role: str


class PlanOut(BaseModel):
    """Schema de respuesta para un plan de internet."""

    id: int
    name: str
    speed_mbps: int
    price: float


class PaymentOut(BaseModel):
    """Schema de respuesta para un pago."""

    id: int
    plan_id: int
    user_id: int
    amount: float
    payment_date: datetime.datetime


class SubscriptionOut(BaseModel):
    """Schema de respuesta para una suscripción, incluyendo datos anidados del usuario y el plan."""

    id: int
    status: str
    subscription_date: datetime.datetime
    user: UserOut  # Anida el modelo de usuario para una respuesta más completa.
    plan: PlanOut  # Anida el modelo de plan.


class Setting(BaseModel):
    """Schema para recibir y devolver una configuración de negocio."""

    setting_name: str
    setting_value: str
    description: str | None = None


# --- Creación de Tablas y Sesión de Base de Datos ---

# Esta línea instruye a SQLAlchemy para que cree en la base de datos todas las tablas
# que heredan de `Base` y que aún no existan.
Base.metadata.create_all(engine)
# `sessionmaker` es una fábrica que produce objetos de Sesión.
Session = sessionmaker(engine)
# `session` es una instancia de una Sesión, que es el manejador de todas las
# interacciones con la base de datos (consultas, inserciones, etc.).
session = Session()
