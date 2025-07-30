# app.py
# -----------------------------------------------------------------------------
# ARCHIVO PRINCIPAL DE LA APLICACIÓN FASTAPI (VERSIÓN SIMPLIFICADA)
# -----------------------------------------------------------------------------

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.db import Base, engine, SessionLocal
from models import models
import logging
from core.logging_config import setup_logging
from routes.billing_routes import generate_monthly_invoices_job

# --- Importaciones de Rutas ---
from routes.user_routes import user_router
from routes.plan_routes import plan_router
from routes.payment_routes import payment_router
from routes.subscription_routes import subscription_router
from routes.admin_routes import admin_router
from routes.billing_routes import billing_router
from routes.invoice_routes import invoice_router

# Configura el logging al inicio de la app.
setup_logging()
# Crea las tablas en la base de datos si no existen.
Base.metadata.create_all(bind=engine)

# Metadatos para la documentación de la API.
tags_metadata = [
    {
        "name": "Usuarios",
        "description": "Endpoints para el login y gestión del perfil de usuario.",
    },
    {
        "name": "Admin",
        "description": "Operaciones administrativas. **Requiere rol de administrador**.",
    },
    {
        "name": "Planes de Internet",
        "description": "Consulta pública y gestión de planes de internet.",
    },
    {
        "name": "Pagos",
        "description": "Endpoints para procesar pagos y consultar historiales.",
    },
    {
        "name": "Suscripciones",
        "description": "Endpoints para gestionar las suscripciones de los clientes.",
    },
    {
        "name": "Facturación",
        "description": "Endpoints para la gestión de facturas.",
    },
]

app = FastAPI(
    title="API de Gestión para UPL (Simplificada)",
    description="API para la gestión de clientes, planes, suscripciones y facturación.",
    version="2.0.0",
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
    # Ya no se crean roles y permisos aquí.

    scheduler.start()
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
    scheduler.shutdown()


# Configuración de CORS
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

# --- Inclusión de los Routers Simplificados ---
app.include_router(user_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(
    admin_router, prefix="/api"
)  # Prefijo de admin se maneja en el propio router
app.include_router(billing_router, prefix="/api")
app.include_router(invoice_router, prefix="/api")

# Rutas que ya no se incluyen:
# app.include_router(token_router, ...)
# app.include_router(role_router, ...)

app.mount("/facturas", StaticFiles(directory="facturas"), name="facturas")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def read_root():
    return {"welcome": "Bienvenido a la API de ISP v2.0"}


# Comando para ejecutar la aplicación con Uvicorn.
# 'uvicorn app:app' -> le dice a uvicorn que busque el objeto 'app' en el archivo 'app.py'.
# '--reload' -> reinicia el servidor automáticamente cada vez que se detecta un cambio en el código.
# uvicorn app:app --reload
