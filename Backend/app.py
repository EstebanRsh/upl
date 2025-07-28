# app.py
# -----------------------------------------------------------------------------
# ARCHIVO PRINCIPAL DE LA APLICACIÓN FASTAPI
# -----------------------------------------------------------------------------
# Este archivo es el corazón del backend. Se encarga de:
# 1. Crear la instancia principal de la aplicación FastAPI.
# 2. Configurar middlewares, como CORS, para permitir la comunicación con el frontend.
# 3. Importar e incluir todos los routers de los diferentes módulos de la API.
# -----------------------------------------------------------------------------

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.db import Base, engine
from sqlalchemy.orm import Session
from config.db import SessionLocal
from routes.user_routes import user_router
from routes.plan_routes import plan_router
from routes.payment_routes import payment_router
from routes.subscription_routes import subscription_router
from routes.admin_routes import admin_router
from routes.token_routes import token_router
from routes.billing_routes import billing_router
from routes.role_routes import role_router
from routes.invoice_routes import invoice_router
from models import models
import logging
from core.logging_config import setup_logging
from routes.billing_routes import generate_monthly_invoices_job
from core.init_data import create_initial_roles_and_permissions

# Llama a la función para configurar el logging al inicio de la app.
setup_logging()
# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Metadatos para las "etiquetas" (tags). Mejora la documentación.
tags_metadata = [
    {
        "name": "Usuarios",
        "description": "Endpoints para el registro y login de usuarios.",
    },
    {
        "name": "Administración",
        "description": "Operaciones administrativas sobre usuarios, planes y suscripciones. **Requiere permisos de administrador**.",
    },
    {
        "name": "Planes de Internet",
        "description": "Consulta pública de los planes de internet disponibles.",
    },
    {
        "name": "Pagos",
        "description": "Endpoints para procesar pagos y consultar historiales.",
    },
    {
        "name": "Suscripciones",
        "description": "Consulta de las suscripciones de un usuario.",
    },
    {
        "name": "Facturación",
        "description": "Operaciones de alto nivel como la generación masiva de facturas y el procesamiento de pagos vencidos.",
    },
    {
        "name": "Token",
        "description": "Endpoint para la renovación de tokens de acceso (refresh token).",
    },
]

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Gestión para UPL",
    description="""
API para la gestión de clientes, planes, suscripciones y facturación de un Proveedor de Servicios de Internet (ISP). 🚀

**Esta API permite:**
* Gestionar clientes (CRUD).
* Definir y administrar planes de internet.
* Manejar suscripciones de clientes a planes.
* Procesar pagos y generar recibos en PDF.
* Automatizar la facturación mensual y el manejo de moras.
    """,
    version="1.1.0",
    openapi_tags=tags_metadata,
)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def get_db_for_job():
    """Función para obtener una sesión de BD para las tareas programadas."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Eventos de inicio y apagado de la aplicación
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación."""
    logger.info("La aplicación se ha iniciado.")
    db = SessionLocal()
    try:
        create_initial_roles_and_permissions(db)
    finally:
        db.close()
    # Iniciar el programador
    scheduler.start()

    # Añadir la tarea de facturación mensual
    scheduler.add_job(
        generate_monthly_invoices_job,
        trigger=CronTrigger(day=1, hour=2, minute=0),
        id="monthly_invoicing_job",
        name="Generación de Facturas Mensuales",
        replace_existing=True,
        args=[next(get_db_for_job())],
    )
    logger.info("Tarea de facturación mensual programada.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("La aplicación se está apagando.")
    # Detener el programador
    scheduler.shutdown()


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de los routers
app.include_router(user_router, prefix="/api", tags=["Usuarios"])
app.include_router(plan_router, prefix="/api", tags=["Planes de Internet"])
app.include_router(payment_router, prefix="/api", tags=["Pagos"])
app.include_router(subscription_router, prefix="/api", tags=["Suscripciones"])
app.include_router(admin_router, prefix="/api/admin", tags=["Administración"])
app.include_router(token_router, prefix="/api", tags=["Token"])
app.include_router(billing_router, prefix="/api", tags=["Facturación"])
app.include_router(role_router, prefix="/api/admin", tags=["Roles y Permisos"])
app.include_router(invoice_router, prefix="/api", tags=["Facturación"])
app.mount("/facturas", StaticFiles(directory="facturas"), name="facturas")


@app.get("/")
def read_root():
    return {"welcome": "Bienvenido a la API de ISP"}


# Comando para ejecutar la aplicación con Uvicorn.
# 'uvicorn app:app' -> le dice a uvicorn que busque el objeto 'app' en el archivo 'app.py'.
# '--reload' -> reinicia el servidor automáticamente cada vez que se detecta un cambio en el código.
# uvicorn app:app --reload
