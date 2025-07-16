# tests/conftest.py
import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, UserDetail, InternetPlan, Subscription, Invoice
from datetime import datetime, timedelta

# --- CONFIGURACIÓN INICIAL ---
# Se define la clave secreta para el entorno de pruebas
os.environ["JWT_SECRET_KEY"] = "super_secret_key_for_tests"

# Se añade el directorio raíz a la ruta de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Se importan la app y las dependencias de la base de datos
from app import app
from config.db import Base, get_db
from auth.security import Security

# --- CONFIGURACIÓN DE LA BASE DE DATOS POSTGRESQL DE PRUEBA ---
# Asegúrate de que tus variables de entorno (DB_USER, DB_PASS, DB_HOST) están disponibles
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
# Apuntamos a la nueva base de datos de prueba 'upl_test'
TEST_DB_NAME = "upl_test"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{TEST_DB_NAME}"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- GESTIÓN DEL CICLO DE VIDA DE LA BASE DE DATOS ---


@pytest.fixture(scope="module")
def client():
    """
    Fixture que gestiona la base de datos. Crea las tablas una vez por
    módulo de tests y las elimina al final para una limpieza completa.
    """
    # Se crean todas las tablas en la base de datos de prueba
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c

    # Se eliminan todas las tablas al final de los tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(client):  # Depende de 'client' para asegurar que las tablas ya existen
    """
    Proporciona una sesión de BD aislada para cada test.
    Todo lo que se haga en el test se revierte al final.
    """
    connection = engine.connect()
    # Inicia una transacción
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)

    # Sobrescribimos la dependencia 'get_db' de la app para que use esta sesión
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield db

    # Al final del test, se cierra la sesión y se revierte la transacción
    db.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
    # Se limpia el override
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def admin_auth_client(client, db_session):
    """
    Crea un cliente autenticado usando la sesión del test actual.
    """
    from models.models import User, UserDetail

    hashed_password = Security.get_password_hash("testpassword")
    admin_user = User(
        username="testadmin",
        password=hashed_password,
        email="admin@test.com",
        role="administrador",
    )
    admin_details = UserDetail(
        dni=1,
        firstname="Admin",
        lastname="Test",
        address="123 Test St",
        phone="555",
    )
    admin_user.userdetail = admin_details
    db_session.add(admin_user)
    db_session.commit()

    response = client.post(
        "/api/users/login",
        json={"username": "testadmin", "password": "testpassword"},
    )
    if response.status_code != 200:
        # Esto nos dará el error exacto si vuelve a fallar
        print("Cuerpo del error en login:", response.json())
    assert response.status_code == 200, "Fallo en el login del admin fixture"

    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    client.headers.pop("Authorization", None)


@pytest.fixture
def create_test_user(admin_auth_client):
    """
    Un factory fixture para crear usuarios de prueba con datos únicos.
    Esto nos permite crear varios usuarios diferentes en nuestros tests.
    """

    def _create_user(username, email, dni):
        response = admin_auth_client.post(
            "/api/admin/users/add",
            json={
                "username": username,
                "password": "testpassword123",
                "email": email,
                "dni": dni,
                "firstname": "Test",
                "lastname": "User",
                "address": "123 Test Street",
                "phone": "123456789",
            },
        )
        assert (
            response.status_code == 201
        ), f"No se pudo crear el usuario de prueba: {response.json()}"
        return response.json()

    return _create_user


@pytest.fixture
def create_test_plan(admin_auth_client):
    """
    Un factory fixture para crear planes de internet de prueba.
    """

    def _create_plan(name, speed, price):
        response = admin_auth_client.post(
            "/api/admin/plans/add",
            json={"name": name, "speed_mbps": speed, "price": price},
        )
        assert response.status_code == 201
        return response.json()

    return _create_plan


@pytest.fixture
def setup_user_with_invoice(
    db_session, admin_auth_client, create_test_user, create_test_plan
):
    """
    Un fixture completo que crea un usuario, un plan, una suscripción
    y una factura pendiente lista para ser pagada.
    """
    # Arrange: Crear usuario, plan y suscripción
    create_test_user("payer_user", "payer@test.com", 5050)
    user = db_session.query(User).filter_by(username="payer_user").first()

    create_test_plan("Plan de Pago", 200, 55.50)
    plan = db_session.query(InternetPlan).filter_by(name="Plan de Pago").first()

    assign_res = admin_auth_client.post(
        "/api/admin/subscriptions/assign", json={"user_id": user.id, "plan_id": plan.id}
    )
    assert assign_res.status_code == 201
    subscription = db_session.query(Subscription).filter_by(user_id=user.id).first()

    # Arrange: Crear una factura para esa suscripción
    invoice = Invoice(
        user_id=user.id,
        subscription_id=subscription.id,
        due_date=datetime.now() + timedelta(days=15),
        base_amount=plan.price,
        total_amount=plan.price,  # Sin mora
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)

    return {"user": user, "plan": plan, "invoice": invoice}
