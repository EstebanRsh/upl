# tests/test_edge_cases.py

import pytest
from models.models import User, InternetPlan


def test_add_user_with_duplicate_username(admin_auth_client, create_test_user):
    """
    Prueba que la API rechaza la creación de un usuario si el 'username' ya existe.
    """
    # Arrange: Creamos un usuario inicial.
    create_test_user("duplicate_user", "first@test.com", 9090)

    # Act: Intentamos crear OTRO usuario con el MISMO username.
    response = admin_auth_client.post(
        "/api/admin/users/add",
        json={
            "username": "duplicate_user",  # Username repetido
            "password": "p",
            "email": "second@test.com",
            "dni": 9091,
            "firstname": "f",
            "lastname": "l",
            "address": "a",
            "phone": "p",
        },
    )

    # Assert
    assert response.status_code == 409
    # En un escenario ideal, se podría capturar este error específico y devolver un 409 Conflict.
    assert "ya existen" in response.json().get("detail", "")


def test_get_non_existent_user_details(admin_auth_client):
    """
    Prueba que la API devuelve un error 404 si se intentan obtener
    los detalles de un usuario que no existe.
    """
    # Arrange: Un ID de usuario que sabemos que no existe.
    non_existent_user_id = 999999

    # Act
    response = admin_auth_client.get(f"/api/users/{non_existent_user_id}/subscriptions")

    # Assert
    assert response.status_code == 404
    assert "Usuario no encontrado" in response.json()["message"]


def test_update_plan_with_invalid_price(
    admin_auth_client, db_session, create_test_plan
):
    """
    Prueba la validación de Pydantic: la API debe rechazar la actualización
    de un plan con un precio negativo.
    """
    # Arrange
    create_test_plan("Plan a Invalidar", 100, 50)
    plan = db_session.query(InternetPlan).filter_by(name="Plan a Invalidar").first()
    update_data = {"price": -10.0}  # Precio inválido

    # Act
    response = admin_auth_client.put(
        f"/api/admin/plans/update/{plan.id}", json=update_data
    )

    # Assert
    assert response.status_code == 422  # Unprocessable Entity
    error_detail = response.json()["detail"][0]
    assert error_detail["msg"] == "Input should be greater than 0"
    assert error_detail["loc"] == ["body", "price"]
