"""Detección y decodificación ultra-robusta de QR y sticker de identidad 30×20 mm en la página 1.

Arquitectura multicapa optimizada para escáneres ADF (incluyendo escaneos binarios 1-bit
CCITTFaxDecode a 200 DPI y etiquetas térmicas de 30×20 mm):
- Capa 1 (Decodificación Matricial 2D): Búsqueda multizona con OpenCV QRCodeDetector /
  QRCodeDetectorAruco, realce CLAHE/Otsu, rotación cardinal y adelgazamiento morfológico
  sobre el recorte exacto del QR.
- Capa 2 (Localización Topológica de Patrones de Búsqueda `回` + Lectura Impresa del Sticker):
  Cuando el escáner binario 1-bit fusiona los módulos internos de datos pero preserva los
  anillos concéntricos 7×7 / 5×5 / 3×3 del QR, localiza las coordenadas exactas del sticker
  30×20 mm, enmascara la matriz ruidosa y extrae mediante RapidOCR + Tesseract la FORMA (A/B),
  CÉDULA y NOMBRE COMPLETO impresos en el sticker.
- Capa 3 (Enriquecimiento y Reconciliación contra Nómina en Base de Datos):
  Cruza la identidad extraída del sticker con `TrabajadorNomina` (exacta o tolerante a 1 bit
  de ruido fax validado por tokens del nombre) para restituir los 26 campos de la ficha
  sociodemográfica oficial.
"""

from __future__ import annotations

import difflib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from .qr_codec import decode_payload, empty_ficha, normalize_ficha

# Caché ligero en memoria de la nómina para evitar consultas repetidas en lotes masivos
_NOMINA_CACHE: Dict[str, Any] = {"ts": 0.0, "records": [], "by_cc": {}}
_NOMINA_TTL_SEC = 15.0

_STOP_WORDS_STICKER = {
    "FORMA",
    "FORMAA",
    "FORMAB",
    "FIRMAB",
    "FIRMAA",
    "ORMA",
    "RMAB",
    "RMAA",
    "APLIC",
    "NAC",
    "CONSIENTE",
    "CONSENTIMIENTO",
    "INFORMADO",
    "PSICOLOGO",
    "PSICOLOGA",
    "EVALUACION",
    "RIESGO",
    "PSICOSOCIAL",
    "BATERIA",
    "MINISTERIO",
    "PROTECCION",
    "SOCIAL",
    "JAVERIANA",
    "DOCUMENTO",
    "IDENTIDAD",
    "FIRMA",
    "FECHA",
    "EMPRESA",
    "TRABAJADOR",
    "DATOS",
    "GENERALES",
    "CUESTIONARIO",
    "FACTORES",
    "INTRALABORAL",
    "EXTRALABORAL",
}


