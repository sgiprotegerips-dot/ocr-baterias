"""Codec compacto BRP1 para etiquetas QR de la ficha sociodemográfica.

Payload de orden fijo (campos de la hoja FICHA DATOS GENERALES + fecha de nacimiento):

    BRP1|{forma}|{fecha_aplicacion}|{cedula}|...|{tipo_salario}
"""

from __future__ import annotations

from typing import Any, Dict, Optional

FICHA_FIELDS = [
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
]

PREFIX = "BRP1"

_MAX_LEN = {
    "nombre": 50,
    "cargo": 40,
    "cargo_ocupacion": 40,
    "tipo_cargo": 40,
    "area": 40,
    "nivel_estudios": 24,
    "residencia": 28,
    "lugar_trabajo": 28,
}


def _clean(value: Any, field: str) -> str:
    if value is None:
        return ""
    text = str(value).replace("|", "/").replace("\n", " ").strip()
    limit = _MAX_LEN.get(field, 32)
    if len(text) > limit:
        text = text[:limit].rstrip()
    return text


def empty_ficha() -> Dict[str, str]:
    return {k: "" for k in FICHA_FIELDS}


def normalize_ficha(data: Optional[Dict[str, Any]]) -> Dict[str, str]:
    src = data or {}
    out = empty_ficha()
    for key in FICHA_FIELDS:
        out[key] = _clean(src.get(key, ""), key)
    if out["forma"] in ("FORMA A", "A", "a"):
        out["forma"] = "A"
    elif out["forma"] in ("FORMA B", "B", "b"):
        out["forma"] = "B"
    if not out["anio_nacimiento"] and out["fecha_nacimiento"]:
        out["anio_nacimiento"] = out["fecha_nacimiento"][:4]
    if not out["fecha_nacimiento"] and out["anio_nacimiento"] and len(out["anio_nacimiento"]) == 4:
        # El Excel oficial solo trae año; se deja fecha vacía a propósito.
        pass
    return out


def encode_payload(data: Dict[str, Any]) -> str:
    ficha = normalize_ficha(data)
    return PREFIX + "|" + "|".join(ficha[k] for k in FICHA_FIELDS)


def decode_payload(raw: Optional[str]) -> Optional[Dict[str, str]]:
    text = (raw or "").strip()
    if not text.startswith(PREFIX + "|"):
        return None
    parts = text.split("|")
    values = parts[1:]
    if len(values) < 3:
        return None
    ficha = empty_ficha()
    for i, key in enumerate(FICHA_FIELDS):
        if i < len(values):
            ficha[key] = values[i].strip()
    if not ficha["cedula"]:
        return None
    if ficha["forma"] not in ("", "A", "B"):
        ficha["forma"] = ficha["forma"][-1].upper() if ficha["forma"] else ""
    return ficha


def identity_from_ficha(ficha: Dict[str, Any]) -> Dict[str, Any]:
    n = normalize_ficha(ficha)
    return {
        "nombre": n["nombre"],
        "cargo": n["cargo"],
        "dependencia": n["area"],
        "fecha": n["fecha_aplicacion"],
        "id_documento": n["cedula"] or None,
        "fuente": "qr",
        "ficha": n,
    }


def label_display_name(nombre: str) -> str:
    parts = [p for p in (nombre or "").split() if p]
    if len(parts) >= 3:
        return " ".join(parts[-2:])
    return " ".join(parts) or "SIN NOMBRE"


def render_qr_svg(payload: str) -> str:
    import segno

    qr = segno.make(payload, error="m")
    return qr.svg_inline(scale=4, border=1)


def render_qr_bgr(payload: str, box_px: int = 180):
    import cv2
    import numpy as np
    import segno

    qr = segno.make(payload, error="m")
    matrix = np.array(qr.matrix, dtype=np.uint8)
    padded = np.pad(matrix, 2, constant_values=0)
    h, w = padded.shape
    scale = max(1, int(box_px / max(h, w)))
    scaled = np.kron(padded, np.ones((scale, scale), dtype=np.uint8))
    gray = np.where(scaled == 1, 0, 255).astype(np.uint8)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
