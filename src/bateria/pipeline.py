from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path

import cv2

import fitz

from .classify import classify_page, get_expected_items
from .ingest import pdf_to_images, sha256_file
from .ocr_fields import extract_consentimiento, extract_id_and_name, extract_cover_date
from .omr import read_likert_tables
from .qr_codec import identity_from_ficha
from .qr_detect import detect_identity_qr
from .scoring import score_persona


def generate_ordered_pdf(pdf_path: Path, pages_info: list[dict], dest_path: Path) -> Path:
    """Genera un archivo PDF físico con las 24 páginas en orden físico secuencial (1..24).

    Corrige rotaciones si alguna página vino invertida (180°).
    """
    doc_in = fitz.open(pdf_path)
    doc_out = fitz.open()

    phys_map: dict[int, dict] = {}
    for p in pages_info:
        phys = p.get("physical_page")
        if phys and 1 <= phys <= 24 and phys not in phys_map:
            phys_map[phys] = p

    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    for p_num in range(1, 25):
        info = phys_map.get(p_num)
        if info:
            s_idx = info.get("scan_index", p_num)
            rot = info.get("rot_angle", 0)
        else:
            s_idx = p_num
            rot = 0

        if 1 <= s_idx <= len(doc_in):
            doc_out.insert_pdf(doc_in, from_page=s_idx - 1, to_page=s_idx - 1)
            if rot != 0:
                page = doc_out[-1]
                page.set_rotation((page.rotation + rot) % 360)

    doc_out.save(dest_path)
    doc_out.close()
    doc_in.close()
    return dest_path


def _bucket(kind: str) -> str | None:
    if kind.startswith("intra"):
        return "intra"
    if kind.startswith("extra"):
        return "extra"
    if kind.startswith("estres"):
        return "estres"
    return None


