"""Clasificación determinista de páginas de la Batería de Riesgo Psicosocial.

Detecta orientación, número de página impreso (1..24), forma (A vs B) y tipo semántico
para garantizar el correcto reordenamiento de escáneres ADF dúplex.
"""

from __future__ import annotations

import re
from typing import Optional

import cv2
import numpy as np

from .ocr_engine import normalize_page_orientation, ocr_printed_text

# Mapeo de ítems esperados por página física (1..24)
ITEMS_FORMA_A = {
    8: list(range(1, 13)),     # 12 ítems (1..12)
    9: list(range(13, 24)),    # 11 ítems (13..23)
    10: list(range(24, 39)),   # 15 ítems (24..38)
    11: list(range(39, 53)),   # 14 ítems (39..52)
    12: list(range(53, 63)),   # 10 ítems (53..62)
    13: list(range(63, 76)),   # 13 ítems (63..75)
    14: list(range(76, 90)),   # 14 ítems (76..89)
    15: list(range(90, 106)),  # 16 ítems (90..105)
    16: list(range(106, 115)), # 9 ítems (106..114: clientes/usuarios)
    17: list(range(115, 124)), # 9 ítems (115..123: jefatura)
}

ITEMS_FORMA_B = {
    8: list(range(1, 13)),     # 12 ítems (1..12)
    9: list(range(13, 23)),    # 10 ítems (13..22)
    10: list(range(23, 36)),   # 13 ítems (23..35)
    11: list(range(36, 45)),   # 9 ítems (36..44)
    12: list(range(45, 55)),   # 10 ítems (45..54)
    13: list(range(55, 69)),   # 14 ítems (55..68)
    14: list(range(69, 79)),   # 10 ítems (69..78)
    15: list(range(79, 89)),   # 10 ítems (79..88)
    16: list(range(89, 98)),   # 9 ítems (89..97)
}

ITEMS_EXTRALABORAL = {
    20: list(range(1, 14)),    # 13 ítems (1..13)
    21: list(range(14, 28)),   # 14 ítems (14..27)
    22: list(range(28, 32)),   # 4 ítems (28..31)
}

ITEMS_ESTRES = {
    24: list(range(1, 32)),    # 31 ítems (1..31)
}


def extract_footer_page_number(img: np.ndarray) -> Optional[int]:
    """Extrae con certeza matemática el número de página impreso (1..24) en el pie de página."""
    h, w = img.shape[:2]
    # Zona 1: El 9% inferior absoluto (debajo de la tabla Likert)
    txt_low = ocr_printed_text(img[int(h * 0.91):, :]).strip()
    lines_low = [l.strip() for l in txt_low.split("\n") if l.strip()]
    for l in lines_low:
        m = re.search(r"^\s*[\|\(\[\.\-]?\s*([1-9]|1\d|2[0-4])\s*[\|\)\]\.\-]?\s*$", l)
        if m:
            return int(m.group(1))
        m2 = re.search(r"(?<!\d)([1-9]|1\d|2[0-4])\s*[\|\)\]\.\-]?\s*$", l)
        if m2:
            return int(m2.group(1))

    # Zona 2: El 16% inferior (para páginas donde el pie de página está un poco más alto)
    txt_mid = ocr_printed_text(img[int(h * 0.84):, :]).strip()
    lines_mid = [l.strip() for l in txt_mid.split("\n") if l.strip()]
    for l in reversed(lines_mid[-3:]):
        if "%" in l or "$" in l:
            continue
        m = re.search(r"^\s*[\|\(\[\.\-]?\s*([1-9]|1\d|2[0-4])\s*[\|\)\]\.\-]?\s*$", l)
        if m:
            return int(m.group(1))
        m2 = re.search(r"\s+([1-9]|1\d|2[0-4])\s*[\|\)\]\.\-]?\s*$", l)
        if m2:
            return int(m2.group(1))

    return None


def _extract_page_number_from_footer(bot_text: str) -> Optional[int]:
    """Compatibilidad retrospectiva para cadenas de texto de pie de página."""
    lines = [l.strip() for l in bot_text.split("\n") if l.strip()]
    if not lines:
        return None

    for l in lines:
        m = re.match(r"^\s*([1-9]|1\d|2[0-4])\s*$", l)
        if m:
            return int(m.group(1))

    for l in lines:
        m = re.search(r"(?i)\bp[aá]g(?:ina)?\.?\s*([1-9]|1\d|2[0-4])\b", l)
        if m:
            return int(m.group(1))

    for l in lines:
        nums = re.findall(r"(?<![a-zA-Z0-9])([1-9]|1\d|2[0-4])(?![a-zA-Z0-9])", l)
        if nums:
            return int(nums[0])

    return None


