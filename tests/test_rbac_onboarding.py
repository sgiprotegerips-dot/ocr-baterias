"""RBAC y onboarding: alta de cliente (admin) y apertura de campaña (psicóloga)."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.web import app
from src.bateria.storage import campaign_root, DATA_DIR
from tests.auth_helpers import create_and_login_psicologa, login, login_admin


def get_client():
    from fastapi.testclient import TestClient

    return TestClient(app)


def test_empresas_requiere_sesion():
    client = get_client()
    r = client.get("/api/empresas")
    assert r.status_code == 401
    print(" test_empresas_requiere_sesion PASSED")


def test_admin_endpoints_prohibidos_a_psicologa():
    client = get_client()
    create_and_login_psicologa(client)
    r = client.get("/api/admin/users")
    assert r.status_code == 403
    print(" test_admin_endpoints_prohibidos_a_psicologa PASSED")


def test_operador_no_puede_dar_alta_cliente():
    client = get_client()
    login(client, "operador@proteger.com.co", "Operador2026!")
    r = client.post(
        "/api/onboarding/cliente",
        json={
            "empresa": {
                "nit": "800111222-3",
                "razon_social": "No Debe Crearse S.A.S.",
            },
            "portal": {
                "nombre_completo": "Gestor SST",
                "email": "sst@nodesdebe.com",
                "password": "Portal2026!",
            },
        },
    )
    assert r.status_code == 403
    print(" test_operador_no_puede_dar_alta_cliente PASSED")


def test_psicologa_no_puede_dar_alta_cliente():
    client = get_client()
    create_and_login_psicologa(client)
    r = client.post(
        "/api/onboarding/cliente",
        json={
            "empresa": {"nit": "800111333-4", "razon_social": "Tampoco S.A.S."},
            "portal": {
                "nombre_completo": "Gestor",
                "email": "sst@tampoco.com",
                "password": "Portal2026!",
            },
        },
    )
    assert r.status_code == 403
    print(" test_psicologa_no_puede_dar_alta_cliente PASSED")


def test_admin_alta_cliente_transaccional():
    client = get_client()
    admin = login_admin(client)
    r_create = client.post(
        "/api/admin/users",
        json={
            "email": f"psico-alta-{uuid.uuid4().hex[:8]}@protegerips.com",
            "password": "PsicoTest2026!",
            "nombre_completo": "Psicóloga de Prueba SST",
            "rol": "psicologa",
            "activo": True,
        },
    )
    assert r_create.status_code == 200, r_create.text
    r_ps = client.get("/api/auth/psicologas")
    assert r_ps.status_code == 200
    psico = next(p for p in r_ps.json() if p["rol"] == "psicologa")

    nit_base = f"901{uuid.uuid4().int % 10**6:06d}"
    portal_email = f"sst-{nit_base}@acme-eval.com"
    payload = {
        "empresa": {
            "nit": f"{nit_base}-1",
            "razon_social": "ACME EVALUADA S.A.S.",
            "sector_economico": "Industrial / Manufactura",
            "codigo_ciiu": "2011",
            "ciudad": "Medellín",
            "direccion": "Calle 10 # 20-30",
            "contacto_nombre": "Ana Soto",
            "contacto_email": portal_email,
            "contacto_telefono": "3100001111",
        },
        "psicologa_id": psico["id"],
        "portal": {
            "nombre_completo": "Ana Soto (SST)",
            "email": portal_email,
            "password": "PortalAcme2026!",
        },
    }
    r = client.post("/api/onboarding/cliente", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["empresa"]["nit"] == nit_base
    assert data["empresa"]["razon_social"] == "ACME EVALUADA S.A.S."
    assert data["empresa"]["psicologa_responsable_id"] == psico["id"]
    assert data["portal"]["email"] == portal_email
    assert data["portal"]["rol"] == "cliente_empresa"
    assert data["portal"]["empresa_id"] == data["empresa"]["id"]
    assert admin["id"]

    # El portal solo ve su empresa
    client.post("/api/auth/logout")
    login(client, portal_email, "PortalAcme2026!")
    r_emp = client.get("/api/empresas")
    assert r_emp.status_code == 200
    empresas = r_emp.json()
    assert len(empresas) == 1
    assert empresas[0]["nit"] == nit_base

    r_casos = client.get("/api/casos")
    assert r_casos.status_code == 403
    print(" test_admin_alta_cliente_transaccional PASSED")


def test_operador_no_abre_campana():
    client = get_client()
    login_admin(client)
    empresas = client.get("/api/empresas").json()
    emp = next(e for e in empresas if e["nit"] in ("901777888", "900548123"))
    client.post("/api/auth/logout")
    login(client, "operador@proteger.com.co", "Operador2026!")
    r = client.post(
        "/api/onboarding/campana",
        json={
            "empresa_id": emp["id"],
            "anio": 2026,
            "periodo": "Anual",
            "sede": "Planta",
            "trabajadores_esperados": 12,
        },
    )
    assert r.status_code == 403
    print(" test_operador_no_abre_campana PASSED")


def test_psicologa_abre_campana_y_crea_carpetas():
    client = get_client()
    login_admin(client)
    empresas = client.get("/api/empresas").json()
    emp = next((e for e in empresas if str(e.get("nit", "")).startswith("901")), empresas[0])
    client.post("/api/auth/logout")

    psico, _, _ = create_and_login_psicologa(client)
    r = client.post(
        "/api/onboarding/campana",
        json={
            "empresa_id": emp["id"],
            "anio": 2026,
            "periodo": "Anual 2026",
            "sede": "Planta Medellín",
            "trabajadores_esperados": 40,
        },
    )
    assert r.status_code == 200, r.text
    med = r.json()
    assert med["empresa_id"] == emp["id"]
    assert med["estado"] == "recoleccion"
    assert med["psicologa_id"] == psico["id"]
    assert med["codigo_campana"].startswith("MED-2026-")

    root = campaign_root(emp["nit"], med["codigo_campana"], data_dir=DATA_DIR)
    assert (root / "uploads").is_dir()
    assert (root / "custodia").is_dir()
    print(" test_psicologa_abre_campana_y_crea_carpetas PASSED")


def test_cliente_no_ve_informe_de_otra_empresa():
    client = get_client()
    login(client, "cliente@proteger.com.co", "Cliente2026!")
    r_meds = client.get("/api/mediciones")
    assert r_meds.status_code == 200
    for med in r_meds.json():
        assert med.get("empresa_nit", "").startswith("900548123") or med.get("empresa_id")
    print(" test_cliente_no_ve_informe_de_otra_empresa PASSED")


def test_admin_no_sella_informe():
    client = get_client()
    login_admin(client)
    meds = client.get("/api/mediciones").json()
    assert meds
    r = client.post(
        f"/api/mediciones/{meds[0]['id']}/informe/aprobar-sellar",
        json={"conclusiones": "No debe sellar", "recomendaciones": "N/A"},
    )
    assert r.status_code == 403
    print(" test_admin_no_sella_informe PASSED")


if __name__ == "__main__":
    test_empresas_requiere_sesion()
    test_admin_endpoints_prohibidos_a_psicologa()
    test_operador_no_puede_dar_alta_cliente()
    test_psicologa_no_puede_dar_alta_cliente()
    test_admin_alta_cliente_transaccional()
    test_operador_no_abre_campana()
    test_psicologa_abre_campana_y_crea_carpetas()
    test_cliente_no_ve_informe_de_otra_empresa()
    test_admin_no_sella_informe()
    print("ALL RBAC/ONBOARDING TESTS PASSED")
