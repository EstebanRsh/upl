# routes/user_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE GESTIÓN DE USUARIOS (REGISTRO Y LOGIN)
# -----------------------------------------------------------------------------
# Este módulo define los endpoints públicos para la interacción de los usuarios:
# 1. Registrar un nuevo usuario (cliente) en el sistema.
# 2. Iniciar sesión (login), que autentica al usuario y le devuelve los tokens.
# -----------------------------------------------------------------------------
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models.models import session, User, UserDetail, InputUser, InputLogin
from auth.security import Security
from sqlalchemy.orm import joinedload

# Creación de un router específico para las rutas de usuarios.
user_router = APIRouter()


@user_router.post("admin/users/add")
def add_user(user_data: InputUser):
    """
    Registra un nuevo usuario (cliente) y sus detalles personales en la base de datos.
    """
    try:
        # Se crea primero el objeto 'UserDetail' con los datos personales.
        new_user_detail = UserDetail(
            dni=user_data.dni,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            address=user_data.address,
            phone=user_data.phone,
        )
        # Se hashea la contraseña antes de guardarla. NUNCA se guarda en texto plano.
        hashed_password = Security.get_password_hash(user_data.password)

        # Se crea el objeto 'User' principal.
        new_user = User(
            username=user_data.username,
            password=hashed_password,
            email=user_data.email,
            role="cliente",  # Por defecto, todos los nuevos registros son de tipo 'cliente'.
        )

        # Se vinculan los dos objetos a través de la relación de SQLAlchemy.
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


@user_router.post("/users/login")
def login(user_credentials: InputLogin):
    """
    Autentica a un usuario y, si tiene éxito, devuelve un token de acceso
    y establece un token de actualización en una cookie segura.
    """
    try:
        # Busca al usuario por su nombre de usuario en la base de datos.
        user_in_db = (
            session.query(User)
            .filter(User.username == user_credentials.username)
            .first()
        )

        # Verifica si el usuario existe Y si la contraseña proporcionada es correcta.
        if not user_in_db or not Security.verify_password(
            user_credentials.password, user_in_db.password
        ):
            return JSONResponse(
                status_code=401,  # Unauthorized
                content={
                    "success": False,
                    "message": "Usuario o contraseña incorrectos",
                },
            )

        # Si las credenciales son correctas, se generan ambos tokens.
        access_token = Security.generate_access_token(user_in_db)
        refresh_token = Security.generate_refresh_token(user_in_db)

        # Se guarda el nuevo refresh token en la base de datos para la rotación de tokens.
        user_in_db.refresh_token = refresh_token
        session.commit()

        # Se construye la respuesta.
        response_body = {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
        }
        response = JSONResponse(content=response_body)
        # Se establece la cookie 'httpOnly' con el refresh token.
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=True,
        )
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error interno del servidor: {e}"},
        )
    finally:
        session.close()
