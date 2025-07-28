# Backend/core/init_data.py
import logging
from sqlalchemy.orm import Session
from models.models import Role, Permission, PERMISSIONS_LIST

logger = logging.getLogger(__name__)

# --- AQUÍ DEFINES TUS ROLES Y SUS PERMISOS ---
# Esta es la única parte que necesitarás modificar en el futuro.
ROLES_WITH_PERMISSIONS = {
    "Cliente": [],  # Los clientes no tienen permisos especiales, se manejan por rutas
    "Técnico": [
        "users:read_all",
        "users:update",
    ],
    "Cobrador": [
        "payments:create",
        "users:read_all",
    ],
    "Admin": "all",  # "all" significa que tendrá todos los permisos
    "Gerente": "all",  # "all" también para el gerente
}


def create_initial_roles_and_permissions(db: Session):
    """
    Crea todos los permisos y roles definidos en el sistema si no existen.
    Esta función es segura de ejecutar en cada inicio de la aplicación.
    """
    logger.info("Verificando y creando roles y permisos iniciales...")

    # 1. Crear todos los permisos de la lista PERMISSIONS_LIST
    permissions_map = {}
    for perm_data in PERMISSIONS_LIST:
        perm_name = perm_data["name"]
        existing_perm = db.query(Permission).filter_by(name=perm_name).first()
        if not existing_perm:
            existing_perm = Permission(**perm_data)
            db.add(existing_perm)
        permissions_map[perm_name] = existing_perm
    db.commit()

    # 2. Crear los roles y asignar sus permisos
    all_permissions = list(permissions_map.values())
    for role_name, perm_list in ROLES_WITH_PERMISSIONS.items():
        existing_role = db.query(Role).filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name, description=f"Rol para {role_name}")

            if perm_list == "all":
                new_role.permissions = all_permissions
            else:
                new_role.permissions = [
                    permissions_map[p_name]
                    for p_name in perm_list
                    if p_name in permissions_map
                ]

            db.add(new_role)
            logger.info(f"Rol '{role_name}' creado.")
    db.commit()
    logger.info("Configuración de roles y permisos completada.")
