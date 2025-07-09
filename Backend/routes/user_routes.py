# routes/user_routes.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models.models import session, User, UserDetail, InputUser, InputLogin
from auth.security import Security

# Cambiamos el nombre del router para que sea más específico
user_router = APIRouter()

@user_router.post("/users/add")
def add_user(user_data: InputUser):
    try:
        # Creamos el detalle del usuario primero
        new_user_detail = UserDetail(
            dni=user_data.dni,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            address=user_data.address,
            phone=user_data.phone
        )
        
        # Creamos el usuario principal
        new_user = User(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email
        )
        
        # Vinculamos ambos objetos usando la relación ORM
        new_user.userdetail = new_user_detail
        
        session.add(new_user)
        session.commit()
        
        return JSONResponse(status_code=201, content={"message": "Cliente agregado exitosamente"})
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()

# --- FUNCIÓN DE LOGIN COMPLETA ---
@user_router.post("/users/login")
def login(user_credentials: InputLogin):
    """
    Autentica a un usuario y devuelve un token JWT si las credenciales son válidas.
    """
    try:
        # Busca al usuario por su nombre de usuario
        user_in_db = session.query(User).filter(User.username == user_credentials.username).first()

        # Verifica si el usuario no existe o si la contraseña es incorrecta
        if not user_in_db or not user_in_db.password == user_credentials.password:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Usuario o contraseña incorrectos",
                },
            )
        
        # Si las credenciales son correctas, genera el token
        token = Security.generate_token(user_in_db)
        
        if not token:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Error al generar el token",
                },
            )
            
        # Devuelve el token
        return JSONResponse(
            status_code=200, content={"success": True, "token": token}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error interno del servidor: {e}",
            },
        )
    finally:
        session.close()