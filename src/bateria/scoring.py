"""Puntuación según el modelo Villalobos / MinProtección (batería 2010).

Puntaje transformado = (bruto / (n_ítems_respondidos * max_escala)) * 100
cuando se usa el factor de transformación = n * max_escala.

Escala intra/extra: 0–4. Estrés: 0–3.
Ítems protectores se invierten (4 - x) o (3 - x).

Baremos de total Intra A (Tabla 33) tomados de implementaciones del informe oficial.
Baremos por dimensión siguen la estructura Tablas 29–34; los cortes finos se
ajustan a los publicados en el manual (sin riesgo … muy alto).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

LIKERT5 = {"siempre": 4, "casi siempre": 3, "algunas veces": 2, "casi nunca": 1, "nunca": 0}
LIKERT4 = {"siempre": 3, "casi siempre": 2, "a veces": 1, "nunca": 0}


def _r(*items: int) -> list[int]:
    return list(items)


def _span(a: int, b: int) -> list[int]:
    return list(range(a, b + 1))


# --- Forma A: 123 ítems, 19 dimensiones, 4 dominios ---
FORMA_A = {
    "Demandas ambientales y de esfuerzo físico": {
        "dominio": "Demandas del trabajo",
        "items": _span(1, 12),
        "invert": {4, 5, 6, 9, 12},
    },
    "Demandas cuantitativas": {
        "dominio": "Demandas del trabajo",
        "items": [13, 14, 15],
        "invert": {14},
    },
    "Demandas de carga mental": {
        "dominio": "Demandas del trabajo",
        "items": _span(16, 21),
        "invert": set(),
    },
    "Exigencias de responsabilidad del cargo": {
        "dominio": "Demandas del trabajo",
        "items": _span(22, 26),
        "invert": set(),
    },
    "Consistencia del rol": {
        "dominio": "Demandas del trabajo",
        "items": _span(27, 30),
        "invert": set(),
    },
    "Demandas de la jornada de trabajo": {
        "dominio": "Demandas del trabajo",
        "items": _span(31, 34),
        "invert": {32, 34},
    },
    "Influencia del trabajo sobre el entorno extralaboral": {
        "dominio": "Demandas del trabajo",
        "items": _span(35, 38),
        "invert": set(),
    },
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": {
        "dominio": "Control sobre el trabajo",
        "items": _span(39, 42),
        "invert": {39, 40, 41, 42},
    },
    "Control y autonomía sobre el trabajo": {
        "dominio": "Control sobre el trabajo",
        "items": _span(43, 47),
        "invert": {43, 44, 45, 46, 47},
    },
    "Participación y manejo del cambio": {
        "dominio": "Control sobre el trabajo",
        "items": _span(48, 52),
        "invert": {48, 49, 50, 51},
    },
    "Claridad de rol": {
        "dominio": "Control sobre el trabajo",
        "items": _span(53, 59),
        "invert": {53, 54, 55, 56, 57, 58, 59},
    },
    "Capacitación": {
        "dominio": "Control sobre el trabajo",
        "items": _span(60, 62),
        "invert": {60, 61, 62},
    },
    "Características del liderazgo": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(63, 75),
        "invert": set(range(63, 76)),
    },
    "Relaciones sociales en el trabajo": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(76, 82) + [107, 108],
        "invert": set(_span(76, 82) + [107, 108]),
    },
    "Retroalimentación del desempeño": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(83, 87),
        "invert": set(range(83, 88)),
    },
    "Relación con los colaboradores": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(88, 92),
        "invert": set(range(88, 93)),
        "opcional_jefatura": True,
    },
    "Demandas emocionales": {
        "dominio": "Demandas del trabajo",
        "items": _span(93, 98) + [101, 102, 103],
        "invert": set(),
    },
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": {
        "dominio": "Recompensas",
        "items": [99, 100, 104, 105, 106],
        "invert": {99, 100, 104, 105, 106},
    },
    "Reconocimiento y compensación": {
        "dominio": "Recompensas",
        "items": _span(109, 123),
        "invert": set(range(109, 124)),
    },
}

# Forma B: 97 ítems (sin relación con colaboradores ni varias demandas de jefatura)
FORMA_B = {
    "Demandas ambientales y de esfuerzo físico": {
        "dominio": "Demandas del trabajo",
        "items": _span(1, 12),
        "invert": {4, 5, 6, 9, 12},
    },
    "Demandas cuantitativas": {
        "dominio": "Demandas del trabajo",
        "items": [13, 14, 15],
        "invert": {14},
    },
    "Demandas de carga mental": {
        "dominio": "Demandas del trabajo",
        "items": _span(16, 20),
        "invert": set(),
    },
    "Demandas de la jornada de trabajo": {
        "dominio": "Demandas del trabajo",
        "items": _span(21, 24),
        "invert": {24},
    },
    "Influencia del trabajo sobre el entorno extralaboral": {
        "dominio": "Demandas del trabajo",
        "items": _span(25, 28),
        "invert": set(),
    },
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": {
        "dominio": "Control sobre el trabajo",
        "items": _span(29, 32),
        "invert": set(range(29, 33)),
    },
    "Control y autonomía sobre el trabajo": {
        "dominio": "Control sobre el trabajo",
        "items": _span(33, 37),
        "invert": set(range(33, 38)),
    },
    "Participación y manejo del cambio": {
        "dominio": "Control sobre el trabajo",
        "items": _span(38, 40),
        "invert": set(range(38, 41)),
    },
    "Claridad de rol": {
        "dominio": "Control sobre el trabajo",
        "items": _span(41, 45),
        "invert": set(range(41, 46)),
    },
    "Capacitación": {
        "dominio": "Control sobre el trabajo",
        "items": _span(46, 48),
        "invert": set(range(46, 49)),
    },
    "Características del liderazgo": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(49, 61),
        "invert": set(range(49, 62)),
    },
    "Relaciones sociales en el trabajo": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(62, 73),
        "invert": {62, 63, 64, 65, 67, 68, 69, 70, 71, 72, 73},
    },
    "Retroalimentación del desempeño": {
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": _span(74, 78),
        "invert": set(range(74, 79)),
    },
    "Reconocimiento y compensación": {
        "dominio": "Recompensas",
        "items": _span(79, 84),
        "invert": set(range(79, 85)),
    },
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": {
        "dominio": "Recompensas",
        "items": _span(85, 88),
        "invert": set(range(85, 89)),
    },
    "Demandas emocionales": {
        "dominio": "Demandas del trabajo",
        "items": _span(89, 97),
        "invert": set(),
        "opcional_clientes": True,
    },
}

EXTRALABORAL = {
    "Desplazamiento vivienda-trabajo-vivienda": {
        "items": _span(1, 4),
        "invert": {1, 2},
    },
    "Características de la vivienda y de su entorno": {
        "items": _span(5, 13),
        "invert": {5, 6, 7, 8, 9, 10, 11, 12, 13},
    },
    "Tiempo fuera del trabajo": {
        "items": _span(14, 17),
        "invert": {14, 15, 16, 17},
    },
    "Comunicación y relaciones interpersonales": {
        "items": [18, 19, 20, 21, 23],
        "invert": {18, 19, 20, 21, 23},
    },
    "Relaciones familiares": {
        "items": [22, 25, 27],
        "invert": {22, 25, 27},
    },
    "Influencia del entorno extralaboral sobre el trabajo": {
        "items": [24, 26, 28],
        "invert": set(),
    },
    "Situación económica del grupo familiar": {
        "items": [29, 30, 31],
        "invert": {29},
    },
}

# Estrés 3ª versión: 31 ítems, ninguno invertido, escala 0-3
ESTRES_ITEMS = _span(1, 31)

# Cortes (sin, bajo, medio, alto) — el resto es muy alto. Manual Tablas 29–34 / 6 / 17–18.
BAREMOS_DIM_A = {
    "Características del liderazgo": (3.8, 15.4, 30.8, 46.2),
    "Relaciones sociales en el trabajo": (5.4, 16.2, 25.0, 37.5),
    "Retroalimentación del desempeño": (10.0, 25.0, 40.0, 55.0),
    "Relación con los colaboradores": (13.0, 25.0, 37.5, 50.0),
    "Claridad de rol": (0.9, 10.7, 21.4, 39.3),
    "Capacitación": (0.9, 16.7, 33.3, 50.0),
    "Participación y manejo del cambio": (12.5, 25.0, 37.5, 50.0),
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": (0.9, 6.3, 18.8, 31.3),
    "Control y autonomía sobre el trabajo": (8.3, 25.0, 41.7, 58.3),
    "Demandas ambientales y de esfuerzo físico": (14.6, 22.9, 31.3, 39.6),
    "Demandas emocionales": (16.7, 33.3, 47.2, 58.3),
    "Demandas cuantitativas": (25.0, 33.3, 50.0, 66.7),
    "Influencia del trabajo sobre el entorno extralaboral": (18.8, 31.3, 43.8, 56.3),
    "Exigencias de responsabilidad del cargo": (37.5, 54.2, 66.7, 79.2),
    "Demandas de carga mental": (60.0, 70.0, 80.0, 90.0),
    "Consistencia del rol": (15.0, 25.0, 35.0, 45.0),
    "Demandas de la jornada de trabajo": (6.3, 18.8, 31.3, 43.8),
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": (0.9, 6.3, 18.8, 31.3),
    "Reconocimiento y compensación": (4.2, 16.7, 25.0, 37.5),
}

BAREMOS_DOM_A = {
    "Liderazgo y relaciones sociales en el trabajo": (9.1, 17.7, 25.6, 34.8),
    "Control sobre el trabajo": (10.0, 19.0, 29.0, 40.0),
    "Demandas del trabajo": (28.5, 35.0, 41.5, 48.0),
    "Recompensas": (4.5, 12.5, 20.5, 29.0),
}

BAREMOS_DIM_B = {
    "Características del liderazgo": (3.8, 13.5, 25.0, 38.5),
    "Relaciones sociales en el trabajo": (6.3, 14.6, 27.1, 37.5),
    "Retroalimentación del desempeño": (5.0, 20.0, 30.0, 50.0),
    "Claridad de rol": (0.9, 5.0, 15.0, 30.0),
    "Capacitación": (0.9, 16.7, 25.0, 50.0),
    "Participación y manejo del cambio": (16.7, 33.3, 41.7, 58.3),
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": (12.5, 25.0, 37.5, 56.3),
    "Control y autonomía sobre el trabajo": (33.3, 50.0, 66.7, 75.0),
    "Demandas ambientales y de esfuerzo físico": (22.9, 31.3, 39.6, 47.9),
    "Demandas emocionales": (19.4, 27.8, 38.9, 47.2),
    "Demandas cuantitativas": (16.7, 33.3, 41.7, 50.0),
    "Influencia del trabajo sobre el entorno extralaboral": (12.5, 25.0, 31.3, 50.0),
    "Demandas de carga mental": (50.0, 65.0, 75.0, 85.0),
    "Demandas de la jornada de trabajo": (25.0, 37.5, 45.8, 58.3),
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": (0.9, 6.3, 12.5, 18.8),
    "Reconocimiento y compensación": (0.9, 12.5, 25.0, 37.5),
}

BAREMOS_DOM_B = {
    "Liderazgo y relaciones sociales en el trabajo": (8.3, 17.5, 26.7, 38.3),
    "Control sobre el trabajo": (19.4, 26.4, 34.7, 43.1),
    "Demandas del trabajo": (26.9, 33.3, 37.8, 44.2),
    "Recompensas": (2.5, 10.0, 17.5, 27.5),
}

BAREMOS_TOTAL_A = (19.7, 25.8, 31.5, 38.0)
BAREMOS_TOTAL_B = (20.6, 26.0, 31.9, 38.7)
BAREMOS_ESTRES_JEFES = (7.8, 12.6, 17.7, 25.0)
BAREMOS_ESTRES_AUX = (6.5, 11.8, 17.0, 23.4)

# Baremos de dimensiones Extralaborales (Resolución 2646 / Villalobos)
# Tabla 17: Jefatura, profesionales y técnicos (Forma A / grupo "jefes")
BAREMOS_EXTRA_DIM_A = {
    "Tiempo fuera del trabajo": (6.3, 25.0, 37.5, 50.0),
    "Relaciones familiares": (8.3, 25.0, 33.3, 50.0),
    "Comunicación y relaciones interpersonales": (0.9, 10.0, 20.0, 30.0),
    "Situación económica del grupo familiar": (8.3, 25.0, 33.3, 50.0),
    "Características de la vivienda y de su entorno": (5.6, 11.1, 13.9, 22.2),
    "Influencia del entorno extralaboral sobre el trabajo": (8.3, 16.7, 25.0, 41.7),
    "Desplazamiento vivienda-trabajo-vivienda": (0.9, 12.5, 25.0, 43.8),
}

# Tabla 18: Auxiliares y operarios (Forma B / grupo "auxiliares")
BAREMOS_EXTRA_DIM_B = {
    "Tiempo fuera del trabajo": (6.3, 25.0, 37.5, 50.0),
    "Relaciones familiares": (8.3, 25.0, 33.3, 50.0),
    "Comunicación y relaciones interpersonales": (5.0, 15.0, 25.0, 35.0),
    "Situación económica del grupo familiar": (16.7, 25.0, 41.7, 50.0),
    "Características de la vivienda y de su entorno": (5.6, 11.1, 16.7, 27.8),
    "Influencia del entorno extralaboral sobre el trabajo": (0.9, 16.7, 25.0, 41.7),
    "Desplazamiento vivienda-trabajo-vivienda": (0.9, 12.5, 25.0, 43.8),
}

# Baremos total cuestionario Extralaboral (Tablas 17 y 18)
BAREMOS_EXTRA_TOTAL_JEFES = (11.3, 16.9, 22.6, 29.0)
BAREMOS_EXTRA_TOTAL_AUX = (12.9, 17.7, 24.2, 32.3)
BAREMOS_EXTRA_JEFES = BAREMOS_EXTRA_TOTAL_JEFES
BAREMOS_EXTRA_AUX = BAREMOS_EXTRA_TOTAL_AUX

# Baremos total general (Intralaboral + Extralaboral) (Tabla 34)
BAREMOS_TOTAL_GENERAL_A = (18.8, 24.4, 29.5, 35.4)
BAREMOS_TOTAL_GENERAL_B = (19.9, 24.8, 29.5, 35.4)

NIVELES = ("Sin riesgo", "Riesgo bajo", "Riesgo medio", "Riesgo alto", "Riesgo muy alto")


def nivel_riesgo(puntaje: Optional[float], cortes: tuple[float, float, float, float]) -> Optional[str]:
    if puntaje is None:
        return None
    a, b, c, d = cortes
    if puntaje <= a:
        return NIVELES[0]
    if puntaje <= b:
        return NIVELES[1]
    if puntaje <= c:
        return NIVELES[2]
    if puntaje <= d:
        return NIVELES[3]
    return NIVELES[4]


def _raw(choice_index: int, invert: bool, vmax: int) -> int:
    """choice_index 0 = Siempre (izquierda). Riesgo directo: Siempre=vmax."""
    direct = vmax - choice_index
    return choice_index if invert else direct


@dataclass
class DimensionScore:
    nombre: str
    dominio: str
    n_esperados: int
    n_respondidos: int
    bruto: Optional[float]
    transformado: Optional[float]
    nivel: Optional[str]
    incompleta: bool


def score_block(
    answers: dict[int, Optional[int]],
    spec: dict,
    vmax: int,
    baremos_dim: dict[str, tuple],
    baremos_dom: dict[str, tuple] | None = None,
    skip_optional_if_empty: bool = True,
) -> dict:
    dims: list[DimensionScore] = []
    dom_acc: dict[str, list[int]] = {}

    for name, meta in spec.items():
        items = meta["items"]
        invert = meta.get("invert", set())
        optional = meta.get("opcional_jefatura", False) or meta.get("opcional_clientes", False)
        vals = []
        missing = 0
        for i in items:
            v = answers.get(i)
            if v is None:
                missing += 1
                continue
            vals.append(_raw(int(v), i in invert, vmax))
        if optional and not vals:
            continue
        n = len(vals)
        incompleta = n < len(items)
        if n == 0:
            dims.append(DimensionScore(name, meta.get("dominio", ""), len(items), 0, None, None, None, True))
            continue
        bruto = sum(vals)
        factor = n * vmax
        trans = round(bruto / factor * 100, 1)
        cortes = baremos_dim.get(name)
        nivel = nivel_riesgo(trans, cortes) if cortes else None
        dims.append(
            DimensionScore(name, meta.get("dominio", ""), len(items), n, bruto, trans, nivel, incompleta)
        )
        dom = meta.get("dominio")
        if dom:
            dom_acc.setdefault(dom, []).extend(vals)

    dominios = []
    for dom, vals in dom_acc.items():
        bruto = sum(vals)
        trans = round(bruto / (len(vals) * vmax) * 100, 1) if vals else None
        cortes = (baremos_dom or {}).get(dom)
        dominios.append(
            {
                "nombre": dom,
                "n": len(vals),
                "bruto": bruto,
                "transformado": trans,
                "nivel": nivel_riesgo(trans, cortes) if cortes and trans is not None else None,
            }
        )
    return {"dimensiones": [d.__dict__ for d in dims], "dominios": dominios}


def score_persona(
    forma: str,
    intra: dict[int, Optional[int]],
    extra: dict[int, Optional[int]],
    estres: dict[int, Optional[int]],
    grupo: str = "jefes",
) -> dict:
    forma = (forma or "A").upper()
    spec = FORMA_A if forma != "B" else FORMA_B
    vmax = 4
    intra_sc = score_block(
        intra,
        spec,
        vmax,
        BAREMOS_DIM_A if forma != "B" else BAREMOS_DIM_B,
        BAREMOS_DOM_A if forma != "B" else BAREMOS_DOM_B,
    )
    all_vals = []
    for name, meta in spec.items():
        is_opt = meta.get("opcional_jefatura") or meta.get("opcional_clientes")
        if is_opt and not any(intra.get(i) is not None for i in meta["items"]):
            continue
        for i in meta["items"]:
            v = intra.get(i)
            if v is None:
                continue
            all_vals.append(_raw(int(v), i in meta.get("invert", set()), vmax))
    if all_vals:
        total_t = round(sum(all_vals) / (len(all_vals) * vmax) * 100, 1)
        cortes_t = BAREMOS_TOTAL_A if forma != "B" else BAREMOS_TOTAL_B
        esperados = 0
        for m in spec.values():
            is_opt = m.get("opcional_jefatura") or m.get("opcional_clientes")
            if is_opt and not any(intra.get(i) is not None for i in m["items"]):
                continue
            esperados += len(m["items"])
        intra_sc["total"] = {
            "transformado": total_t,
            "nivel": nivel_riesgo(total_t, cortes_t),
            "n": len(all_vals),
            "esperados": esperados,
        }
    else:
        intra_sc["total"] = {"transformado": None, "nivel": None, "n": 0, "esperados": 123 if forma != "B" else 97}

    extra_baremos_dim = BAREMOS_EXTRA_DIM_A if forma != "B" else BAREMOS_EXTRA_DIM_B
    extra_cortes_total = BAREMOS_EXTRA_TOTAL_JEFES if grupo == "jefes" else BAREMOS_EXTRA_TOTAL_AUX
    extra_sc = score_block(
        extra,
        {k: {**v, "dominio": "Extralaboral"} for k, v in EXTRALABORAL.items()},
        4,
        extra_baremos_dim,
        {},
    )
    ev = []
    for meta in EXTRALABORAL.values():
        for i in meta["items"]:
            v = extra.get(i)
            if v is None:
                continue
            ev.append(_raw(int(v), i in meta.get("invert", set()), 4))
    extra_total = round(sum(ev) / (len(ev) * 4) * 100, 1) if ev else None
    extra_sc["total"] = {
        "transformado": extra_total,
        "nivel": nivel_riesgo(extra_total, extra_cortes_total),
        "n": len(ev),
        "esperados": 31,
    }

    sv = [_raw(int(estres[i]), False, 3) for i in ESTRES_ITEMS if estres.get(i) is not None]
    st = round(sum(sv) / (len(sv) * 3) * 100, 1) if sv else None
    estres_sc = {
        "total": {
            "transformado": st,
            "nivel": nivel_riesgo(st, BAREMOS_ESTRES_JEFES if grupo == "jefes" else BAREMOS_ESTRES_AUX),
            "n": len(sv),
            "esperados": 31,
        }
    }

    # Total General (Intralaboral + Extralaboral) según Tabla 34
    general_sc = None
    if all_vals and ev:
        total_items_gen = len(all_vals) + len(ev)
        total_bruto_gen = sum(all_vals) + sum(ev)
        gen_t = round(total_bruto_gen / (total_items_gen * 4) * 100, 1)
        gen_cortes = BAREMOS_TOTAL_GENERAL_A if forma != "B" else BAREMOS_TOTAL_GENERAL_B
        general_sc = {
            "transformado": gen_t,
            "nivel": nivel_riesgo(gen_t, gen_cortes),
            "n": total_items_gen,
            "esperados": esperados + 31,
        }

    return {"forma": forma, "intra": intra_sc, "extra": extra_sc, "estres": estres_sc, "general": general_sc}
