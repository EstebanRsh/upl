# tests/test_plan_routes.py
import pytest
from models.models import InternetPlan, User

# --- Pruebas para POST /admin/plans/add ---


def test_admin_can_add_a_new_plan(admin_auth_client, db_session):
    """
    Prueba que un administrador puede crear un nuevo plan de internet.
    """
    # Arrange
    plan_data = {"name": "Plan Fibra 500", "speed_mbps": 500, "price": 50.75}

    # Act
    response = admin_auth_client.post("/api/admin/plans/add", json=plan_data)

    # Assert
    assert response.status_code == 201
    assert "agregado" in response.json()["message"]

    # Verifica que el plan realmente se guardó en la base de datos
    plan_in_db = db_session.query(InternetPlan).filter_by(name="Plan Fibra 500").first()
    assert plan_in_db is not None
    assert plan_in_db.price == 50.75


# --- Pruebas para GET /plans/all ---


def test_admin_can_get_all_plans(admin_auth_client, create_test_plan):
    """
    Prueba que un admin puede obtener una lista paginada de todos los planes.
    """
    # Arrange: Creamos varios planes para asegurarnos de que la paginación funcione
    create_test_plan("Plan Básico", 50, 20.0)
    create_test_plan("Plan Gamer", 1000, 80.5)

    # Act
    response = admin_auth_client.get("/api/plans/all?page=1&size=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 2

    plan_names = {item["name"] for item in data["items"]}
    assert "Plan Básico" in plan_names
    assert "Plan Gamer" in plan_names


# --- Pruebas para PUT /admin/plans/update/{plan_id} ---


def test_admin_can_update_plan(admin_auth_client, db_session, create_test_plan):
    """
    Prueba que un administrador puede actualizar los datos de un plan existente.
    """
    # Arrange
    create_test_plan("Plan a Modificar", 100, 30)
    plan = db_session.query(InternetPlan).filter_by(name="Plan a Modificar").first()
    assert plan is not None
    update_data = {"name": "Plan Modificado", "price": 35.50}

    # Act
    response = admin_auth_client.put(
        f"/api/admin/plans/update/{plan.id}", json=update_data
    )

    # Assert
    assert response.status_code == 200
    assert "actualizado exitosamente" in response.json()["message"]

    db_session.refresh(plan)
    assert plan.name == "Plan Modificado"
    assert plan.price == 35.50


# --- Pruebas para DELETE /admin/plans/delete/{plan_id} ---


def test_admin_can_delete_plan(admin_auth_client, db_session, create_test_plan):
    """
    Prueba que un administrador puede eliminar un plan que no tiene suscripciones.
    """
    # Arrange
    create_test_plan("Plan a Eliminar", 20, 10)
    plan = db_session.query(InternetPlan).filter_by(name="Plan a Eliminar").first()
    assert plan is not None
    plan_id_to_delete = plan.id

    # Act
    response = admin_auth_client.delete(f"/api/admin/plans/delete/{plan_id_to_delete}")

    # Assert
    assert response.status_code == 200
    assert "eliminado exitosamente" in response.json()["message"]

    deleted_plan = (
        db_session.query(InternetPlan).filter_by(id=plan_id_to_delete).first()
    )
    assert deleted_plan is None


def test_cannot_delete_plan_with_subscriptions(
    admin_auth_client, db_session, create_test_user, create_test_plan
):
    """
    Prueba que la API previene la eliminación de un plan si este tiene clientes suscritos.
    Este es un test de una regla de negocio CRÍTICA.
    """
    # Arrange: Necesitamos un usuario y un plan, y luego suscribir el usuario al plan.
    create_test_user("suscriptor", "s@test.com", 9999)
    user = db_session.query(User).filter_by(username="suscriptor").first()

    create_test_plan("Plan Popular", 300, 60)
    plan = db_session.query(InternetPlan).filter_by(name="Plan Popular").first()

    # Asignamos el plan al usuario (simulando una suscripción)
    assign_response = admin_auth_client.post(
        "/api/admin/subscriptions/assign", json={"user_id": user.id, "plan_id": plan.id}
    )
    assert assign_response.status_code == 201

    # Act: Intentamos eliminar el plan
    response = admin_auth_client.delete(f"/api/admin/plans/delete/{plan.id}")

    # Assert
    assert response.status_code == 400  # Esperamos un "Bad Request"
    content = response.json()
    assert "No se puede eliminar el plan" in content["message"]
    assert "cliente(s) están suscritos a él" in content["message"]