def _get_nomina_Lookup() -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Obtiene y cachea temporalmente las fichas de TrabajadorNomina desde PostgreSQL."""
    now = time.monotonic()
    if now - _NOMINA_CACHE["ts"] < _NOMINA_TTL_SEC and _NOMINA_CACHE["records"]:
        return _NOMINA_CACHE["records"], _NOMINA_CACHE["by_cc"]

    records: List[Dict[str, str]] = []
    by_cc: Dict[str, Dict[str, str]] = {}
    try:
        from .db.models import TrabajadorNomina
        from .db.session import SyncSessionLocal

        with SyncSessionLocal() as s:
            rows = s.query(TrabajadorNomina).all()
            for r in rows:
                d = r.to_dict().get("ficha") or {}
                nf = normalize_ficha(d)
                cc = nf.get("cedula", "").strip()
                if cc:
                    records.append(nf)
                    by_cc[cc] = nf
    except Exception:
        return _NOMINA_CACHE["records"], _NOMINA_CACHE["by_cc"]

    _NOMINA_CACHE["ts"] = now
    _NOMINA_CACHE["records"] = records
    _NOMINA_CACHE["by_cc"] = by_cc
    return records, by_cc


def _enrich_with_nomina(ficha: Dict[str, str]) -> Dict[str, str]:
    """Completa campos vacíos de una ficha QR usando TrabajadorNomina si la cédula existe."""
    cc = (ficha.get("cedula") or "").strip()
    if not cc:
        return ficha
    _, by_cc = _get_nomina_Lookup()
    nom = by_cc.get(cc)
    if not nom:
        return ficha
    merged = dict(nom)
    for k, v in ficha.items():
        if v:
            if k == "nombre" and len(nom.get("nombre", "")) > len(v):
                continue
            merged[k] = v
    return normalize_ficha(merged)


def _find_qr_finder_boxes(gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Detecta los patrones de búsqueda (`回`) del código QR en la mitad superior de la página 1.

    Escala dinámicamente todos los umbrales geométricos según la resolución de la página
    (soportando nativamente escaneos de 150 DPI, 200 DPI, 300 DPI y 400 DPI).
    Usa tanto la jerarquía de 3 niveles (anillo negro 7×7 -> anillo blanco 5×5 -> centro negro 3×3)
    como la validación concéntrica del hueco blanco 5×5 con centro negro 3×3 (inmune a la fusión
    del borde exterior 7×7 con módulos de datos en escaneos binarios CCITTFaxDecode).
    """
    h, w = gray.shape[:2]
    scale = max(0.70, min(2.50, max(h, w) / 2190.0))
    _, bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, hier = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None or len(contours) == 0:
        return []

    max_y = int(h * 0.58)
    raw_boxes: List[Tuple[int, int, int, int]] = []

    min_w1 = max(12, int(round(12.5 * scale)))
    max_w1 = int(round(32 * scale))
    min_w2 = max(5, int(round(5.5 * scale)))
    max_w2 = int(round(18 * scale))

    min_outer = max(18, int(round(20 * scale)))
    max_outer = int(round(48 * scale))

    for i, c in enumerate(contours):
        parent = int(hier[0][i][3])
        child = int(hier[0][i][2])

        # Caso A: Contorno hueco blanco 5×5 (tiene padre negro y centro hijo negro 3×3)
        if parent != -1 and child != -1:
            x1, y1, w1, h1 = cv2.boundingRect(c)
            if y1 < max_y and min_w1 <= w1 <= max_w1 and min_w1 <= h1 <= max_w1 and 0.65 <= (w1 / float(h1)) <= 1.45:
                x2, y2, w2, h2 = cv2.boundingRect(contours[child])
                if min_w2 <= w2 <= max_w2 and min_w2 <= h2 <= max_w2 and 0.60 <= (w2 / float(h2)) <= 1.50:
                    cx1, cy1 = x1 + w1 * 0.5, y1 + h1 * 0.5
                    cx2, cy2 = x2 + w2 * 0.5, y2 + h2 * 0.5
                    tol = max(3.5 * scale, w1 * 0.18)
                    if abs(cx1 - cx2) <= tol and abs(cy1 - cy2) <= tol:
                        pad = int(round(w1 * 0.22))
                        raw_boxes.append((max(0, x1 - pad), max(0, y1 - pad), w1 + 2 * pad, h1 + 2 * pad))
                        continue

        # Caso B: Contorno exterior negro 7×7 con hijo 5×5 y nieto 3×3
        if child != -1:
            grandchild = int(hier[0][child][2])
            if grandchild != -1:
                x, y, bw_box, bh_box = cv2.boundingRect(c)
                if y < max_y and min_outer <= bw_box <= max_outer and min_outer <= bh_box <= max_outer and 0.68 <= (bw_box / float(bh_box)) <= 1.42:
                    xg, yg, wg, hg = cv2.boundingRect(contours[grandchild])
                    if min_w2 <= wg <= max_w2 and min_w2 <= hg <= max_w2:
                        cx, cy = x + bw_box * 0.5, y + bh_box * 0.5
                        cxg, cyg = xg + wg * 0.5, yg + hg * 0.5
                        tol = max(4.0 * scale, bw_box * 0.18)
                        if abs(cx - cxg) <= tol and abs(cy - cyg) <= tol:
                            raw_boxes.append((x, y, bw_box, bh_box))

    # Deduplicar cajas superpuestas (por ejemplo cuando Caso A y Caso B detectan el mismo patrón)
    dedup_tol = max(10.0, 10.0 * scale)
    deduped: List[Tuple[int, int, int, int]] = []
    for bx, by, bw_b, bh_b in raw_boxes:
        cx, cy = bx + bw_b * 0.5, by + bh_b * 0.5
        if any(abs(cx - (dx + dw * 0.5)) <= dedup_tol and abs(cy - (dy + dh * 0.5)) <= dedup_tol for dx, dy, dw, dh in deduped):
            continue
        deduped.append((bx, by, bw_b, bh_b))

    return deduped


