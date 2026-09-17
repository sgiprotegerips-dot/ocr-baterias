"""Tests del módulo de etiquetas QR y nómina de ficha sociodemográfica."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from src.bateria.qr_codec import (
    FICHA_FIELDS,
    decode_payload,
    encode_payload,
    identity_from_ficha,
    label_display_name,
)


SAMPLE = {
    "forma": "A",
    "fecha_aplicacion": "2026-08-20",
    "cedula": "1032381023",
    "nombre": "MAYRA ALEJANDRA GOMEZ PARRA",
    "sexo": "F",
    "fecha_nacimiento": "1987-03-12",
    "anio_nacimiento": "1987",
    "edad": "39",
    "estado_civil": "CASADA",
    "nivel_estudios": "TECN-COMPL",
    "cargo_ocupacion": "REGENTE DE FARMACIA",
    "residencia": "GRANADA",
    "departamento": "META",
    "estrato": "3",
    "tipo_vivienda": "ARRIENDO",
    "n_dependientes": "1",
    "lugar_trabajo": "GRANADA",
    "dpto_trabajo": "META",
    "tiempo_empresa": "<1",
    "cargo": "DIRECTOR TECNICO",
    "tipo_cargo": "JEFATURA TIENE PERSONAL A CARGO",
    "tiempo_cargo": "<1",
    "area": "ADMINISTRATIVO",
    "tipo_contrato": "T<1",
    "horas_diarias": "8",
    "tipo_salario": "F",
}


def test_ficha_fields_cover_excel_base():
    required = {
        "forma",
        "fecha_aplicacion",
        "cedula",
        "nombre",
        "sexo",
        "fecha_nacimiento",
        "anio_nacimiento",
        "edad",
        "estado_civil",
        "nivel_estudios",
        "cargo_ocupacion",
        "residencia",
        "departamento",
        "estrato",
        "tipo_vivienda",
        "n_dependientes",
        "lugar_trabajo",
        "dpto_trabajo",
        "tiempo_empresa",
        "cargo",
        "tipo_cargo",
        "tiempo_cargo",
        "area",
        "tipo_contrato",
        "horas_diarias",
        "tipo_salario",
    }
    assert required.issubset(set(FICHA_FIELDS))


def test_encode_decode_roundtrip_includes_nacimiento():
    payload = encode_payload(SAMPLE)
    assert payload.startswith("BRP1|")
    decoded = decode_payload(payload)
    assert decoded is not None
    assert decoded["cedula"] == "1032381023"
    assert decoded["nombre"] == "MAYRA ALEJANDRA GOMEZ PARRA"
    assert decoded["fecha_nacimiento"] == "1987-03-12"
    assert decoded["anio_nacimiento"] == "1987"
    assert decoded["sexo"] == "F"
    assert decoded["forma"] == "A"
    assert decoded["cargo"] == "DIRECTOR TECNICO"
    assert decoded["area"] == "ADMINISTRATIVO"
    assert decoded["estado_civil"] == "CASADA"
    assert decoded["estrato"] == "3"


def test_decode_rejects_foreign_qr():
    assert decode_payload("https://example.com/foo") is None
    assert decode_payload("") is None
    assert decode_payload("BRP2|nope") is None


def test_pipes_in_values_do_not_break_payload():
    data = dict(SAMPLE)
    data["nombre"] = "GOMEZ | PARRA"
    decoded = decode_payload(encode_payload(data))
    assert decoded is not None
    assert "|" not in decoded["nombre"]
    assert "GOMEZ" in decoded["nombre"]


def test_identity_from_ficha_maps_ocr_fields():
    ident = identity_from_ficha(SAMPLE)
    assert ident["id_documento"] == "1032381023"
    assert ident["nombre"] == "MAYRA ALEJANDRA GOMEZ PARRA"
    assert ident["cargo"] == "DIRECTOR TECNICO"
    assert ident["dependencia"] == "ADMINISTRATIVO"
    assert ident["fecha"] == "2026-08-20"
    assert ident["fuente"] == "qr"
    assert ident["ficha"]["fecha_nacimiento"] == "1987-03-12"
    assert ident["ficha"]["anio_nacimiento"] == "1987"


def test_label_display_name_uses_apellidos():
    assert "GOMEZ" in label_display_name("MAYRA ALEJANDRA GOMEZ PARRA")


def test_parse_ficha_excel_two_formas():
    from openpyxl import Workbook

    from src.bateria.nomina import parse_ficha_excel

    wb = Workbook()
    ws = wb.active
    ws.title = "FICHA DATOS GENERALES"
    headers = [
        "No.",
        "FECHA APLICACIÓN",
        "CEDULA",
        "NOMBRE COMPLETO",
        "SEXO",
        "AÑO NACIMIENTO",
        "EDAD",
        "ESTADO CIVIL",
        "NIVEL DE ESTUDIOS",
        "CARGO U OCUPACION",
        "RESID. ACTUAL",
        "DEPARTAMENTO",
        "ESTRATO",
        "TIPO VIVIENDA",
        "No. PERSONAS QUE DEPENDEN DE UD.",
        "LUGAR DE TRABAJO ACTUAL",
        "DPTO. TRABAJO",
        "TIEMPO EN LA EMPRESA EN AÑOS",
        "CARGO ACTUAL",
        "TIPO DE CARGO",
        "TIEMPO EN CARGO ACTUAL EN AÑOS",
        "AREA",
        "TIPO CONTRATO",
        "HORAS DIARIAS DE TRABAJO",
        "TIPO SALARIO",
    ]
    ws.append(["FORMA A"])
    ws.append(headers)
    ws.append(
        [
            1,
            datetime(2026, 8, 20),
            1032381023,
            "MAYRA ALEJANDRA GOMEZ PARRA",
            "F",
            1987,
            39,
            "CASADA",
            "TECN-COMPL",
            "REGENTE DE FARMACIA",
            "GRANADA",
            "META",
            3,
            "ARRIENDO",
            1,
            "GRANADA",
            "META",
            "<1",
            "DIRECTOR TECNICO",
            "JEFATURA",
            "<1",
            "ADMINISTRATIVO",
            "T<1",
            8,
            "F",
        ]
    )
    ws.append(["FORMA B"])
    ws.append(headers)
    ws.append(
        [
            1,
            datetime(2026, 8, 20),
            1107529591,
            "PAULA VASQUEZ",
            "F",
            1999,
            27,
            "SOLTERA",
            "TECN-COMPL",
            "REGENTE DE FARMACIA",
            "GRANADA",
            "META",
            2,
            "FAMILIAR",
            1,
            "GRANADA",
            "META",
            "<1",
            "AUXILIAR DE FARMACIA",
            "AUXILIAR",
            "<1",
            "AUXILIAR DE FARMACIA",
            "T<1",
            7,
            "F",
        ]
    )
    tmp = Path("/tmp/ficha_qr_test.xlsx")
    wb.save(tmp)

    rows = parse_ficha_excel(tmp)
    assert len(rows) == 2
    assert rows[0]["forma"] == "A"
    assert rows[0]["cedula"] == "1032381023"
    assert rows[0]["anio_nacimiento"] == "1987"
    assert rows[0]["fecha_nacimiento"] == ""
    assert rows[1]["forma"] == "B"
    assert rows[1]["cedula"] == "1107529591"
    assert rows[1]["nombre"] == "PAULA VASQUEZ"


def test_parse_ficha_excel_ignores_instruction_row_with_cedula_nombre():
    from openpyxl import Workbook

    from src.bateria.nomina import parse_ficha_excel

    wb = Workbook()
    ws = wb.active
    ws.title = "FICHA DATOS GENERALES"
    ws.append(
        [
            "Obligatorios para importar: CEDULA + NOMBRE COMPLETO. Pegue aquí la nómina."
        ]
    )
    ws.append(["FORMA A"])
    ws.append(["No.", "FECHA APLICACIÓN", "CEDULA", "NOMBRE COMPLETO", "SEXO", "TIPO SALARIO"])
    ws.append([1, "2026-09-17", 1010101010, "ANA PRUEBA", "F", "F"])
    tmp = Path("/tmp/ficha_instrucciones.xlsx")
    wb.save(tmp)
    rows = parse_ficha_excel(tmp)
    assert len(rows) == 1
    assert rows[0]["cedula"] == "1010101010"
    assert rows[0]["sexo"] == "F"
    assert rows[0]["tipo_salario"] == "F"


def test_shipped_plantilla_etiquetas_has_official_25_columns():
    from src.bateria.nomina import HEADER_MAP, _cell_str, _norm_header, parse_ficha_excel

    path = Path("app/static/plantillas/importador_etiquetas_qr.xlsx")
    assert path.is_file()
    rows = parse_ficha_excel(path)
    assert len(rows) >= 2
    by_cc = {r["cedula"]: r for r in rows}
    a = by_cc["1032381023"]
    b = by_cc["1107529591"]
    assert a["forma"] == "A"
    assert a["tipo_salario"] == "F"
    assert a["tipo_cargo"]
    assert a["fecha_aplicacion"]
    assert a["sexo"] == "F"
    assert b["forma"] == "B"
    official = [
        "FECHA APLICACIÓN",
        "CEDULA",
        "NOMBRE COMPLETO",
        "SEXO",
        "AÑO NACIMIENTO",
        "EDAD",
        "ESTADO CIVIL",
        "NIVEL DE ESTUDIOS",
        "CARGO U OCUPACION",
        "RESID. ACTUAL",
        "DEPARTAMENTO",
        "ESTRATO",
        "TIPO VIVIENDA",
        "No. PERSONAS QUE DEPENDEN DE UD.",
        "LUGAR DE TRABAJO ACTUAL",
        "DPTO. TRABAJO",
        "TIEMPO EN LA EMPRESA EN AÑOS",
        "CARGO ACTUAL",
        "TIPO DE CARGO",
        "TIEMPO EN CARGO ACTUAL EN AÑOS",
        "AREA",
        "TIPO CONTRATO",
        "HORAS DIARIAS DE TRABAJO",
        "TIPO SALARIO",
    ]
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True)
    ws = wb["FICHA DATOS GENERALES"]
    header = None
    for row in ws.iter_rows(values_only=True):
        vals = [_cell_str(v) for v in row]
        if vals and vals[0] == "No." and "CEDULA" in vals:
            header = vals
            break
    assert header is not None
    for name in official:
        assert name in header, name
        assert HEADER_MAP.get(_norm_header(name)), name
    wb.close()


def test_detect_qr_only_on_page_1():
    import cv2

    from src.bateria.qr_detect import detect_identity_qr
    from src.bateria.qr_codec import render_qr_bgr

    payload = encode_payload(SAMPLE)
    qr_img = render_qr_bgr(payload, box_px=180)

    page1 = np.full((1400, 1000, 3), 255, dtype=np.uint8)
    h, w = qr_img.shape[:2]
    page1[40 : 40 + h, 40 : 40 + w] = qr_img

    page2 = np.full((1400, 1000, 3), 255, dtype=np.uint8)
    page2[40 : 40 + h, 40 : 40 + w] = qr_img

    classified = [
        {"target_page": 1, "img": page1, "info": {"kind": "consentimiento"}},
        {"target_page": 2, "img": page2, "info": {"kind": "ficha"}},
    ]
    hit = detect_identity_qr(classified)
    assert hit is not None
    assert hit["cedula"] == "1032381023"
    assert hit["fecha_nacimiento"] == "1987-03-12"

    only_page2 = [
        {"target_page": 2, "img": page2, "info": {"kind": "ficha"}},
    ]
    assert detect_identity_qr(only_page2) is None

    # sanity: OpenCV sí ve el QR en pág 2, pero el detector de identidad lo ignora
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(page2)
    assert data.startswith("BRP1|")


def test_print_html_declares_30x20mm_and_ficha_fields():
    from src.bateria.nomina import render_labels_html

    html = render_labels_html([SAMPLE])
    assert "30mm" in html
    assert "20mm" in html
    assert "1032381023" in html
    assert "FORMA A" in html
    assert "1987" in html


def test_import_real_mardo_ariari_excel_if_present():
    from src.bateria.nomina import parse_ficha_excel

    path = Path("/Users/orlansh/Downloads/TAB FINAL DROGUERIAS MARDO Y ARIARI (1).xlsx")
    if not path.exists():
        print(" skip test_import_real_mardo_ariari_excel_if_present (xlsx ausente)")
        return
    rows = parse_ficha_excel(path)
    assert len(rows) == 19
    formas = [r["forma"] for r in rows]
    assert formas.count("A") == 4
    assert formas.count("B") == 15
    assert {r["cedula"] for r in rows} == {
        "1032381023",
        "79372765",
        "21203410",
        "1120380618",
        "1107529591",
        "1141314413",
        "1120502943",
        "1127386331",
        "1120366378",
        "9432366",
        "1006697281",
        "40326627",
        "1121820547",
        "1120504351",
        "1006828189",
        "40422915",
        "40420370",
        "1120359136",
        "1006828045",
    }
    mayra = next(r for r in rows if r["cedula"] == "1032381023")
    assert mayra["anio_nacimiento"] == "1987"
    assert mayra["sexo"] == "F"


def test_api_manual_then_print_label():
    from tests.test_pipeline_and_web import get_client

    client = get_client()
    from tests.auth_helpers import create_and_login_psicologa

    create_and_login_psicologa(client)
    meds = client.get("/api/mediciones")
    assert meds.status_code == 200
    med_list = meds.json()
    assert med_list, "Se requiere al menos una medición sembrada"
    mid = med_list[0]["id"]

    payload = dict(SAMPLE)
    payload["cedula"] = "1099000111"
    payload["nombre"] = "PRUEBA MANUAL QR"
    r = client.post(f"/api/mediciones/{mid}/nomina", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cedula"] == "1099000111"
    assert body["ficha"]["fecha_nacimiento"] == "1987-03-12"
    assert body["ficha"]["anio_nacimiento"] == "1987"

    listed = client.get(f"/api/mediciones/{mid}/nomina")
    assert listed.status_code == 200
    ceds = [t["cedula"] for t in listed.json()["trabajadores"]]
    assert "1099000111" in ceds

    html = client.get(f"/api/mediciones/{mid}/nomina/1099000111/etiqueta.html")
    assert html.status_code == 200
    assert "30mm" in html.text
    assert "20mm" in html.text
    assert "1099000111" in html.text
    assert "<svg" in html.text.lower()


def test_api_import_ficha_excel():
    from datetime import datetime as dt

    from openpyxl import Workbook

    from tests.test_pipeline_and_web import get_client

    client = get_client()
    from tests.auth_helpers import create_and_login_psicologa

    create_and_login_psicologa(client)
    meds = client.get("/api/mediciones").json()
    mid = meds[0]["id"]

    wb = Workbook()
    ws = wb.active
    ws.title = "FICHA DATOS GENERALES"
    headers = [
        "No.",
        "FECHA APLICACIÓN",
        "CEDULA",
        "NOMBRE COMPLETO",
        "SEXO",
        "AÑO NACIMIENTO",
        "EDAD",
        "ESTADO CIVIL",
        "NIVEL DE ESTUDIOS",
        "CARGO U OCUPACION",
        "RESID. ACTUAL",
        "DEPARTAMENTO",
        "ESTRATO",
        "TIPO VIVIENDA",
        "No. PERSONAS QUE DEPENDEN DE UD.",
        "LUGAR DE TRABAJO ACTUAL",
        "DPTO. TRABAJO",
        "TIEMPO EN LA EMPRESA EN AÑOS",
        "CARGO ACTUAL",
        "TIPO DE CARGO",
        "TIEMPO EN CARGO ACTUAL EN AÑOS",
        "AREA",
        "TIPO CONTRATO",
        "HORAS DIARIAS DE TRABAJO",
        "TIPO SALARIO",
    ]
    ws.append(["FORMA A"])
    ws.append(headers)
    ws.append(
        [
            1,
            dt(2026, 8, 20),
            1999888777,
            "IMPORTADO QR TEST",
            "M",
            1990,
            36,
            "SOLTERO",
            "PROF",
            "AUXILIAR",
            "GRANADA",
            "META",
            2,
            "PROPIA",
            0,
            "GRANADA",
            "META",
            "1",
            "AUXILIAR",
            "AUXILIAR",
            "1",
            "OPERATIVO",
            "TI",
            8,
            "F",
        ]
    )
    tmp = Path("/tmp/ficha_import_api.xlsx")
    wb.save(tmp)
    with tmp.open("rb") as fh:
        r = client.post(
            f"/api/mediciones/{mid}/nomina/import",
            files={"file": ("ficha.xlsx", fh, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert r.status_code == 200, r.text
    assert r.json()["imported"] >= 1
    listed = client.get(f"/api/mediciones/{mid}/nomina").json()
    assert any(t["cedula"] == "1999888777" for t in listed["trabajadores"])


if __name__ == "__main__":
    test_ficha_fields_cover_excel_base()
    print(" test_ficha_fields_cover_excel_base PASSED")
    test_encode_decode_roundtrip_includes_nacimiento()
    print(" test_encode_decode_roundtrip_includes_nacimiento PASSED")
    test_decode_rejects_foreign_qr()
    print(" test_decode_rejects_foreign_qr PASSED")
    test_pipes_in_values_do_not_break_payload()
    print(" test_pipes_in_values_do_not_break_payload PASSED")
    test_identity_from_ficha_maps_ocr_fields()
    print(" test_identity_from_ficha_maps_ocr_fields PASSED")
    test_label_display_name_uses_apellidos()
    print(" test_label_display_name_uses_apellidos PASSED")
    test_parse_ficha_excel_two_formas()
    print(" test_parse_ficha_excel_two_formas PASSED")
    test_parse_ficha_excel_ignores_instruction_row_with_cedula_nombre()
    print(" test_parse_ficha_excel_ignores_instruction_row_with_cedula_nombre PASSED")
    test_shipped_plantilla_etiquetas_has_official_25_columns()
    print(" test_shipped_plantilla_etiquetas_has_official_25_columns PASSED")
    test_detect_qr_only_on_page_1()
    print(" test_detect_qr_only_on_page_1 PASSED")
    test_print_html_declares_30x20mm_and_ficha_fields()
    print(" test_print_html_declares_30x20mm_and_ficha_fields PASSED")
    test_import_real_mardo_ariari_excel_if_present()
    print(" test_import_real_mardo_ariari_excel_if_present PASSED")
    test_api_manual_then_print_label()
    print(" test_api_manual_then_print_label PASSED")
    test_api_import_ficha_excel()
    print(" test_api_import_ficha_excel PASSED")
    print("ALL QR/NOMINA TESTS PASSED")
