# tests/test_auth_routes.py

import pytest
from models.models import User

# --- Pruebas para POST /users/login ---


def test_login_with_correct_credentials_returns_tokens(
    client, db_session, create_test_user
):
    """
    Prueba el "camino feliz": un usuario se loguea con credenciales correctas,
    recibe un access_token y una cookie httpOnly con el refresh_token.
    """
    # Arrange
    create_test_user("login_user", "login@test.com", 6060)
    login_data = {"username": "login_user", "password": "testpassword123"}

    # Act
    response = client.post("/api/users/login", json=login_data)

    # Assert
    assert response.status_code == 200
    content = response.json()
    assert content["success"] is True
    assert "access_token" in content
    assert content["token_type"] == "bearer"

    # Verificamos que la cookie del refresh token se haya establecido
    assert "refresh_token" in response.cookies
    # Verificamos que el refresh token se guardó en la BD para ese usuario
    user_in_db = db_session.query(User).filter_by(username="login_user").first()
    assert user_in_db.refresh_token is not None


def test_login_with_incorrect_password_fails(client, create_test_user):
    """
    Prueba que el login falla con un error 401 Unauthorized si la contraseña es incorrecta.
    """
    # Arrange
    create_test_user("bad_password_user", "badpass@test.com", 7070)
    login_data = {"username": "bad_password_user", "password": "password_incorrecto"}

    # Act
    response = client.post("/api/users/login", json=login_data)

    # Assert
    assert response.status_code == 401
    assert "Usuario o contraseña incorrectos" in response.json()["message"]


# --- Pruebas para POST /token/refresh ---


def test_refresh_token_returns_new_access_token(client, db_session, create_test_user):
    """
    Prueba el flujo completo de renovación de token:
    1. Login para obtener tokens iniciales.
    2. Usar la cookie de refresh_token para obtener un nuevo access_token.
    """
    # Arrange: 1. Login inicial
    create_test_user("refresh_user", "refresh@test.com", 8080)
    login_data = {"username": "refresh_user", "password": "testpassword123"}
    login_response = client.post("/api/users/login", json=login_data)
    assert login_response.status_code == 200

    user_in_db = db_session.query(User).filter_by(username="refresh_user").first()
    first_refresh_token = user_in_db.refresh_token

    refresh_cookie_value = login_response.cookies.get("refresh_token")

    client.cookies.set("refresh_token", refresh_cookie_value)

    # Act: 2. Petición de renovación
    refresh_response = client.post("/api/token/refresh")

    client.cookies.clear()

    # Assert
    assert refresh_response.status_code == 200
    content = refresh_response.json()
    assert "access_token" in content

    db_session.refresh(user_in_db)
    assert user_in_db.refresh_token is not None
    assert user_in_db.refresh_token != first_refresh_token
