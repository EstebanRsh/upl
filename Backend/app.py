# app.py
# -----------------------------------------------------------------------------
# ARCHIVO PRINCIPAL DE LA APLICACIÓN FASTAPI
# -----------------------------------------------------------------------------
# Este archivo es el corazón del backend. Se encarga de:
# 1. Crear la instancia principal de la aplicación FastAPI.
# 2. Configurar middlewares, como CORS, para permitir la comunicación con el frontend.
# 3. Importar e incluir todos los routers de los diferentes módulos de la API.
# -----------------------------------------------------------------------------

# Importaciones de FastAPI y de los routers locales.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user_routes import user_router
from routes.plan_routes import plan_router
from routes.payment_routes import payment_router
from routes.subscription_routes import subscription_router
from routes.admin_routes import admin_router
from routes.token_routes import token_router
from routes.billing_routes import billing_router

# Creación de la instancia de FastAPI.
# Se le añaden metadatos que se usarán en la documentación automática (en /docs o /redoc).
app = FastAPI(
    title="API para ISP",
    description="Backend para la gestión de clientes y pagos de un proveedor de internet.",
    version="1.0.0",
)

# Configuración del Middleware de CORS (Cross-Origin Resource Sharing).
# Es una medida de seguridad del navegador que impide que una página web haga peticiones
# a un dominio diferente al que la sirvió. Este middleware le dice al navegador que
# permita peticiones desde cualquier origen ('*').
origins = [
    "http://localhost:3000",  # Si tu frontend corre en el puerto 3000
    "http://localhost:8080",
    "https://mi-empresa-isp.com",
    "https://www.mi-empresa-isp.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # IMPORTANTE: En producción, se debe restringir a los dominios del frontend.
    allow_credentials=True,  # Permite que las cookies se incluyan en las peticiones.
    allow_methods=[
        "*"
    ],  # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"],  # Permite todas las cabeceras HTTP.
)

# Inclusión de los routers en la aplicación principal.
# Cada router contiene un conjunto de rutas relacionadas con una entidad específica (usuarios, planes, etc.).
# 'prefix="/api"' añade "/api" al principio de todas las rutas de ese router.
# 'tags' agrupa las rutas en la documentación de la API.
app.include_router(user_router, prefix="/api", tags=["Usuarios"])
app.include_router(plan_router, prefix="/api", tags=["Planes de Internet"])
app.include_router(payment_router, prefix="/api", tags=["Pagos"])
app.include_router(subscription_router, prefix="/api", tags=["Suscripciones"])
app.include_router(admin_router, prefix="/api", tags=["Administración"])
app.include_router(token_router, prefix="/api", tags=["Token"])
app.include_router(billing_router, prefix="/api", tags=["Facturación"])


# Definición de una ruta raíz de bienvenida.
# Es útil para hacer una comprobación rápida de que el servidor está funcionando.
@app.get("/")
def read_root():
    """Ruta de bienvenida para verificar el estado de la API."""
    return {"welcome": "Bienvenido a la API de ISP"}


# Comando para ejecutar la aplicación con Uvicorn.
# 'uvicorn app:app' -> le dice a uvicorn que busque el objeto 'app' en el archivo 'app.py'.
# '--reload' -> reinicia el servidor automáticamente cada vez que se detecta un cambio en el código.
# uvicorn app:app --reload
