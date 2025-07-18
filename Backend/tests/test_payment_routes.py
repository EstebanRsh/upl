# tests/test_payment_routes.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.models import Invoice, Payment, User


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
