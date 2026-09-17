"""Compatibilidad: el generador HTML imprimible vive en src.bateria.report."""

from __future__ import annotations

from typing import Any, Dict

from .report.builder import generate_printable_report_html as _generate


def generate_printable_report_html(report_data: Dict[str, Any]) -> str:
    return _generate(report_data)
