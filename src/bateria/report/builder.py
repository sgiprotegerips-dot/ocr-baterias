"""Ensambla el visor HTML imprimible y numera las hojas."""

from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

from .css import REPORT_CSS
from .pages import Page, assemble_content_pages, esc


def _ctx(report_data: Dict[str, Any]) -> Dict[str, Any]:
    empresa = report_data.get("empresa") or {}
    medicion = report_data.get("medicion") or {}
    psicologa = report_data.get("psicologa") or {}
    hash_sha = (
        report_data.get("hash_sha256")
        or medicion.get("hash_integridad_sha256")
        or "BORRADOR_AUDITORIA_PRELIMINAR"
    )
    is_sealed = bool(
        medicion.get("estado") == "cerrada"
        or report_data.get("sellado_inmutable")
        or (hash_sha != "BORRADOR_AUDITORIA_PRELIMINAR" and len(str(hash_sha)) == 64)
    )
    return {
        "empresa": empresa,
        "medicion": medicion,
        "psicologa": psicologa,
        "baremos": report_data.get("baremos_consolidados") or {},
        "socio": report_data.get("resumen_sociodemografico") or {},
        "prioritarias": report_data.get("dimensiones_prioritarias") or [],
        "cruces": report_data.get("cruces") or {},
        "conclusiones": report_data.get("conclusiones")
        or report_data.get("conclusiones_sugeridas")
        or "",
        "recomendaciones": report_data.get("recomendaciones")
        or report_data.get("recomendaciones_sugeridas")
        or "",
        "hash_sha": hash_sha,
        "is_sealed": is_sealed,
        "total_evaluados": report_data.get("total_evaluados") or 0,
    }


def _toc_page(entries: List[Tuple[int, str]]) -> str:
    rows = "".join(
        f'<tr><td>{html.escape(title)}</td><td class="num">{num}</td></tr>' for num, title in entries
    )
    return f"""
    <div class="section-hdr">Tabla de contenido</div>
    <p class="muted">Documento carta, visor HTML imprimible. Use «Imprimir / Guardar en PDF» del navegador.</p>
    <table class="toc-table" style="width:100%;border-collapse:collapse;margin-top:10px">{rows}</table>
    """


def _wrap(inner: str, ctx: Dict[str, Any], page_no: int, total: int, running: str) -> str:
    e, m = ctx["empresa"], ctx["medicion"]
    return f"""
    <div class="report-page">
      <header class="header-box">
        <div class="ips-data">
          <h2>PROTEGER I.P.S. S.A.S.</h2>
          <p>Evaluación de riesgo psicosocial · {esc(e.get("razon_social") or "Empresa")}</p>
        </div>
        <div class="title-data">
          <h1>{esc(running)}</h1>
          <span>{esc(m.get("codigo_campana") or "MED")}</span>
        </div>
      </header>
      {inner}
      <div class="page-footer">
        <span>PROTEGER I.P.S. S.A.S. · Informe diagnóstico psicosocial</span>
        <span>Página {page_no} de {total}</span>
        <span>{esc(str(ctx["hash_sha"])[:12])}</span>
      </div>
    </div>"""


def generate_printable_report_html(report_data: Dict[str, Any]) -> str:
    ctx = _ctx(report_data)
    content = assemble_content_pages(ctx)
    # Insertar TOC como tercera hoja (después de portada y control).
    toc_placeholder: Page = ("Tabla de contenido", "")
    ordered: List[Page] = content[:2] + [toc_placeholder] + content[2:]
    total = len(ordered)
    toc_entries = [(i, title) for i, (title, _) in enumerate(ordered, start=1)]
    ordered[2] = ("Tabla de contenido", _toc_page(toc_entries))

    sheets = []
    for i, (title, inner) in enumerate(ordered, start=1):
        running = "INFORME DIAGNÓSTICO PSICOSOCIAL" if i <= 2 else title
        sheets.append(_wrap(inner, ctx, i, total, running))

    e = ctx["empresa"]
    sealed_cls = "sealed" if ctx["is_sealed"] else "draft"
    sealed_lbl = (
        "[OFICIAL SELLADO · CUSTODIA 20 AÑOS]" if ctx["is_sealed"] else "[BORRADOR AUDITORÍA CLÍNICA]"
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Informe Diagnóstico SST · {esc(e.get("razon_social") or "Empresa")}</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
  <div class="print-toolbar">
    <div class="toolbar-info">
      <span class="toolbar-brand">PROTEGER I.P.S. · SST</span>
      <span class="toolbar-badge {sealed_cls}">{sealed_lbl}</span>
      <span class="toolbar-tip">Resolución 2764 de 2022 · {total} páginas carta · visor imprimible</span>
    </div>
    <div class="toolbar-actions">
      <button type="button" class="btn-print-primary" onclick="window.print()">Imprimir / Guardar en PDF</button>
      <a href="javascript:window.close()" class="btn-print-ghost">Cerrar</a>
    </div>
  </div>
  {''.join(sheets)}
</body>
</html>"""
