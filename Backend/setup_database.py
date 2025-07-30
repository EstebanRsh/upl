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
    InputPayment,
    BusinessSettings,
)
from auth.security import Security
from services.payment_service import process_new_payment
import datetime

# --- Configuración ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATOS INICIALES ---
COMPANY_SETTINGS = [
    {
        "setting_name": "BUSINESS_NAME",
        "setting_value": "UPL Telecomunicaciones",
        "description": "Nombre comercial de la empresa.",
    },
    {
        "setting_name": "BUSINESS_CUIT",
        "setting_value": "30-12345678-9",
        "description": "CUIT de la empresa.",
    },
    {
        "setting_name": "BUSINESS_ADDRESS",
        "setting_value": "Av. Siempreviva 742",
        "description": "Dirección fiscal de la empresa.",
    },
    {
        "setting_name": "BUSINESS_CITY",
        "setting_value": "Springfield",
        "description": "Ciudad de la empresa.",
    },
    {
        "setting_name": "BUSINESS_PHONE",
        "setting_value": "11-5555-4444",
        "description": "Teléfono de contacto.",
    },
    {
        "setting_name": "payment_window_days",
        "setting_value": "15",
        "description": "Días de plazo para el pago de facturas.",
    },
    {
        "setting_name": "late_fee_amount",
        "setting_value": "500",
        "description": "Monto del recargo por pago fuera de término.",
    },
    {
        "setting_name": "days_for_suspension",
        "setting_value": "30",
        "description": "Días tras el vencimiento para suspender el servicio.",
    },
    {
        "setting_name": "auto_invoicing_enabled",
        "setting_value": "true",
        "description": "Habilita o deshabilita la facturación automática mensual.",
    },
]

PLAN_EJEMPLO = {"name": "Fibra 100MB", "speed_mbps": 100, "price": 5000.00}


# --- LÓGICA DEL SCRIPT ---
def setup_database():
    db: Session = SessionLocal()
    try:
        logger.info(
            "--- Iniciando configuración de la base de datos (versión simplificada) ---"
        )

        logger.warning("Borrando todas las tablas existentes...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas recreadas exitosamente.")

        # 1. Guardar la configuración de la empresa
        for setting in COMPANY_SETTINGS:
            db.add(BusinessSettings(**setting))
        db.commit()
        logger.info("Configuración de la empresa guardada.")

        # 2. Crear el primer Superusuario (Administrador)
        print("\n--- Creación del Usuario Administrador ---")
        username = input("Nombre de usuario para el Administrador: ")
        email = input("Email del Administrador: ")
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")

        firstname = input("Nombre: ")
        lastname = input("Apellido: ")
        dni = input("DNI: ")

        hashed_password = Security.get_password_hash(password)

        admin_detail = UserDetail(
            dni=int(dni),
            firstname=firstname,
            lastname=lastname,
            type="administrador",  # Asignación directa del rol
        )
        admin_user = User(username=username, password=hashed_password, email=email)
        admin_user.userdetail = admin_detail
        db.add(admin_user)
        db.commit()
        logger.info(f"¡Usuario Administrador '{username}' creado exitosamente!")

        # 3. Crear datos de ejemplo (1 cliente con 1 factura pagada)
        logger.info("Creando datos de ejemplo (cliente, plan, factura y pago)...")
        plan = InternetPlan(**PLAN_EJEMPLO)
        cliente_detail = UserDetail(
            dni=12345678,
            firstname="Juan",
            lastname="Perez",
            type="cliente",  # Asignación directa del rol
            address="Calle Falsa 123",
            barrio="Centro",
            city="Ciudad Ejemplo",
        )
        cliente_user = User(
            username="juanperez",
            password=Security.get_password_hash("password123"),
            email="juan.perez@cliente.com",
        )
        cliente_user.userdetail = cliente_detail
        db.add(plan)
        db.add(cliente_user)
        db.commit()

        subscription = Subscription(user_id=cliente_user.id, plan_id=plan.id)
        db.add(subscription)
        db.commit()

        invoice = Invoice(
            user_id=cliente_user.id,
            subscription_id=subscription.id,
            due_date=datetime.date.today() + datetime.timedelta(days=15),
            base_amount=plan.price,
            total_amount=plan.price,
        )
        db.add(invoice)
        db.commit()

        # Simular un pago para la factura creada
        payment_input = InputPayment(
            user_id=cliente_user.id, plan_id=plan.id, amount=plan.price
        )
        # Asumiendo que process_new_payment puede ser llamado aquí
        # Si da error, puede que necesite ser adaptado o llamado de otra forma
        try:
            process_new_payment(payment_input, db)
            db.commit()
            logger.info(
                "Cliente de ejemplo 'juanperez' (pass: password123) creado con una factura pagada."
            )
        except Exception as payment_error:
            logger.error(f"No se pudo procesar el pago de ejemplo: {payment_error}")
            db.rollback()

        logger.info("\n--- ¡Configuración completada! La base de datos está lista. ---")

    except Exception as e:
        logger.error(f"Ocurrió un error durante la configuración: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    respuesta = input(
        "ADVERTENCIA: Este script borrará TODOS los datos y configurará la BD desde cero. ¿Estás seguro? (s/n): "
    )
    if respuesta.lower() == "s":
        setup_database()
    else:
        print("Operación cancelada.")
