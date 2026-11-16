import os 
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from database import obtener_sesion
from models import Usuario

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET or len(JWT_SECRET) <32:
    raise RuntimeError (
        "Configura JWT_SECRET con una clave segura en .env"
    )

ALGORITMO = "HS256"
EMISOR = "inventario-api"
MINUTOS_EXPIRACION = 30

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token"
)

# Crear hash de contraseña 
def hashear_password(password: str) -> str:
    return password_hash.hash(password)

# Verufucar contraseña
def verificar_password(password: str, hash_guardado: str) -> bool:
    
    return password_hash.verify(password, hash_guardado)

# Generar JWT
def crear_access_token(usuario_id: int) -> str:
    ahora = datetime.now(timezone.utc)

    payload = {
        "sub": str(usuario_id),
        "iss": EMISOR,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=MINUTOS_EXPIRACION)
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITMO)

# Identificar usuario de una petición
def usuario_actual(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated[Session, Depends(obtener_sesion)]
) -> Usuario:

    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ivalidado o vencido",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITMO],
            issuer=EMISOR,
            options={
                "require": ["sub", "iss", "iat", "exp"]
            }
        )

        usuario_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, TypeError):
        raise error_credenciales

    usuario = db.get(Usuario, usuario_id)

    if usuario is None or not usuario.activo:
        raise error_credenciales

    return usuario

# Controlar acceso del administrador
def solo_admin(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:

    if usuario.rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes"
        )

    return usuario