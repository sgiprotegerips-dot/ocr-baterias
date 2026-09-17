from __future__ import annotations

import argparse
from pathlib import Path

from .export import export_workbook
from .pipeline import process_folder, process_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR/OMR Batería de Riesgo Psicosocial")
    parser.add_argument("entrada", type=Path, help="PDF o carpeta de PDFs")
    parser.add_argument("-o", "--out", type=Path, default=Path("out"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.entrada.is_dir():
        results = process_folder(args.entrada, args.out / "json")
    else:
        results = [process_pdf(args.entrada, out_dir=args.out / "json")]
    xlsx = export_workbook(results, args.out / "respuestas.xlsx")
    print(f"Procesados: {len(results)}")
    print(f"Excel: {xlsx}")
    for r in results:
        q = r.get("calidad") or {}
        print(
            f"  {r.get('archivo')} forma={r.get('forma')} "
            f"intra={q.get('intra_leidos')}/{q.get('intra_esperados')} "
            f"extra={q.get('extra_leidos')} estres={q.get('estres_leidos')} "
            f"ambiguos={len(r.get('ambiguos') or [])}"
        )


if __name__ == "__main__":
    main()
