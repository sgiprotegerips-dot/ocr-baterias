"""Nómina de trabajadores a partir de FICHA DATOS GENERALES e impresión 30×20 mm."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from openpyxl import load_workbook

from .qr_codec import (
    FICHA_FIELDS,
    encode_payload,
    label_display_name,
    normalize_ficha,
    render_qr_svg,
)

HEADER_MAP = {
    "fecha aplicacion": "fecha_aplicacion",
    "fecha aplicación": "fecha_aplicacion",
    "cedula": "cedula",
    "cédula": "cedula",
    "nombre completo": "nombre",
    "nombre": "nombre",
    "sexo": "sexo",
    "año nacimiento": "anio_nacimiento",
    "ano nacimiento": "anio_nacimiento",
    "anio nacimiento": "anio_nacimiento",
    "fecha nacimiento": "fecha_nacimiento",
    "fecha de nacimiento": "fecha_nacimiento",
    "edad": "edad",
    "estado civil": "estado_civil",
    "nivel de estudios": "nivel_estudios",
    "cargo u ocupacion": "cargo_ocupacion",
    "cargo u ocupación": "cargo_ocupacion",
    "resid. actual": "residencia",
    "resid actual": "residencia",
    "residencia": "residencia",
    "departamento": "departamento",
    "estrato": "estrato",
    "tipo vivienda": "tipo_vivienda",
    "no. personas que dependen de ud.": "n_dependientes",
    "no personas que dependen de ud": "n_dependientes",
    "lugar de trabajo actual": "lugar_trabajo",
    "dpto. trabajo": "dpto_trabajo",
    "dpto trabajo": "dpto_trabajo",
    "tiempo en la empresa en años": "tiempo_empresa",
    "tiempo en la empresa en anos": "tiempo_empresa",
    "cargo actual": "cargo",
    "tipo de cargo": "tipo_cargo",
    "tiempo en cargo actual en años": "tiempo_cargo",
    "tiempo en cargo actual en anos": "tiempo_cargo",
    "area": "area",
    "área": "area",
    "tipo contrato": "tipo_contrato",
    "horas diarias de trabajo": "horas_diarias",
    "tipo salario": "tipo_salario",
}


def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def _norm_header(value: Any) -> str:
    text = _cell_str(value).lower()
    text = text.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return " ".join(text.split())


def parse_ficha_excel(path: Union[str, Path]) -> List[Dict[str, str]]:
    """Lee la hoja FICHA DATOS GENERALES (secciones FORMA A / FORMA B)."""
    wb = load_workbook(path, data_only=True, read_only=True)
    try:
        sheet_name = "FICHA DATOS GENERALES"
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb[wb.sheetnames[0]]
        forma = ""
        col_map: Dict[int, str] = {}
        rows: List[Dict[str, str]] = []

        for row in ws.iter_rows(values_only=True):
            vals = list(row)
            if not vals:
                continue
            first = _cell_str(vals[0]).upper()
            if first in ("FORMA A", "FORMA B"):
                forma = "B" if first.endswith("B") else "A"
                continue
            joined = " ".join(_cell_str(v).upper() for v in vals[:4])
            if "CEDULA" in joined.replace("É", "E") and "NOMBRE" in joined:
                new_map: Dict[int, str] = {}
                for idx, cell in enumerate(vals):
                    mapped = HEADER_MAP.get(_norm_header(cell))
                    if mapped:
                        new_map[idx] = mapped
                mapped_fields = set(new_map.values())
                # Una fila de instrucciones que menciona «cédula» y «nombre»
                # no es encabezado: hace falta que esos dos campos sean celdas propias.
                if "cedula" in mapped_fields and "nombre" in mapped_fields:
                    col_map = new_map
                continue
            if not col_map:
                continue
            if first in ("", "NO.", "N°", "Nº"):
                continue
            rec = {k: "" for k in FICHA_FIELDS}
            rec["forma"] = forma
            for idx, field in col_map.items():
                if idx < len(vals):
                    rec[field] = _cell_str(vals[idx])
            rec = normalize_ficha(rec)
            if rec["cedula"] and rec["nombre"]:
                rows.append(rec)
        return rows
    finally:
        wb.close()


def render_labels_html(fichas: Iterable[Dict[str, Any]]) -> str:
    pages = []
    for raw in fichas:
        ficha = normalize_ficha(raw)
        payload = encode_payload(ficha)
        svg = render_qr_svg(payload)
        nombre = label_display_name(ficha["nombre"])
        forma = ficha["forma"] or "-"
        nac = ficha["fecha_nacimiento"] or ficha["anio_nacimiento"] or ""
        pages.append(
            f"""
<article class="label">
  <div class="qr">{svg}</div>
  <div class="meta">
    <div class="name">{_html(nombre)}</div>
    <div class="cc">CC { _html(ficha["cedula"]) }</div>
    <div class="line">FORMA { _html(forma) }</div>
    <div class="line">NAC { _html(nac) }</div>
  </div>
</article>
"""
        )

    body = "\n".join(pages)
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Etiquetas QR 30×20 mm</title>
  <style>
    @page {{ size: 30mm 20mm; margin: 0; }}
    html, body {{
      margin: 0;
      padding: 0;
      width: 30mm;
      height: 20mm;
      background: #fff;
      color: #000;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .label {{
      width: 30mm;
      height: 20mm;
      box-sizing: border-box;
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 1.2mm;
      padding: 1mm 1.2mm;
      page-break-after: always;
      break-after: page;
      overflow: hidden;
    }}
    .qr {{
      width: 16mm;
      height: 16mm;
      flex: 0 0 16mm;
    }}
    .qr svg {{
      width: 16mm;
      height: 16mm;
      display: block;
    }}
    .meta {{
      flex: 1 1 auto;
      min-width: 0;
      line-height: 1.15;
    }}
    .name {{
      font-size: 5.4pt;
      font-weight: 700;
      text-transform: uppercase;
      white-space: nowrap;
      overflow: hidden;
    }}
    .cc {{
      font-size: 5.2pt;
      font-weight: 700;
      letter-spacing: 0.01em;
    }}
    .line {{
      font-size: 4.6pt;
      font-weight: 600;
    }}
  </style>
</head>
<body>
{body}
<script>window.addEventListener("load", function() {{ setTimeout(function() {{ window.print(); }}, 250); }});</script>
</body>
</html>
"""


def _html(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def ficha_to_worker_kwargs(ficha: Dict[str, Any], origen: str = "excel") -> Dict[str, Any]:
    n = normalize_ficha(ficha)
    return {
        "cedula": n["cedula"],
        "nombre_completo": n["nombre"],
        "forma": n["forma"] or "B",
        "cargo": n["cargo"],
        "area": n["area"],
        "fecha_aplicacion": n["fecha_aplicacion"],
        "fecha_nacimiento": n["fecha_nacimiento"],
        "anio_nacimiento": n["anio_nacimiento"],
        "sexo": n["sexo"],
        "ficha_json": n,
        "payload_qr": encode_payload(n),
        "origen": origen,
    }
