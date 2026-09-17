"""Pruebas automáticas completas del pipeline OMR/OCR y la API Web."""

from pathlib import Path

from app.web import app
from src.bateria.classify import classify_page, get_expected_items
from src.bateria.ocr_engine import normalize_page_orientation, ocr_digits_only
from src.bateria.scoring import score_persona


def get_client():
    try:
        from fastapi.testclient import TestClient
        return TestClient(app)
    except Exception:
        import requests
        class RequestsClient:
            def __init__(self, base="http://localhost:8000"):
                self.base = base
                self.s = requests.Session()
            def get(self, path, **kwargs):
                return self.s.get(f"{self.base}{path}", **kwargs)
            def post(self, path, **kwargs):
                return self.s.post(f"{self.base}{path}", **kwargs)
        return RequestsClient()


def test_scoring_villalobos():
    # Test caso perfecto Forma A
    intra = {i: 0 for i in range(1, 124)}
    extra = {i: 0 for i in range(1, 32)}
    estres = {i: 0 for i in range(1, 32)}
    sc = score_persona("A", intra, extra, estres)
    assert sc["intra"]["total"]["n"] == 123
    assert sc["extra"]["total"]["n"] == 31
    assert sc["estres"]["total"]["n"] == 31
    assert sc["intra"]["total"]["transformado"] is not None
    print(" test_scoring_villalobos PASSED")


def test_expected_items():
    assert len(get_expected_items(8, "A")) == 12
    assert len(get_expected_items(24, "A")) == 31
    assert len(get_expected_items(20, "A")) == 13
    print(" test_expected_items PASSED")


def test_web_endpoints():
    client = get_client()

    # 1. Home
    r = client.get("/")
    assert r.status_code == 200
    assert "Sala de Lectura Masiva" in r.text

    from tests.auth_helpers import create_and_login_psicologa

    create_and_login_psicologa(client)

    # 2. Demo Case
    r_demo = client.post("/api/demo")
    assert r_demo.status_code == 200
    demo = r_demo.json()
    assert demo["caso_id"]

    # 3. Casos List
    r_list = client.get("/api/casos")
    assert r_list.status_code == 200
    data = r_list.json()
    assert "casos" in data
    assert "stats" in data
    assert data["stats"]["total"] >= 1

    # 4. Single Case
    cid = demo["caso_id"]
    r_single = client.get(f"/api/casos/{cid}")
    assert r_single.status_code == 200
    assert r_single.json()["caso_id"] == cid

    # 5. Save Datos
    r_datos = client.post(
        f"/api/casos/{cid}/datos",
        json={
            "nombre": "Elena Maria Rios",
            "cargo": "Supervisora de Operaciones",
            "fecha": "12/09/2026",
            "dependencia": "Operaciones",
            "id_documento": "52918234",
            "psicologa": "Dra. Patricia Silva - SST 19482",
        },
    )
    assert r_datos.status_code == 200
    updated = r_datos.json()
    assert updated["identidad"]["nombre"] == "Elena Maria Rios"

    # 6. Decide Doble Chuleado
    r_decide = client.post(
        f"/api/casos/{cid}/decidir",
        json={
            "amb_id": "I013",
            "choice": 0,
            "psicologa": "Dra. Patricia Silva",
        },
    )
    assert r_decide.status_code == 200
    decided = r_decide.json()
    amb = next(a for a in decided["ambiguos"] if a["id"] == "I013")
    assert amb["decision"] == 0

    # 7. Excel
    r_excel = client.get("/api/excel")
    assert r_excel.status_code == 200
    assert len(r_excel.content) > 1000

    # 8. Health and OCR Engines
    r_health = client.get("/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["status"] == "healthy"
    assert "rapid_ocr_onnx" in h_data["engines"]
    assert "workers" in h_data

    r_engines = client.get("/api/ocr/engines")
    assert r_engines.status_code == 200
    eng_data = r_engines.json()
    assert "active_engine" in eng_data

    # 9. OCR Benchmark
    r_bench = client.get("/api/ocr/benchmark")
    assert r_bench.status_code == 200
    bench_data = r_bench.json()
    assert isinstance(bench_data, dict)

    print(" test_web_endpoints PASSED")


def test_zip_upload():
    import io
    import zipfile

    client = get_client()
    client.post(
        "/api/auth/login",
        json={"email": "operador@proteger.com.co", "password": "Operador2026!"},
    )

    # Crear ZIP con un PDF de prueba en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Usar un PDF real existente de baterias de prueba si existe
        sample_pdf = Path("orlando20260912_11544668.pdf")
        if not sample_pdf.exists():
            sample_pdf = Path("data/uploads/orlando20260912_11544668.pdf")
        if sample_pdf.exists():
            zf.writestr("cuadernillo_test.pdf", sample_pdf.read_bytes())
        else:
            zf.writestr("test.pdf", b"%PDF-1.4 test")

    zip_buffer.seek(0)
    files = [("files", ("lote_test.zip", zip_buffer.getvalue(), "application/zip"))]

    r_up = client.post("/api/upload", files=files)
    assert r_up.status_code == 200
    res = r_up.json()
    assert "job_id" in res
    assert res["total"] >= 1
    print(" test_zip_upload PASSED")


if __name__ == "__main__":
    test_scoring_villalobos()
    test_expected_items()
    test_web_endpoints()
    test_zip_upload()
    print("ALL TESTS PASSED SUCCESSFULLY!")

