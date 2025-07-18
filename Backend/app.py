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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.db import Base, engine  # Modificado
from routes.user_routes import user_router
from routes.plan_routes import plan_router
from routes.payment_routes import payment_router
from routes.subscription_routes import subscription_router
from routes.admin_routes import admin_router
from routes.token_routes import token_router
from routes.billing_routes import billing_router
from models import models

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

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://mi-empresa-isp.com",
    "https://www.mi-empresa-isp.com",
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


@app.get("/")
def read_root():
    return {"welcome": "Bienvenido a la API de ISP"}


# Comando para ejecutar la aplicación con Uvicorn.
# 'uvicorn app:app' -> le dice a uvicorn que busque el objeto 'app' en el archivo 'app.py'.
# '--reload' -> reinicia el servidor automáticamente cada vez que se detecta un cambio en el código.
# uvicorn app:app --reload
