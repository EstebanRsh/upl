# tests/test_admin_routes.py
from models.models import User, UserDetail


def test_admin_can_get_all_users(admin_auth_client, db_session):
    """Prueba que un admin puede obtener la lista de usuarios."""
    response_add = admin_auth_client.post(
        "/api/admin/users/add",  # <-- RUTA UNIFICADA
        json={
            "username": "list_user",
            "password": "p",
            "email": "list@test.com",
            "dni": 11,
            "firstname": "f",
            "lastname": "l",
            "address": "a",
            "phone": "p",
        },
    )
    assert response_add.status_code == 201

    response = admin_auth_client.get("/api/admin/users/all")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 2
    usernames = [item["username"] for item in data["items"]]
    assert "testadmin" in usernames
    assert "list_user" in usernames


def test_admin_can_update_user_details(admin_auth_client, db_session):
    """Prueba que un admin puede actualizar los detalles de otro usuario."""
    response_add = admin_auth_client.post(
        "/api/admin/users/add",  # <-- RUTA UNIFICADA
        json={
            "username": "update_user",
            "password": "p",
            "email": "update@test.com",
            "dni": 12,
            "firstname": "OriginalF",
            "lastname": "OriginalL",
            "address": "OriginalA",
            "phone": "OriginalP",
        },
    )
    assert response_add.status_code == 201

    user_to_update = db_session.query(User).filter_by(username="update_user").first()
    assert user_to_update is not None
    user_id_to_update = user_to_update.id

    response = admin_auth_client.put(
        f"/api/admin/users/{user_id_to_update}/details",  # <-- RUTA UNIFICADA
        json={"firstname": "NuevoNombre", "address": "Nueva Direccion"},
    )
    assert response.status_code == 200

    db_session.refresh(user_to_update.userdetail)
    assert user_to_update.userdetail.firstname == "NuevoNombre"
    assert user_to_update.userdetail.address == "Nueva Direccion"


def test_admin_can_delete_user(admin_auth_client, db_session):
    """Prueba que un admin puede eliminar a otro usuario."""
    response_add = admin_auth_client.post(
        "/api/admin/users/add",  # <-- RUTA UNIFICADA
        json={
            "username": "delete_user",
            "password": "p",
            "email": "delete@test.com",
            "dni": 13,
            "firstname": "f",
            "lastname": "l",
            "address": "a",
            "phone": "p",
        },
    )
    assert response_add.status_code == 201

    user_to_delete = db_session.query(User).filter_by(username="delete_user").first()
    assert user_to_delete is not None
    user_id_to_delete = user_to_delete.id

    response = admin_auth_client.delete(
        f"/api/admin/users/{user_id_to_delete}"
    )  # <-- RUTA UNIFICADA
    assert response.status_code == 200

    deleted_user = db_session.query(User).filter_by(id=user_id_to_delete).first()
    assert deleted_user is None
