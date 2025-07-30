# schemas/plan_schemas.py
from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    """Schema de respuesta para un plan de internet."""

    id: int
    name: str
    speed_mbps: int
    price: float
    model_config = ConfigDict(from_attributes=True)
