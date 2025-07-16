# tests/test_admin_routes.py
import pytest
from models.models import User

# --- Pruebas para GET /admin/users/all ---


def test_get_all_users_returns_list_of_users(admin_auth_client, create_test_user):
    """
    Prueba que un admin puede obtener una lista de todos los usuarios.
    """
    # Arrange: Asegurémonos de que haya al menos dos usuarios
    create_test_user("user_one", "one@test.com", 1111)
    create_test_user("user_two", "two@test.com", 2222)

    # Act: Hacemos la llamada a la API
    response = admin_auth_client.get("/api/admin/users/all")

    # Assert: Verificamos la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 3  # El admin + los 2 que creamos
    assert data["current_page"] == 1

    usernames = {item["username"] for item in data["items"]}
    assert "testadmin" in usernames
    assert "user_one" in usernames
    assert "user_two" in usernames


# --- Pruebas para PUT /admin/users/{user_id}/details ---


def test_update_user_details_modifies_user_in_db(
    admin_auth_client, db_session, create_test_user
):
    """
    Prueba que un admin puede actualizar los detalles de un usuario y se reflejan en la BD.
    """
    # Arrange
    create_test_user("user_to_update", "update@test.com", 3333)
    user = db_session.query(User).filter_by(username="user_to_update").first()
    assert user is not None
    update_data = {"firstname": "NombreActualizado", "address": "DireccionActualizada"}

    # Act
    response = admin_auth_client.put(
        f"/api/admin/users/{user.id}/details",
        json=update_data,
    )

    # Assert
    assert response.status_code == 200
    assert "actualizados exitosamente" in response.json()["message"]

    db_session.refresh(user.userdetail)  # Refrescamos el objeto desde la BD
    assert user.userdetail.firstname == "NombreActualizado"
    assert user.userdetail.address == "DireccionActualizada"


# --- Pruebas para DELETE /admin/users/{user_id} ---


def test_delete_user_removes_user_from_db(
    admin_auth_client, db_session, create_test_user
):
    """
    Prueba que un admin puede eliminar un usuario y este desaparece de la BD.
    """
    # Arrange
    create_test_user("user_to_delete", "delete@test.com", 4444)
    user = db_session.query(User).filter_by(username="user_to_delete").first()
    assert user is not None
    user_id_to_delete = user.id

    # Act
    response = admin_auth_client.delete(f"/api/admin/users/{user_id_to_delete}")

    # Assert
    assert response.status_code == 200
    assert "han sido eliminados" in response.json()["message"]

    deleted_user = db_session.query(User).filter_by(id=user_id_to_delete).first()
    assert deleted_user is None


# --- Pruebas de Casos Borde y Validación ---


def test_admin_cannot_delete_themselves(admin_auth_client, db_session):
    """
    Prueba que un administrador no puede eliminarse a sí mismo.
    """
    # Arrange
    admin_user = db_session.query(User).filter_by(username="testadmin").first()
    admin_id = admin_user.id

    # Act
    response = admin_auth_client.delete(f"/api/admin/users/{admin_id}")

    # Assert
    assert response.status_code == 400  # Bad Request
    assert "no puede eliminarse a sí mismo" in response.json()["detail"]


@pytest.mark.parametrize(
    "field, value, error_message",
    [
        ("username", None, "Input should be a valid string"),
        ("email", "not-an-email", "value is not a valid email address"),
        ("dni", "not-a-number", "Input should be a valid integer"),
    ],
)
def test_add_user_with_invalid_data_returns_error(
    admin_auth_client, field, value, error_message
):
    """
    Usa 'parametrize' para probar múltiples casos de datos inválidos al crear un usuario.
    """
    # Arrange
    user_data = {
        "username": "valid_user",
        "password": "p",
        "email": "valid@email.com",
        "dni": 12345,
        "firstname": "f",
        "lastname": "l",
        "address": "a",
        "phone": "p",
    }
    user_data[field] = value  # Sobrescribimos el campo con el dato inválido

    # Act
    response = admin_auth_client.post("/api/admin/users/add", json=user_data)

    # Assert
    assert (
        response.status_code == 422
    )  # Unprocessable Entity (error de validación de Pydantic)
    # Aquí podrías hacer aserciones más específicas sobre el cuerpo del error si lo necesitas
