# routes/plan_routes.py
from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from models.models import session, InternetPlan, InputPlan, UpdatePlan
from auth.security import is_admin

plan_router = APIRouter()

@plan_router.post("/plans/add")
def add_plan(plan_data: InputPlan, admin_user: dict = Depends(is_admin)):
    try:
        new_plan = InternetPlan(
            name=plan_data.name,
            speed_mbps=plan_data.speed_mbps,
            price=plan_data.price
        )
        session.add(new_plan)
        session.commit()
        return JSONResponse(status_code=201, content={"message": f"Plan '{plan_data.name}' agregado."})
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()

@plan_router.get("/plans/all")
def get_all_plans(admin_user: dict = Depends(is_admin)):
    try:
        plans = session.query(InternetPlan).all()
        return plans
    finally:
        session.close()

@plan_router.put("/plans/update/{plan_id}")
def update_plan(plan_id: int, plan_data: UpdatePlan, admin_user: dict = Depends(is_admin)):
    try:
        plan_to_update = session.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        if not plan_to_update:
            return JSONResponse(status_code=404, content={"message": "Plan no encontrado"})
        if plan_data.name is not None:
            plan_to_update.name = plan_data.name
        if plan_data.speed_mbps is not None:
            plan_to_update.speed_mbps = plan_data.speed_mbps
        if plan_data.price is not None:
            plan_to_update.price = plan_data.price
        session.commit()
        session.refresh(plan_to_update)
        return {"message": "Plan actualizado exitosamente", "plan": plan_to_update}
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()

@plan_router.delete("/plans/delete/{plan_id}")
def delete_plan(plan_id: int, admin_user: dict = Depends(is_admin)):
    try:
        plan_to_delete = session.query(InternetPlan).filter(InternetPlan.id == plan_id).first()
        if not plan_to_delete:
            return JSONResponse(status_code=404, content={"message": "Plan no encontrado"})
        session.delete(plan_to_delete)
        session.commit()
        return {"message": f"Plan con ID {plan_id} eliminado exitosamente"}
    except Exception as e:
        session.rollback()
        if "violates foreign key constraint" in str(e).lower():
            return JSONResponse(status_code=400, content={"message": "No se puede eliminar el plan porque tiene pagos asociados."})
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()