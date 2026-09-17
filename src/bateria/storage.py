"""Árbol de archivos por empresa y campaña de medición.

Fuente operativa de PDFs, recortes e informes:

    data/empresas/{nit}/mediciones/{codigo}/
        uploads/ pdf_ordenados/ crops/ informes/ custodia/
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Sequence, Union

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

CAMPAIGN_SUBDIRS: Sequence[str] = (
    "uploads",
    "pdf_ordenados",
    "crops",
    "informes",
    "custodia",
)


def sanitize_nit(nit: str) -> str:
    raw = (nit or "").strip()
    if "-" in raw:
        raw = raw.split("-", 1)[0]
    digits = re.sub(r"[^0-9]", "", raw)
    if not digits:
        raise ValueError("NIT vacío o inválido")
    return digits


def sanitize_codigo(codigo: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", (codigo or "").strip())
    if not cleaned:
        raise ValueError("codigo_campana vacío")
    return cleaned


def campaign_root(
    nit: str,
    codigo_campana: str,
    data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    base = Path(data_dir) if data_dir is not None else DATA_DIR
    return base / "empresas" / sanitize_nit(nit) / "mediciones" / sanitize_codigo(codigo_campana)


def ensure_campaign_dirs(
    nit: str,
    codigo_campana: str,
    data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    root = campaign_root(nit, codigo_campana, data_dir=data_dir)
    for sub in CAMPAIGN_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def save_upload(
    nit: str,
    codigo_campana: str,
    filename: str,
    content: bytes,
    data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    root = ensure_campaign_dirs(nit, codigo_campana, data_dir=data_dir)
    safe_name = os.path.basename(filename) or "upload.pdf"
    if not safe_name.lower().endswith(".pdf"):
        safe_name = f"{safe_name}.pdf"
    dest = root / "uploads" / safe_name
    dest.write_bytes(content)
    return dest
