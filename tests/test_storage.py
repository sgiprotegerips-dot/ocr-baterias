"""Tests del árbol de almacenamiento por empresa y campaña."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.bateria.storage import (
    campaign_root,
    ensure_campaign_dirs,
    save_upload,
    sanitize_codigo,
    sanitize_nit,
)


def test_sanitize_nit_strips_punctuation():
    assert sanitize_nit("900.548.123-4") == "900548123"
    assert sanitize_nit("900548123") == "900548123"
    print(" test_sanitize_nit_strips_punctuation PASSED")


def test_campaign_root_nests_empresa_and_codigo():
    with tempfile.TemporaryDirectory() as tmp:
        root = campaign_root("900.548.123", "MED-2026-001", data_dir=Path(tmp))
        assert root == Path(tmp) / "empresas" / "900548123" / "mediciones" / "MED-2026-001"
    print(" test_campaign_root_nests_empresa_and_codigo PASSED")


def test_ensure_campaign_dirs_creates_standard_subfolders():
    with tempfile.TemporaryDirectory() as tmp:
        root = ensure_campaign_dirs("900548123", "MED-2026-001", data_dir=Path(tmp))
        for sub in ("uploads", "pdf_ordenados", "crops", "informes", "custodia"):
            assert (root / sub).is_dir()
    print(" test_ensure_campaign_dirs_creates_standard_subfolders PASSED")


def test_save_upload_writes_pdf_under_campaign_uploads():
    with tempfile.TemporaryDirectory() as tmp:
        dest = save_upload(
            "900548123",
            "MED-2026-001",
            "lote/cuadernillo_01.pdf",
            b"%PDF-1.4 test",
            data_dir=Path(tmp),
        )
        assert dest.name == "cuadernillo_01.pdf"
        assert dest.parent.name == "uploads"
        assert dest.read_bytes() == b"%PDF-1.4 test"
    print(" test_save_upload_writes_pdf_under_campaign_uploads PASSED")


def test_sanitize_codigo_rejects_empty():
    try:
        sanitize_codigo("   ")
        raise AssertionError("sanitize_codigo debió rechazar código vacío")
    except ValueError:
        pass
    print(" test_sanitize_codigo_rejects_empty PASSED")


if __name__ == "__main__":
    test_sanitize_nit_strips_punctuation()
    test_campaign_root_nests_empresa_and_codigo()
    test_ensure_campaign_dirs_creates_standard_subfolders()
    test_save_upload_writes_pdf_under_campaign_uploads()
    test_sanitize_codigo_rejects_empty()
    print("ALL STORAGE TESTS PASSED")
