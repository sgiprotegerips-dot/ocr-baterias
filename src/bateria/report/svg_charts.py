"""Barras SVG imprimibles (sin JavaScript ni CDN)."""

from __future__ import annotations

from typing import Dict, Mapping

NIVELES = [
    ("Sin riesgo", "#047857"),
    ("Riesgo bajo", "#1d4ed8"),
    ("Riesgo medio", "#b45309"),
    ("Riesgo alto", "#c2410c"),
    ("Riesgo muy alto", "#b91c1c"),
]


def _pct(dist: Mapping, nivel: str) -> float:
    val = dist.get(nivel)
    if isinstance(val, dict):
        return float(val.get("porcentaje") or 0)
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def stacked_bar(dist: Mapping, width: int = 520, height: int = 22) -> str:
    parts = []
    x = 0.0
    for nivel, color in NIVELES:
        p = max(0.0, _pct(dist, nivel))
        w = round(width * p / 100.0, 2)
        if w <= 0:
            continue
        parts.append(
            f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{height}" fill="{color}"/>'
        )
        x += w
    return (
        f'<svg class="bar-svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#e2e8f0"/>'
        f"{''.join(parts)}</svg>"
    )


def legend_html() -> str:
    chips = "".join(
        f'<span class="leg-chip"><i style="background:{c}"></i>{n}</span>'
        for n, c in NIVELES
    )
    return f'<div class="bar-legend">{chips}</div>'


def hbar_critico(items: Dict[str, float], width: int = 420, row_h: int = 18, max_n: int = 8) -> str:
    ranked = sorted(items.items(), key=lambda kv: kv[1], reverse=True)[:max_n]
    if not ranked:
        return '<p class="muted">Sin dimensiones críticas en esta medición.</p>'
    top = max(v for _, v in ranked) or 100
    h = 8 + len(ranked) * (row_h + 6)
    rows = []
    y = 4
    for name, val in ranked:
        bw = round((width - 180) * (val / top), 2) if top else 0
        label = name if len(name) <= 42 else name[:40] + "…"
        rows.append(
            f'<text x="0" y="{y + 13}" font-size="8" fill="#334155">{_esc(label)}</text>'
            f'<rect x="180" y="{y + 3}" width="{width - 180}" height="12" fill="#e2e8f0"/>'
            f'<rect x="180" y="{y + 3}" width="{bw}" height="12" fill="#b91c1c"/>'
            f'<text x="{width - 2}" y="{y + 13}" font-size="8" fill="#7f1d1d" text-anchor="end">{val:.1f}%</text>'
        )
        y += row_h + 6
    return (
        f'<svg class="hbar-svg" width="{width}" height="{h}" '
        f'viewBox="0 0 {width} {h}" xmlns="http://www.w3.org/2000/svg">{"".join(rows)}</svg>'
    )


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
