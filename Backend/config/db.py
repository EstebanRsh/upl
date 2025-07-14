# config/db.py
# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------------------------------------------
# Este archivo configura la conexión con la base de datos PostgreSQL usando SQLAlchemy.
# -----------------------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# 'create_engine' crea el objeto principal de SQLAlchemy para la conexión.
# La cadena de conexión define el dialecto (postgresql), usuario (postgres),
# contraseña (1234), host (localhost), puerto (5432) y nombre de la BD (upl_db).
# ¡IMPORTANTE! En un entorno de producción, esta cadena NUNCA debe estar en el código.
# Debe construirse a partir de variables de entorno.
engine = create_engine("postgresql://postgres:1234@localhost:5432/upl_db")

# 'declarative_base' crea una clase base de la que heredarán todos los modelos ORM.
Base = declarative_base()
