# routes/role_routes.py
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from config.db import get_db
from models.models import (
    Role,
    Permission,
    RoleCreate,
    RoleOut,
    RolePermissionUpdate,
    PermissionOut,
)
from auth.security import has_permission

logger = logging.getLogger(__name__)
role_router = APIRouter()


@role_router.post(
    "/roles",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
    dependencies=[Depends(has_permission("roles:manage"))],
)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    logger.info(f"Intentando crear el rol: {role_data.name}")
    if db.query(Role).filter_by(name=role_data.name).first():
        raise HTTPException(status_code=400, detail="El nombre del rol ya existe.")

    new_role = Role(**role_data.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    logger.info(f"Rol '{new_role.name}' creado.")
    return new_role


@role_router.get(
    "/roles",
    response_model=List[RoleOut],
    summary="Listar todos los roles",
    dependencies=[Depends(has_permission("roles:manage"))],
)
def get_all_roles(db: Session = Depends(get_db)):
    logger.info("Solicitando la lista de todos los roles.")
    return db.query(Role).options(joinedload(Role.permissions)).all()


@role_router.get(
    "/permissions",
    response_model=List[PermissionOut],
    summary="Listar todos los permisos disponibles",
    dependencies=[Depends(has_permission("roles:manage"))],
)
def get_all_permissions(db: Session = Depends(get_db)):
    logger.info("Solicitando la lista de todos los permisos del sistema.")
    return db.query(Permission).all()


@role_router.put(
    "/roles/{role_id}/permissions",
    response_model=RoleOut,
    summary="Actualizar permisos de un rol",
    dependencies=[Depends(has_permission("roles:manage"))],
)
def update_role_permissions(
    role_id: int, update_data: RolePermissionUpdate, db: Session = Depends(get_db)
):
    logger.info(f"Actualizando permisos para el rol ID: {role_id}")
    role = db.query(Role).filter_by(id=role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")

    permissions = (
        db.query(Permission).filter(Permission.id.in_(update_data.permission_ids)).all()
    )
    if len(permissions) != len(update_data.permission_ids):
        raise HTTPException(
            status_code=400, detail="Uno o más IDs de permisos son inválidos."
        )

    role.permissions = permissions
    db.commit()
    db.refresh(role)
    logger.info(f"Permisos para el rol '{role.name}' actualizados.")
    return role
