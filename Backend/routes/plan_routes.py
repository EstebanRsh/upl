# routes/plan_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from models.models import session, InternetPlan, InputPlan
from auth.security import Security

plan_router = APIRouter()

@plan_router.post("/plans/add")
def add_plan(plan_data: InputPlan, req: Request):
    # Verificamos el token antes de continuar
    has_access = Security.verify_token(req.headers)
    if not "iat" in has_access:
        return JSONResponse(status_code=401, content=has_access)
    
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
def get_all_plans(req: Request):
    # Verificamos el token
    has_access = Security.verify_token(req.headers)
    if not "iat" in has_access:
        return JSONResponse(status_code=401, content=has_access)
        
    try:
        plans = session.query(InternetPlan).all()
        return plans
    finally:
        session.close()