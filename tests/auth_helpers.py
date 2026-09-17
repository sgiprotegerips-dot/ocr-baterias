"""Credenciales y altas de prueba (el login de producto ya no expone cuentas demo)."""

from __future__ import annotations

import uuid
from typing import Optional

ADMIN_EMAIL = "sgi@protegerips.com"
ADMIN_PASSWORD = "Proteger2026"


def login(client, email: str, password: str):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]


def login_admin(client):
    return login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


def create_and_login_psicologa(client, email: Optional[str] = None, password: str = "PsicoTest2026!"):
    login_admin(client)
    email = email or f"psico-{uuid.uuid4().hex[:8]}@protegerips.com"
    r = client.post(
        "/api/admin/users",
        json={
            "email": email,
            "password": password,
            "nombre_completo": "Psicóloga de Prueba SST",
            "rol": "psicologa",
            "activo": True,
        },
    )
    assert r.status_code == 200, r.text
    client.post("/api/auth/logout")
    user = login(client, email, password)
    return user, email, password
