# models/models.py
from config.db import engine, Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, EmailStr
import datetime

# --- Modelos de la Base de Datos (SQLAlchemy) ---

class User(Base):
    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column("password", String)
    email = Column("email", String(80), nullable=False, unique=True)
    id_userdetail = Column(Integer, ForeignKey("userdetails.id"))
    
    userdetail = relationship("UserDetail", uselist=False)
    payments = relationship("Payment", back_populates="user")

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

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
    speed_mbps = Column(Integer) # Velocidad del plan
    price = Column(Float) # Precio del plan

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

# --- Creación de Tablas y Sesión ---
Base.metadata.create_all(engine)
Session = sessionmaker(engine)
session = Session()