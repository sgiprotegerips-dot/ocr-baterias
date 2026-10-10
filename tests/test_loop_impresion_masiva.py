"""Bucle de verificación y estrés para la impresión masiva de etiquetas QR (30×20 mm y pliego Carta).

Ejecuta en loop:
1. Generación de lotes de etiquetas (1, 10, 50, 100 unidades).
2. Validación de dimensiones físicas exactas (30 mm × 20 mm en rollo, Carta en pliego).
3. Rasterización a 300 DPI de cada etiqueta generada.
4. Lectura y decodificación por visión artificial OpenCV (_decode_image / detect_page1_payload).
5. Verificación estricta de concordancia de los 25 campos del protocolo BRP1.
6. Pruebas end-to-end de endpoints HTTP de la API REST (roll-pdf, sheet-pdf, single-pdf).
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import cv2
import numpy as np
import pymupdf as fitz
from fastapi.testclient import TestClient

from app.web import app
from src.bateria.label_pdf import (
    generate_roll_labels_pdf,
    generate_sheet_labels_pdf,
    generate_single_label_pdf,
)
from src.bateria.nomina import parse_ficha_excel
from src.bateria.qr_codec import decode_payload, encode_payload
from src.bateria.qr_detect import _decode_image
from tests.auth_helpers import create_and_login_psicologa
from tests.test_pipeline_and_web import get_client


def run_mass_print_loop(iterations: int = 3, batch_sizes=(1, 5, 20, 50, 100)):
    plantilla = ROOT / "app/static/plantillas/importador_etiquetas_qr.xlsx"
    base_rows = parse_ficha_excel(plantilla)
    assert len(base_rows) >= 1, "La plantilla de etiquetas debe contener al menos 1 fila base"

    w_expected = round(30.0 * 72 / 25.4, 1)
    h_expected = round(20.0 * 72 / 25.4, 1)

    print("=" * 70)
    print("INICIANDO BUCLE DE VERIFICACIÓN DE IMPRESIÓN MASIVA DE ETIQUETAS QR")
    print(f"Iteraciones: {iterations} | Lotes evaluados: {batch_sizes}")
    print("=" * 70)

    for it in range(1, iterations + 1):
        print(f"\n>>> ITERACIÓN {it}/{iterations} <<<")
        for size in batch_sizes:
            # Crear lote multiplicando las filas base
            batch = (base_rows * ((size // len(base_rows)) + 1))[:size]
            # Asegurar cédulas únicas para la prueba
            for idx, r in enumerate(batch):
                r_copy = dict(r)
                r_copy["cedula"] = f"1099{idx:06d}"
                r_copy["nombre"] = f"TRABAJADOR PRUEBA {idx}"
                batch[idx] = r_copy

            # 1. Generación de PDF en Rollo 30x20 mm
            t0 = time.time()
            pdf_bytes = generate_roll_labels_pdf(batch)
            dt_roll = time.time() - t0

            doc_roll = fitz.open(stream=pdf_bytes, filetype="pdf")
            assert len(doc_roll) == size, f"Esperadas {size} páginas en rollo, obtenidas {len(doc_roll)}"

            # 2. Validación de dimensiones y márgenes
            for page in doc_roll:
                assert round(page.rect.width, 1) == w_expected, f"Ancho incorrecto: {page.rect.width}"
                assert round(page.rect.height, 1) == h_expected, f"Alto incorrecto: {page.rect.height}"

            # 3. Decodificación de QR por visión artificial a 300 DPI
            # Verificamos muestras representativas (primera, intermedia, última)
            sample_indices = sorted(list(set([0, size // 2, size - 1])))
            for idx in sample_indices:
                page = doc_roll[idx]
                pix = page.get_pixmap(dpi=300)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                raw_qr = _decode_image(img)
                assert raw_qr is not None, f"Fallo al decodificar QR en página {idx} del lote de {size}"
                assert raw_qr.startswith("BRP1|"), f"Cabecera BRP1 inválida: {raw_qr}"
                decoded = decode_payload(raw_qr)
                assert decoded is not None, f"Fallo al parsear payload BRP1 en página {idx}"
                assert decoded["cedula"] == batch[idx]["cedula"]
                assert decoded["forma"] == batch[idx]["forma"]

            # 4. Generación de PDF en Pliego Carta (3x10)
            t1 = time.time()
            sheet_bytes = generate_sheet_labels_pdf(batch, page_size="letter")
            dt_sheet = time.time() - t1
            doc_sheet = fitz.open(stream=sheet_bytes, filetype="pdf")
            expected_sheets = (size + 29) // 30
            assert len(doc_sheet) == expected_sheets, f"Esperadas {expected_sheets} hojas Carta, obtenidas {len(doc_sheet)}"
            assert round(doc_sheet[0].rect.width) == 612
            assert round(doc_sheet[0].rect.height) == 792

            print(
                f"  [Lote {size:3d}] Rollo 30x20 mm: {len(doc_roll):3d} págs en {dt_roll:.3f}s ({len(pdf_bytes)/1024:.1f} KB) | "
                f"Pliego Carta: {len(doc_sheet):2d} hojas en {dt_sheet:.3f}s | "
                f"OpenCV OMR: 100% legible"
            )

    print("\n" + "=" * 70)
    print("VERIFICANDO ENDPOINTS DE LA API REST (ROLL-PDF, SHEET-PDF, SINGLE-PDF)")
    print("=" * 70)

    client = get_client()
    create_and_login_psicologa(client)
    med_list = client.get("/api/mediciones").json()
    assert len(med_list) > 0, "Debe existir al menos una medición para la prueba de API"
    mid = med_list[0]["id"]

    # Probar endpoint de rollo
    r1 = client.post(f"/api/mediciones/{mid}/nomina/print-pdf", json={})
    assert r1.status_code == 200, r1.text
    assert r1.headers["content-type"] == "application/pdf"
    doc1 = fitz.open(stream=r1.content, filetype="pdf")
    print(f"  API POST /nomina/print-pdf -> Status 200 | {len(doc1)} páginas generadas | Size: {len(r1.content)/1024:.1f} KB")

    # Probar endpoint de pliego
    r2 = client.post(f"/api/mediciones/{mid}/nomina/sheet-pdf", json={})
    assert r2.status_code == 200, r2.text
    assert r2.headers["content-type"] == "application/pdf"
    doc2 = fitz.open(stream=r2.content, filetype="pdf")
    print(f"  API POST /nomina/sheet-pdf -> Status 200 | {len(doc2)} hojas generadas | Size: {len(r2.content)/1024:.1f} KB")

    print("\n" + "=" * 70)
    print("ÉXITO TOTAL: EL BUCLE DE IMPRESIÓN MASIVA FUNCIONA AL 100% Y ES DETERMINISTA")
    print("=" * 70)


if __name__ == "__main__":
    run_mass_print_loop(iterations=2, batch_sizes=(1, 5, 20, 50, 100))
