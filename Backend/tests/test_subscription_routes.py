# tests/test_subscription_routes.py

import pytest
from models.models import User, InternetPlan, Subscription

# --- Pruebas para GET /users/{user_id}/subscriptions ---


def test_user_can_get_their_own_subscriptions(
    client, db_session, create_test_user, create_test_plan
):
    """
    Prueba que un usuario regular puede consultar su propia lista de suscripciones.
    """
    # Arrange: Creamos un usuario, un plan y una suscripción.
    create_test_user("testuser", "user@test.com", 1010)
    user = db_session.query(User).filter_by(username="testuser").first()

    create_test_plan("Plan Personal", 150, 40)
    plan = db_session.query(InternetPlan).filter_by(name="Plan Personal").first()

    subscription = Subscription(user_id=user.id, plan_id=plan.id)
    db_session.add(subscription)
    db_session.commit()

    # Act: Hacemos login como ESE usuario para obtener su token.
    login_res = client.post(
        "/api/users/login", json={"username": "testuser", "password": "testpassword123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/api/users/{user.id}/subscriptions", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["subscription_id"] == subscription.id
    assert data[0]["plan_details"]["name"] == "Plan Personal"


def test_user_cannot_get_another_users_subscriptions(
    client, db_session, create_test_user
):
    """
    Prueba que un usuario regular recibe un error 403 Forbidden si intenta
    ver las suscripciones de otro usuario.
    """
    # Arrange: Creamos dos usuarios.
    create_test_user("user_one", "one@test.com", 2020)
    user_one = db_session.query(User).filter_by(username="user_one").first()

    create_test_user("user_two", "two@test.com", 3030)
    user_two = db_session.query(User).filter_by(username="user_two").first()

    # Act: Hacemos login como user_one...
    login_res = client.post(
        "/api/users/login", json={"username": "user_one", "password": "testpassword123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # ... pero intentamos ver las suscripciones de user_two.
    response = client.get(
        f"/api/users/{user_two.id}/subscriptions", headers=auth_headers
    )

    # Assert
    assert response.status_code == 403  # Forbidden
    assert "No tienes permiso" in response.json()["detail"]


def test_admin_can_get_any_users_subscriptions(
    admin_auth_client, db_session, create_test_user, create_test_plan
):
    """
    Prueba que un administrador puede ver las suscripciones de cualquier usuario.
    """
    # Arrange: Creamos un usuario, plan y suscripción.
    create_test_user("some_user", "some@user.com", 4040)
    user = db_session.query(User).filter_by(username="some_user").first()

    create_test_plan("Plan Empresa", 600, 120)
    plan = db_session.query(InternetPlan).filter_by(name="Plan Empresa").first()

    subscription = Subscription(user_id=user.id, plan_id=plan.id)
    db_session.add(subscription)
    db_session.commit()

    # Act: Usamos el cliente del admin para consultar las suscripciones del usuario.
    response = admin_auth_client.get(f"/api/users/{user.id}/subscriptions")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["plan_details"]["name"] == "Plan Empresa"
