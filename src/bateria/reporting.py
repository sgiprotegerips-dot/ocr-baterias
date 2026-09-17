"""Motor de Consolidación Estadística, Baremos Colectivos e Informes Diagnósticos SST.
Conforme a la Resolución 2764 de 2022 y 2646 de 2008 del Ministerio del Trabajo de Colombia.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any, Dict, List, Optional

from .db.models import CasoCuadernillo, InformeDiagnostico, Medicion, Usuario
from .report.catalog_narratives import interpolar_lectura, narrativa


def consolidate_medicion_report(medicion: Medicion, casos: List[CasoCuadernillo], psicologa: Optional[Usuario] = None) -> Dict[str, Any]:
    """Calcula y consolida todas las tablas epidemiológicas y sociodemográficas de la medición."""
    total_casos = len(casos)
    if total_casos == 0:
        return {
            "total_evaluados": 0,
            "resumen_sociodemografico": {},
            "baremos_consolidados": {},
            "dimensiones_prioritarias": [],
            "cruces": {},
        }

    # 1. Muestra y formas
    forma_a_count = sum(1 for c in casos if (c.forma or "A").upper() == "A")
    forma_b_count = sum(1 for c in casos if (c.forma or "A").upper() == "B")

    # 2. Perfil sociodemográfico (de fichas de datos leídas)
    cargos = Counter(c.cargo for c in casos if c.cargo)
    areas = Counter(c.area_dependencia for c in casos if c.area_dependencia)

    ambiguos_pendientes_total = 0
    completos_total = 0
    for c in casos:
        est = getattr(c, "estado", None) if hasattr(c, "estado") else (c.get("estado") if isinstance(c, dict) else None)
        if est == "listo":
            completos_total += 1
        ambs = getattr(c, "ambiguos", None) or (c.get("ambiguos") if isinstance(c, dict) else []) or []
        for a in ambs:
            dec = a.get("decision") if isinstance(a, dict) else getattr(a, "decision", None)
            if dec is None:
                ambiguos_pendientes_total += 1

    sociodemografico = {
        "total_evaluados": total_casos,
        "total_participantes": total_casos,
        "forma_a_conteo": forma_a_count,
        "forma_b_conteo": forma_b_count,
        "completos_conteo": completos_total,
        "ambiguos_pendientes": ambiguos_pendientes_total,
        "cobertura_porcentaje": round((total_casos / (medicion.trabajadores_esperados or total_casos)) * 100, 1),
        "distribucion_forma": {
            "Forma A (Jefes / Técnicos / Profesionales)": forma_a_count,
            "Forma B (Auxiliares / Operarios)": forma_b_count,
        },
        "cargos_principales": dict(cargos.most_common(8)),
        "areas_principales": dict(areas.most_common(8)),
    }

    # 3. Niveles de Riesgo Estándar
    NIVELES_STD = ["Sin riesgo", "Riesgo bajo", "Riesgo medio", "Riesgo alto", "Riesgo muy alto"]

    DOMINIOS_INTRALABORALES_OFICIALES = [
        "Liderazgo y relaciones sociales en el trabajo",
        "Control sobre el trabajo",
        "Demandas del trabajo",
        "Recompensas",
    ]

    DIMENSIONES_EXTRALABORALES_OFICIALES = [
        "Tiempo fuera del trabajo",
        "Relaciones familiares",
        "Comunicación y relaciones interpersonales",
        "Situación económica del grupo familiar",
        "Características de la vivienda y de su entorno",
        "Influencia del entorno extralaboral sobre el trabajo",
        "Desplazamiento vivienda-trabajo-vivienda",
    ]

    def init_distribution() -> Dict[str, int]:
        return {nivel: 0 for nivel in NIVELES_STD}

    def calc_percentages(counts: Dict[str, int], total_n: Optional[int] = None) -> Dict[str, Any]:
        result = {}
        n_eval = sum(counts.values())
        denom = n_eval if n_eval > 0 else (total_n or 0)
        for nivel in NIVELES_STD:
            cnt = counts.get(nivel, 0)
            pct = round((cnt / denom * 100), 1) if denom > 0 else 0.0
            result[nivel] = {"cantidad": cnt, "porcentaje": pct}
        result["_n_eval"] = n_eval
        return result

    def to_simple_dist(pct_dict: Dict[str, Any]) -> Dict[str, float]:
        return {k: v["porcentaje"] for k, v in pct_dict.items() if not k.startswith("_")}

    def match_nivel(nv: Optional[str]) -> Optional[str]:
        if not nv:
            return None
        if nv in NIVELES_STD:
            return nv
        nv_lower = nv.lower()
        if "despreciable" in nv_lower or "sin riesgo" in nv_lower or "muy bajo" in nv_lower:
            return "Sin riesgo"
        if "muy alto" in nv_lower:
            return "Riesgo muy alto"
        if "alto" in nv_lower:
            return "Riesgo alto"
        if "medio" in nv_lower:
            return "Riesgo medio"
        if "bajo" in nv_lower:
            return "Riesgo bajo"
        return None

    # 4. Consolidación Intralaboral (Total, Dominios y Dimensiones)
    intra_total_counts = init_distribution()
    dims_intra_counts: Dict[str, Dict[str, int]] = {}
    dominios_intra_counts: Dict[str, Dict[str, int]] = {
        dom: init_distribution() for dom in DOMINIOS_INTRALABORALES_OFICIALES
    }

    extra_total_counts = init_distribution()
    dims_extra_counts: Dict[str, Dict[str, int]] = {
        dim: init_distribution() for dim in DIMENSIONES_EXTRALABORALES_OFICIALES
    }

    estres_total_counts = init_distribution()
    general_total_counts = init_distribution()

    dim_transformados: Dict[str, List[float]] = defaultdict(list)
    dom_transformados: Dict[str, List[float]] = defaultdict(list)
    intra_t_vals: List[float] = []
    extra_t_vals: List[float] = []
    estres_t_vals: List[float] = []
    general_t_vals: List[float] = []

    cruces_forma = {
        "A": {"intra": init_distribution(), "extra": init_distribution(), "estres": init_distribution()},
        "B": {"intra": init_distribution(), "extra": init_distribution(), "estres": init_distribution()},
    }
    cruces_area_intra: Dict[str, Dict[str, int]] = defaultdict(init_distribution)
    cruces_cargo_intra: Dict[str, Dict[str, int]] = defaultdict(init_distribution)

    for c in casos:
        sc = c.scoring_villalobos or {}
        forma_c = (getattr(c, "forma", None) or "A").upper()
        if forma_c not in ("A", "B"):
            forma_c = "A"
        area_c = (getattr(c, "area_dependencia", None) or "Sin área").strip() or "Sin área"
        cargo_c = (getattr(c, "cargo", None) or "Sin cargo").strip() or "Sin cargo"

        # Intra Total
        sc_intra = (sc.get("intra") or {}).get("total") or {}
        nv_intra = match_nivel(sc_intra.get("nivel"))
        if nv_intra:
            intra_total_counts[nv_intra] += 1
            cruces_forma[forma_c]["intra"][nv_intra] += 1
            cruces_area_intra[area_c][nv_intra] += 1
            cruces_cargo_intra[cargo_c][nv_intra] += 1
        if sc_intra.get("transformado") is not None:
            intra_t_vals.append(float(sc_intra["transformado"]))

        # Intra Dominios
        for dom in (sc.get("intra") or {}).get("dominios") or []:
            dom_nom = dom.get("nombre")
            dom_nv = match_nivel(dom.get("nivel"))
            if dom_nom:
                if dom_nom not in dominios_intra_counts:
                    dominios_intra_counts[dom_nom] = init_distribution()
                if dom_nv:
                    dominios_intra_counts[dom_nom][dom_nv] += 1
                if dom.get("transformado") is not None:
                    dom_transformados[dom_nom].append(float(dom["transformado"]))

        # Intra Dimensiones
        for d in (sc.get("intra") or {}).get("dimensiones") or []:
            d_nom = d.get("nombre")
            d_nv = match_nivel(d.get("nivel"))
            if d_nom:
                if d_nom not in dims_intra_counts:
                    dims_intra_counts[d_nom] = init_distribution()
                if d_nv:
                    dims_intra_counts[d_nom][d_nv] += 1
                if d.get("transformado") is not None:
                    dim_transformados[d_nom].append(float(d["transformado"]))

        # Extra Total
        sc_extra = (sc.get("extra") or {}).get("total") or {}
        nv_extra = match_nivel(sc_extra.get("nivel"))
        if nv_extra:
            extra_total_counts[nv_extra] += 1
            cruces_forma[forma_c]["extra"][nv_extra] += 1
        if sc_extra.get("transformado") is not None:
            extra_t_vals.append(float(sc_extra["transformado"]))

        # Extra Dimensiones
        for d in (sc.get("extra") or {}).get("dimensiones") or []:
            d_nom = d.get("nombre")
            d_nv = match_nivel(d.get("nivel"))
            if d_nom:
                if d_nom not in dims_extra_counts:
                    dims_extra_counts[d_nom] = init_distribution()
                if d_nv:
                    dims_extra_counts[d_nom][d_nv] += 1
                if d.get("transformado") is not None:
                    dim_transformados[d_nom].append(float(d["transformado"]))

        # Estrés Total
        sc_estres = (sc.get("estres") or {}).get("total") or {}
        nv_estres = match_nivel(sc_estres.get("nivel"))
        if nv_estres:
            estres_total_counts[nv_estres] += 1
            cruces_forma[forma_c]["estres"][nv_estres] += 1
        if sc_estres.get("transformado") is not None:
            estres_t_vals.append(float(sc_estres["transformado"]))

        # Total General Combinado (Intra + Extra)
        sc_gen = sc.get("general") or {}
        nv_gen = match_nivel(sc_gen.get("nivel"))
        if nv_gen:
            general_total_counts[nv_gen] += 1
        if sc_gen.get("transformado") is not None:
            general_t_vals.append(float(sc_gen["transformado"]))

    # 5. Formatear porcentajes para gráficas y tablas
    baremos_consolidados = {
        "intralaboral_total": calc_percentages(intra_total_counts, total_casos),
        "extralaboral_total": calc_percentages(extra_total_counts, total_casos),
        "estres_total": calc_percentages(estres_total_counts, total_casos),
        "general_total": calc_percentages(general_total_counts, total_casos),
        "dominios_intralaborales": {
            dom: calc_percentages(cnts, total_casos) for dom, cnts in dominios_intra_counts.items()
        },
        "dimensiones_intralaborales": {
            dim: calc_percentages(cnts, total_casos) for dim, cnts in dims_intra_counts.items()
        },
        "dimensiones_extralaborales": {
            dim: calc_percentages(cnts, total_casos) for dim, cnts in dims_extra_counts.items()
        },
        # Jerarquía para componentes UI
        "intralaboral": {
            "general": {"distribucion": to_simple_dist(calc_percentages(intra_total_counts, total_casos))},
            "dominios": {dom: {"distribucion": to_simple_dist(calc_percentages(cnts, total_casos))} for dom, cnts in dominios_intra_counts.items()},
            "dimensiones": {dim: {"distribucion": to_simple_dist(calc_percentages(cnts, total_casos))} for dim, cnts in dims_intra_counts.items()},
        },
        "extralaboral": {
            "general": {"distribucion": to_simple_dist(calc_percentages(extra_total_counts, total_casos))},
            "dimensiones": {dim: {"distribucion": to_simple_dist(calc_percentages(cnts, total_casos))} for dim, cnts in dims_extra_counts.items()},
        },
        "estres": {
            "distribucion": to_simple_dist(calc_percentages(estres_total_counts, total_casos)),
        },
        "general": {
            "distribucion": to_simple_dist(calc_percentages(general_total_counts, total_casos)),
        },
    }

    def _stats_t(vals: List[float]) -> Dict[str, Optional[float]]:
        if not vals:
            return {"media": None, "mediana": None, "n": 0}
        return {
            "media": round(mean(vals), 1),
            "mediana": round(median(vals), 1),
            "n": len(vals),
        }

    def _enriquecer(dist: Dict[str, Any], nombre: str, tipo: str, dominio: str = "") -> Dict[str, Any]:
        n_eval = int(dist.get("_n_eval") or 0)
        n_alto = int(dist.get("Riesgo alto", {}).get("cantidad") or 0)
        n_ma = int(dist.get("Riesgo muy alto", {}).get("cantidad") or 0)
        n_critico = n_alto + n_ma
        pct_critico = round(
            (dist.get("Riesgo alto", {}).get("porcentaje") or 0)
            + (dist.get("Riesgo muy alto", {}).get("porcentaje") or 0),
            1,
        )
        st = _stats_t(dim_transformados.get(nombre) or dom_transformados.get(nombre) or [])
        out = dict(dist)
        out["n_eval"] = n_eval
        out["n_critico"] = n_critico
        out["porcentaje_critico"] = pct_critico
        out["media_transformado"] = st["media"]
        out["mediana_transformado"] = st["mediana"]
        out["lectura"] = interpolar_lectura(nombre, pct_critico, n_critico, n_eval or total_casos, st["media"])
        nav = narrativa(nombre)
        out["definicion"] = nav.get("definicion")
        out["intervencion_primaria"] = nav.get("intervencion_primaria")
        out["intervencion_secundaria"] = nav.get("intervencion_secundaria")
        out["tipo"] = tipo
        out["dominio"] = dominio or nav.get("dominio") or tipo
        return out

    dims_intra_enr = {
        dim: _enriquecer(dist, dim, "Intralaboral")
        for dim, dist in baremos_consolidados["dimensiones_intralaborales"].items()
    }
    dims_extra_enr = {
        dim: _enriquecer(dist, dim, "Extralaboral")
        for dim, dist in baremos_consolidados["dimensiones_extralaborales"].items()
    }
    dominios_enr = {
        dom: _enriquecer(dist, dom, "Intralaboral", dom)
        for dom, dist in baremos_consolidados["dominios_intralaborales"].items()
    }
    baremos_consolidados["dimensiones_intralaborales"] = dims_intra_enr
    baremos_consolidados["dimensiones_extralaborales"] = dims_extra_enr
    baremos_consolidados["dominios_intralaborales"] = dominios_enr
    baremos_consolidados["medias"] = {
        "intralaboral_total": _stats_t(intra_t_vals),
        "extralaboral_total": _stats_t(extra_t_vals),
        "estres_total": _stats_t(estres_t_vals),
        "general_total": _stats_t(general_t_vals),
    }

    # 6. Identificar dimensiones prioritarias (con mayor % de Riesgo Alto + Muy Alto)
    prioritarias = []
    for dim, dist in dims_intra_enr.items():
        if dist["porcentaje_critico"] > 0:
            prioritarias.append(
                {
                    "dimension": dim,
                    "tipo": "Intralaboral",
                    "dominio": dist.get("dominio"),
                    "porcentaje_critico": dist["porcentaje_critico"],
                    "n_critico": dist["n_critico"],
                    "n_eval": dist["n_eval"],
                    "media_transformado": dist["media_transformado"],
                    "intervencion_primaria": dist["intervencion_primaria"],
                }
            )

    for dim, dist in dims_extra_enr.items():
        if dist["porcentaje_critico"] > 0:
            prioritarias.append(
                {
                    "dimension": dim,
                    "tipo": "Extralaboral",
                    "dominio": "Extralaboral",
                    "porcentaje_critico": dist["porcentaje_critico"],
                    "n_critico": dist["n_critico"],
                    "n_eval": dist["n_eval"],
                    "media_transformado": dist["media_transformado"],
                    "intervencion_primaria": dist["intervencion_primaria"],
                }
            )

    prioritarias.sort(key=lambda x: x["porcentaje_critico"], reverse=True)

    def _cross_pct(counter_map: Dict[str, Dict[str, int]], limit: int = 8) -> Dict[str, Any]:
        items = sorted(counter_map.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:limit]
        return {k: calc_percentages(v, total_casos) for k, v in items}

    cruces = {
        "forma": {
            "A": {inst: calc_percentages(cnts, total_casos) for inst, cnts in cruces_forma["A"].items()},
            "B": {inst: calc_percentages(cnts, total_casos) for inst, cnts in cruces_forma["B"].items()},
        },
        "areas_intralaboral": _cross_pct(cruces_area_intra),
        "cargos_intralaboral": _cross_pct(cruces_cargo_intra),
    }

    # 7. Sugerencias automáticas de intervención normativa
    conclusiones_auto = (
        f"Se evaluó un total de {total_casos} trabajadores de la empresa {medicion.empresa.razon_social if medicion.empresa else ''} "
        f"en el marco de la Resolución 2764 de 2022. La distribución de la muestra comprende {forma_a_count} personas en Forma A "
        f"y {forma_b_count} en Forma B. "
    )
    if prioritarias:
        top3 = ", ".join(f"'{p['dimension']}' ({p['porcentaje_critico']}%)" for p in prioritarias[:3])
        conclusiones_auto += f"Las dimensiones con mayor concentración en niveles de riesgo Alto y Muy Alto son: {top3}."

    recomendaciones_auto = (
        "1. Priorizar el diseño del Programa de Vigilancia Epidemiológica (PVE) de Factores Psicosociales en las dimensiones críticas.\n"
        "2. Desarrollar talleres de gestión del tiempo y desconexión laboral para los factores extralaborales.\n"
        "3. Fortalecer los liderazgos y la claridad de rol en las áreas operativas identificadas con mayor sobrecarga."
    )

    return {
        "empresa": medicion.empresa.to_dict() if medicion.empresa else {},
        "medicion": medicion.to_dict(),
        "psicologa": psicologa.to_dict() if psicologa else (medicion.psicologa.to_dict() if medicion.psicologa else {}),
        "total_evaluados": total_casos,
        "resumen_sociodemografico": sociodemografico,
        "baremos_consolidados": baremos_consolidados,
        "dimensiones_prioritarias": prioritarias,
        "cruces": cruces,
        "conclusiones_sugeridas": conclusiones_auto,
        "recomendaciones_sugeridas": recomendaciones_auto,
        "generado_en": datetime.now(timezone.utc).isoformat(),
    }


def compute_report_hash(report_data: Dict[str, Any]) -> str:
    """Calcula un hash SHA-256 determinista para sellado legal e inmutabilidad de 20 años."""
    raw_bytes = json.dumps(report_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()
