"""Nómina de trabajadores a partir de FICHA DATOS GENERALES e impresión 30×20 mm."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from openpyxl import load_workbook

from .qr_codec import (
    FICHA_FIELDS,
    encode_compact_payload,
    encode_payload,
    label_display_name,
    normalize_ficha,
    render_qr_png_data_uri,
    render_qr_svg,
)
from .label_pdf import (
    generate_roll_labels_pdf,
    generate_sheet_labels_pdf,
    generate_single_label_pdf,
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
        payload = encode_compact_payload(ficha)
        png_uri = render_qr_png_data_uri(payload, scale=8, border=1)
        nombre = label_display_name(ficha["nombre"])
        forma = ficha["forma"] or "A"
        nac = ficha.get("fecha_nacimiento") or ficha.get("anio_nacimiento") or ""
        pages.append(
            f"""
<article class="label">
  <div class="qr">
    <img class="qr-img" src="{png_uri}" alt="QR" />
  </div>
  <div class="meta">
    <div class="line" style="font-weight:700;font-size:5.6pt;">FORMA { _html(forma) }</div>
    <div class="cc">CC { _html(ficha["cedula"]) }</div>
    <div class="name">{_html(nombre)}</div>
    <div class="line" style="font-size:4.6pt;color:#444;">{ _html(nac) }</div>
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
    *, *:before, *:after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    @page {{
      size: 30mm 20mm;
      margin: 0mm;
    }}
    html, body {{
      margin: 0;
      padding: 0;
      width: 30mm;
      height: 20mm;
      background: #fff;
      color: #000;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, Helvetica, sans-serif;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .label {{
      width: 30mm;
      height: 20mm;
      max-width: 30mm;
      max-height: 20mm;
      box-sizing: border-box;
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: flex-start;
      gap: 1mm;
      padding: 1.5mm 1mm;
      page-break-inside: avoid;
      break-inside: avoid;
      page-break-after: always;
      break-after: page;
      overflow: hidden;
      background: #fff;
    }}
    .label:last-child {{
      page-break-after: avoid;
      break-after: avoid;
    }}
    .qr {{
      width: 17.5mm;
      height: 17.5mm;
      flex: 0 0 17.5mm;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
    }}
    .qr-img {{
      width: 17.5mm;
      height: 17.5mm;
      display: block;
      image-rendering: pixelated;
      image-rendering: -moz-crisp-edges;
      image-rendering: crisp-edges;
    }}
    .meta {{
      flex: 1 1 auto;
      min-width: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 0.3mm;
      line-height: 1.15;
      overflow: hidden;
    }}
    .name {{
      font-size: 4.8pt;
      font-weight: 700;
      text-transform: uppercase;
      white-space: nowrap;
      overflow: hidden;
      color: #000;
      letter-spacing: -0.01em;
    }}
    .cc {{
      font-size: 5.0pt;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      color: #000;
      letter-spacing: -0.02em;
    }}
    .line {{
      font-size: 5.4pt;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      color: #000;
      letter-spacing: -0.01em;
    }}

    @media print {{
      html, body {{
        margin: 0 !important;
        padding: 0 !important;
        width: 30mm !important;
        height: 20mm !important;
        overflow: hidden !important;
      }}
      .label {{
        width: 30mm !important;
        height: 20mm !important;
        max-width: 30mm !important;
        max-height: 20mm !important;
        padding: 1.2mm 1mm !important;
        gap: 0.8mm !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        page-break-after: always !important;
        break-after: page !important;
      }}
      .label:last-child {{
        page-break-after: avoid !important;
        break-after: avoid !important;
      }}
      .qr {{
        width: 17.5mm !important;
        height: 17.5mm !important;
        flex: 0 0 17.5mm !important;
      }}
      .qr-img {{
        width: 17.5mm !important;
        height: 17.5mm !important;
      }}
      .name {{ font-size: 4.8pt !important; }}
      .cc {{ font-size: 5.0pt !important; }}
      .line {{ font-size: 5.4pt !important; }}
    }}
  </style>
</head>
<body>
{body}
<script>
  function doPrint() {{
    window.focus();
    try {{ window.print(); }} catch (e) {{}}
  }}
  if (document.readyState === "complete") {{
    setTimeout(doPrint, 200);
  }} else {{
    window.addEventListener("load", function() {{ setTimeout(doPrint, 200); }});
  }}
</script>
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
