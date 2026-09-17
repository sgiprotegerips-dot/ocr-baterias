"""Extracción robusta de datos demográficos, Cédula/ID y campos de Consentimiento Informado.

Aplica OCR multimodelo (Apple Vision + RapidOCR + Tesseract) con patrones regex tolerantes a
manuscritos y errores comunes de escáner.
"""

from __future__ import annotations

import re
from typing import Optional

import cv2
import numpy as np

from .ocr_engine import ocr_digits_only, ocr_full_text, ocr_printed_text


def _clean_text(s: str) -> str:
    """Limpia cadenas extraídas eliminando signos de puntuación iniciales y espacios sobrantes."""
    s = re.sub(r"\s+", " ", s or "").strip(" :-_.,;|")
    s = re.sub(r"(?i)^o\s*dependencia\s*[:\-.]?\s*", "", s).strip(" :-_.,;|")
    # Eliminar palabras cliché que a veces se pegan del formato
    for noise in [
        "en forma voluntaria",
        "mediante la cual",
        "de manera voluntaria",
        "consiente a que",
        "declaro que",
        "fui informado",
    ]:
        s = re.sub(rf"(?i)\s*{re.escape(noise)}.*", "", s).strip()
    return s if len(s) >= 2 else ""


def extract_cover_date(img: np.ndarray) -> str:
    """Extrae la fecha de aplicación desde las portadas de cuestionarios (pág 6, 18, 23)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = gray.shape
    roi = gray[: int(h * 0.55), :]
    text = ocr_full_text(roi)
    m = re.search(
        r"(?:FECHA(?:\s+DE\s+APLICACI[OÓ]N)?)\s*[:\-.]?\s*([0-9]{1,2}\s*[\/\-.]\s*[0-9]{1,2}\s*[\/\-.]\s*[0-9]{2,4})",
        text,
        re.I,
    )
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m2 = re.search(r"\b([0-3]?[0-9]\s*[\/\-]\s*[0-1]?[0-9]\s*[\/\-]\s*(?:20\d\d|\d{2}))\b", text)
    if m2:
        return re.sub(r"\s+", "", m2.group(1))
    return ""


def extract_id_and_name(img: np.ndarray) -> dict:
    """Extrae el número de cédula/ID desde el recuadro 'Número de identificación del respondiente (ID)'."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = gray.shape

    # La casilla de ID en las portadas y fichas siempre se ubica en el 45% superior
    roi_gray = gray[: int(h * 0.45), :]
    digits = None

    # 1. Búsqueda semántica ultrarrápida con OCR de texto impreso
    printed_text = ocr_printed_text(roi_gray)
    lines = [l.strip() for l in printed_text.split("\n") if l.strip()]

    has_anchor = False
    for i, line in enumerate(lines):
        line_clean = line.lower()
        if any(k in line_clean for k in ["(id)", "(1d)", "(d)", "identificación", "identificacion", "respondiente"]):
            has_anchor = True
            found = re.findall(r"\b\d{6,11}\b", line)
            if found:
                digits = found[0]
                break
            if i + 1 < len(lines):
                next_found = re.findall(r"\b\d{6,11}\b", lines[i + 1])
                if next_found:
                    digits = next_found[0]
                    break

    # Si la página no contiene ningún encabezado de identificación, abortar inmediatamente (0.1s)
    if not has_anchor:
        return {"id_documento": None, "ocr_encabezado": None}

    # 2. Localización por contorno rectangular de la casilla ID si aún no se tiene
    if not digits:
        bw = cv2.adaptiveThreshold(
            ~roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2
        )
        contours, _ = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for c in contours:
            x, y, bw_c, bh_c = cv2.boundingRect(c)
            aspect = bw_c / float(bh_c)
            # Casilla de cédula: relación aspecto 2.0 a 8.5
            if 1.8 <= aspect <= 8.5 and w * 0.10 <= bw_c <= w * 0.55 and 20 <= bh_c <= 120:
                candidates.append((x, y, bw_c, bh_c))

        for bx, by, bw_c, bh_c in sorted(candidates, key=lambda b: b[1]):
            pad_x = max(3, int(bw_c * 0.05))
            pad_y = max(3, int(bh_c * 0.08))
            crop = roi_gray[by + pad_y : by + bh_c - pad_y, bx + pad_x : bx + bw_c - pad_x]
            if crop.size > 0:
                c_num = ocr_digits_only(crop)
                if c_num and 6 <= len(c_num) <= 11:
                    digits = c_num
                    break

    return {
        "id_documento": digits,
        "ocr_encabezado": "ID detectado" if digits else None,
    }


