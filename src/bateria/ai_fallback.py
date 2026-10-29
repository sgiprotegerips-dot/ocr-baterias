"""Asistente Multimodal de IA invocado ESTRICTAMENTE ante inconsistencias.

Principios de arquitectura e invariantes normativas (GEMINI.md):
1. Cero llamadas a IA durante la operación determinista normal (OMR OpenCV + QR + RapidOCR).
2. Activación exclusiva cuando el motor local detecta una inconsistencia real:
   - Página sin clasificar o con colisión en el reordenamiento ADF 1..24 (Regla 3).
   - Identidad / Cédula / Datos de consentimiento faltantes o discrepantes entre portada y pág. 1.
   - Celda Likert en blanco (`vacio`) dentro de una tabla respondida que sí presenta tinta oscura real
     (`pixel < 145` sobre papel blanco `> 180`, Regla 2 Anti-Bleed-Through) pegada al borde de la grilla.
   - Diagnóstico visual orientativo en ítems con `status: "ambiguo"` (doble marca / tachón), SIN
     desempatar jamás automáticamente ni sustituir la decisión manual obligatoria de la psicóloga (Regla 4).
3. Separación estricta OMR vs OCR (Regla 1): en recortes Likert solo se inspeccionan las casillas
   geométricas numeradas `0..N-1` delimitadas por OpenCV, nunca las palabras impresas de encabezado.
"""

from __future__ import annotations

import base64
import difflib
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("bateria.ai_fallback")

_TELEMETRY_LOCK = threading.Lock()
_AI_TELEMETRY: Dict[str, Any] = {
    "calls_total": 0,
    "calls_page_order": 0,
    "calls_identity": 0,
    "calls_likert_audit": 0,
    "errors_total": 0,
    "last_latency_ms": 0.0,
}
_ENV_LOADED = False


