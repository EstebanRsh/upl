# routes/plan_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PLANES DE INTERNET (CRUD)
# -----------------------------------------------------------------------------
# Este módulo define los endpoints para las operaciones CRUD (Crear, Leer,
# Actualizar, Borrar) sobre los planes de internet. Todas estas operaciones
# son administrativas y están protegidas por la dependencia 'is_admin'.
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, Query
import math
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import (
    InternetPlan,
    InputPlan,
    UpdatePlan,
    PaginatedResponse,
    PlanOut,
    Subscription,
)
from sqlalchemy.orm import Session
from config.db import get_db
from auth.security import is_admin

# Creación de un router específico para las rutas de planes.
plan_router = APIRouter()


@plan_router.post("/admin/plans/add")
def add_plan(
    plan_data: InputPlan,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Crea un nuevo plan de internet en la base de datos."""
    try:
        new_plan = InternetPlan(
            name=plan_data.name, speed_mbps=plan_data.speed_mbps, price=plan_data.price
        )
        db.add(new_plan)
        db.commit()
        return JSONResponse(
            status_code=201, content={"message": f"Plan '{plan_data.name}' agregado."}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@plan_router.get("/plans/all", response_model=PaginatedResponse[PlanOut])
def get_all_plans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Obtiene una lista paginada de todos los planes de internet existentes."""
    try:
        offset = (page - 1) * size
        total_items = db.query(InternetPlan).count()
        if total_items == 0:
            return PaginatedResponse(
                total_items=0, total_pages=0, current_page=1, items=[]
            )

        plans_query = db.query(InternetPlan).offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=plans_query,
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@plan_router.put("/admin/plans/update/{plan_id}")
def update_plan(
    plan_id: int,
    plan_data: UpdatePlan,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """Actualiza los datos de un plan de internet existente."""
    try:
        plan_to_update = (
            db.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        )
        if not plan_to_update:
            return JSONResponse(
                status_code=404, content={"message": "Plan no encontrado"}
            )

        # Actualización parcial de los datos.
        if plan_data.name is not None:
            plan_to_update.name = plan_data.name
        if plan_data.speed_mbps is not None:
            plan_to_update.speed_mbps = plan_data.speed_mbps
        if plan_data.price is not None:
            plan_to_update.price = plan_data.price

        db.commit()
        db.refresh(
            plan_to_update
        )  # Refresca el objeto para devolver los datos actualizados.
        return {"message": "Plan actualizado exitosamente", "plan": plan_to_update}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@plan_router.delete("/admin/plans/delete/{plan_id}")
def delete_plan(
    plan_id: int, admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    """
    Elimina un plan de internet, solo si no tiene suscripciones activas.
    """
    try:
        # 1. Buscar el plan que se quiere eliminar
        plan_to_delete = (
            db.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        )
        if not plan_to_delete:
            return JSONResponse(
                status_code=404, content={"message": "Plan no encontrado"}
            )

        # 2. VERIFICACIÓN EXPLÍCITA: Contar cuántas suscripciones usan este plan.
        subscription_count = (
            db.query(Subscription).filter(Subscription.plan_id == plan_id).count()
        )

        # 3. LÓGICA DE NEGOCIO: Si hay una o más suscripciones, denegar la eliminación.
        if subscription_count > 0:
            return JSONResponse(
                status_code=400,  # Bad Request
                content={
                    "message": f"No se puede eliminar el plan porque {subscription_count} cliente(s) están suscritos a él."
                },
            )

        # 4. Si no hay suscripciones, proceder con la eliminación.
        db.delete(plan_to_delete)
        db.commit()
        return {"message": f"Plan con ID {plan_id} eliminado exitosamente"}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
