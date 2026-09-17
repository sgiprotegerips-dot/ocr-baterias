"""Detección de QR de identidad únicamente en la página 1 del cuadernillo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from .qr_codec import decode_payload


def _decode_image(img: np.ndarray) -> Optional[str]:
    if img is None or getattr(img, "size", 0) == 0:
        return None
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    detector = cv2.QRCodeDetector()
    variants = [gray]
    h, w = gray.shape[:2]
    # Esquina superior (sitio típico del sticker en el consentimiento)
    variants.append(gray[: max(1, int(h * 0.45)), :])
    variants.append(gray[: max(1, int(h * 0.45)), max(0, int(w * 0.55)) :])
    # Umbral por si el térmico queda gris
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(bw)

    for candidate in variants:
        if candidate.size == 0:
            continue
        try:
            data, points, _ = detector.detectAndDecode(candidate)
        except cv2.error:
            continue
        if data:
            return data
        try:
            ok, decoded, _pts, _ = detector.detectAndDecodeMulti(candidate)
        except (cv2.error, ValueError):
            ok, decoded = False, None
        if ok and decoded is not None:
            for item in decoded:
                if item:
                    return item
    return None


def detect_page1_payload(img: np.ndarray) -> Optional[Dict[str, str]]:
    raw = _decode_image(img)
    return decode_payload(raw)


def detect_identity_qr(classified: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Busca BRP1 solo en la página física 1 / consentimiento.

    El sticker de 30×20 mm se pega únicamente en la portada (pág. 1).
    """
    page1 = None
    for item in classified or []:
        info = item.get("info") or {}
        if item.get("target_page") == 1 or info.get("kind") == "consentimiento":
            page1 = item
            break
    if page1 is None:
        return None
    return detect_page1_payload(page1.get("img"))
