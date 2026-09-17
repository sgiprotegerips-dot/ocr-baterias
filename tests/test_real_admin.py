"""Administrador real (Orlando Hernández Manrique) y retiro de cuentas demo de psicóloga."""

from __future__ import annotations

from app.web import app


def get_client():
    from fastapi.testclient import TestClient

    return TestClient(app)


def test_orlando_es_el_administrador():
    client = get_client()
    r = client.post(
        "/api/auth/login",
        json={"email": "sgi@protegerips.com", "password": "Proteger2026"},
    )
    assert r.status_code == 200, r.text
    user = r.json()["user"]
    assert user["rol"] == "admin"
    assert user["email"] == "sgi@protegerips.com"
    assert "Orlando" in user["nombre_completo"]
    r_stats = client.get("/api/admin/stats")
    assert r_stats.status_code == 200
    print(" test_orlando_es_el_administrador PASSED")


def test_admin_demo_ya_no_entra():
    client = get_client()
    r = client.post(
        "/api/auth/login",
        json={"email": "admin@proteger.com.co", "password": "AdminSST2026!"},
    )
    assert r.status_code == 401
    print(" test_admin_demo_ya_no_entra PASSED")


def test_psicologa_demo_ya_no_entra():
    client = get_client()
    r = client.post(
        "/api/auth/login",
        json={"email": "dra.valencia@proteger.com.co", "password": "PsicoSST2026!"},
    )
    assert r.status_code == 401
    print(" test_psicologa_demo_ya_no_entra PASSED")


if __name__ == "__main__":
    test_orlando_es_el_administrador()
    test_admin_demo_ya_no_entra()
    test_psicologa_demo_ya_no_entra()
    print("ALL REAL ADMIN TESTS PASSED")
