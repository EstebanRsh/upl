# routes/plan_routes.py
from fastapi import APIRouter
from models.models import session, InternetPlan, InputPlan

plan_router = APIRouter()

@plan_router.post("/plans/add")
def add_plan(plan_data: InputPlan):
    try:
        new_plan = InternetPlan(
            name=plan_data.name,
            speed_mbps=plan_data.speed_mbps,
            price=plan_data.price
        )
        session.add(new_plan)
        session.commit()
        return {"message": f"Plan '{plan_data.name}' agregado."}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()

@plan_router.get("/plans/all")
def get_all_plans():
    try:
        plans = session.query(InternetPlan).all()
        return plans
    finally:
        session.close()