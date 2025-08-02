# Backend/setup_database.py
import logging
from getpass import getpass
from sqlalchemy.orm import Session
from config.db import SessionLocal, Base, engine
from models.models import (
    User,
    UserDetail,
    InternetPlan,
    Subscription,
    Invoice,
    Payment,
    CompanySettings,  # <-- ¡CORREGIDO! Se usa el nuevo modelo
)
from auth.security import Security
import datetime

# --- Configuración ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATOS INICIALES (sin la vieja configuración) ---
PLANS_DATA = [
    {"name": "Fibra 50MB", "speed_mbps": 50, "price": 4500.00},
    {"name": "Fibra 100MB", "speed_mbps": 100, "price": 6000.00},
    {"name": "Fibra 300MB", "speed_mbps": 300, "price": 8500.00},
]

CLIENTS_DATA = [
    {
        "user": {
            "username": "lmartinez",
            "email": "lucia.martinez@example.com",
            "password": "password123",
        },
        "detail": {
            "dni": 28123456,
            "firstname": "Lucía",
            "lastname": "Martinez",
            "address": "Calle Sol 45",
            "city": "Villa Crespo",
        },
        "plan_name": "Fibra 100MB",
        "scenario": "pagado",
    },
    {
        "user": {
            "username": "cgomez",
            "email": "carlos.gomez@example.com",
            "password": "password123",
        },
        "detail": {
            "dni": 32789012,
            "firstname": "Carlos",
            "lastname": "Gomez",
            "address": "Av. Luna 820",
            "city": "Palermo",
        },
        "plan_name": "Fibra 50MB",
        "scenario": "pendiente",
    },
    {
        "user": {
            "username": "asanchez",
            "email": "ana.sanchez@example.com",
            "password": "password123",
        },
        "detail": {
            "dni": 35456789,
            "firstname": "Ana",
            "lastname": "Sanchez",
            "address": "Jr. Estrella 112",
            "city": "Caballito",
        },
        "plan_name": "Fibra 300MB",
        "scenario": "vencido",
    },
    {
        "user": {
            "username": "mfernandez",
            "email": "martin.fernandez@example.com",
            "password": "password123",
        },
        "detail": {
            "dni": 30112233,
            "firstname": "Martín",
            "lastname": "Fernandez",
            "address": "Pje. Cometa 99",
            "city": "Flores",
        },
        "plan_name": "Fibra 100MB",
        "scenario": "pagado_transferencia",
    },
]


def create_admin_user(db: Session):
    """
    Función para crear el usuario administrador, interactiva.
    ESTA ES TU FUNCIÓN ORIGINAL, SIN CAMBIOS.
    """
    print("\n--- Creación del Usuario Administrador ---")
    use_default = input(
        "¿Deseas usar el administrador por defecto ('Admin', pass: 'adminpass')? (s/n): "
    ).lower()

    if use_default == "s":
        username, email, password, firstname, lastname, dni = (
            "Admin",
            "admin@upl.com",
            "adminpass",
            "Admin",
            "UPL",
            "111111",
        )
        logger.info("Usando datos por defecto para el administrador.")
    else:
        username = input("Nombre de usuario para el Administrador: ")
        email = input("Email del Administrador: ")
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        firstname, lastname, dni = (
            input("Nombre: "),
            input("Apellido: "),
            input("DNI: "),
        )

    hashed_password = Security.get_password_hash(password)
    admin_detail = UserDetail(
        dni=int(dni), firstname=firstname, lastname=lastname, type="administrador"
    )
    admin_user = User(username=username, password=hashed_password, email=email)
    admin_user.userdetail = admin_detail
    db.add(admin_user)
    db.commit()
    logger.info(f"¡Usuario Administrador '{username}' creado exitosamente!")


def setup_database():
    db: Session = SessionLocal()
    try:
        logger.info("--- Iniciando configuración de la base de datos ---")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas recreadas exitosamente.")

        # --- LÓGICA CORREGIDA Y SIMPLIFICADA ---
        logger.info("Creando la configuración inicial de la empresa...")
        # Llama a CompanySettings() sin argumentos para usar los valores por defecto.
        initial_settings = CompanySettings()
        db.add(initial_settings)
        db.commit()
        logger.info("Configuración de la empresa creada con valores por defecto.")

        # --- TU LÓGICA ORIGINAL PARA CREAR ADMIN Y CLIENTES, SIN CAMBIOS ---
        create_admin_user(db)

        logger.info("Creando planes de internet...")
        plans = {
            plan_data["name"]: InternetPlan(**plan_data) for plan_data in PLANS_DATA
        }
        db.add_all(plans.values())
        db.commit()

        logger.info("Creando datos de clientes y facturación de ejemplo...")
        today = datetime.date.today()
        for client_data in CLIENTS_DATA:
            user_info = client_data["user"]
            detail_info = client_data["detail"]
            user_pass = Security.get_password_hash(user_info["password"])
            user_detail = UserDetail(**detail_info, type="cliente")
            new_user = User(
                username=user_info["username"],
                password=user_pass,
                email=user_info["email"],
            )
            new_user.userdetail = user_detail
            db.add(new_user)
            db.commit()

            plan = plans[client_data["plan_name"]]
            subscription = Subscription(user_id=new_user.id, plan_id=plan.id)
            db.add(subscription)
            db.commit()

            due_date = today + datetime.timedelta(days=15)
            if client_data["scenario"] == "vencido":
                due_date = today - datetime.timedelta(days=5)

            invoice = Invoice(
                user_id=new_user.id,
                subscription_id=subscription.id,
                due_date=due_date,
                base_amount=plan.price,
                total_amount=plan.price,
            )
            if "pagado" in client_data["scenario"]:
                invoice.status = "Pagado"

            db.add(invoice)
            db.commit()

            if "pagado" in client_data["scenario"]:
                payment_method = (
                    "Transferencia"
                    if client_data["scenario"] == "pagado_transferencia"
                    else "Efectivo"
                )
                payment = Payment(
                    user_id=new_user.id, amount=plan.price, invoice_id=invoice.id
                )
                payment.payment_method = payment_method
                payment.payment_date = datetime.datetime.now() - datetime.timedelta(
                    days=3
                )
                db.add(payment)
                db.commit()

        logger.info(f"{len(CLIENTS_DATA)} clientes de ejemplo creados.")
        logger.info("\n--- ¡Configuración completada! ---")

    except Exception as e:
        logger.error(f"Ocurrió un error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    respuesta = input(
        "ADVERTENCIA: Esto borrará TODOS los datos. ¿Estás seguro? (s/n): "
    )
    if respuesta.lower() == "s":
        setup_database()
    else:
        print("Operación cancelada.")
