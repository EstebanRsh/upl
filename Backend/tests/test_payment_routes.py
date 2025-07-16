# tests/test_payment_routes.py

import pytest
from datetime import datetime, timedelta
from models.models import User, InternetPlan, Subscription, Invoice, Payment


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


# --- Pruebas para POST /payments/add ---


def test_admin_can_add_payment_for_pending_invoice(
    admin_auth_client, db_session, setup_user_with_invoice
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
        "plan_id": setup_user_with_invoice[
            "plan"
        ].id,  # Aunque no se usa en la lógica, el modelo lo pide
        "amount": invoice.total_amount,  # El monto exacto
    }

    # Act
    response = admin_auth_client.post("/api/payments/add", json=payment_data)

    # Assert
    assert response.status_code == 201
    assert "Pago registrado" in response.json()["message"]

    # Verificamos los cambios en la BD
    db_session.refresh(invoice)
    assert invoice.status == "paid"
    payment = db_session.query(Payment).filter_by(invoice_id=invoice.id).first()
    assert payment is not None
    assert payment.amount == invoice.total_amount


def test_cannot_add_payment_with_incorrect_amount(
    admin_auth_client, setup_user_with_invoice
):
    """
    Prueba la regla de negocio: la API debe rechazar un pago si el monto
    no coincide con el total de la factura.
    """
    # Arrange
    invoice = setup_user_with_invoice["invoice"]
    user = setup_user_with_invoice["user"]

    payment_data = {
        "user_id": user.id,
        "plan_id": setup_user_with_invoice["plan"].id,
        "amount": invoice.total_amount - 10,  # Un monto incorrecto
    }

    # Act
    response = admin_auth_client.post("/api/payments/add", json=payment_data)

    # Assert
    assert response.status_code == 400  # Bad Request
    content = response.json()
    assert "El monto del pago no coincide" in content["message"]
    assert content["monto_requerido"] == invoice.total_amount


# --- Pruebas para GET /users/{user_id}/payments ---


def test_admin_can_get_user_payment_history(
    admin_auth_client, db_session, setup_user_with_invoice
):
    """
    Prueba que un admin puede consultar el historial de pagos de un usuario.
    """
    # Arrange: Registramos un pago primero
    invoice = setup_user_with_invoice["invoice"]
    user = setup_user_with_invoice["user"]
    payment_data = {
        "user_id": user.id,
        "plan_id": setup_user_with_invoice["plan"].id,
        "amount": invoice.total_amount,
    }
    admin_auth_client.post("/api/payments/add", json=payment_data)

    # Act
    response = admin_auth_client.get(f"/api/users/{user.id}/payments")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 1
    assert data["items"][0]["amount"] == invoice.total_amount
