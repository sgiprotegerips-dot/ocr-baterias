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
    normalize_ficha,
)


# Factores de conversión milímetros a puntos PDF (72 puntos = 1 pulgada = 25.4 mm)
MM_TO_PT = 72.0 / 25.4


def _split_word_to_width(word: str, max_w: float, fontname: str, fontsize: float) -> List[str]:
    """Divide una palabra extremadamente larga si supera el ancho disponible."""
    if fitz.get_text_length(word, fontname=fontname, fontsize=fontsize) <= max_w:
        return [word]
    parts: List[str] = []
    cur = ""
    for ch in word:
        if fitz.get_text_length(cur + ch, fontname=fontname, fontsize=fontsize) <= max_w or not cur:
            cur += ch
        else:
            parts.append(cur)
            cur = ch
    if cur:
        parts.append(cur)
    return parts


def _wrap_and_fit_text(
    text: str,
    max_w: float,
    max_h: float,
    max_lines: int = 2,
    fontname: str = "hebo",
    max_fs: float = 5.6,
    min_fs: float = 3.0,
) -> tuple[float, List[str]]:
    """Ajusta dinámicamente el tamaño de fuente y divide en líneas para que el texto
    completo (nombre o identificación) siempre sea visible sin que PyMuPDF lo omita.
    """
    raw_words = [w for w in (text or "").strip().split() if w]
    if not raw_words:
        return min_fs, ["SIN NOMBRE"]

    fs = max_fs
    while fs >= min_fs - 1e-5:
        lines: List[str] = []
        cur = ""
        possible = True
        for w in raw_words:
            if fitz.get_text_length(w, fontname=fontname, fontsize=fs) > max_w:
                possible = False
                break
            cand = f"{cur} {w}".strip() if cur else w
            if fitz.get_text_length(cand, fontname=fontname, fontsize=fs) <= max_w:
                cur = cand
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        line_h = fs * 1.12
        if possible and len(lines) <= max_lines and (len(lines) * line_h) <= max_h + 0.6:
            return round(fs, 2), lines
        fs -= 0.2

    # Fallback en tamaño mínimo dividiendo palabras que excedan el ancho total
    fs = min_fs
    tokens: List[str] = []
    for w in raw_words:
        tokens.extend(_split_word_to_width(w, max_w, fontname, fs))

    lines = []
    cur = ""
    for w in tokens:
        cand = f"{cur} {w}".strip() if cur else w
        if fitz.get_text_length(cand, fontname=fontname, fontsize=fs) <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    if len(lines) > max_lines:
        kept = lines[: max_lines - 1]
        rest = " ".join(lines[max_lines - 1 :])
        while len(rest) > 1 and fitz.get_text_length(rest, fontname=fontname, fontsize=fs) > max_w:
            rest = rest[:-1].rstrip()
        lines = kept + [rest]

    return round(fs, 2), lines


def _fit_single_line(
    text: str,
    max_w: float,
    fontname: str = "hebo",
    max_fs: float = 7.2,
    min_fs: float = 3.6,
) -> float:
    """Calcula el mayor tamaño de fuente que permite dibujar una línea sin desbordar max_w."""
    fs = max_fs
    while fs > min_fs and fitz.get_text_length(text, fontname=fontname, fontsize=fs) > max_w:
        fs -= 0.2
    return round(max(min_fs, fs), 2)


