"""Detección y decodificación ultra-robusta de QR de identidad en la página 1 del cuadernillo.

Optimizado específicamente para escáneres ADF (Fujitsu, Epson, Canon, HP) y etiquetas
térmicas 30×20 mm:
- Compensación de ángulo y desalineación por pegado manual (rotación 0°, 90°, 180°, 270° y sub-ángulos ±12°, ±6°).
- Detección multizona en Consentimiento Informado (encabezado derecho, encabezado izquierdo, zona de firma inferior).
- Ecualización CLAHE y binarización adaptativa contra bajo contraste térmico, papel traslúcido y sombras de rodillo.
- Margen de seguridad (quiet zone padding) para garantizar la lectura de patrones de búsqueda (finder patterns).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from .qr_codec import decode_payload


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

    detectors = []
    if hasattr(cv2, "QRCodeDetectorAruco"):
        try:
            detectors.append(cv2.QRCodeDetectorAruco())
        except Exception:
            pass
    detectors.append(cv2.QRCodeDetector())

    def _extract_qr_string(det: Any, candidate_img: np.ndarray) -> Optional[str]:
        try:
            val, _, _ = det.detectAndDecode(candidate_img)
            if val and val.strip().startswith("BRP"):
                return val.strip()
        except cv2.error:
            pass
        try:
            ok, multi, _, _ = det.detectAndDecodeMulti(candidate_img)
            if ok and multi is not None:
                for item in multi:
                    if item and item.strip().startswith("BRP"):
                        return item.strip()
        except (cv2.error, ValueError):
            pass
        return None

    # Zonas prioritarias de búsqueda en la página 1 (Consentimiento Informado)
    zones = [
        # 1. Esquina superior derecha (ubicación estándar recomendada del sticker 30×20 mm)
        gray[: max(1, int(h * 0.45)), max(0, int(w * 0.45)) :],
        # 2. Esquina superior izquierda
        gray[: max(1, int(h * 0.45)), : max(1, int(w * 0.55))],
        # 3. Franja superior completa (encabezado)
        gray[: max(1, int(h * 0.45)), :],
        # 4. Esquina inferior derecha (zona de firma del trabajador)
        gray[max(0, int(h * 0.55)) :, max(0, int(w * 0.45)) :],
        # 5. Esquina inferior izquierda (zona de firma)
        gray[max(0, int(h * 0.55)) :, : max(1, int(w * 0.55))],
        # 6. Franja inferior completa (pie de página / firmas)
        gray[max(0, int(h * 0.55)) :, :],
        # 7. Margen medio derecho
        gray[max(0, int(h * 0.35)) : min(h, int(h * 0.75)), max(0, int(w * 0.45)) :],
        # 8. Página completa
        gray,
    ]

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    # Fase 1: Búsqueda rápida con padding en escala de grises cruda
    for zone in zones:
        if zone.size == 0:
            continue
        pad = max(16, int(min(zone.shape[:2]) * 0.04))
        padded = cv2.copyMakeBorder(zone, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        for det in detectors:
            res = _extract_qr_string(det, padded)
            if res:
                return res

    # Fase 2: Búsqueda exhaustiva con filtros de realce térmico, rotación y deskew
    for zone_idx, zone in enumerate(zones):
        if zone.size == 0:
            continue
        pad = max(20, int(min(zone.shape[:2]) * 0.05))
        padded = cv2.copyMakeBorder(zone, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)

        # 1. CLAHE (compensa bajo contraste e iluminación heterogénea)
        c_enh = clahe.apply(padded)
        # 2. Binarización Otsu
        _, otsu = cv2.threshold(c_enh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 3. Binarización adaptativa gaussiana (elimina sombras y trasluz de fondo)
        adapt = cv2.adaptiveThreshold(padded, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 8)

        candidates = [c_enh, otsu, adapt]

        for cand in candidates:
            # 4 orientaciones cardinales (0°, 90°, 180°, 270°)
            for rot_code in [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]:
                test_img = cand if rot_code is None else cv2.rotate(cand, rot_code)
                for det in detectors:
                    res = _extract_qr_string(det, test_img)
                    if res:
                        return res

            # Corrección de inclinación manual (deskew ±12°, ±6°) en zonas principales
            if zone_idx < 4:
                cw, ch = cand.shape[1], cand.shape[0]
                center = (cw / 2.0, ch / 2.0)
                for angle in [-12, 12, -6, 6]:
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    skewed = cv2.warpAffine(cand, M, (cw, ch), borderValue=255)
                    for det in detectors:
                        res = _extract_qr_string(det, skewed)
                        if res:
                            return res

    return None


def detect_page1_payload(img: np.ndarray) -> Optional[Dict[str, str]]:
    """Decodifica y estructura el payload BRP1 a partir de la imagen de la página 1."""
    raw = _decode_image(img)
    return decode_payload(raw)


def detect_identity_qr(classified: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Busca BRP1 exclusivamente en la página física 1 / consentimiento del cuadernillo.

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
