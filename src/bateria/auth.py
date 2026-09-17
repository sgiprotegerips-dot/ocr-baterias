"""Módulo de Autenticación, Seguridad y RBAC (Control de Acceso Basado en Roles)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db.models import Usuario
from .db.session import get_db

# Configuración JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "SST_SecretKey_Resolucion2764_2026_Colombia")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 Horas
COOKIE_NAME = "bateria_sst_token"

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Genera hash bcrypt seguro con salt automático."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crea token JWT con expiración."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida firma del JWT."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.PyJWTError, Exception):
        return None


async def get_current_user_optional(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    cookie_token: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> Optional[Usuario]:
    """Obtiene el usuario autenticado si existe, sin lanzar excepción 401."""
    token = None
    if cookie_token:
        token = cookie_token
    elif bearer and bearer.credentials:
        token = bearer.credentials

    if not token:
        return None

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None

    user_id = payload["sub"]
    result = await db.execute(select(Usuario).where(Usuario.id == user_id, Usuario.activo.is_(True)))
    return result.scalar_one_or_none()


async def get_current_user(
    current_user: Optional[Usuario] = Depends(get_current_user_optional),
) -> Usuario:
    """Obliga a que el usuario esté autenticado. Lanza 401 si no hay sesión."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado. Inicie sesión para acceder.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(allowed_roles: List[str]):
    """Genera una dependencia que valida que el usuario pertenezca a los roles autorizados."""
    async def role_checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker
