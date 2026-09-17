"""El HTML imprimible y el Excel requieren sesión y responden con el tipo correcto."""

from __future__ import annotations

from app.web import app
from tests.auth_helpers import login_admin


def get_client():
    from fastapi.testclient import TestClient

    return TestClient(app)


def _first_medicion_id(client):
    r = client.get("/api/mediciones")
    assert r.status_code == 200, r.text
    meds = r.json()
    assert meds, "Se requiere al menos una medición"
    return meds[0]["id"]


def test_html_imprimible_sin_sesion_es_401():
    client = get_client()
    mid = "00000000-0000-0000-0000-000000000000"
    r = client.get(f"/api/mediciones/{mid}/informe/html")
    assert r.status_code == 401
    print(" test_html_imprimible_sin_sesion_es_401 PASSED")


def test_html_imprimible_con_sesion_es_html():
    client = get_client()
    login_admin(client)
    mid = _first_medicion_id(client)
    r = client.get(f"/api/mediciones/{mid}/informe/html")
    assert r.status_code == 200, r.text[:400]
    assert "text/html" in r.headers.get("content-type", "")
    assert b"<!doctype html>" in r.content.lower() or b"<html" in r.content.lower()
    assert b"Informe" in r.content or b"INFORME" in r.content
    print(" test_html_imprimible_con_sesion_es_html PASSED")


def test_excel_medicion_con_sesion():
    client = get_client()
    login_admin(client)
    mid = _first_medicion_id(client)
    r = client.get(f"/api/mediciones/{mid}/excel")
    assert r.status_code == 200, r.text[:400]
    assert r.content[:2] == b"PK"
    print(" test_excel_medicion_con_sesion PASSED")


if __name__ == "__main__":
    test_html_imprimible_sin_sesion_es_401()
    test_html_imprimible_con_sesion_es_html()
    test_excel_medicion_con_sesion()
    print("ALL INFORME DOC TESTS PASSED")
