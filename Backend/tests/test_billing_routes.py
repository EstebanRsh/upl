# tests/test_billing_routes.py

import pytest
from datetime import datetime, date, timedelta
from models.models import BusinessSettings, Invoice, Subscription


@pytest.fixture
def setup_billing_rules(db_session):
    """
    Fixture para configurar las reglas de negocio necesarias para la facturación.
    """
    db_session.add(
        BusinessSettings(setting_name="payment_window_days", setting_value="15")
    )
    db_session.add(
        BusinessSettings(setting_name="late_fee_amount", setting_value="5.0")
    )
    db_session.add(
        BusinessSettings(setting_name="days_for_suspension", setting_value="30")
    )
    db_session.commit()


# --- Pruebas para POST /admin/invoices/generate-monthly ---


def test_generate_monthly_invoices_creates_invoice_for_active_user(
    admin_auth_client, db_session, setup_billing_rules, setup_user_with_invoice
):
    """
    Prueba que el endpoint genera una factura para un usuario con una suscripción activa.
    *Nota: Se reutiliza el fixture 'setup_user_with_invoice' para tener un usuario listo.*
    """
    # Arrange: Eliminamos cualquier factura creada por el fixture para empezar de cero.
    db_session.query(Invoice).delete()
    db_session.commit()

    # Act
    response = admin_auth_client.post("/api/admin/invoices/generate-monthly")

    # Assert
    assert response.status_code == 200
    content = response.json()
    assert content["facturas_generadas"] == 1
    assert content["facturas_omitidas_por_duplicado"] == 0

    # Verificamos que la factura se creó en la BD
    user_id = setup_user_with_invoice["user"].id
    invoice = db_session.query(Invoice).filter_by(user_id=user_id).first()
    assert invoice is not None
    assert invoice.status == "pending"
    assert invoice.total_amount == setup_user_with_invoice["plan"].price


def test_generate_monthly_invoices_skips_if_invoice_exists(
    admin_auth_client, db_session, setup_billing_rules, setup_user_with_invoice
):
    """
    Prueba que la lógica anti-duplicados funciona, omitiendo la generación si ya
    existe una factura para el mes y año actual.
    """
    # Arrange: El fixture 'setup_user_with_invoice' ya creó una factura para este mes.

    # Act
    response = admin_auth_client.post("/api/admin/invoices/generate-monthly")

    # Assert
    assert response.status_code == 200
    content = response.json()
    assert content["facturas_generadas"] == 0
    assert content["facturas_omitidas_por_duplicado"] == 1


# --- Pruebas para POST /admin/invoices/process-overdue ---


def test_process_overdue_invoices_applies_late_fee(
    admin_auth_client, db_session, setup_billing_rules, setup_user_with_invoice
):
    """
    Prueba que se aplica una multa por mora a una factura vencida.
    """
    # Arrange: Hacemos que la factura del fixture esté vencida
    invoice = setup_user_with_invoice["invoice"]
    original_amount = invoice.total_amount
    invoice.due_date = date.today() - timedelta(days=1)
    db_session.commit()

    # Act
    response = admin_auth_client.post("/api/admin/invoices/process-overdue")

    # Assert
    assert response.status_code == 200
    assert response.json()["facturas_con_recargo"] == 1

    db_session.refresh(invoice)
    assert invoice.late_fee == 5.0  # El valor que configuramos en el fixture
    assert invoice.total_amount == original_amount + 5.0


def test_process_overdue_invoices_suspends_service(
    admin_auth_client, db_session, setup_billing_rules, setup_user_with_invoice
):
    """
    Prueba que el servicio de un usuario se suspende si la factura está
    muy vencida (según la regla de negocio).
    """
    # Arrange: Hacemos que la factura esté muy vencida
    invoice = setup_user_with_invoice["invoice"]
    subscription_id = invoice.subscription_id
    invoice.due_date = date.today() - timedelta(
        days=31
    )  # Supera los 30 días para suspensión
    db_session.commit()

    # Act
    response = admin_auth_client.post("/api/admin/invoices/process-overdue")

    # Assert
    assert response.status_code == 200
    assert response.json()["servicios_suspendidos"] == 1

    subscription = db_session.query(Subscription).filter_by(id=subscription_id).first()
    assert subscription.status == "suspended"
