# tests/test_payment_routes.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.models import Invoice, Payment, User, Subscription, UserDetail, InternetPlan


def test_admin_can_add_payment_for_pending_invoice(
    admin_auth_client: TestClient, db_session: Session, setup_user_with_invoice: dict
):
    """
    Prueba el "camino feliz": un administrador registra un pago por el monto exacto
    de una factura pendiente.
    """
    # Arrange
    invoice = setup_user_with_invoice["invoice"]
    user = setup_user_with_invoice["user"]

    payment_data = {
        "user_id": user.id,
        "plan_id": setup_user_with_invoice["plan"].id,
        "amount": invoice.total_amount,
    }

    # Act
    response = admin_auth_client.post("/api/payments/add", json=payment_data)

    # Assert
    assert (
        response.status_code == 201
    ), f"El contenido de la respuesta fue: {response.json()}"

    # Verifica que el estado de la factura ahora sea "paid"
    updated_invoice = db_session.query(Invoice).filter(Invoice.id == invoice.id).one()
    assert updated_invoice.status == "paid"

    # Verifica que se creó un registro de pago
    payment = db_session.query(Payment).filter(Payment.invoice_id == invoice.id).first()
    assert payment is not None
    assert payment.amount == invoice.total_amount


def test_cannot_add_payment_for_non_existent_user(
    admin_auth_client: TestClient,
):
    """
    Prueba que no se puede registrar un pago si el user_id no existe.
    """
    payment_data = {"user_id": 9999, "plan_id": 1, "amount": 100}
    response = admin_auth_client.post("/api/payments/add", json=payment_data)
    assert response.status_code == 404
    # Actualizamos el mensaje esperado para que coincida con la nueva lógica
    assert (
        "No se encontró una suscripción para este usuario y plan"
        in response.json()["message"]
    )


def test_cannot_add_payment_if_no_pending_invoice(
    admin_auth_client: TestClient, setup_user_with_invoice: dict, db_session: Session
):
    """
    Prueba que no se puede registrar un pago si no hay facturas pendientes.
    """
    # Cambia el estado de la factura a "paid"
    invoice = setup_user_with_invoice["invoice"]
    invoice.status = "paid"
    db_session.commit()

    payment_data = {
        "user_id": setup_user_with_invoice["user"].id,
        "plan_id": setup_user_with_invoice["plan"].id,
        "amount": invoice.total_amount,
    }
    response = admin_auth_client.post("/api/payments/add", json=payment_data)
    assert response.status_code == 404
    assert "No se encontró una factura pendiente" in response.json()["message"]


def test_admin_can_get_user_payment_history(
    admin_auth_client: TestClient, db_session: Session, setup_user_with_invoice: dict
):
    """
    Prueba que un admin puede consultar el historial de pagos de un usuario.
    """
    # Arrange: Registramos un pago primero
    user = setup_user_with_invoice["user"]
    invoice = setup_user_with_invoice["invoice"]

    payment_data = {
        "user_id": user.id,
        "plan_id": setup_user_with_invoice["plan"].id,
        "amount": invoice.total_amount,
    }
    # La llamada al endpoint realiza el pago
    post_response = admin_auth_client.post("/api/payments/add", json=payment_data)
    assert post_response.status_code == 201

    # Act: Consultamos el historial del usuario
    response = admin_auth_client.get(f"/api/users/{user.id}/payments")

    # Assert
    assert response.status_code == 200
    paginated_response = response.json()
    # Verificamos que la respuesta es un diccionario con la clave "items"
    assert "items" in paginated_response

    payment_history = paginated_response["items"]

    # Ahora sí, payment_history es la lista que queremos probar
    assert isinstance(payment_history, list)
    assert len(payment_history) == 1
    assert payment_history[0]["amount"] == invoice.total_amount
    assert payment_history[0]["user_id"] == user.id


def test_payment_applied_to_correct_invoice_with_multiple_subscriptions(
    admin_auth_client: TestClient, db_session: Session
):
    """
    Prueba el escenario crítico:
    1. Un usuario tiene una suscripción vieja (Plan A) con una factura pendiente.
    2. El usuario obtiene una nueva suscripción (Plan B) con su propia factura.
    3. Se realiza un pago para el Plan B.
    4. Verifica que el pago se aplique a la factura del Plan B y no a la del Plan A.
    """
    # -- 1. CONFIGURACIÓN DEL ESCENARIO --

    # a. Crear el usuario de prueba
    test_user = User(
        username="multi_sub_user_final",
        email="cliente_multi_final@example.com",
        password="password123",
    )
    db_session.add(test_user)
    db_session.flush()

    test_user_detail = UserDetail(
        dni=12345678,
        firstname="Cliente",
        lastname="Final",
        address="Calle Verdadera 456",
        phone="555-6789",
    )
    test_user.userdetail = test_user_detail
    db_session.add(test_user_detail)

    # b. Crear los dos planes de prueba
    plan_a = InternetPlan(name="Plan Final A", price=50.0, speed_mbps=50)
    plan_b = InternetPlan(name="Plan Final B", price=100.0, speed_mbps=100)
    db_session.add_all([plan_a, plan_b])
    db_session.commit()

    # c. Crear la suscripción antigua (Plan A) y su factura
    # ¡ESTA ES LA CORRECCIÓN! Creamos la suscripción y LUEGO modificamos su estado.
    sub_a = Subscription(user_id=test_user.id, plan_id=plan_a.id)
    sub_a.status = "cancelled"  # <-- Se modifica el atributo aquí.
    db_session.add(sub_a)
    db_session.flush()

    invoice_a = Invoice(
        subscription_id=sub_a.id,
        user_id=test_user.id,
        base_amount=plan_a.price,
        total_amount=plan_a.price,
        due_date=datetime(2024, 6, 15),
    )
    db_session.add(invoice_a)

    # d. Crear la suscripción nueva (Plan B) y su factura
    # El status aquí es 'active', que es el valor por defecto, por lo que no hace falta modificarlo.
    sub_b = Subscription(user_id=test_user.id, plan_id=plan_b.id)
    db_session.add(sub_b)
    db_session.flush()

    invoice_b = Invoice(
        subscription_id=sub_b.id,
        user_id=test_user.id,
        base_amount=plan_b.price,
        total_amount=plan_b.price,
        due_date=datetime(2024, 7, 15),
    )
    db_session.add(invoice_b)
    db_session.commit()

    # -- 2. EJECUCIÓN DE LA ACCIÓN --

    payment_data = {
        "user_id": test_user.id,
        "plan_id": plan_b.id,
        "amount": plan_b.price,
    }
    response = admin_auth_client.post("/api/payments/add", json=payment_data)

    # -- 3. VERIFICACIÓN --

    assert response.status_code == 201, f"Error en la API: {response.json()}"
    assert "Pago registrado exitosamente" in response.json().get("message", "")

    db_session.refresh(invoice_a)
    db_session.refresh(invoice_b)

    assert (
        invoice_a.status == "pending"
    ), "La factura del Plan A no debería haber cambiado."
    assert invoice_b.status == "paid", "La factura del Plan B debería estar pagada."
