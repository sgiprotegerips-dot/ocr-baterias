"""Generador de etiquetas PDF vectoriales de alta precisión para la Batería SST.

Soporta dos modalidades de salida:
1. Rollo Térmico 30×20 mm: 1 página = 1 etiqueta, escala 1:1, 0 márgenes (Zebra, TSC, Brother, etc.).
2. Pliego Carta / A4: Cuadrícula de 3 columnas × 10 filas (30 etiquetas por hoja) para papel adhesivo troquelado.
"""

from __future__ import annotations

import io
from typing import Any, Dict, Iterable, List, Optional, Union

import pymupdf as fitz
import segno

from .qr_codec import (
    encode_compact_payload,
    encode_payload,
    label_display_name,
    normalize_ficha,
)


# Factores de conversión milímetros a puntos PDF (72 puntos = 1 pulgada = 25.4 mm)
MM_TO_PT = 72.0 / 25.4


def generate_roll_labels_pdf(fichas: Iterable[Dict[str, Any]], full_payload: bool = False) -> bytes:
    """Genera un archivo PDF multi-página en rollo térmico continuo de 30×20 mm.

    Cada página corresponde a un sticker individual de 30×20 mm con 0 márgenes.
    El código QR utiliza un tamaño maximizado de 17.5 × 17.5 mm (87.5% de la altura de la etiqueta)
    y un payload compacto BRP1 (Versión 2/3, 29×29 módulos) con módulos grandes de ~0.56 mm,
    garantizando lectura instantánea por cámaras de teléfonos móviles y escáneres térmicos.
    """
    doc = fitz.open()
    w_pt = 30.0 * MM_TO_PT  # ~85.04 pt
    h_pt = 20.0 * MM_TO_PT  # ~56.69 pt
    qr_mm = 17.5
    qr_pt = qr_mm * MM_TO_PT  # ~49.6 pt
    qr_y = (h_pt - qr_pt) / 2.0  # ~3.5 pt (1.25 mm margen vertical)
    qr_x = 1.4 * MM_TO_PT  # ~4.0 pt (1.4 mm margen izquierdo)

    items = list(fichas)
    if not items:
        doc.new_page(width=w_pt, height=h_pt)
        return doc.tobytes()

    for raw in items:
        ficha = normalize_ficha(raw)
        page = doc.new_page(width=w_pt, height=h_pt)

        # 1. Código QR maximizado de 17.5 mm con módulos grandes (nivel M, borde 1)
        if full_payload:
            payload = encode_payload(ficha, compact=False)
        else:
            payload = encode_compact_payload(ficha)

        qr = segno.make(payload, error="m")
        png_buf = io.BytesIO()
        qr.save(png_buf, kind="png", scale=8, border=1)
        qr_pix = fitz.Pixmap(png_buf.getvalue())
        qr_rect = fitz.Rect(qr_x, qr_y, qr_x + qr_pt, qr_y + qr_pt)
        page.insert_image(qr_rect, pixmap=qr_pix)

        # 2. Textos legibles y ordenados en la columna derecha (~11 mm)
        nombre = label_display_name(ficha.get("nombre", ""))
        cc = ficha.get("cedula", "")
        forma = ficha.get("forma", "A") or "A"

        tx_x = qr_x + qr_pt + 2.5
        tx_w = w_pt - tx_x - 1.0

        # Bloque FORMA (destacado arriba)
        page.insert_textbox(
            fitz.Rect(tx_x, 2.5, w_pt - 1.0, 15.0),
            f"FORMA {forma}",
            fontsize=6.2,
            fontname="helv",
            color=(0, 0, 0),
        )

        # Bloque Cédula (medio)
        page.insert_textbox(
            fitz.Rect(tx_x, 15.0, w_pt - 1.0, 29.0),
            f"CC\n{cc}",
            fontsize=5.2,
            fontname="helv",
            color=(0, 0, 0),
        )

        # Bloque Nombre / Apellidos (abajo)
        page.insert_textbox(
            fitz.Rect(tx_x, 30.0, w_pt - 1.0, h_pt - 2.0),
            nombre,
            fontsize=4.8,
            fontname="helv",
            color=(0, 0, 0),
        )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_sheet_labels_pdf(fichas: Iterable[Dict[str, Any]], page_size: str = "letter") -> bytes:
    """Genera un archivo PDF en pliego Carta (8.5 × 11 in) con cuadrícula 3×10 (30 etiquetas/hoja).

    Diseñado para imprimir en impresoras láser/inyección con papel adhesivo troquelado estándar
    (compatible con formatos tipo Avery 5160 / 30 etiquetas por hoja Carta).
    """
    doc = fitz.open()

    if page_size.lower() == "a4":
        page_w = 210.0 * MM_TO_PT
        page_h = 297.0 * MM_TO_PT
    else:
        # Carta (Letter): 612 × 792 pt
        page_w = 8.5 * 72.0
        page_h = 11.0 * 72.0

    margin_x = 18.0  # 0.25 in (~6.35 mm)
    margin_y = 36.0  # 0.50 in (~12.7 mm)
    col_w = (page_w - 2 * margin_x) / 3.0  # ~192 pt
    row_h = (page_h - 2 * margin_y) / 10.0  # ~72 pt (~25.4 mm)
    qr_size = min(row_h - 14.0, 48.0)  # ~17 mm

    items = list(fichas)
    if not items:
        doc.new_page(width=page_w, height=page_h)
        return doc.tobytes()

    current_page = None
    for idx, raw in enumerate(items):
        if idx % 30 == 0:
            current_page = doc.new_page(width=page_w, height=page_h)

        ficha = normalize_ficha(raw)
        pos = idx % 30
        col = pos % 3
        row = pos // 3

        x0 = margin_x + col * col_w
        y0 = margin_y + row * row_h
        x1 = x0 + col_w
        y1 = y0 + row_h

        # Borde guía sutil (gris muy claro) para corte o verificación de troquel
        current_page.draw_rect(
            fitz.Rect(x0 + 2.0, y0 + 2.0, x1 - 2.0, y1 - 2.0),
            color=(0.88, 0.88, 0.88),
            width=0.4,
        )

        # Código QR maximizado y legible
        payload = encode_compact_payload(ficha)
        qr = segno.make(payload, error="m")
        png_buf = io.BytesIO()
        qr.save(png_buf, kind="png", scale=5, border=1)
        qr_pix = fitz.Pixmap(png_buf.getvalue())
        qr_size = min(row_h - 10.0, 56.0)  # ~20 mm
        qr_y = y0 + (row_h - qr_size) / 2.0
        qr_rect = fitz.Rect(x0 + 5.0, qr_y, x0 + 5.0 + qr_size, qr_y + qr_size)
        current_page.insert_image(qr_rect, pixmap=qr_pix)

        # Textos informativos
        nombre = label_display_name(ficha.get("nombre", ""))
        cc = ficha.get("cedula", "")
        forma = ficha.get("forma", "A") or "A"

        text = f"FORMA {forma}\nCC {cc}\n{nombre}"
        text_rect = fitz.Rect(x0 + 5.0 + qr_size + 6.0, y0 + 10.0, x1 - 4.0, y1 - 6.0)
        current_page.insert_textbox(text_rect, text, fontsize=7.0, fontname="helv")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_single_label_pdf(ficha: Dict[str, Any]) -> bytes:
    """Genera el PDF de 1 sola etiqueta de 30×20 mm."""
    return generate_roll_labels_pdf([ficha])
