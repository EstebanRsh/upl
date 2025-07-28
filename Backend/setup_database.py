# Backend/setup_database.py
import logging
from getpass import getpass
from sqlalchemy.orm import Session
from config.db import SessionLocal, Base, engine
from models.models import (
    User,
    UserDetail,
    Role,
    Permission,
    PERMISSIONS_LIST,
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
# Aquí defines la configuración y los datos de ejemplo
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
]
ROLES = ["Cliente", "Técnico", "Cobrador", "Admin", "Gerente"]
PERMISSIONS_FOR_ROLES = {
    "Técnico": ["users:read_all", "users:update"],
    "Cobrador": ["payments:create", "users:read_all"],
}
PLANS_TO_CREATE = [
    {"name": "Fibra 100MB", "speed_mbps": 100, "price": 5000.00},
]


# --- LÓGICA DEL SCRIPT ---
def setup_database():
    db: Session = SessionLocal()
    try:
        logger.info("--- Iniciando configuración completa de la base de datos ---")

        logger.warning("Borrando todas las tablas existentes...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas recreadas exitosamente.")

        # 1. Crear Permisos
        permissions_map = {p["name"]: Permission(**p) for p in PERMISSIONS_LIST}
        db.add_all(permissions_map.values())
        db.commit()
        logger.info(f"{len(permissions_map)} permisos creados.")

        # 2. Crear Roles y Asignar Permisos
        roles_map = {}
        all_permissions = list(permissions_map.values())
        for role_name in ROLES:
            role = Role(name=role_name, description=f"Rol para {role_name}")
            if role_name in ["Admin", "Gerente"]:
                role.permissions = all_permissions
            elif role_name in PERMISSIONS_FOR_ROLES:
                role.permissions = [
                    permissions_map[p_name]
                    for p_name in PERMISSIONS_FOR_ROLES[role_name]
                ]
            db.add(role)
            roles_map[role_name] = role
        db.commit()
        logger.info(f"{len(roles_map)} roles creados y permisos asignados.")

        # 3. Guardar la configuración de la empresa
        for setting in COMPANY_SETTINGS:
            db.add(BusinessSettings(**setting))
        db.commit()
        logger.info("Configuración de la empresa guardada.")

        # 4. Crear el primer Superusuario (Gerente)
        print("\n--- Creación del Usuario Gerente ---")
        username = input("Nombre de usuario para el Gerente: ")
        email = input("Email del Gerente: ")
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")

        firstname = input("Nombre: ")
        lastname = input("Apellido: ")
        dni = input("DNI: ")

        hashed_password = Security.get_password_hash(password)

        # Se crea el usuario y luego se asignan las relaciones para evitar errores
        gerente_user = User(username=username, password=hashed_password, email=email)
        gerente_detail = UserDetail(
            dni=int(dni), firstname=firstname, lastname=lastname
        )
        gerente_user.userdetail = gerente_detail
        gerente_user.role_obj = roles_map["Gerente"]

        db.add(gerente_user)
        db.commit()
        logger.info(f"¡Usuario Gerente '{username}' creado exitosamente!")

        # 5. Crear datos de ejemplo (1 cliente con 1 factura pagada y PDF)
        logger.info("Creando datos de ejemplo (cliente, plan, factura y pago)...")
        plan = InternetPlan(**PLANS_TO_CREATE[0])
        cliente_detail = UserDetail(
            dni=12345678,
            firstname="Juan",
            lastname="Perez",
            address="Calle Falsa 123",
            barrio="Centro",
            city="Ciudad Ejemplo",
        )

        # Contraseña para el cliente de ejemplo: "password123"
        cliente_user = User(
            username="juanperez",
            password=Security.get_password_hash("password123"),
            email="juan.perez@cliente.com",
        )
        cliente_user.userdetail = cliente_detail
        cliente_user.role_obj = roles_map["Cliente"]
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

        payment_input = InputPayment(
            user_id=cliente_user.id, plan_id=plan.id, amount=plan.price
        )
        process_new_payment(payment_input, db)
        db.commit()
        logger.info(
            "Cliente de ejemplo 'juanperez' (pass: password123) creado con una factura pagada y un recibo PDF."
        )

        logger.info(
            "\n--- ¡Configuración completada! La base de datos está lista para usar. ---"
        )

    except Exception as e:
        logger.error(f"Ocurrió un error durante la configuración: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    respuesta = input(
        "ADVERTENCIA: Este script borrará TODOS los datos de tu BD y la configurará desde cero. ¿Estás seguro? (s/n): "
    )
    if respuesta.lower() == "s":
        setup_database()
    else:
        print("Operación cancelada.")