def generate_roll_labels_pdf(fichas: Iterable[Dict[str, Any]], full_payload: bool = False) -> bytes:
    """Genera un archivo PDF multi-página en rollo térmico continuo de 30×20 mm.

    Cada página corresponde a un sticker individual de 30×20 mm con 0 márgenes.
    Diseño optimizado para ubicación rápida de la batería física:
    - Superior izquierdo: Código QR de alta densidad (13.8 × 13.8 mm) con quiet zone limpia.
    - Superior derecho: Bloque FORMA (A/B) en alto contraste + CÉDULA en tipografía grande autoajustada.
    - Franja inferior de ancho completo (28.6 mm): NOMBRE COMPLETO autoajustado en 1 o 2 líneas
      mediante `insert_text` directo para garantizar que jamás se omita ningún nombre ni cédula.
    """
    doc = fitz.open()
    w_pt = 30.0 * MM_TO_PT  # ~85.04 pt
    h_pt = 20.0 * MM_TO_PT  # ~56.69 pt
    qr_mm = 13.8
    qr_pt = qr_mm * MM_TO_PT  # ~39.12 pt
    qr_x = 1.6
    qr_y = 1.0

    items = list(fichas)
    if not items:
        doc.new_page(width=w_pt, height=h_pt)
        return doc.tobytes()

    for raw in items:
        ficha = normalize_ficha(raw)
        page = doc.new_page(width=w_pt, height=h_pt)

        # 1. Código QR de alta legibilidad (nivel M, borde 1)
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

        # 2. Columna superior derecha: FORMA + CÉDULA siempre visibles y ajustadas
        nombre_full = (ficha.get("nombre", "") or "SIN NOMBRE").strip().upper()
        cc = (ficha.get("cedula", "") or "SIN CC").strip()
        forma = (ficha.get("forma", "A") or "A").strip().upper()

        rx = qr_x + qr_pt + 2.0
        rw = w_pt - rx - 2.0

        # Etiqueta FORMA destacada en pastilla negra
        badge_rect = fitz.Rect(rx, 1.8, w_pt - 2.0, 11.6)
        page.draw_rect(badge_rect, color=(0, 0, 0), fill=(0, 0, 0))
        forma_txt = f"FORMA {forma}"
        forma_fs = _fit_single_line(forma_txt, rw - 3.0, fontname="hebo", max_fs=6.2, min_fs=4.0)
        forma_tw = fitz.get_text_length(forma_txt, fontname="hebo", fontsize=forma_fs)
        page.insert_text(
            (rx + (rw - forma_tw) / 2.0, 8.9),
            forma_txt,
            fontsize=forma_fs,
            fontname="hebo",
            color=(1, 1, 1),
        )

        # Bloque Cédula (título + número en negrita grande autoajustado)
        page.insert_text(
            (rx, 18.2),
            "C.C. / ID:",
            fontsize=4.4,
            fontname="hebo",
            color=(0.2, 0.2, 0.2),
        )
        cc_fs = _fit_single_line(cc, rw, fontname="hebo", max_fs=7.2, min_fs=4.0)
        page.insert_text(
            (rx, 26.8),
            cc,
            fontsize=cc_fs,
            fontname="hebo",
            color=(0, 0, 0),
        )

        # Línea divisoria sutil en columna derecha + fecha/año de referencia
        page.draw_line((rx, 31.0), (w_pt - 2.0, 31.0), color=(0.78, 0.78, 0.78), width=0.4)
        ref_date = (
            ficha.get("fecha_aplicacion")
            or ficha.get("fecha_nacimiento")
            or ficha.get("anio_nacimiento")
            or ""
        ).strip()
        if ref_date:
            ref_txt = f"F: {ref_date[:10]}"
            ref_fs = _fit_single_line(ref_txt, rw, fontname="helv", max_fs=4.2, min_fs=3.4)
            page.insert_text(
                (rx, 37.2),
                ref_txt,
                fontsize=ref_fs,
                fontname="helv",
                color=(0.3, 0.3, 0.3),
            )

        # 3. Franja inferior de ancho completo: NOMBRE COMPLETO autoajustado (1 a 2 líneas)
        name_top = 41.6
        name_max_h = h_pt - name_top - 1.2
        name_max_w = w_pt - 4.0
        n_fs, n_lines = _wrap_and_fit_text(
            nombre_full,
            max_w=name_max_w,
            max_h=name_max_h,
            max_lines=2,
            fontname="hebo",
            max_fs=5.5,
            min_fs=3.0,
        )
        total_h = len(n_lines) * (n_fs * 1.1)
        y_cursor = name_top + max(0.0, (name_max_h - total_h) / 2.0) + n_fs * 0.88
        for ln in n_lines:
            page.insert_text(
                (2.0, y_cursor),
                ln,
                fontsize=n_fs,
                fontname="hebo",
                color=(0, 0, 0),
            )
            y_cursor += n_fs * 1.12

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_sheet_labels_pdf(fichas: Iterable[Dict[str, Any]], page_size: str = "letter") -> bytes:
    """Genera un archivo PDF en pliego Carta (8.5 × 11 in) con cuadrícula 3×10 (30 etiquetas/hoja).

    Diseñado para imprimir en impresoras láser/inyección con papel adhesivo troquelado estándar
    (compatible con formatos tipo Avery 5160 / 30 etiquetas por hoja Carta).
    Muestra siempre Forma, Cédula y Nombre completo autoajustados.
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

        # Textos informativos completos y autoajustados (Forma, Cédula, Nombre completo)
        nombre_full = (ficha.get("nombre", "") or "SIN NOMBRE").strip().upper()
        cc = (ficha.get("cedula", "") or "SIN CC").strip()
        forma = (ficha.get("forma", "A") or "A").strip().upper()

        tx_x = x0 + 5.0 + qr_size + 5.0
        tx_w = (x1 - 5.0) - tx_x

        # 1. FORMA
        forma_str = f"FORMA {forma}"
        forma_fs = _fit_single_line(forma_str, tx_w, fontname="hebo", max_fs=7.8, min_fs=5.0)
        current_page.insert_text(
            (tx_x, y0 + 16.0),
            forma_str,
            fontsize=forma_fs,
            fontname="hebo",
            color=(0, 0, 0),
        )

        # 2. CÉDULA
        cc_str = f"CC {cc}"
        cc_fs = _fit_single_line(cc_str, tx_w, fontname="hebo", max_fs=8.2, min_fs=5.0)
        current_page.insert_text(
            (tx_x, y0 + 28.0),
            cc_str,
            fontsize=cc_fs,
            fontname="hebo",
            color=(0, 0, 0),
        )

        # 3. NOMBRE COMPLETO autoajustado en hasta 3 líneas
        name_top = y0 + 33.0
        name_max_h = (y1 - 5.0) - name_top
        n_fs, n_lines = _wrap_and_fit_text(
            nombre_full,
            max_w=tx_w,
            max_h=name_max_h,
            max_lines=3,
            fontname="hebo",
            max_fs=6.8,
            min_fs=4.2,
        )
        y_cursor = name_top + n_fs * 0.95
        for ln in n_lines:
            current_page.insert_text(
                (tx_x, y_cursor),
                ln,
                fontsize=n_fs,
                fontname="hebo",
                color=(0, 0, 0),
            )
            y_cursor += n_fs * 1.15

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_single_label_pdf(ficha: Dict[str, Any]) -> bytes:
    """Genera el PDF de 1 sola etiqueta de 30×20 mm."""
    return generate_roll_labels_pdf([ficha])
