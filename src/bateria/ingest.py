from __future__ import annotations

import hashlib
from pathlib import Path

import fitz
import numpy as np

DPI = 200


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _page_native_long_px(page: fitz.Page) -> int:
    """Detecta la resolución nativa (lado largo en píxeles) de la imagen escaneada en la página."""
    try:
        imgs = page.get_images(full=True)
        if imgs:
            return max(max(int(im[2]), int(im[3])) for im in imgs)
    except Exception:
        pass
    return 0


def pdf_to_images(path: Path, dpi: int = DPI) -> list[np.ndarray]:
    """Renderiza las páginas del PDF adaptándose automáticamente a escaneos de 200 DPI y 300 DPI.

    - Normaliza el factor de escala respecto al tamaño físico de la página PDF para que escáneres
      que escriben cajas `page.rect` no estándar a 200 o 300 DPI mantengan geometría consistente.
    - En las páginas candidatas a portada/consentimiento (primera y última del flujo ADF), si el
      escaneo nativo embebido es de 300 DPI (>= 2800 px de alto), preserva los 300 DPI nativos
      para maximizar la nitidez de los módulos del código QR de 30×20 mm.
    """
    doc = fitz.open(path)
    n_pages = len(doc)
    images = []

    for idx, page in enumerate(doc):
        effective_dpi = dpi
        # Preservar 300 DPI nativos en portada/consentimiento (inicio o fin de lote ADF)
        if idx in (0, 1, n_pages - 1, n_pages - 2):
            native_px = _page_native_long_px(page)
            if native_px >= 2800:
                effective_dpi = max(dpi, 300)

        long_pt = max(float(page.rect.width), float(page.rect.height))
        if long_pt > 100.0:
            # Una hoja Carta/Oficio estándar mide ~792 pt (11 pulgadas) de alto.
            # Escalar hacia (effective_dpi * 11.0) px garantiza ~2200 px a 200 DPI y ~3300 px a 300 DPI
            # sin importar si el escáner declaró 72 pt/in o dimensiones crudas en el PDF.
            target_long_px = (effective_dpi / 200.0) * 2190.0
            zoom = target_long_px / long_pt
        else:
            zoom = effective_dpi / 72.0

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            arr = arr[:, :, :3]
        images.append(arr.copy())

    doc.close()
    return images
