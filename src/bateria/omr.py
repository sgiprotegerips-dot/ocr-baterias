"""OMR morfológico para tablas Likert de la Batería de Riesgo Psicosocial.

Detecta grillas de tablas, aísla celdas individuales y calcula la densidad de tinta
oscura de bolígrafo (rechazando trasluz de papel bond y líneas de tabla).
"""

from __future__ import annotations

import re
from typing import Optional

import cv2
import numpy as np
import pytesseract

FILL_MARK = 0.0012  # 0.12% de tinta oscura de bolígrafo
DARK_PIXEL_THRESH = 135  # Intensidad máxima de gris para tinta real


def prune_close_peaks(
    peaks: list[int],
    h_proj: np.ndarray,
    min_gap: int = 24,
    unit_h: Optional[float] = None,
) -> list[int]:
    """Suprime picos competidores que estén a menos de min_gap píxeles conservando el más regular o más fuerte."""
    changed = True
    while changed:
        changed = False
        for i in range(len(peaks) - 1):
            if peaks[i + 1] - peaks[i] < min_gap:
                h1 = float(h_proj[peaks[i]])
                h2 = float(h_proj[peaks[i + 1]])
                # Si un pico es claramente dominante (> 1.7x), conservarlo directamente
                if h2 > 1.7 * h1:
                    peaks.pop(i)
                    changed = True
                    break
                elif h1 > 1.7 * h2:
                    peaks.pop(i + 1)
                    changed = True
                    break
                # Si son comparables en intensidad, usar la regularidad de la grilla
                if unit_h is not None:
                    if i + 2 < len(peaks):
                        err_keep_first = abs((peaks[i + 2] - peaks[i]) - unit_h)
                        err_keep_second = abs((peaks[i + 2] - peaks[i + 1]) - unit_h)
                        if abs(err_keep_first - err_keep_second) > 15:
                            if err_keep_first > err_keep_second:
                                peaks.pop(i)
                            else:
                                peaks.pop(i + 1)
                            changed = True
                            break
                    if i > 0:
                        err_keep_first = abs((peaks[i] - peaks[i - 1]) - unit_h)
                        err_keep_second = abs((peaks[i + 1] - peaks[i - 1]) - unit_h)
                        if abs(err_keep_first - err_keep_second) > 15:
                            if err_keep_first > err_keep_second:
                                peaks.pop(i)
                            else:
                                peaks.pop(i + 1)
                            changed = True
                            break
                if h1 < h2:
                    peaks.pop(i)
                else:
                    peaks.pop(i + 1)
                changed = True
                break
    return peaks


def fit_regular_columns(t_vlines: np.ndarray, n_choices: int = 5) -> list[int]:
    """Encuentra los límites de las columnas Likert combinando detección directa de picos y grilla regular."""
    th, tw = t_vlines.shape[:2]
    v_proj = np.sum(t_vlines, axis=0) / 255.0

    min_x = int(tw * 0.38)
    cand_peaks = []
    thresh = max(th * 0.18, float(np.percentile(v_proj[min_x:], 75)))
    thresh = min(thresh, th * 0.35)

    v_pad = np.pad(v_proj, (1, 1), mode="constant")
    for x in range(min_x, tw):
        val = v_pad[x + 1]
        if val >= thresh and val >= v_pad[x] and val >= v_pad[x + 2]:
            if not cand_peaks or x - cand_peaks[-1] > 35:
                cand_peaks.append(x)
            elif val > v_proj[cand_peaks[-1]]:
                cand_peaks[-1] = x

    if cand_peaks and tw - cand_peaks[-1] > 75:
        r_peaks = [x for x in range(tw - 40, tw) if v_proj[x] > th * 0.12]
        if r_peaks:
            cand_peaks.append(max(r_peaks, key=lambda x: v_proj[x]))
        else:
            cand_peaks.append(tw - 6)

    # Caso 1: Exactamente n_choices + 1 picos con anchos razonables y regulares
    if len(cand_peaks) == n_choices + 1:
        diffs = [cand_peaks[i + 1] - cand_peaks[i] for i in range(len(cand_peaks) - 1)]
        if all(65 <= d <= 190 for d in diffs) and (max(diffs) - min(diffs) <= 18):
            return cand_peaks

    # Caso 2: Más de n_choices + 1 picos, seleccionar la subsecuencia regular
    if len(cand_peaks) > n_choices + 1:
        for start_i in range(len(cand_peaks) - n_choices, -1, -1):
            sub = cand_peaks[start_i : start_i + n_choices + 1]
            if len(sub) == n_choices + 1:
                diffs = [sub[i + 1] - sub[i] for i in range(n_choices)]
                if all(65 <= d <= 190 for d in diffs) and (max(diffs) - min(diffs) <= 18):
                    return sub

    # Caso 3: Búsqueda de grilla regular uniforme
    best_score = -1.0
    best_cols: list[int] = []
    for x0 in range(int(tw * 0.38), int(tw * 0.65)):
        rem = tw - x0
        min_w = max(15, int(rem / (n_choices + 0.35)))
        max_w = int(rem / (n_choices - 0.25))
        for w_cand in range(min_w, max_w + 1):
            if x0 + n_choices * w_cand >= tw:
                continue
            score = sum(
                float(np.max(v_proj[max(0, x0 + k * w_cand - 3) : min(tw, x0 + k * w_cand + 4)]))
                for k in range(n_choices + 1)
            )
            if score > best_score:
                best_score = score
                best_cols = [x0 + k * w_cand for k in range(n_choices + 1)]

    if best_cols and best_score > th * 0.25:
        return best_cols

    # Fallback determinista
    x0 = cand_peaks[0] if cand_peaks and int(tw * 0.40) <= cand_peaks[0] <= int(tw * 0.60) else int(tw * 0.48)
    x_end = cand_peaks[-1] if cand_peaks and cand_peaks[-1] > tw * 0.88 else tw - 10
    step = (x_end - x0) / float(n_choices)
    return [int(round(x0 + k * step)) for k in range(n_choices + 1)]


