# routes/user_routes.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models.models import session, User, UserDetail, InputUser, InputLogin
from auth.security import Security
from sqlalchemy.orm import joinedload

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
            phone=user_data.phone,
        )
        # Hasheamos la contraseña antes de crear el objeto User
        hashed_password = Security.get_password_hash(user_data.password)

        # Creamos el usuario principal
        new_user = User(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            role="cliente",
        )

        # Vinculamos ambos objetos usando la relación ORM
        new_user.userdetail = new_user_detail

        session.add(new_user)
        session.commit()

        return JSONResponse(
            status_code=201, content={"message": "Cliente agregado exitosamente"}
        )
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
        user_in_db = (
            session.query(User)
            .filter(User.username == user_credentials.username)
            .first()
        )

        # Verificamos si el usuario existe y si la contraseña es correcta usando el hash
        if not user_in_db or not Security.verify_password(
            user_credentials.password, user_in_db.password
        ):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Usuario o contraseña incorrectos",
                },
            )

        # Si las credenciales son correctas, genera los tokens
        access_token = Security.generate_access_token(user_in_db)
        refresh_token = Security.generate_refresh_token(user_in_db)

        # Guardar el nuevo refresh token en la base de datos
        user_in_db.refresh_token = refresh_token
        session.commit()

        # Crear la respuesta y AÑADIR LA COOKIE
        response_body = {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
        }
        response = JSONResponse(content=response_body)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # El navegador no permite a JS leer esta cookie
            samesite="strict",  # Protección contra ataques CSRF
            secure=True,  # Solo enviar por HTTPS en producción
        )
        return response
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