def _locate_qr_cluster(gray: np.ndarray) -> Optional[Tuple[int, int, int, List[Tuple[int, int, int, int]]]]:
    """Agrupa los patrones de búsqueda (`回`) del QR y estima el cuadro `(qx, qy, qsize)` (200 y 300 DPI)."""
    finders = _find_qr_finder_boxes(gray)
    if not finders:
        return None

    h, w = gray.shape[:2]
    scale = max(0.70, min(2.50, max(h, w) / 2190.0))
    min_p = int(round(21 * scale))
    max_p = int(round(44 * scale))
    expected_fw = 26.0 * scale

    # Filtrar tamaños típicos de finder patterns de sticker 30×20 mm según DPI
    primary = [f for f in finders if min_p <= f[2] <= max_p and min_p <= f[3] <= max_p]
    candidates = primary if primary else finders

    best_cluster: List[Tuple[int, int, int, int]] = []
    for f in candidates:
        cx, cy = f[0] + f[2] * 0.5, f[1] + f[3] * 0.5
        max_dist = f[2] * 3.95
        cl = [
            g
            for g in candidates
            if abs((g[0] + g[2] * 0.5) - cx) <= max_dist
            and abs((g[1] + g[3] * 0.5) - cy) <= max_dist
            and abs(g[2] - f[2]) <= max(4.0 * scale, f[2] * 0.25)
        ]
        # Asegurar que el bounding box del cluster completo no supere 4.35 * f[2] (tamaño físico del QR)
        if len(cl) > 1:
            cl_w = max(g[0] + g[2] for g in cl) - min(g[0] for g in cl)
            cl_h = max(g[1] + g[3] for g in cl) - min(g[1] for g in cl)
            if cl_w > f[2] * 4.45 or cl_h > f[2] * 4.45:
                cl = [g for g in cl if (g[0] - f[0]) <= f[2] * 3.6 and (g[1] - f[1]) <= f[2] * 3.6]
        if len(cl) > len(best_cluster):
            best_cluster = cl
        elif len(cl) == len(best_cluster) and best_cluster:
            # Preferir cluster con ancho más cercano al tamaño esperado de 13.8mm según el DPI
            if abs(f[2] - expected_fw) < abs(best_cluster[0][2] - expected_fw):
                best_cluster = cl

    if not best_cluster:
        return None

    avg_w = sum(f[2] for f in best_cluster) / float(len(best_cluster))
    qsize = int(round(avg_w * 3.95))
    min_x = min(f[0] for f in best_cluster)
    min_y = min(f[1] for f in best_cluster)
    max_x = max(f[0] + f[2] for f in best_cluster)
    max_y = max(f[1] + f[3] for f in best_cluster)

    if len(best_cluster) >= 2:
        qsize = min(int(round(avg_w * 4.35)), max(qsize, max_x - min_x, max_y - min_y))
        qx, qy = min_x, min_y
        # Si los dos patrones están alineados verticalmente pero son la esquina derecha
        if (max_x - min_x) < avg_w * 1.6 and (max_y - min_y) > avg_w * 2.0:
            qx = min_x
            qy = min_y
    else:
        # Un solo patrón detectado: estimar hacia qué cuadrante está la densidad de módulos del QR
        fx, fy, fw, fh = best_cluster[0]
        _, bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        best_density = -1.0
        qx, qy = fx, fy
        for dx in (0, -int(qsize - fw)):
            for dy in (0, -int(qsize - fh)):
                cx0 = max(0, fx + dx)
                cy0 = max(0, fy + dy)
                cx1 = min(gray.shape[1], cx0 + qsize)
                cy1 = min(gray.shape[0], cy0 + qsize)
                roi = bw[cy0:cy1, cx0:cx1]
                dens = float(roi.mean()) if roi.size > 0 else 0.0
                if 45.0 <= dens <= 210.0 and dens > best_density:
                    best_density = dens
                    qx, qy = cx0, cy0

    return qx, qy, qsize, best_cluster