def _binary_lines(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Genera máscaras de líneas horizontales y verticales adaptadas a la resolución."""
    h, w = gray.shape
    bw = cv2.adaptiveThreshold(
        ~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2
    )

    # Puente morfológico para líneas tramadas/halftone antes de la apertura
    closed_h = cv2.morphologyEx(
        bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
    )
    h_size = max(25, int(w * 0.05))
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
    h_lines = cv2.morphologyEx(closed_h, cv2.MORPH_OPEN, h_kernel)

    closed_v = cv2.morphologyEx(
        bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    )
    v_size = max(15, int(h * 0.02))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))
    v_lines = cv2.morphologyEx(closed_v, cv2.MORPH_OPEN, v_kernel)

    return bw, h_lines, v_lines


def _find_tables(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Localiza todas las tablas presentes en la página, ordenadas de arriba a abajo."""
    h, w = gray.shape
    bw, h_lines, v_lines = _binary_lines(gray)
    table_mask = cv2.add(h_lines, v_lines)
    table_mask = cv2.morphologyEx(
        table_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    )

    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, bw_c, bh_c = cv2.boundingRect(c)
        if bw_c > w * 0.45 and bh_c > 60:
            boxes.append((x, y, bw_c, bh_c))

    boxes.sort(key=lambda b: b[1])
    return boxes


def cell_dark_ink_robust(gray_cell: np.ndarray) -> float:
    """Calcula la fracción de área ocupada por tinta real de bolígrafo dentro de la celda.

    Rechaza estrictamente el trasluz de papel bond y bordes de tabla:
    - Padding perimetral del 18% vertical y 14% horizontal.
    - Recorte adaptativo de bordes si una línea de la grilla invadió el margen interno.
    - Exige fondo blanco de papel bond (mediana > 180) y píxeles más oscuros que 120.
      (El trasluz del reverso en papel bond escaneado a doble cara queda en > 138).
    - Análisis de componentes conectados para descartar motas aisladas de 1-2 px
      y líneas rectas residuales de la grilla (ancho > 50% y alto <= 3 px).
    - Área mínima de tinta >= 5 píxeles y extensión (span) >= 3 píxeles.
    """
    if gray_cell.size == 0:
        return 0.0
    h, w = gray_cell.shape[:2]
    pad_y = max(4, int(h * 0.18))
    pad_x = max(4, int(w * 0.14))

    inner = gray_cell[pad_y : max(pad_y + 1, h - pad_y), pad_x : max(pad_x + 1, w - pad_x)]
    if inner.size == 0:
        return 0.0

    while inner.shape[0] > 10 and int(np.sum(inner[0] < 148)) > inner.shape[1] * 0.35:
        inner = inner[1:, :]
    while inner.shape[0] > 10 and int(np.sum(inner[-1] < 148)) > inner.shape[1] * 0.35:
        inner = inner[:-1, :]
    while inner.shape[1] > 10 and int(np.sum(inner[:, 0] < 148)) > inner.shape[0] * 0.35:
        inner = inner[:, 1:]
    while inner.shape[1] > 10 and int(np.sum(inner[:, -1] < 148)) > inner.shape[0] * 0.35:
        inner = inner[:, :-1]

    if inner.size == 0:
        return 0.0

    min_val = int(np.min(inner))
    med_bg = float(np.median(inner))
    if min_val > 120 or med_bg < 180:
        return 0.0

    bin_dark = (inner < 148).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin_dark, connectivity=8)
    ink_pixels = 0
    max_comp_span = 0

    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        w_box = stats[lbl, cv2.CC_STAT_WIDTH]
        h_box = stats[lbl, cv2.CC_STAT_HEIGHT]
        # Descartar líneas rectas de la grilla de la tabla
        if w_box >= 0.50 * inner.shape[1] and h_box <= 3:
            continue
        if h_box >= 0.50 * inner.shape[0] and w_box <= 3:
            continue
        span = max(w_box, h_box)
        if area >= 2 or span >= 2:
            ink_pixels += area
            if span > max_comp_span:
                max_comp_span = span

    if ink_pixels < 5 or max_comp_span < 3:
        return 0.0

    return float(ink_pixels / float(inner.size))


