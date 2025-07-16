# tests/test_payment_routes.py

import pytest
from datetime import datetime, timedelta
from models.models import Payment


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