def _decode_image(img: np.ndarray) -> Optional[str]:
    """Decodifica el código QR BRP1 en una imagen escaneada con tolerancia a rotación, ruido y bajo contraste."""
    if img is None or getattr(img, "size", 0) == 0:
        return None
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    h, w = gray.shape[:2]
    if h < 50 or w < 50:
        return None

    det = cv2.QRCodeDetector()
    aruco_det = None
    if hasattr(cv2, "QRCodeDetectorAruco"):
        try:
            aruco_det = cv2.QRCodeDetectorAruco()
        except Exception:
            aruco_det = None

    def _extract_qr_string(detector: Any, candidate_img: np.ndarray) -> Optional[str]:
        try:
            val, _, _ = detector.detectAndDecode(candidate_img)
            if val and val.strip().startswith("BRP"):
                return val.strip()
        except cv2.error:
            pass
        return None

    def _shrink(z: np.ndarray, max_dim: int = 850) -> np.ndarray:
        zh, zw = z.shape[:2]
        if max(zh, zw) <= max_dim:
            return z
        sc = max_dim / float(max(zh, zw))
        return cv2.resize(z, (max(1, int(zw * sc)), max(1, int(zh * sc))), interpolation=cv2.INTER_AREA)

    # Fase 0: Si localizamos el cuadro exacto del QR por sus patrones `回`, intentar decodificarlo directo y con adelgazamiento
    cluster_info = _locate_qr_cluster(gray)
    if cluster_info is not None:
        qx, qy, qsize, _ = cluster_info
        pad_q = max(12, int(qsize * 0.18))
        y0 = max(0, qy - pad_q)
        y1 = min(h, qy + qsize + pad_q)
        x0 = max(0, qx - pad_q)
        x1 = min(w, qx + qsize + pad_q)
        qr_crop = gray[y0:y1, x0:x1]
        if qr_crop.size > 0:
            bordered = cv2.copyMakeBorder(qr_crop, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
            up2 = cv2.resize(bordered, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            kernel = np.ones((2, 2), np.uint8)
            thinned = cv2.dilate(up2, kernel, iterations=1)
            for cand_q in (bordered, up2, thinned):
                res = _extract_qr_string(det, cand_q)
                if res:
                    return res
                if aruco_det is not None:
                    res = _extract_qr_string(aruco_det, cand_q)
                    if res:
                        return res

    # Zonas prioritarias de búsqueda en la página 1 (Consentimiento Informado)
    zones = [
        # 1. Esquina superior derecha (ubicación estándar del sticker 30×20 mm)
        gray[: max(1, int(h * 0.45)), max(0, int(w * 0.45)) :],
        # 2. Esquina superior izquierda
        gray[: max(1, int(h * 0.45)), : max(1, int(w * 0.55))],
        # 3. Mitad inferior (zona de firma del trabajador)
        gray[max(0, int(h * 0.50)) :, :],
        # 4. Página completa
        gray,
    ]

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    # Fase 1: Búsqueda ultrarrápida en escala de grises cruda
    for zone in zones:
        if zone.size == 0:
            continue
        pad = max(14, int(min(zone.shape[:2]) * 0.04))
        padded = cv2.copyMakeBorder(zone, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        res = _extract_qr_string(det, padded)
        if res:
            return res
        if aruco_det is not None:
            res = _extract_qr_string(aruco_det, _shrink(padded, 900))
            if res:
                return res

    # Fase 2: Búsqueda con realce CLAHE / Otsu y orientaciones cardinales sobre zonas compactadas
    for zone in zones[:3]:
        if zone.size == 0:
            continue
        small_zone = _shrink(zone, 750)
        pad = max(16, int(min(small_zone.shape[:2]) * 0.05))
        padded = cv2.copyMakeBorder(small_zone, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)

        c_enh = clahe.apply(padded)
        _, otsu = cv2.threshold(c_enh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        for cand in (c_enh, otsu):
            for rot_code in (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE):
                test_img = cand if rot_code is None else cv2.rotate(cand, rot_code)
                res = _extract_qr_string(det, test_img)
                if res:
                    return res

    return None


def _read_sticker_printed_identity(gray: np.ndarray) -> Optional[Dict[str, str]]:
    """Capa 2 y 3: Localiza el sticker 30×20 mm por sus patrones `回`, enmascara la matriz QR
    y lee la FORMA, CÉDULA y NOMBRE impresos en el sticker, reconciliando contra TrabajadorNomina.
    """
    cluster_info = _locate_qr_cluster(gray)
    if cluster_info is None:
        return None

    qx, qy, qsize, cluster = cluster_info
    h, w = gray.shape[:2]

    # Recortar la región completa del sticker 30×20 mm alrededor del QR (13.8×13.8 mm)
    sx0 = max(0, qx - int(qsize * 0.18))
    sy0 = max(0, qy - int(qsize * 0.18))
    sx1 = min(w, qx + int(qsize * 2.68))
    sy1 = min(h, qy + int(qsize * 1.88))

    crop = gray[sy0:sy1, sx0:sx1].copy()
    if crop.size == 0:
        return None

    # Enmascarar en blanco la matriz QR para que el OCR solo vea el texto impreso del sticker
    mqx0 = max(0, qx - sx0)
    mqy0 = max(0, qy - sy0)
    mqx1 = min(crop.shape[1], qx - sx0 + qsize)
    mqy1 = min(crop.shape[0], qy - sy0 + qsize)
    crop[mqy0:mqy1, mqx0:mqx1] = 255

    # Si todo el resto del recorte está prácticamente en blanco (ej. test sintético solo con QR), abortar
    non_white_ratio = float(np.count_nonzero(crop < 200)) / float(crop.size)
    if non_white_ratio < 0.008:
        return None

    up = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    texts: List[str] = []
    try:
        from .ocr_engine import run_rapid_ocr

        r_txt = run_rapid_ocr(up)
        if r_txt:
            texts.append(r_txt)
    except Exception:
        pass

    try:
        import pytesseract

        t_txt = pytesseract.image_to_string(up, config="--oem 1 --psm 6")
        if t_txt:
            texts.append(t_txt)
    except Exception:
        pass

    # También invertir el cuadrante superior derecho del sticker (pastilla negra con texto blanco "FORMA A/B")
    badge_x0 = max(0, qx - sx0 + qsize - 4)
    badge_y0 = 0
    badge_x1 = crop.shape[1]
    badge_y1 = min(crop.shape[0], int((qy - sy0 + qsize) * 0.48))
    if badge_x1 > badge_x0 + 10 and badge_y1 > badge_y0 + 8:
        badge_inv = 255 - crop[badge_y0:badge_y1, badge_x0:badge_x1]
        badge_up = cv2.resize(badge_inv, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        try:
            from .ocr_engine import run_rapid_ocr

            b_txt = run_rapid_ocr(badge_up)
            if b_txt:
                texts.append(b_txt)
        except Exception:
            pass

    combined_raw = "\n".join(texts)
    if not combined_raw.strip():
        return None

    combined_upper = combined_raw.upper()

    # 1. Detectar FORMA (A o B) impresa en el sticker
    detected_forma = ""
    if re.search(r"F[O0I]?RMA\s*[B8]", combined_upper) or "RMAB" in combined_upper:
        detected_forma = "B"
    elif re.search(r"F[O0I]?RMA\s*A", combined_upper) or "RMAA" in combined_upper:
        detected_forma = "A"

    # 2. Extraer candidatos numéricos de Cédula (6 a 12 dígitos)
    digit_candidates: List[str] = []
    for line in combined_upper.splitlines():
        clean_line = re.sub(r"[.,\s]+(?=\d)", "", line)
        # Reemplazar confusiones comunes en líneas predominantemente numéricas
        for m in re.findall(r"\d{6,12}", clean_line):
            if m not in digit_candidates:
                digit_candidates.append(m)
            # Si tiene un '0' o '4' o '1' espurio al inicio de 11 dígitos, agregar sufijo de 10 dígitos
            if len(m) == 11 and m[1:] not in digit_candidates:
                digit_candidates.append(m[1:])
            if len(m) == 11 and m[:-1] not in digit_candidates:
                digit_candidates.append(m[:-1])
        for m in re.findall(r"\d{6,12}", line):
            if m not in digit_candidates:
                digit_candidates.append(m)

    # 3. Extraer tokens de Nombre Impreso (solo palabras en mayúsculas del sticker, excluyendo texto del consentimiento)
    name_tokens: List[str] = []
    clean_name_lines: List[str] = []
    for line in combined_raw.splitlines():
        s_line = line.strip()
        if not s_line:
            continue
        # Ignorar líneas que pertenecen al párrafo impreso del Consentimiento Informado (en minúsculas)
        lower_chars = sum(1 for ch in s_line if "a" <= ch <= "z")
        upper_chars = sum(1 for ch in s_line if "A" <= ch <= "Z")
        if lower_chars > upper_chars and lower_chars >= 5:
            continue
        u_line = s_line.upper()
        if any(
            kw in u_line
            for kw in ("CONSIENTE", "PSICOLOG", "RESOLUCION", "CUESTIONARIO", "CONSENTIMIENTO", "EVALUACION")
        ):
            continue
        words = [
            w
            for w in re.findall(r"[A-ZÑ]{3,}", u_line)
            if w not in _STOP_WORDS_STICKER
        ]
        if words:
            clean_name_lines.append(" ".join(words))
            for w in words:
                if w not in name_tokens:
                    name_tokens.append(w)

    # 4. Reconciliación contra TrabajadorNomina (Capa 3)
    records, by_cc = _get_nomina_Lookup()
    if by_cc:
        # 4a. Coincidencia exacta de cédula
        for cand_cc in digit_candidates:
            if cand_cc in by_cc:
                hit = dict(by_cc[cand_cc])
                if detected_forma in ("A", "B") and not hit.get("forma"):
                    hit["forma"] = detected_forma
                return normalize_ficha(hit)

        # 4b. Coincidencia combinada (Similitud de Cédula + Tokens del Nombre del Trabajador)
        best_nom: Optional[Dict[str, str]] = None
        best_score = 0.0

        for rec in records:
            nom_cc = rec.get("cedula", "")
            nom_name = rec.get("nombre", "").upper()
            nom_words = [w for w in re.findall(r"[A-ZÑ]{3,}", nom_name) if len(w) >= 3]

            # Similitud de cédula
            cc_sim = 0.0
            for cand_cc in digit_candidates:
                sim = difflib.SequenceMatcher(None, cand_cc, nom_cc).ratio()
                if abs(len(cand_cc) - len(nom_cc)) <= 2 and sim > cc_sim:
                    cc_sim = sim

            # Coincidencia de palabras del nombre
            matched_words = 0
            if nom_words and name_tokens:
                for nw in nom_words:
                    if any(
                        nw == ow or difflib.SequenceMatcher(None, nw, ow).ratio() >= 0.80
                        for ow in name_tokens
                    ):
                        matched_words += 1
            name_ratio = (matched_words / float(len(nom_words))) if nom_words else 0.0

            # Reglas de aceptación de alta confianza:
            # - Al menos 75% de similitud en cédula Y al menos 1 apellido/nombre coincide
            # - O al menos 65% de similitud en cédula Y al menos 2 palabras del nombre coinciden
            # - O al menos 3 palabras del nombre coinciden (>= 75% del nombre completo)
            accepted = False
            if cc_sim >= 0.75 and matched_words >= 1:
                accepted = True
            elif cc_sim >= 0.65 and matched_words >= 2:
                accepted = True
            elif matched_words >= 3 and name_ratio >= 0.74:
                accepted = True
            elif cc_sim >= 0.90 and len(nom_cc) >= 8:
                accepted = True

            if accepted:
                total_score = (cc_sim * 1.4) + name_ratio + (matched_words * 0.15)
                if total_score > best_score:
                    best_score = total_score
                    best_nom = rec

        if best_nom is not None:
            return normalize_ficha(best_nom)

    # 5. Fallback autónomo (cuando el trabajador no está en TrabajadorNomina pero el sticker es claro)
    valid_ccs = [c for c in digit_candidates if 6 <= len(c) <= 10]
    if valid_ccs and name_tokens and (len(cluster) >= 2 or detected_forma in ("A", "B")):
        ficha = empty_ficha()
        ficha["cedula"] = valid_ccs[0]
        ficha["nombre"] = " ".join(name_tokens[:5])
        ficha["forma"] = detected_forma or "A"
        return normalize_ficha(ficha)

    return None


def detect_page1_payload(img: np.ndarray) -> Optional[Dict[str, str]]:
    """Decodifica y estructura el payload BRP1 o lee el sticker 30×20 mm de la página 1."""
    raw = _decode_image(img)
    if raw:
        decoded = decode_payload(raw)
        if decoded:
            return _enrich_with_nomina(decoded)

    # Si la matriz 2D estaba fusionada por escaneo binario 1-bit Fax a 200 DPI, leer el sticker 30×20 mm
    return _read_sticker_printed_identity(
        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None and img.ndim == 3 else img
    )


def detect_identity_qr(classified: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Busca el sticker QR 30×20 mm exclusivamente en la página física 1 / consentimiento del cuadernillo.

    El sticker de 30×20 mm se pega únicamente en la portada (pág. 1).
    Si la clasificación semántica tiene dudas, se analiza la página con physical_page == 1
    o la primera página del lote.
    """
    candidate_pages: List[Dict[str, Any]] = []

    # Prioridad 1: Página clasificada como consentimiento o target_page == 1
    for item in classified or []:
        info = item.get("info") or {}
        if item.get("target_page") == 1 or info.get("kind") == "consentimiento":
            candidate_pages.append(item)
            break

    # Prioridad 2: Página con physical_page == 1 si no coincidió con prioridad 1
    if not candidate_pages:
        for item in classified or []:
            if item.get("physical_page") == 1:
                candidate_pages.append(item)
                break

    # Prioridad 3: Primera página del cuadernillo si aún no se determinó
    if not candidate_pages and classified:
        first = classified[0]
        # Solo si no está explícitamente clasificada como otra página numerada > 1
        if first.get("target_page") in (None, 1):
            candidate_pages.append(first)

    for page_item in candidate_pages:
        img = page_item.get("img")
        if img is not None:
            res = detect_page1_payload(img)
            if res:
                return res

    return None
