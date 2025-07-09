# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user_routes import user_router
from routes.plan_routes import plan_router
from routes.payment_routes import payment_router
from routes.subscription_routes import subscription_router

app = FastAPI(
    title="API para ISP",
    description="Backend para la gestión de clientes y pagos de un proveedor de internet.",
    version="1.0.0"
)

# Configuración de CORS [cite: 80]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, deberías limitar esto a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas de los diferentes módulos
app.include_router(user_router, prefix="/api", tags=["Usuarios"])
app.include_router(plan_router, prefix="/api", tags=["Planes de Internet"])
app.include_router(payment_router, prefix="/api", tags=["Pagos"])
app.include_router(subscription_router, prefix="/api", tags=["Suscripciones"])

@app.get("/")
def read_root():
    return {"welcome": "Bienvenido a la API de ISP"}