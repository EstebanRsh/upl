# config/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker  # ¡Importante añadir sessionmaker!
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)


# 1. Creamos una fábrica de sesiones en lugar de una sesión global.
#    Esto nos permitirá crear una sesión nueva y fresca para cada petición.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 2. Creamos la dependencia de FastAPI.
#    Esta función se encargará de crear la sesión, entregarla a la ruta (yield db),
#    y asegurarse de que siempre se cierre al final (finally: db.close()).
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
