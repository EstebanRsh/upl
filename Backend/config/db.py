# config/db.py
# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------------------------------------------
# Este archivo configura la conexión con la base de datos PostgreSQL usando SQLAlchemy.
# -----------------------------------------------------------------------------
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()
# Cargar las variables de entorno desde el archivo .env
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)

Base = declarative_base()
