# schemas/user_schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr


class UserOut(BaseModel):
    """Schema de respuesta para un usuario, no incluye la contraseña."""

    id: int
    username: str
    email: EmailStr
    dni: int
    firstname: str
    lastname: str
    address: str | None = None
    barrio: str | None = None
    city: str | None = None
    phone: str | None = None
    phone2: str | None = None
    role: str  # El rol simplificado

    model_config = ConfigDict(from_attributes=True)
