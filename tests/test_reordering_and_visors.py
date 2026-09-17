from __future__ import annotations

import io
from pathlib import Path
import cv2
import fitz
import numpy as np
import os
import requests

from src.bateria.classify import classify_page, extract_footer_page_number
from src.bateria.ingest import pdf_to_images
from src.bateria.pipeline import generate_ordered_pdf, process_pdf

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8001")


def test_classify_all_5_booklets_24_pages():
    """Valida que cada uno de los 5 cuadernillos de prueba detecte determinísticamente sus 24 páginas."""
    pdf_paths = sorted(Path("baterias de prueba").glob("*.pdf"))
    assert len(pdf_paths) == 5, f"Esperados 5 PDFs en 'baterias de prueba', encontrados {len(pdf_paths)}"

    for p in pdf_paths:
        imgs = pdf_to_images(p)
        assert len(imgs) == 24, f"{p.name} tiene {len(imgs)} páginas en vez de 24"

        detected_pages = set()
        for idx, im in enumerate(imgs, 1):
            info = classify_page(im)
            page_no = info.get("printed_page")
            if page_no and 1 <= page_no <= 24:
                detected_pages.add(page_no)

        print(f"Booklet {p.name}: {len(detected_pages)}/24 páginas identificadas")
        assert len(detected_pages) == 24, f"Faltan páginas en {p.name}: {set(range(1, 25)) - detected_pages}"

    print(" test_classify_all_5_booklets_24_pages PASSED (120/120 páginas verificadas)")


def test_physical_pdf_reordering():
    """Valida que la función generate_ordered_pdf ensamble un PDF de 24 páginas con pie de página 1..24."""
    p = Path("baterias de prueba/orlando20260912_13042032.pdf")
    res = process_pdf(p, out_dir=Path("out"))
    ord_name = res.get("pdf_ordenado")
    assert ord_name, "No se generó el nombre de pdf_ordenado"

    ord_path = Path("out/casos") / ord_name
    assert ord_path.exists(), f"El archivo {ord_path} no fue creado en disco"

    doc = fitz.open(ord_path)
    assert len(doc) == 24, f"Esperadas 24 páginas en PDF reordenado, hay {len(doc)}"

    for p_num in range(1, 25):
        page = doc[p_num - 1]
        pix = page.get_pixmap(dpi=150)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        foot = extract_footer_page_number(img)
        if foot is not None:
            assert foot == p_num, f"Página física {p_num} tiene pie {foot}"

    print(" test_physical_pdf_reordering PASSED")


def test_web_endpoints_reordered_visor():
    """Valida que los endpoints web sirvan la página física correcta y permitan descargar el PDF ordenado."""
    # Verificar salud
    r_health = requests.get(f"{BASE_URL}/health")
    assert r_health.status_code == 200, f"Error en health: {r_health.text}"

    # Obtener un caso
    r_casos = requests.get(f"{BASE_URL}/api/casos")
    assert r_casos.status_code == 200, f"Error en /api/casos: {r_casos.text}"
    data = r_casos.json()
    casos = data.get("casos", [])
    assert len(casos) > 0, "No hay casos en la API"

    # Buscar caso de 13042032 o el primero disponible
    target_caso = next((c for c in casos if "13042032" in c.get("archivo", "")), casos[0])
    cid = target_caso["caso_id"]

    # 1. Probar que /api/casos/{cid}/pagina/13 devuelve página física 13
    r_p13 = requests.get(f"{BASE_URL}/api/casos/{cid}/pagina/13")
    assert r_p13.status_code == 200
    assert r_p13.headers.get("content-type") == "image/jpeg"

    # Decodificar imagen y verificar número de pie
    nparr = np.frombuffer(r_p13.content, np.uint8)
    im13 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    f13 = extract_footer_page_number(im13)
    assert f13 == 13, f"Se esperaba pie de página 13 en el visor para pág 13, se obtuvo {f13}"

    # 2. Probar que /api/casos/{cid}/pagina/24 devuelve página física 24
    r_p24 = requests.get(f"{BASE_URL}/api/casos/{cid}/pagina/24")
    assert r_p24.status_code == 200
    nparr24 = np.frombuffer(r_p24.content, np.uint8)
    im24 = cv2.imdecode(nparr24, cv2.IMREAD_COLOR)
    f24 = extract_footer_page_number(im24)
    assert f24 == 24, f"Se esperaba pie de página 24 en el visor para pág 24, se obtuvo {f24}"

    # 3. Probar descarga de PDF ordenado
    r_ord = requests.get(f"{BASE_URL}/api/casos/{cid}/pdf-ordenado")
    assert r_ord.status_code == 200
    assert r_ord.headers.get("content-type") == "application/pdf"
    doc_dl = fitz.open(stream=r_ord.content, filetype="pdf")
    assert len(doc_dl) == 24, f"El PDF descargado tiene {len(doc_dl)} páginas en vez de 24"

    print(" test_web_endpoints_reordered_visor PASSED")


if __name__ == "__main__":
    test_classify_all_5_booklets_24_pages()
    test_physical_pdf_reordering()
    test_web_endpoints_reordered_visor()
    print("ALL VERIFICATION TESTS COMPLETED WITH 100% SUCCESS!")
