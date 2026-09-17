from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


OPCIONES_5 = {
    0: "Siempre",
    1: "Casi siempre",
    2: "Algunas veces",
    3: "Casi nunca",
    4: "Nunca",
}

OPCIONES_4 = {
    0: "Siempre",
    1: "Casi siempre",
    2: "A veces",
    3: "Nunca",
}


def export_workbook(results: list[dict], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    ws = wb.active
    ws.title = "Resumen"
    headers = [
        "archivo",
        "sha256",
        "forma",
        "id_documento",
        "nombre",
        "cargo",
        "fecha",
        "dependencia",
        "n_paginas",
        "intra_leidos",
        "intra_esperados",
        "extra_leidos",
        "estres_leidos",
        "n_ambiguos",
        "intra_T",
        "intra_nivel",
        "extra_T",
        "extra_nivel",
        "estres_T",
        "estres_nivel",
        "general_T",
        "general_nivel",
    ]
    ws.append(headers)
    for r in results:
        if r.get("error"):
            ws.append([r.get("archivo"), r.get("sha256"), r.get("error")])
            continue
        q = r.get("calidad") or {}
        sc = r.get("scoring") or r.get("scoring_villalobos") or {}
        n_amb = 0
        for a in r.get("ambiguos") or []:
            if isinstance(a, dict):
                if a.get("decision") is None:
                    n_amb += 1
            else:
                n_amb += 1

        intra_leidos = q.get("intra_leidos", len(r.get("intra") or {}))
        intra_esp = q.get("intra_esperados", (97 if r.get("forma") == "B" else 123))
        extra_leidos = q.get("extra_leidos", len(r.get("extra") or {}))
        estres_leidos = q.get("estres_leidos", len(r.get("estres") or {}))

        ws.append(
            [
                r.get("archivo"),
                r.get("sha256"),
                r.get("forma"),
                r.get("id_documento"),
                (r.get("identidad") or {}).get("nombre"),
                (r.get("identidad") or {}).get("cargo"),
                (r.get("identidad") or {}).get("fecha"),
                (r.get("identidad") or {}).get("dependencia"),
                r.get("n_paginas"),
                intra_leidos,
                intra_esp,
                extra_leidos,
                estres_leidos,
                n_amb,
                (sc.get("intra") or {}).get("total", {}).get("transformado"),
                (sc.get("intra") or {}).get("total", {}).get("nivel"),
                (sc.get("extra") or {}).get("total", {}).get("transformado"),
                (sc.get("extra") or {}).get("total", {}).get("nivel"),
                (sc.get("estres") or {}).get("total", {}).get("transformado"),
                (sc.get("estres") or {}).get("total", {}).get("nivel"),
                (sc.get("general") or {}).get("transformado"),
                (sc.get("general") or {}).get("nivel"),
            ]
        )
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")

    wi = wb.create_sheet("Items_intra")
    wi.append(["archivo", "item", "codigo", "opcion_texto", "faltante"])
    for cell in wi[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")
    for r in results:
        if r.get("error"):
            continue
        answers = {int(k): v for k, v in (r.get("intra") or {}).items()}
        n = 123 if r.get("forma") != "B" else 97
        for i in range(1, n + 1):
            val = answers.get(i)
            txt = OPCIONES_5.get(val, "En blanco" if val is None else str(val))
            wi.append([r.get("archivo"), i, val, txt, i not in answers])

    we = wb.create_sheet("Items_extra")
    we.append(["archivo", "item", "codigo", "opcion_texto", "faltante"])
    for cell in we[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")
    for r in results:
        if r.get("error"):
            continue
        answers = {int(k): v for k, v in (r.get("extra") or {}).items()}
        for i in range(1, 32):
            val = answers.get(i)
            txt = OPCIONES_5.get(val, "En blanco" if val is None else str(val))
            we.append([r.get("archivo"), i, val, txt, i not in answers])

    ws2 = wb.create_sheet("Items_estres")
    ws2.append(["archivo", "item", "codigo", "opcion_texto", "faltante"])
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")
    for r in results:
        if r.get("error"):
            continue
        answers = {int(k): v for k, v in (r.get("estres") or {}).items()}
        for i in range(1, 32):
            val = answers.get(i)
            txt = OPCIONES_4.get(val, "En blanco" if val is None else str(val))
            ws2.append([r.get("archivo"), i, val, txt, i not in answers])

    wd = wb.create_sheet("Dimensiones")
    wd.append(["archivo", "bloque", "dimension", "dominio", "n_resp", "n_esp", "T", "nivel", "incompleta"])
    for cell in wd[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")
    for r in results:
        if r.get("error"):
            continue
        sc = r.get("scoring") or r.get("scoring_villalobos") or {}
        for dim in (sc.get("intra") or {}).get("dimensiones") or []:
            wd.append(
                [
                    r.get("archivo"),
                    "intra",
                    dim.get("nombre"),
                    dim.get("dominio"),
                    dim.get("n_respondidos"),
                    dim.get("n_esperados"),
                    dim.get("transformado"),
                    dim.get("nivel"),
                    dim.get("incompleta"),
                ]
            )
        for dim in (sc.get("extra") or {}).get("dimensiones") or []:
            wd.append(
                [
                    r.get("archivo"),
                    "extra",
                    dim.get("nombre"),
                    dim.get("dominio"),
                    dim.get("n_respondidos"),
                    dim.get("n_esperados"),
                    dim.get("transformado"),
                    dim.get("nivel"),
                    dim.get("incompleta"),
                ]
            )

    wp = wb.create_sheet("Paginas")
    wp.append(["archivo", "scan_index", "kind", "pagina_fisica", "forma", "n_likert_rows"])
    for cell in wp[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F766E")
    for r in results:
        if r.get("error"):
            continue
        for p in r.get("paginas") or []:
            wp.append([r.get("archivo"), p.get("scan_index"), p.get("kind"), p.get("physical_page") or p.get("printed_page"), p.get("forma"), p.get("n_likert_rows")])

    # Auto-ajustar anchos de columna en todas las hojas
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = min(len(val_str), 45)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 10)

    wb.save(path)
    return path
