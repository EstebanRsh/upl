# routes/plan_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE PLANES DE INTERNET (CRUD)
# -----------------------------------------------------------------------------
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
from auth.security import is_admin

logger = logging.getLogger(__name__)
plan_router = APIRouter()


@plan_router.post("/admin/plans/add", status_code=status.HTTP_201_CREATED)
def add_plan(
    plan_data: InputPlan,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' creando nuevo plan: '{plan_data.name}'."
    )
    try:
        new_plan = InternetPlan(
            name=plan_data.name, speed_mbps=plan_data.speed_mbps, price=plan_data.price
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        logger.info(f"Plan '{new_plan.name}' creado con ID: {new_plan.id}.")
        return {"message": f"Plan '{plan_data.name}' agregado."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en add_plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.get("/plans/all", response_model=PaginatedResponse[PlanOut])
def get_all_plans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.info("Solicitud pública para obtener todos los planes.")
    try:
        # ... (lógica sin cambios) ...
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
        logger.error(f"Error inesperado en get_all_plans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.put("/admin/plans/update/{plan_id}")
def update_plan(
    plan_id: int,
    plan_data: UpdatePlan,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin '{admin_user.get('sub')}' actualizando plan ID: {plan_id}.")
    try:
        plan_to_update = (
            db.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        )
        if not plan_to_update:
            logger.warning(
                f"Intento de actualizar un plan no existente (ID: {plan_id})."
            )
            raise HTTPException(status_code=404, detail="Plan no encontrado")
        update_data = plan_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan_to_update, key, value)
        db.commit()
        db.refresh(plan_to_update)
        logger.info(f"Plan ID {plan_id} actualizado exitosamente.")
        return {
            "message": "Plan actualizado exitosamente",
            "plan": PlanOut.model_validate(plan_to_update),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en update_plan (ID: {plan_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@plan_router.delete("/admin/plans/delete/{plan_id}")
def delete_plan(
    plan_id: int, admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' intentando eliminar plan ID: {plan_id}."
    )
    try:
        plan_to_delete = (
            db.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        )
        if not plan_to_delete:
            logger.warning(f"Intento de eliminar un plan no existente (ID: {plan_id}).")
            raise HTTPException(status_code=404, detail="Plan no encontrado")
        subscription_count = (
            db.query(Subscription).filter(Subscription.plan_id == plan_id).count()
        )
        if subscription_count > 0:
            logger.warning(
                f"Intento fallido de eliminar plan ID {plan_id}: tiene {subscription_count} suscripciones activas."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el plan porque {subscription_count} cliente(s) están suscritos a él.",
            )
        db.delete(plan_to_delete)
        db.commit()
        logger.info(
            f"Plan ID {plan_id} ('{plan_to_delete.name}') eliminado exitosamente."
        )
        return {"message": f"Plan con ID {plan_id} eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en delete_plan (ID: {plan_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