SPANISH_KEYWORDS = [
    "ministerio", "proteccion", "protección", "social", "republica", "república",
    "colombia", "pontificia", "universidad", "javeriana", "cuestionario", "factores",
    "riesgo", "psicosocial", "intralaboral", "extralaboral", "estres", "estrés",
    "trabajador", "fecha", "instrucciones", "preguntas", "siempre", "nunca",
    "datos", "generales", "identificacion", "identificación", "respondiente",
    "consentimiento", "informado", "colaboracion", "colaboración"
]


def classify_page(img: np.ndarray) -> dict:
    """Clasifica la página determinísticamente combinando número impreso y anclas semánticas.

    Asegura que la imagen esté enderezada antes de extraer encabezados y pie de página.
    """
    # 1. Normalización de orientación (anti-duplex invertido 180° / rotaciones ADF)
    upright_img, rotated, rot_angle = normalize_page_orientation(img)
    h, w = upright_img.shape[:2]

    # Verificar si la página vino de cabeza (180°) usando presencia de vocabulario español real (top 45%)
    top_roi_0 = upright_img[: int(h * 0.45), :]
    top_text_0 = ocr_printed_text(top_roi_0).lower()
    kw_0 = sum(1 for k in SPANISH_KEYWORDS if k in top_text_0)

    if kw_0 < 2:
        rot_180 = cv2.rotate(upright_img, cv2.ROTATE_180)
        top_roi_180 = rot_180[: int(h * 0.45), :]
        top_text_180 = ocr_printed_text(top_roi_180).lower()
        kw_180 = sum(1 for k in SPANISH_KEYWORDS if k in top_text_180)
        if kw_180 >= 2 and kw_180 > kw_0:
            upright_img = rot_180
            rotated = True
            rot_angle = (rot_angle + 180) % 360
            top_text = top_text_180
        else:
            top_text = top_text_0
    else:
        top_text = top_text_0

    # Extracción de pie de página de alta certeza
    page_no = extract_footer_page_number(upright_img)

    # 2. Detección de Forma A vs Forma B mediante regex robusto
    forma = None
    m_forma = re.search(r"\bforma\s*[\"']?([ab])[\"']?\b", top_text, re.IGNORECASE)
    if m_forma:
        forma = m_forma.group(1).upper()
    elif any(k in top_text for k in ["intralaboral forma b", "instrucciones forma b", "cuestionario forma b", '(b)']):
        forma = "B"
    elif any(k in top_text for k in ["intralaboral forma a", "instrucciones forma a", "cuestionario forma a", '(a)']):
        forma = "A"

    has_id_box = any(
        k in top_text
        for k in ["(id)", "(1d)", "identificación", "identificacion", "respondiente", "número de identificación", "numero de identificacion"]
    )
    has_instructions = "instrucciones" in top_text

    # 3. Identificación semántica por palabras clave inequívocas
    kind = "otra"
    semantic_page = None

    # 1. Consentimiento Informado -> Page 1
    if "consentimiento informado" in top_text or ("proteger i.p.s" in top_text and "voluntaria" in top_text):
        kind = "consentimiento"
        semantic_page = 1

    # 2. Portada Intralaboral (tiene recuadro de ID y no tiene instrucciones) -> Page 6
    elif "intralaboral" in top_text and has_id_box and not has_instructions:
        kind = "intra_portada"
        semantic_page = 6

    # 3. Instrucciones Intralaboral (declara Forma A/B o instrucciones, sin recuadro ID) -> Page 7
    elif "intralaboral" in top_text and (has_instructions or forma is not None) and not has_id_box:
        kind = "intra_instrucciones"
        semantic_page = 7

    # 4. Portada Extralaboral (tiene recuadro de ID y no tiene instrucciones) -> Page 18
    elif ("extralaboral" in top_text or "extralaborales" in top_text) and has_id_box and not has_instructions:
        kind = "extra_portada"
        semantic_page = 18

    # 5. Instrucciones Extralaboral (tiene instrucciones, sin recuadro ID) -> Page 19
    elif ("extralaboral" in top_text or "extralaborales" in top_text) and (has_instructions or "cuestionario" in top_text) and not has_id_box:
        kind = "extra_instrucciones"
        semantic_page = 19

    # 6. Cuestionario de Estrés con 31 síntomas -> Page 24
    elif "malestares" in top_text or "dolores en el cuello" in top_text or "síntomas" in top_text or "sintomas" in top_text:
        kind = "estres_items"
        semantic_page = 24

    # 7. Portada Estrés -> Page 23
    elif "evaluación del estrés" in top_text or "evaluacion del estres" in top_text or "tercera versión" in top_text or "tercera version" in top_text:
        kind = "estres_portada"
        semantic_page = 23

    # 8. Ítems Intralaborales específicos (Págs 8..17)
    elif "soy jefe de otras personas" in top_text or "jefe de otras personas" in top_text or "supervisa o dirige" in top_text:
        kind = "intra_items"
        semantic_page = 17
    elif "atención a clientes" in top_text or "servicio a clientes" in top_text or "atención a usuarios" in top_text or "brindar servicio" in top_text:
        kind = "intra_items"
        semantic_page = 16
    elif "rendimiento en el trabajo" in top_text or "hago bien en mi trabajo" in top_text or "reconocimiento" in top_text or "orgullo de trabajar" in top_text:
        kind = "intra_items"
        semantic_page = 15
    elif ("relaciones con otras personas" in top_text and "apoyo entre" in top_text) or "compañeros de trabajo" in top_text:
        kind = "intra_items"
        semantic_page = 14
    elif "el o los jefes" in top_text or "mi jefe" in top_text or "puntos de vista" in top_text or "jefe inmediato" in top_text:
        kind = "intra_items"
        semantic_page = 13
    elif "información que la empresa" in top_text or "cuáles son mis funciones" in top_text or "hacer mejor mi trabajo" in top_text:
        kind = "intra_items"
        semantic_page = 12
    elif "decisiones y el control" in top_text or "desarrollar mis habilidades" in top_text or "aprender cosas nuevas" in top_text or "habilidades y conocimientos" in top_text:
        kind = "intra_items"
        semantic_page = 11
    elif "seguridad de otros" in top_text or "cuidar la salud" in top_text or "toda mi área" in top_text or "responsabilidad por los resultados" in top_text:
        kind = "intra_items"
        semantic_page = 10
    elif "cantidad de trabajo" in top_text or "tiempo adicional" in top_text or "alcanza el tiempo" in top_text:
        kind = "intra_items"
        semantic_page = 9
    elif "condiciones ambientales" in top_text or "ruido en el lugar" in top_text or "frío en el lugar" in top_text:
        kind = "intra_items"
        semantic_page = 8

    # 9. Extralaboral items (Págs 20..22)
    elif "zona donde usted vive" in top_text or "trasportarme entre mi casa" in top_text or "transporte entre mi casa" in top_text:
        kind = "extra_items"
        semantic_page = 20
    elif "vida fuera del trabajo" in top_text or "actividades de recreación" in top_text or "tiempo para descansar" in top_text:
        kind = "extra_items"
        semantic_page = 21
    elif "problemas personales o familiares" in top_text or "gastos básicos" in top_text or "presupuesto familiar" in top_text or "vivienda es cómoda" in top_text:
        kind = "extra_items"
        semantic_page = 22

    # 10. Ficha de Datos Generales (Págs 2..5)
    elif "último nivel de estudios" in top_text or "ultimo nivel de estudios" in top_text or "ocupación o profesión" in top_text:
        kind = "ficha"
        semantic_page = 3
    elif "lugar donde trabaja actualmente" in top_text or "cuántos años que trabaja" in top_text or "cuantos anos que trabaja" in top_text or "nombre del cargo" in top_text:
        kind = "ficha"
        semantic_page = 4
    elif "seleccione el tipo de contrato" in top_text or "horas de trabajo al día" in top_text or "muchas gracias por su colaboración" in top_text:
        kind = "ficha"
        semantic_page = 5
    elif ("ficha de datos generales" in top_text or ("fecha de nacimiento" in top_text and "sexo" in top_text)) and not any(w in top_text for w in ["si su respuesta fue no", "pasar a la", "pase a", "siguiente sección"]):
        kind = "ficha"
        semantic_page = 2

    # Resolución de página final con validación cruzada determinista
    valid_footer = False
    if page_no:
        if kind == "intra_items" and 8 <= page_no <= 17:
            valid_footer = True
        elif kind == "extra_items" and 20 <= page_no <= 22:
            valid_footer = True
        elif kind == "estres_items" and page_no == 24:
            valid_footer = True
        elif kind == "estres_portada" and page_no == 23:
            valid_footer = True
        elif kind == "ficha" and 2 <= page_no <= 5:
            valid_footer = True
        elif kind == "consentimiento" and page_no == 1:
            valid_footer = True
        elif kind in ("intra_portada", "intra_instrucciones", "extra_portada", "extra_instrucciones"):
            valid_footer = (page_no == semantic_page)
        elif kind == "otra" and 1 <= page_no <= 24:
            valid_footer = True

    if valid_footer:
        final_page = page_no
    elif semantic_page is not None:
        final_page = semantic_page
    elif page_no and 1 <= page_no <= 24:
        final_page = page_no
    else:
        final_page = None

    return {
        "kind": kind,
        "forma": forma,
        "printed_page": final_page,
        "upright_img": upright_img,
        "rotated": rotated,
        "rot_angle": rot_angle,
        "ocr_preview": top_text[:300],
    }


def get_expected_items(page_num: int, forma: str = "A") -> list[int]:
    """Retorna la lista de números de ítem exactos que contiene la página indicada."""
    if page_num in (20, 21, 22):
        return ITEMS_EXTRALABORAL.get(page_num, [])
    if page_num == 24:
        return ITEMS_ESTRES.get(page_num, [])

    if forma == "B":
        return ITEMS_FORMA_B.get(page_num, [])
    return ITEMS_FORMA_A.get(page_num, [])
