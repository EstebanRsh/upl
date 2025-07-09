# routes/token_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from models.models import session, User
from auth.security import Security
import jwt

token_router = APIRouter()


@token_router.post("/token/refresh")
def refresh_access_token(refresh_token: str):
    try:
        # 1. Decodificar el refresh token para validar que no haya expirado
        payload = jwt.decode(refresh_token, Security.secret, algorithms=["HS256"])

        # 2. Obtener el username del payload del token
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Refresh token inválido")

        # 3. Buscar al usuario en la base de datos
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=401, detail="Usuario del token no encontrado"
            )

        # 4. Generar un nuevo access token y devolverlo
        new_access_token = Security.generate_access_token(user)

        return JSONResponse(
            status_code=200,
            content={"access_token": new_access_token, "token_type": "bearer"},
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    finally:
        session.close()