def _load_dotenv_if_needed() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if os.getenv("GEMINI_API_KEY"):
        return
    try:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.is_file():
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def get_ai_api_key() -> str:
    _load_dotenv_if_needed()
    flag = os.getenv("AI_FALLBACK_ON_INCONSISTENCY", "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return ""
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_ai_model() -> str:
    _load_dotenv_if_needed()
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def is_ai_fallback_enabled() -> bool:
    return bool(get_ai_api_key())


def get_ai_telemetry() -> Dict[str, Any]:
    with _TELEMETRY_LOCK:
        return {
            "enabled": is_ai_fallback_enabled(),
            "model": get_ai_model(),
            "mode": "on_inconsistency_only",
            **_AI_TELEMETRY,
        }


def _encode_image_part(img: np.ndarray, max_dim: int = 1100, use_png: bool = False) -> Optional[Dict[str, Any]]:
    if img is None or getattr(img, "size", 0) == 0:
        return None
    work = img
    h, w = work.shape[:2]
    if max(h, w) > max_dim:
        sc = max_dim / float(max(h, w))
        work = cv2.resize(work, (max(1, int(w * sc)), max(1, int(h * sc))), interpolation=cv2.INTER_AREA)

    if use_png:
        ok, buf = cv2.imencode(".png", work)
        mime = "image/png"
    else:
        ok, buf = cv2.imencode(".jpg", work, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        mime = "image/jpeg"
    if not ok:
        return None
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return {"inline_data": {"mime_type": mime, "data": b64}}


def _parse_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    txt = (raw_text or "").strip()
    if not txt:
        return None
    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\s*```$", "", txt)
    try:
        parsed = json.loads(txt)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                return None
    return None


def _call_gemini_json(
    prompt: str,
    images: List[Tuple[np.ndarray, int, bool]],
    category: str,
    timeout: float = 14.0,
) -> Optional[Dict[str, Any]]:
    """Realiza una llamada multimodal puntual a Gemini retornando un diccionario JSON."""
    api_key = get_ai_api_key()
    if not api_key:
        return None

    parts: List[Dict[str, Any]] = []
    for im, max_dim, use_png in images:
        p = _encode_image_part(im, max_dim=max_dim, use_png=use_png)
        if p is not None:
            parts.append(p)
    if not parts:
        return None
    parts.append({"text": prompt})

    model = get_ai_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    configs_to_try = [
        {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
        {
            "temperature": 0.0,
            "responseMimeType": "application/json",
        },
    ]

    t0 = time.perf_counter()
    last_err: Optional[Exception] = None

    for gen_cfg in configs_to_try:
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": gen_cfg,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_resp = json.loads(resp.read().decode("utf-8"))
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            with _TELEMETRY_LOCK:
                _AI_TELEMETRY["calls_total"] += 1
                if category in _AI_TELEMETRY:
                    _AI_TELEMETRY[category] += 1
                _AI_TELEMETRY["last_latency_ms"] = dt_ms

            cands = raw_resp.get("candidates") or []
            if not cands:
                return None
            c_parts = ((cands[0].get("content") or {}).get("parts")) or []
            text_out = "\n".join(str(p.get("text", "")) for p in c_parts if p.get("text"))
            return _parse_json_object(text_out)
        except urllib.error.HTTPError as he:
            # Si el modelo no admite thinkingConfig (HTTP 400), reintentar con config estándar
            if he.code == 400 and "thinkingConfig" in gen_cfg:
                continue
            last_err = he
            break
        except Exception as exc:
            last_err = exc
            break

    with _TELEMETRY_LOCK:
        _AI_TELEMETRY["calls_total"] += 1
        _AI_TELEMETRY["errors_total"] += 1
    logger.warning(f"AI fallback ({category}) no pudo completar consulta: {last_err}")
    return None


# ---------------------------------------------------------------------------
# 1. Resolución de Inconsistencia en Reordenamiento / Clasificación ADF (1..24)
# ---------------------------------------------------------------------------

_VALID_PAGE_KINDS = {
    "consentimiento",
    "ficha",
    "intra_portada",
    "intra_instrucciones",
    "intra_items",
    "extra_portada",
    "extra_instrucciones",
    "extra_items",
    "estres_portada",
    "estres_items",
    "otra",
}


def ai_resolve_page_inconsistency(img: np.ndarray) -> Optional[Dict[str, Any]]:
    """Identifica el número de página oficial (1..24), tipo y rotación cuando el clasificador local duda."""
    if not is_ai_fallback_enabled() or img is None:
        return None

    prompt = (
        "Eres un verificador documental de la Batería de Riesgo Psicosocial de Colombia (24 páginas).\n"
        "Estructura oficial del cuadernillo:\n"
        "- Página 1: Consentimiento Informado (kind='consentimiento').\n"
        "- Páginas 2 a 5: Ficha de Datos Generales sociodemográficos (kind='ficha').\n"
        "- Página 6: Portada Cuestionario Intralaboral con recuadro de ID (kind='intra_portada').\n"
        "- Página 7: Instrucciones Cuestionario Intralaboral Forma A o B (kind='intra_instrucciones').\n"
        "- Páginas 8 a 17 (Forma A) o 8 a 16 (Forma B): Tablas de preguntas Intralaborales (kind='intra_items').\n"
        "- Página 18: Portada Cuestionario Extralaboral (kind='extra_portada').\n"
        "- Página 19: Instrucciones Extralaboral (kind='extra_instrucciones').\n"
        "- Páginas 20 a 22: Tablas de preguntas Extralaborales 1..31 (kind='extra_items').\n"
        "- Página 23: Portada Cuestionario Evaluación del Estrés (kind='estres_portada').\n"
        "- Página 24: Tabla de 31 síntomas/malestares de Estrés (kind='estres_items').\n\n"
        "Analiza la imagen y devuelve SOLO este objeto JSON:\n"
        "{\n"
        '  "printed_page": <entero 1..24 o null>,\n'
        '  "kind": "<uno de: consentimiento, ficha, intra_portada, intra_instrucciones, intra_items, extra_portada, extra_instrucciones, extra_items, estres_portada, estres_items, otra>",\n'
        '  "forma": "<A o B o null>",\n'
        '  "rot_angle_needed": <0, 90, 180 o 270 grados en sentido horario necesarios para dejar la página derecha>\n'
        "}"
    )

    res = _call_gemini_json(prompt, [(img, 960, False)], category="calls_page_order")
    if not res:
        return None

    p_no = res.get("printed_page")
    try:
        p_no = int(p_no) if p_no is not None else None
        if p_no is not None and not (1 <= p_no <= 24):
            p_no = None
    except Exception:
        p_no = None

    kind = str(res.get("kind") or "otra").strip().lower()
    if kind not in _VALID_PAGE_KINDS:
        kind = "otra"

    forma = str(res.get("forma") or "").strip().upper()
    if forma not in ("A", "B"):
        forma = None

    rot = res.get("rot_angle_needed", 0)
    try:
        rot = int(rot) % 360
        if rot not in (0, 90, 180, 270):
            rot = 0
    except Exception:
        rot = 0

    return {
        "printed_page": p_no,
        "kind": kind,
        "forma": forma,
        "rot_angle_needed": rot,
    }


# ---------------------------------------------------------------------------
# 2. Resolución de Inconsistencia en Identidad / Sticker / Consentimiento
# ---------------------------------------------------------------------------

def ai_resolve_identity_inconsistency(
    page1_img: Optional[np.ndarray],
    page6_img: Optional[np.ndarray] = None,
    page4_img: Optional[np.ndarray] = None,
) -> Optional[Dict[str, Any]]:
    """Extrae identidad del trabajador apoyándose en IA únicamente cuando falta o discrepa algún campo clave."""
    if not is_ai_fallback_enabled():
        return None

    crops: List[Tuple[np.ndarray, int, bool]] = []

    if page1_img is not None and getattr(page1_img, "size", 0) > 0:
        h1, w1 = page1_img.shape[:2]
        # Si hay un sticker QR en la mitad superior, enviar primero su recorte nítido en PNG
        try:
            from .qr_detect import _locate_qr_cluster

            gray1 = cv2.cvtColor(page1_img, cv2.COLOR_BGR2GRAY) if page1_img.ndim == 3 else page1_img
            cl = _locate_qr_cluster(gray1)
            if cl is not None:
                qx, qy, qsize, _ = cl
                sx0 = max(0, qx - int(qsize * 0.25))
                sy0 = max(0, qy - int(qsize * 0.25))
                sx1 = min(w1, qx + int(qsize * 2.80))
                sy1 = min(h1, qy + int(qsize * 2.00))
                sticker_crop = page1_img[sy0:sy1, sx0:sx1]
                if sticker_crop.size > 0:
                    up_st = cv2.resize(sticker_crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    crops.append((up_st, 900, True))
        except Exception:
            pass
        # Enviar página 1 completa (cubre encabezado, sticker y bloque inferior de firma/cédula/cargo)
        crops.append((page1_img, 1150, False))

    if page6_img is not None and getattr(page6_img, "size", 0) > 0:
        h6 = page6_img.shape[0]
        crops.append((page6_img[: int(h6 * 0.60), :], 950, False))

    if page4_img is not None and getattr(page4_img, "size", 0) > 0:
        h4 = page4_img.shape[0]
        crops.append((page4_img[int(h4 * 0.12) : int(h4 * 0.85), :], 950, False))

    if not crops:
        return None

    prompt = (
        "Extrae los datos de identificación del trabajador en este cuadernillo de Batería de Riesgo Psicosocial.\n"
        "Prioriza el texto impreso en el sticker adhesivo de 30x20 mm (si aparece junto al código QR con FORMA A/B, "
        "C.C./ID y NOMBRE) y complementa con los campos manuscritos de Consentimiento Informado, Portada o Ficha "
        "(Nombre completo, Cédula/ID numérico sin puntos ni espacios, Cargo/Ocupación, Área/Dependencia y Fecha de aplicación).\n"
        "Devuelve SOLO este JSON exacto (usa cadena vacía \"\" si un dato no es legible, no inventes valores):\n"
        "{\n"
        '  "id_documento": "<solo dígitos de la cédula, ej. 1032381023>",\n'
        '  "nombre": "<nombre completo en mayúsculas>",\n'
        '  "cargo": "<cargo actual u ocupación>",\n'
        '  "dependencia": "<área, departamento o sección de la empresa>",\n'
        '  "fecha": "<fecha de aplicación YYYY-MM-DD o DD/MM/YYYY>",\n'
        '  "forma": "<A o B o vacío>"\n'
        "}"
    )

    res = _call_gemini_json(prompt, crops, category="calls_identity")
    if not res:
        return None

    raw_cc = re.sub(r"\D", "", str(res.get("id_documento") or ""))
    if not (5 <= len(raw_cc) <= 12):
        raw_cc = ""

    out: Dict[str, Any] = {
        "id_documento": raw_cc or None,
        "nombre": str(res.get("nombre") or "").strip().upper(),
        "cargo": str(res.get("cargo") or "").strip(),
        "dependencia": str(res.get("dependencia") or "").strip(),
        "fecha": str(res.get("fecha") or "").strip(),
        "forma": str(res.get("forma") or "").strip().upper() if str(res.get("forma") or "").strip().upper() in ("A", "B") else "",
        "ficha": {},
    }

    # Reconciliar contra TrabajadorNomina en PostgreSQL si existe coincidencia de alta certeza
    try:
        from .qr_codec import identity_from_ficha
        from .qr_detect import _get_nomina_Lookup

        records, by_cc = _get_nomina_Lookup()
        matched_nom = None
        if raw_cc and raw_cc in by_cc:
            matched_nom = by_cc[raw_cc]
        elif records and (raw_cc or out["nombre"]):
            name_words = [w for w in re.findall(r"[A-ZÑ]{3,}", out["nombre"]) if len(w) >= 3]
            best_sc = 0.0
            for rec in records:
                nom_cc = rec.get("cedula", "")
                nom_words = [w for w in re.findall(r"[A-ZÑ]{3,}", rec.get("nombre", "").upper()) if len(w) >= 3]
                cc_sim = difflib.SequenceMatcher(None, raw_cc, nom_cc).ratio() if (raw_cc and nom_cc) else 0.0
                m_words = sum(
                    1
                    for nw in nom_words
                    if any(nw == ow or difflib.SequenceMatcher(None, nw, ow).ratio() >= 0.82 for ow in name_words)
                )
                n_ratio = (m_words / float(len(nom_words))) if nom_words else 0.0
                if (cc_sim >= 0.80 and m_words >= 1) or (m_words >= 3 and n_ratio >= 0.75):
                    sc = cc_sim * 1.4 + n_ratio
                    if sc > best_sc:
                        best_sc = sc
                        matched_nom = rec

        if matched_nom is not None:
            nom_ident = identity_from_ficha(matched_nom)
            for k in ("id_documento", "nombre", "cargo", "dependencia", "fecha"):
                if nom_ident.get(k):
                    out[k] = nom_ident[k]
            if matched_nom.get("forma") in ("A", "B"):
                out["forma"] = matched_nom["forma"]
            out["ficha"] = nom_ident.get("ficha") or matched_nom
    except Exception:
        pass

    return out


# ---------------------------------------------------------------------------
# 3. Verificación Visual de Inconsistencias en Celdas Likert (Reglas 1, 2 y 4)
# ---------------------------------------------------------------------------

def verify_cell_has_real_dark_ink(cell_gray: np.ndarray) -> bool:
    """Compuerta física Anti-Bleed-Through (Regla 2 de GEMINI.md):
    Verifica que exista tinta oscura real de bolígrafo/lápiz (`pixel <= 145`) sobre papel
    blanco (`mediana >= 180`), excluyendo bordes perimetrales exteriores de 2 px de la tabla.
    Impide que el trasluz del reverso (`pixel > 150`) sea considerado jamás como marca.
    """
    if cell_gray is None or cell_gray.size == 0:
        return False
    h, w = cell_gray.shape[:2]
    my = min(3, max(1, h // 12))
    mx = min(3, max(1, w // 14))
    core = cell_gray[my : max(my + 1, h - my), mx : max(mx + 1, w - mx)]
    if core.size == 0:
        return False

    med_bg = float(np.median(core))
    min_val = int(np.min(core))
    if med_bg < 180.0 or min_val > 145:
        return False

    bin_dark = (core < 145).astype(np.uint8)
    n_lbl, _, stats, _ = cv2.connectedComponentsWithStats(bin_dark, connectivity=8)
    real_px = 0
    for lbl in range(1, n_lbl):
        bw_c = stats[lbl, cv2.CC_STAT_WIDTH]
        bh_c = stats[lbl, cv2.CC_STAT_HEIGHT]
        area = stats[lbl, cv2.CC_STAT_AREA]
        # Ignorar segmentos rectos de líneas impresas de la tabla
        if bw_c >= 0.65 * core.shape[1] and bh_c <= 3:
            continue
        if bh_c >= 0.65 * core.shape[0] and bw_c <= 3:
            continue
        if area >= 2:
            real_px += int(area)
    return real_px >= 6


def _build_numbered_grid_preview(row_bgr: np.ndarray, col_offsets: List[int], n_choices: int) -> np.ndarray:
    """Construye una vista de las N casillas Likert numeradas 0..N-1 usando exactamente
    los límites geométricos de OpenCV, sin incluir palabras impresas de opciones (Regla 1).
    """
    if row_bgr.ndim == 2:
        vis = cv2.cvtColor(row_bgr, cv2.COLOR_GRAY2BGR)
    else:
        vis = row_bgr.copy()

    rh, rw = vis.shape[:2]
    scale = 2.0 if rh < 70 else 1.5
    vis = cv2.resize(vis, (max(1, int(rw * scale)), max(1, int(rh * scale))), interpolation=cv2.INTER_CUBIC)
    vh, vw = vis.shape[:2]

    header_h = 28
    canvas = np.full((vh + header_h, vw, 3), 255, dtype=np.uint8)
    canvas[header_h:, :] = vis

    if not col_offsets or len(col_offsets) < n_choices + 1:
        step = vw / float(n_choices)
        scaled_cols = [int(round(i * step)) for i in range(n_choices + 1)]
    else:
        total_orig = max(1, col_offsets[-1] - col_offsets[0])
        scaled_cols = [
            min(vw - 1, max(0, int(round(((c - col_offsets[0]) / float(total_orig)) * vw))))
            for c in col_offsets[: n_choices + 1]
        ]

    cv2.line(canvas, (0, header_h), (vw - 1, header_h), (40, 90, 200), 1)
    for idx in range(n_choices + 1):
        cx = scaled_cols[idx]
        cv2.line(canvas, (cx, 0), (cx, vh + header_h - 1), (40, 90, 220), 2)
        if idx < n_choices:
            nx = (scaled_cols[idx] + scaled_cols[idx + 1]) // 2 - 6
            cv2.putText(
                canvas,
                str(idx),
                (max(2, nx), 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (20, 60, 180),
                2,
                cv2.LINE_AA,
            )
    return canvas


def ai_inspect_likert_inconsistency(
    row_img: np.ndarray,
    col_offsets: List[int],
    n_choices: int = 5,
) -> Optional[Dict[str, Any]]:
    """Inspecciona una fila Likert inconsistente (`ambiguo` o `vacio` con tinta oscura en borde).

    IMPORTANTE (Regla 4 de GEMINI.md):
    En filas con doble marca / tachón, este resultado SOLO aporta diagnóstico orientativo
    (`ia_sugerencia`, `ia_motivo`) para la interfaz de la psicóloga; el motor jamás desempata
    automáticamente una ambigüedad.
    """
    if not is_ai_fallback_enabled() or row_img is None or getattr(row_img, "size", 0) == 0:
        return None

    preview = _build_numbered_grid_preview(row_img, col_offsets, n_choices)
    max_idx = n_choices - 1

    prompt = (
        f"Observa esta fila de {n_choices} casillas numeradas de 0 a {max_idx} (de izquierda a derecha, separadas por líneas verticales).\n"
        "Identifica qué casillas contienen trazos manuscritos reales (X, chulo, cruz o relleno) e ignora sombras muy tenues de papel traslúcido.\n"
        "Si una casilla fue tachada/borrada intencionalmente para corregir y otra casilla tiene la marca limpia, indícalo en 'tachadas' y 'hay_tachon'.\n"
        "Si hay dos o más casillas marcadas, 'hay_doble_marca' debe ser true.\n"
        "Devuelve SOLO este JSON:\n"
        "{\n"
        f'  "marcadas_activas": [<índices 0..{max_idx} con marca manuscrita válida>],\n'
        f'  "tachadas": [<índices 0..{max_idx} con tachón o intento de borrado>],\n'
        '  "hay_doble_marca": <true o false>,\n'
        '  "hay_tachon": <true o false>,\n'
        f'  "casilla_sugerida": <entero 0..{max_idx} o null>,\n'
        '  "confianza": <número entre 0.0 y 1.0>,\n'
        '  "motivo": "<explicación clínica breve en español, máx 110 caracteres>"\n'
        "}"
    )

    res = _call_gemini_json(prompt, [(preview, 900, True)], category="calls_likert_audit")
    if not res:
        return None

    def _clean_indices(raw_list: Any) -> List[int]:
        out_idx: List[int] = []
        if isinstance(raw_list, list):
            for v in raw_list:
                try:
                    iv = int(v)
                    if 0 <= iv < n_choices and iv not in out_idx:
                        out_idx.append(iv)
                except Exception:
                    pass
        return out_idx

    activas = _clean_indices(res.get("marcadas_activas"))
    tachadas = _clean_indices(res.get("tachadas"))

    sug = res.get("casilla_sugerida")
    try:
        sug_int = int(sug) if sug is not None else None
        if sug_int is not None and not (0 <= sug_int < n_choices):
            sug_int = None
    except Exception:
        sug_int = None

    try:
        conf = float(res.get("confianza") or 0.0)
    except Exception:
        conf = 0.0

    return {
        "marcadas_activas": activas,
        "tachadas": tachadas,
        "hay_doble_marca": bool(res.get("hay_doble_marca")) or (len(activas) >= 2),
        "hay_tachon": bool(res.get("hay_tachon")) or bool(tachadas),
        "casilla_sugerida": sug_int,
        "confianza": round(max(0.0, min(1.0, conf)), 3),
        "motivo": str(res.get("motivo") or "").strip()[:140],
    }