def process_pdf(path: Path, out_dir: Path | None = None) -> dict:
    path = Path(path)
    raw_images = pdf_to_images(path)
    crops_dir = (Path(out_dir) / "crops") if out_dir else None
    if crops_dir:
        crops_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clasificación paralela ultra rápida y detección de páginas impresas
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, max(1, len(raw_images)))) as ex:
            infos = list(ex.map(classify_page, raw_images))
    except (RuntimeError, Exception):
        infos = [classify_page(im) for im in raw_images]

    classified: list[dict] = []
    detected_forma = None

    for idx, (img, info) in enumerate(zip(raw_images, infos), start=1):
        if info.get("forma") == "B":
            detected_forma = "B"
        elif info.get("forma") == "A" and detected_forma is None:
            detected_forma = "A"
        upright = info.get("upright_img") if info.get("upright_img") is not None else img
        classified.append({"scan_index": idx, "img": upright, "info": info})

    forma = detected_forma or "A"

    # 2. Reordenamiento físico ADF (si las páginas 13..24 vinieron en reversa u orden alterno)
    # Asignar página física 1..24 asegurando que no haya colisiones
    used_pages: set[int] = set()
    for item in classified:
        p_no = item["info"].get("printed_page")
        if p_no and 1 <= p_no <= 24 and p_no not in used_pages:
            item["target_page"] = p_no
            used_pages.add(p_no)
        else:
            item["target_page"] = None

    # Mapeo secundario basado en 'kind' para páginas clave no detectadas por footer
    KIND_DEFAULTS = {
        "consentimiento": 1,
        "intra_portada": 6,
        "intra_instrucciones": 7,
        "extra_portada": 18,
        "extra_instrucciones": 19,
        "estres_portada": 23,
        "estres_items": 24,
    }
    for item in classified:
        if item["target_page"] is None:
            k = item["info"].get("kind")
            cand = KIND_DEFAULTS.get(k)
            if cand and cand not in used_pages:
                item["target_page"] = cand
                used_pages.add(cand)

    # Asignar páginas no determinadas por proximidad
    for item in classified:
        if item["target_page"] is None:
            s_idx = item["scan_index"]
            if s_idx <= 24 and s_idx not in used_pages:
                item["target_page"] = s_idx
                used_pages.add(s_idx)
            else:
                for cand in range(1, 25):
                    if cand not in used_pages:
                        item["target_page"] = cand
                        used_pages.add(cand)
                        break

    # Ordenar estrictamente por página física (1..24)
    classified.sort(key=lambda x: x["target_page"] or 999)

    pages = []
    intra: dict[int, int | None] = {}
    extra: dict[int, int | None] = {}
    estres: dict[int, int | None] = {}
    intra_meta: dict[int, dict] = {}
    extra_meta: dict[int, dict] = {}
    estres_meta: dict[int, dict] = {}

    identity = {
        "nombre": "",
        "cargo": "",
        "fecha": "",
        "dependencia": "",
        "id_documento": None,
        "fuente": "ocr",
        "ficha": {},
    }
    ambiguos: list[dict] = []

    # 2b. QR de identidad solo en página 1 (sticker 30×20 mm en el consentimiento)
    qr_hit = detect_identity_qr(classified)
    if qr_hit:
        qr_ident = identity_from_ficha(qr_hit)
        for k in ("nombre", "cargo", "dependencia", "fecha", "id_documento"):
            if qr_ident.get(k):
                identity[k] = qr_ident[k]
        identity["fuente"] = "qr"
        identity["ficha"] = qr_ident.get("ficha") or qr_hit
        if qr_hit.get("forma") in ("A", "B"):
            forma = qr_hit["forma"]

    # 3. Pre-procesamiento OMR paralelo de todas las tablas Likert del cuadernillo
    likert_tasks = []
    for item_data in classified:
        p_no = item_data["target_page"]
        kind = item_data["info"]["kind"]
        is_item_page = p_no in (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 24) or kind.endswith("items")
        if is_item_page and p_no not in (1, 2, 3, 4, 5, 6, 7, 18, 19, 23):
            n_choices = 4 if p_no == 24 or kind.startswith("estres") else 5
            expected = get_expected_items(p_no, forma=forma)
            likert_tasks.append((p_no, item_data["img"], n_choices, expected))

    likert_results: dict[int, list] = {}
    if likert_tasks:
        def _read_table_task(t):
            p, im, nc, exp = t
            return p, read_likert_tables(im, n_choices=nc, expected_items=exp)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(likert_tasks))) as ex:
                for p_no_res, rows_res in ex.map(_read_table_task, likert_tasks):
                    likert_results[p_no_res] = rows_res
        except (RuntimeError, Exception):
            for t in likert_tasks:
                p_no_res, rows_res = _read_table_task(t)
                likert_results[p_no_res] = rows_res

    # 4. Procesamiento ordenado página por página
    for item_data in classified:
        p_no = item_data["target_page"]
        img = item_data["img"]
        info = item_data["info"]
        kind = info["kind"]

        # Extracción de Consentimiento Informado (Pág 1)
        if kind == "consentimiento" or p_no == 1:
            cons = extract_consentimiento(img)
            for k in ("nombre", "cargo", "fecha", "dependencia"):
                if cons.get(k) and not identity.get(k):
                    identity[k] = cons[k]
            if cons.get("id_documento") and not identity.get("id_documento"):
                identity["id_documento"] = cons["id_documento"]

        # Extracción de Cédula / ID y Fecha en portadas o ficha (1, 2, 6, 18, 23) como fallback
        if p_no in (1, 2, 6, 18, 23):
            if not identity.get("id_documento"):
                ident = extract_id_and_name(img)
                if ident.get("id_documento"):
                    identity["id_documento"] = ident["id_documento"]
            if not identity.get("fecha") and p_no in (6, 18, 23):
                cov_date = extract_cover_date(img)
                if cov_date:
                    identity["fecha"] = cov_date

        # Filas OMR Likert pre-procesadas
        rows = likert_results.get(p_no, [])
        if rows:
            bucket = _bucket(kind)
            if not bucket:
                if 8 <= p_no <= 17:
                    bucket = "intra"
                elif 20 <= p_no <= 22:
                    bucket = "extra"
                elif p_no == 24:
                    bucket = "estres"

            target = {"intra": intra, "extra": extra, "estres": estres}.get(bucket)
            meta = {"intra": intra_meta, "extra": extra_meta, "estres": estres_meta}.get(bucket)

            if target is not None:
                for row in rows:
                    item_idx = row.get("item")
                    if item_idx is None:
                        continue

                    if row.get("status") == "ambiguo":
                        crop_rel = None
                        bbox = row.get("row_bbox")
                        if bbox and crops_dir is not None:
                            x, y, w, h = bbox
                            pad = 8
                            y0, y1 = max(0, y - pad), min(img.shape[0], y + h + pad)
                            x0, x1 = max(0, x - pad), min(img.shape[1], x + w + pad)
                            crop = img[y0:y1, x0:x1]
                            fname = f"{path.stem}_{bucket}_{item_idx:03d}.jpg"
                            cv2.imwrite(str(crops_dir / fname), crop)
                            crop_rel = f"crops/{fname}"

                        labels = (
                            ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"]
                            if row.get("n_choices", 5) == 5
                            else ["Siempre", "Casi siempre", "A veces", "Nunca"]
                        )
                        ambiguos.append(
                            {
                                "id": f"{bucket[0].upper()}{item_idx:03d}",
                                "bloque": bucket,
                                "item": item_idx,
                                "pagina": p_no,
                                "fills": row.get("fills"),
                                "marcadas": row.get("marked") or [],
                                "etiquetas": labels,
                                "crop": crop_rel,
                                "decision": None,
                                "decidido_por": None,
                            }
                        )
                        if meta is not None:
                            meta[item_idx] = row
                        continue

                    if row.get("choice_index") is not None:
                        target[item_idx] = row.get("choice_index")
                        if meta is not None:
                            meta[item_idx] = row

        pages.append(
            {
                "scan_index": item_data["scan_index"],
                "physical_page": p_no,
                "kind": kind,
                "forma": forma,
                "rot_angle": info.get("rot_angle", 0),
                "n_likert_rows": len(rows),
                "ocr_preview": info.get("ocr_preview"),
            }
        )

    expected_intra = 123 if forma != "B" else 97
    amb_intra = {a["item"] for a in ambiguos if a["bloque"] == "intra"}
    amb_extra = {a["item"] for a in ambiguos if a["bloque"] == "extra"}
    amb_estres = {a["item"] for a in ambiguos if a["bloque"] == "estres"}

    # Determinar si aplican las secciones opcionales (clientes y jefatura)
    p16_items = list(range(106, 115)) if forma != "B" else list(range(89, 98))
    p17_items = list(range(115, 124)) if forma != "B" else []

    has_any_intra = (len(intra) + len(amb_intra)) > 0
    if has_any_intra:
        aplica_clientes = any(i in intra or i in amb_intra for i in p16_items)
        aplica_jefatura = any(i in intra or i in amb_intra for i in p17_items) if p17_items else False
    else:
        aplica_clientes = True
        aplica_jefatura = True if forma != "B" else False

    # Los ítems opcionales no respondidos NO se consideran faltantes
    items_ignorar = set()
    if not aplica_clientes:
        items_ignorar.update(p16_items)
    if not aplica_jefatura:
        items_ignorar.update(p17_items)

    missing_intra = [n for n in range(1, expected_intra + 1) if n not in intra and n not in amb_intra and n not in items_ignorar]
    missing_extra = [n for n in range(1, 32) if n not in extra and n not in amb_extra]
    missing_estres = [n for n in range(1, 32) if n not in estres and n not in amb_estres]

    real_expected_intra = expected_intra - len(items_ignorar)

    scoring = score_persona(
        forma,
        intra,
        extra,
        estres,
        grupo="jefes" if forma != "B" else "auxiliares",
    )

    ordered_pdf_name = f"{path.stem}_ordenado.pdf"

    result = {
        "archivo": path.name,
        "sha256": sha256_file(path),
        "n_paginas": len(raw_images),
        "forma": forma,
        "identidad": identity,
        "id_documento": identity.get("id_documento"),
        "pdf_ordenado": ordered_pdf_name,
        "paginas": pages,
        "intra": {str(k): v for k, v in sorted(intra.items())},
        "extra": {str(k): v for k, v in sorted(extra.items())},
        "estres": {str(k): v for k, v in sorted(estres.items())},
        "faltantes": {"intra": missing_intra, "extra": missing_extra, "estres": missing_estres},
        "ambiguos": ambiguos,
        "calidad": {
            "intra_leidos": len(intra) + len(amb_intra),
            "intra_esperados": real_expected_intra,
            "extra_leidos": len(extra) + len(amb_extra),
            "estres_leidos": len(estres) + len(amb_estres),
            "secciones_opcionales": {
                "clientes": aplica_clientes,
                "jefatura": aplica_jefatura if forma != "B" else None,
            },
            "paginas_items": sum(1 for p in pages if p["n_likert_rows"] > 0),
        },
        "scoring": scoring,
    }

    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        casos_dir = out_dir / "casos" if (out_dir / "casos").exists() else out_dir
        ordered_pdf_path = casos_dir / ordered_pdf_name
        try:
            generate_ordered_pdf(path, pages, ordered_pdf_path)
            result["pdf_ordenado_path"] = str(ordered_pdf_path)
        except Exception:
            pass

        dest = out_dir / f"{path.stem}.json"
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["json_path"] = str(dest)

    return result


def process_folder(folder: Path, out_dir: Path) -> list[dict]:
    folder = Path(folder)
    pdfs = sorted(folder.glob("*.pdf"))
    seen = set()
    results = []
    for pdf in pdfs:
        digest = sha256_file(pdf)
        if digest in seen:
            results.append({"archivo": pdf.name, "error": "duplicado", "sha256": digest})
            continue
        seen.add(digest)
        results.append(process_pdf(pdf, out_dir=out_dir))
    return results
