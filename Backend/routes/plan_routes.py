# routes/plan_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PLANES DE INTERNET (CRUD)
# -----------------------------------------------------------------------------
# routes/plan_routes.py
import logging
import math
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from models.models import (
    InternetPlan,
    InputPlan,
    UpdatePlan,
    PaginatedResponse,
    PlanOut,
    Subscription,
)
from config.db import get_db
from auth.security import has_permission

logger = logging.getLogger(__name__)
plan_router = APIRouter()


@plan_router.post(
    "/admin/plans/add",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission("plans:create"))],
)
def add_plan(plan_data: InputPlan, db: Session = Depends(get_db)):
    logger.info(f"Creando nuevo plan: '{plan_data.name}'.")
    try:
        new_plan = InternetPlan(**plan_data.model_dump())
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return {"message": f"Plan '{plan_data.name}' agregado."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error en add_plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.get("/plans/all", response_model=PaginatedResponse[PlanOut])
def get_all_plans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Ruta pública, sin cambios
    logger.info("Solicitud pública para obtener todos los planes.")
    try:
        total_items = db.query(InternetPlan).count()
        plans = db.query(InternetPlan).offset((page - 1) * size).limit(size).all()
        return PaginatedResponse(
            total_items=total_items,
            total_pages=math.ceil(total_items / size),
            current_page=page,
            items=plans,
        )
    except Exception as e:
        logger.error(f"Error en get_all_plans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.put(
    "/admin/plans/update/{plan_id}",
    dependencies=[Depends(has_permission("plans:update"))],
)
def update_plan(plan_id: int, plan_data: UpdatePlan, db: Session = Depends(get_db)):
    logger.info(f"Actualizando plan ID: {plan_id}.")
    try:
        plan = db.query(InternetPlan).filter_by(id=plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan no encontrado")

        update_data = plan_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)

        db.commit()
        db.refresh(plan)
        return {"message": "Plan actualizado.", "plan": PlanOut.model_validate(plan)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_plan (ID: {plan_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.delete(
    "/admin/plans/delete/{plan_id}",
    dependencies=[Depends(has_permission("plans:delete"))],
)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    logger.info(f"Intentando eliminar plan ID: {plan_id}.")
    try:
        plan = db.query(InternetPlan).filter_by(id=plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan no encontrado")

        if db.query(Subscription).filter_by(plan_id=plan_id).first():
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar el plan porque tiene clientes suscritos.",
            )

        db.delete(plan)
        db.commit()
        return {"message": f"Plan con ID {plan_id} eliminado."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en delete_plan (ID: {plan_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
