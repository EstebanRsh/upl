# routes/token_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from models.models import session, User
from auth.security import Security
import jwt

token_router = APIRouter()


@token_router.post("/token/refresh")
def refresh_access_token(request: Request, response: Response):
    try:
        # 1. Leer el refresh token desde la cookie
        refresh_token_from_cookie = request.cookies.get("refresh_token")
        if not refresh_token_from_cookie:
            raise HTTPException(
                status_code=401, detail="No se encontró el refresh token"
            )

        payload = jwt.decode(
            refresh_token_from_cookie, Security.secret, algorithms=["HS256"]
        )
        username = payload.get("sub")

        user = session.query(User).filter(User.username == username).first()

        # 2. VALIDAR que el token de la cookie coincide con el de la BD
        if not user or user.refresh_token != refresh_token_from_cookie:
            # Si no coincide, es una señal de posible robo. Invalida el token.
            if user:
                user.refresh_token = None
                session.commit()
            raise HTTPException(
                status_code=401, detail="Refresh token inválido o revocado"
            )

        # 3. ROTAR: Generar nuevos tokens
        new_access_token = Security.generate_access_token(user)
        new_refresh_token = Security.generate_refresh_token(user)

        # 4. Guardar el NUEVO refresh token en la BD
        user.refresh_token = new_refresh_token
        session.commit()

        # 5. Devolver la respuesta con el nuevo access token y la nueva cookie
        response_body = {"access_token": new_access_token, "token_type": "bearer"}
        response = JSONResponse(content=response_body)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="strict",
            secure=True,
        )
        return response

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token ha expirado")
    except (jwt.InvalidTokenError, Exception) as e:
        raise HTTPException(status_code=401, detail=f"Refresh token inválido: {e}")
    finally:
        session.close()