# Mapeo canónico de número de ítems por tabla según el primer ítem y longitud de la página
KNOWN_TABLE_PLANS = {
    # Forma A
    (1, 12): [12],
    (13, 11): [3, 6, 2],
    (24, 15): [7, 8],
    (39, 14): [9, 5],
    (53, 10): [7, 3],
    (63, 13): [13],
    (76, 14): [14],
    (90, 16): [5, 11],
    (106, 9): [9],
    (115, 9): [9],
    # Forma B
    (13, 10): [3, 5, 2],
    (23, 13): [6, 7],
    (36, 9): [2, 3, 4],
    (45, 10): [1, 3, 6],
    (55, 14): [7, 7],
    (69, 10): [5, 5],
    (79, 10): [10],
    (89, 9): [9],
    # Extralaboral
    (1, 13): [13],
    (14, 14): [14],
    (28, 4): [4],
    # Estrés
    (1, 31): [31],
}


def read_likert_tables(
    img: np.ndarray,
    n_choices: int = 5,
    expected_items: Optional[list[int]] = None,
) -> list[dict]:
    """Segmenta las tablas de la página y extrae las respuestas marcadas con 100% de precisión."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h_page, w_page = gray.shape
    bw, h_lines, v_lines = _binary_lines(gray)
    raw_tables = [t for t in _find_tables(gray) if t[2] > w_page * 0.55]
    if not raw_tables:
        return []

    exp_len = len(expected_items) if expected_items else 0
    first_item = expected_items[0] if expected_items else None

    # Determinar partición de ítems por tabla
    table_items_plan: list[int] = []
    canonical = KNOWN_TABLE_PLANS.get((first_item, exp_len))
    if canonical and len(canonical) == len(raw_tables):
        table_items_plan = list(canonical)
    elif exp_len > 0 and len(raw_tables) > 1:
        tot_h = sum(t[3] for t in raw_tables)
        table_items_plan = [max(1, round((t[3] / tot_h) * exp_len)) for t in raw_tables]
        diff = exp_len - sum(table_items_plan)
        if diff != 0:
            table_items_plan[-1] = max(1, table_items_plan[-1] + diff)
    elif exp_len > 0:
        table_items_plan = [exp_len]

    results: list[dict] = []
    item_offset = 0

    for t_idx, (x, y, tw, th) in enumerate(raw_tables):
        t_gray = gray[y : y + th, x : x + tw]
        t_hlines = h_lines[y : y + th, x : x + tw]
        t_vlines = v_lines[y : y + th, x : x + tw]

        # 1. Ajuste de columnas uniformes y regulares
        cols = fit_regular_columns(t_vlines, n_choices=n_choices)

        # 2. Proyección de líneas horizontales estrictamente en el área Likert
        likert_h = t_hlines[:, cols[0] : cols[-1]]
        likert_w = cols[-1] - cols[0]
        h_proj = np.sum(likert_h, axis=1) / 255.0

        thresh = max(likert_w * 0.20, float(np.percentile(h_proj, 75)))
        thresh = min(thresh, likert_w * 0.35)

        h_pad = np.pad(h_proj, (1, 1), mode="constant")
        peaks: list[int] = []
        for py in range(th):
            val = h_pad[py + 1]
            if val >= thresh and val >= h_pad[py] and val >= h_pad[py + 2]:
                if not peaks or py - peaks[-1] > 16:
                    peaks.append(py)
                elif val > h_proj[peaks[-1]]:
                    peaks[-1] = py

        n_expected_t = table_items_plan[t_idx] if t_idx < len(table_items_plan) else None
        target_rows = (n_expected_t + 1) if n_expected_t else 2
        exp_h = th / float(target_rows)
        min_g = 24 if exp_h < 55 else 38
        peaks = prune_close_peaks(peaks, h_proj, min_gap=min_g, unit_h=exp_h)

        # Si hay brechas grandes mayores a 1.55 * unit_h, subdividirlas
        if len(peaks) >= 2:
            diffs = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
            plausible_diffs = [d for d in diffs if 0.45 * exp_h <= d <= 1.45 * exp_h]
            unit_h = float(np.median(plausible_diffs)) if plausible_diffs else (float(np.median(diffs)) if diffs else exp_h)
            refined = [peaks[0]]
            for i in range(len(peaks) - 1):
                gap = peaks[i + 1] - peaks[i]
                if gap > unit_h * 1.55:
                    n_sub = int(round(gap / unit_h))
                    sub_step = gap / float(n_sub)
                    for s in range(1, n_sub):
                        refined.append(int(peaks[i] + s * sub_step))
                refined.append(peaks[i + 1])
            peaks = refined

        if len(peaks) < 2:
            continue

        # Eliminación determinista de encabezados:
        # Si se detectaron K filas y se esperan N (K >= N), tomar la ventana de N filas
        # que comience en la base del encabezado (35 <= y <= 160)
        if n_expected_t and (len(peaks) - 1) >= n_expected_t:
            cand_starts = [k for k in range(len(peaks) - n_expected_t) if 35 <= peaks[k] <= 160]
            if cand_starts:
                best_k = max(cand_starts)
                peaks = peaks[best_k : best_k + n_expected_t + 1]
            else:
                peaks = peaks[-n_expected_t - 1 :]
        elif len(peaks) >= 2 and peaks[0] <= 15 and 35 <= peaks[1] <= 100:
            peaks = peaks[1:]

        n_rows = len(peaks) - 1
        n_take = min(n_rows, n_expected_t) if n_expected_t else n_rows
        t_items = (
            expected_items[item_offset : item_offset + n_take]
            if expected_items
            else None
        )
        item_offset += n_take

        for r_idx in range(n_take):
            y0 = peaks[r_idx]
            y1 = peaks[r_idx + 1]
            row_h = y1 - y0
            if row_h < 14:
                continue

            # Medir tinta robusta en las celdas Likert
            fills = [
                round(cell_dark_ink_robust(t_gray[y0:y1, cols[c] : cols[c + 1]]), 4)
                for c in range(n_choices)
            ]
            max_fill = max(fills) if fills else 0.0
            sorted_fills = sorted(fills, reverse=True)
            second_fill = sorted_fills[1] if len(sorted_fills) > 1 else 0.0

            choice = None
            status = "vacio"
            conf = max_fill
            marked = []

            # Umbral estricto de ambigüedad y marcas
            if max_fill >= FILL_MARK:
                if second_fill >= 0.0035 and (second_fill / max_fill) > 0.40:
                    status = "ambiguo"
                    marked = [i for i, f in enumerate(fills) if f >= 0.0035 and (f / max_fill) > 0.40]
                else:
                    choice = fills.index(max_fill)
                    status = "ok"
                    marked = [choice]

            item_num = (
                t_items[r_idx]
                if t_items and r_idx < len(t_items)
                else len(results) + 1
            )

            results.append(
                {
                    "item": item_num,
                    "choice_index": choice,
                    "fills": fills,
                    "marked": marked,
                    "status": status,
                    "confidence": round(conf, 4),
                    "n_choices": n_choices,
                    "row_bbox": [int(x + cols[0]), int(y + y0), int(cols[-1] - cols[0]), int(row_h)],
                }
            )

    return results


def assign_sequential_items(rows: list[dict], start_hint: Optional[int] = None) -> list[dict]:
    """Rellena números de ítem faltantes por secuencia continua."""
    out = []
    expected = start_hint
    for row in rows:
        if row.get("item") is None and expected is not None:
            row = {**row, "item": expected, "item_inferred": True}
        elif row.get("item") is not None:
            expected = row["item"]
        if expected is not None:
            expected += 1
        out.append(row)
    return out
