# tests/test_admin_routes.py


def test_admin_can_get_all_users(admin_auth_client):
    """Prueba que un admin puede obtener la lista de usuarios."""
    # Preparación: admin_auth_client ya crea un admin (user_id=1).
    # Creamos un segundo usuario para tener más de uno en la lista.
    admin_auth_client.post(
        "/api/admin/users/add",
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

    # Acción
    response = admin_auth_client.get("/api/admin/users/all")
    assert response.status_code == 200

    # Verificación
    data = response.json()
    assert data["total_items"] == 2
    assert data["items"][0]["username"] == "testadmin"
    assert data["items"][1]["username"] == "list_user"


def test_admin_can_update_user_details(admin_auth_client, db_session):
    """Prueba que un admin puede actualizar los detalles de otro usuario."""
    # Preparación: Creamos un usuario para actualizar.
    admin_auth_client.post(
        "/api/admin/users/add",
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

    # Acción: Actualizamos los detalles del usuario recién creado (user_id=2).
    response = admin_auth_client.put(
        "/api/admin/users/2/details",
        json={"firstname": "NuevoNombre", "address": "Nueva Direccion"},
    )
    assert response.status_code == 200

    # Verificación: Consultamos el usuario en la BD para ver los cambios.
    from models.models import UserDetail

    user_details = db_session.query(UserDetail).filter_by(id=2).first()
    assert user_details.firstname == "NuevoNombre"
    assert user_details.address == "Nueva Direccion"
    assert user_details.lastname == "OriginalL"  # El apellido no cambió.


def test_admin_can_delete_user(admin_auth_client, db_session):
    """Prueba que un admin puede eliminar a otro usuario."""
    # Preparación: Creamos un usuario para eliminar.
    admin_auth_client.post(
        "/api/admin/users/add",
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

    # Acción: El admin (user_id=1) elimina al nuevo usuario (user_id=2).
    response = admin_auth_client.delete("/api/admin/users/2")
    assert response.status_code == 200

    # Verificación: Comprobamos que el usuario ya no existe en la BD.
    from models.models import User

    deleted_user = db_session.query(User).filter_by(id=2).first()
    assert deleted_user is None