def extract_consentimiento(img: np.ndarray) -> dict:
    """Extrae Fecha, Cargo, Área/Dependencia, Nombre y Cédula en el Consentimiento Informado (Pág 1)."""
    text = ocr_full_text(img)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    fecha = ""
    cargo = ""
    dep = ""
    nombre = ""
    cc = None

    # 1. Búsqueda de Fecha
    m_f = re.search(r"FECHA\s*[:\-.]?\s*([0-9]{1,2}\s*[\/\-.]\s*[0-9]{1,2}\s*[\/\-.]\s*[0-9]{2,4})", text, re.I)
    if m_f:
        fecha = re.sub(r"\s+", "", m_f.group(1))

    # 2. Búsqueda de Cédula en Consentimiento:
    # "Cc: 1074415717", "Ce: 33376569", "C.C. 80421154"
    m_cc = re.search(r"\b(?:C[CcEe]\.?|C\.C\.?|CEDULA|CÉDULA)\s*[:\-.]?\s*(\d{6,11})\b", text, re.I)
    if m_cc:
        cc = m_cc.group(1)

    # 3. Búsqueda de Cargo
    # "CARGO: DIR. CONTABLE", "CARCO: Oficios generales"
    m_cargo = re.search(r"\b(?:CARGO|CARCO|CARG0|PUESTO)\s*[:\-.]?\s*([^\n\r]{3,50})", text, re.I)
    if m_cargo:
        cand_c = _clean_text(m_cargo.group(1))
        if not any(k in cand_c.lower() for k in ["area", "dependencia", "yo ", "voluntaria"]):
            cargo = cand_c

    # 4. Búsqueda de Área o Dependencia
    m_dep = re.search(r"\b(?:AREA\s*O\s*DEPENDENCIA|DEPENDENCIA|ÁREA|AREA)\s*[:\-.]?\s*([^\n\r]{3,50})", text, re.I)
    if m_dep:
        cand_d = _clean_text(m_dep.group(1))
        if not any(k in cand_d.lower() for k in ["yo ", "voluntaria", "consiente", "cargo"]):
            dep = cand_d

    # 5. Búsqueda de Nombre
    # Prioridad A: "NOMBRE DEL TRABAJADOR: Hugo Andres Baquero"
    m_nom_trab = re.search(
        r"NOMBRE\s*DEL\s*TRABAJADOR\s*[:\-.]?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,60})",
        text,
        re.I,
    )
    if m_nom_trab:
        cand = _clean_text(m_nom_trab.group(1))
        # Cortar si leyó parte del siguiente encabezado (Cc, Firma, Evaluador, etc.)
        cand = re.split(r"(?i)\b(?:CC|CE|FIRMA|EVALUADOR|SALVO|DECLARO)\b", cand)[0].strip()
        if len(cand) >= 4 and "salvo que" not in cand.lower():
            nombre = cand

    # Prioridad B: "Yo Hugo Andres Baquero en forma voluntaria..."
    if not nombre:
        m_yo = re.search(
            r"\bYo\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,60}?)(?:\s+en\s+forma|\s+consiente|\s+mediante|\s*,|$)",
            text,
            re.I,
        )
        if m_yo:
            cand = _clean_text(m_yo.group(1))
            cand = re.split(r"(?i)\b(?:CC|CE|FIRMA|EVALUADOR|SALVO|DECLARO)\b", cand)[0].strip()
            if len(cand) >= 4 and "forma voluntaria" not in cand.lower() and "salvo que" not in cand.lower():
                nombre = cand

    # Prioridad C: Nombre manuscrito arriba a la izquierda/centro en el encabezado
    if not nombre and lines:
        for first_line in lines[:5]:
            words = first_line.split()
            if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
                fl_lower = first_line.lower()
                if not any(
                    w in fl_lower
                    for w in [
                        "consejo",
                        "seguridad",
                        "proteger",
                        "colombiano",
                        "calidad",
                        "trabajando",
                        "consentimiento",
                        "salvo",
                    ]
                ):
                    nombre = first_line
                    break

    # Si la cédula aún no se encontró, buscar número de 7 a 10 dígitos en proximidad al nombre
    if not cc:
        for line in lines:
            if "evaluador" in line.lower():
                break  # Evitar el CC del evaluador si estuviera
            digits_in_line = re.findall(r"\b\d{7,10}\b", line)
            # Evitar teléfonos de Proteger IPS que empiezan por 317, 301, 312, 321, etc.
            valid = [d for d in digits_in_line if not d.startswith(("31", "30", "32", "40", "56", "63"))]
            if valid:
                cc = valid[0]
                break

    return {
        "fecha": fecha,
        "cargo": cargo,
        "dependencia": dep,
        "nombre": nombre,
        "id_documento": cc,
        "ocr_consentimiento": text[:500],
    }
