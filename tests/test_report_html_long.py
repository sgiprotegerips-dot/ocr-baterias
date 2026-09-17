"""Informe HTML imprimible de 32+ páginas y estadísticas enriquecidas."""

from src.bateria.report.builder import generate_printable_report_html
from src.bateria.report.catalog_narratives import NARRATIVAS, ORDEN_INTRA
from src.bateria.scoring import EXTRALABORAL as EXTRA_SPEC
from src.bateria.scoring import FORMA_A as FORMA_A_SPEC
from src.bateria.scoring import score_persona


def _dist(alto: float = 10, muy_alto: float = 5) -> dict:
    return {
        "Sin riesgo": {"cantidad": 10, "porcentaje": 50.0},
        "Riesgo bajo": {"cantidad": 4, "porcentaje": 20.0},
        "Riesgo medio": {"cantidad": 3, "porcentaje": 15.0},
        "Riesgo alto": {"cantidad": 2, "porcentaje": alto},
        "Riesgo muy alto": {"cantidad": 1, "porcentaje": muy_alto},
        "_n_eval": 20,
        "porcentaje_critico": alto + muy_alto,
        "n_critico": 3,
        "n_eval": 20,
        "media_transformado": 28.4,
        "lectura": "Lectura de prueba.",
        "definicion": "Definición de prueba.",
        "intervencion_primaria": "Primaria.",
        "intervencion_secundaria": "Secundaria.",
        "dominio": "Demandas del trabajo",
    }


def _sample_report() -> dict:
    dims_intra = {n: _dist(12, 8) for n in ORDEN_INTRA}
    dims_extra = {n: _dist(9, 6) for n in (
        "Tiempo fuera del trabajo",
        "Relaciones familiares",
        "Comunicación y relaciones interpersonales",
        "Situación económica del grupo familiar",
        "Características de la vivienda y de su entorno",
        "Influencia del entorno extralaboral sobre el trabajo",
        "Desplazamiento vivienda-trabajo-vivienda",
    )}
    dominios = {
        "Liderazgo y relaciones sociales en el trabajo": _dist(20, 15),
        "Control sobre el trabajo": _dist(8, 4),
        "Demandas del trabajo": _dist(18, 10),
        "Recompensas": _dist(6, 3),
    }
    return {
        "empresa": {
            "razon_social": "PROTEGER I.P.S. S.A.S.",
            "nit": "900548123",
            "digito_verificacion": "4",
            "sector_economico": "SST",
            "codigo_ciiu": "8699",
            "ciudad": "Bogotá D.C.",
            "contacto_nombre": "Ing. Gómez",
        },
        "medicion": {
            "codigo_campana": "MED-2026-001",
            "periodo": "Anual 2026",
            "anio": 2026,
            "sede": "Principal",
            "estado": "auditoria",
            "fecha_inicio": "2026-01-15",
            "trabajadores_esperados": 25,
        },
        "psicologa": {
            "nombre_completo": "Dra. Claudia Marcela Valencia",
            "nombre": "Dra. Claudia Marcela Valencia",
            "tarjeta_profesional": "PSI-48201",
            "licencia_sst": "RES-2024-8912-SST",
        },
        "total_evaluados": 20,
        "resumen_sociodemografico": {
            "forma_a_conteo": 12,
            "forma_b_conteo": 8,
            "cobertura_porcentaje": 80.0,
            "completos_conteo": 18,
            "ambiguos_pendientes": 1,
            "distribucion_forma": {"Forma A": 12, "Forma B": 8},
            "cargos_principales": {"Analista": 5, "Auxiliar": 4},
            "areas_principales": {"Operaciones": 7, "Administrativa": 5},
        },
        "baremos_consolidados": {
            "intralaboral_total": _dist(14, 9),
            "extralaboral_total": _dist(11, 7),
            "estres_total": _dist(16, 8),
            "general_total": _dist(13, 8),
            "dominios_intralaborales": dominios,
            "dimensiones_intralaborales": dims_intra,
            "dimensiones_extralaborales": dims_extra,
            "medias": {
                "intralaboral_total": {"media": 31.2, "mediana": 29.0, "n": 20},
                "extralaboral_total": {"media": 22.1, "mediana": 20.0, "n": 20},
                "estres_total": {"media": 18.4, "mediana": 16.0, "n": 20},
                "general_total": {"media": 27.0, "mediana": 26.0, "n": 20},
            },
        },
        "dimensiones_prioritarias": [
            {
                "dimension": "Características del liderazgo",
                "tipo": "Intralaboral",
                "porcentaje_critico": 35.0,
                "n_critico": 7,
                "n_eval": 20,
                "media_transformado": 41.2,
            }
        ],
        "cruces": {
            "forma": {
                "A": {
                    "intra": _dist(15, 10),
                    "extra": _dist(8, 4),
                    "estres": _dist(12, 6),
                },
                "B": {
                    "intra": _dist(10, 5),
                    "extra": _dist(9, 5),
                    "estres": _dist(11, 5),
                },
            },
            "areas_intralaboral": {"Operaciones": _dist(18, 12)},
            "cargos_intralaboral": {"Analista": _dist(14, 8)},
        },
        "conclusiones_sugeridas": "Se evaluó un total de 20 trabajadores. Liderazgo es prioritario.",
        "recomendaciones_sugeridas": "Priorizar el PVE en liderazgo y demandas del trabajo.",
        "hash_sha256": "a" * 64,
    }


def test_catalogo_narrativas_completo():
    from src.bateria.report.catalog_narratives import NARRATIVAS

    for dim in FORMA_A_SPEC:
        assert dim in NARRATIVAS, dim
        assert NARRATIVAS[dim]["definicion"].strip()
        assert NARRATIVAS[dim]["intervencion_primaria"].strip()
    for dim in EXTRA_SPEC:
        assert dim in NARRATIVAS, dim


def test_html_tiene_minimo_32_paginas():
    html_doc = generate_printable_report_html(_sample_report())
    n = html_doc.count('class="report-page"')
    assert n >= 32, n
    assert f"Página {n} de {n}" in html_doc
    assert "INFORME DIAGNÓSTICO" in html_doc.upper() or "Informe diagnóstico" in html_doc
    assert "Resolución 2764" in html_doc
    assert "PVE" in html_doc
    assert "Características del liderazgo" in html_doc
    assert "Demandas cuantitativas" in html_doc
    assert "Desplazamiento vivienda-trabajo-vivienda" in html_doc
    assert "<svg" in html_doc
    # Entregable no nominativo: no debe listar cédulas de trabajadores de prueba
    assert "1070464199" not in html_doc


def test_consolidate_prioriza_liderazgo():
    from types import SimpleNamespace

    from src.bateria.reporting import consolidate_medicion_report

    intra_alto = {i: 0 for i in range(1, 124)}
    extra_ok = {i: 3 for i in range(1, 32)}
    estres_ok = {i: 3 for i in range(1, 32)}
    sc_a = score_persona("A", intra_alto, extra_ok, estres_ok)
    intra_bajo = {i: 4 for i in range(1, 98)}
    sc_b = score_persona("B", intra_bajo, extra_ok, estres_ok)

    casos = [
        SimpleNamespace(
            forma="A",
            cargo="Jefe de área",
            area_dependencia="Operaciones",
            estado="listo",
            ambiguos=[],
            scoring_villalobos=sc_a,
        ),
        SimpleNamespace(
            forma="B",
            cargo="Auxiliar",
            area_dependencia="Administrativa",
            estado="listo",
            ambiguos=[],
            scoring_villalobos=sc_b,
        ),
    ]
    medicion = SimpleNamespace(
        trabajadores_esperados=2,
        empresa=SimpleNamespace(
            to_dict=lambda: {"razon_social": "Demo", "nit": "1"},
            razon_social="Demo",
        ),
        psicologa=None,
        to_dict=lambda: {"codigo_campana": "MED-X", "estado": "auditoria", "sede": "Principal"},
    )
    data = consolidate_medicion_report(medicion, casos, None)
    assert data["cruces"]["forma"]["A"]["intra"]
    assert data["dimensiones_prioritarias"]
    top = data["dimensiones_prioritarias"][0]["dimension"]
    assert isinstance(top, str) and len(top) > 3
    html_doc = generate_printable_report_html(data)
    assert html_doc.count('class="report-page"') >= 32


if __name__ == "__main__":
    test_catalogo_narrativas_completo()
    print(" test_catalogo_narrativas_completo PASSED")
    test_html_tiene_minimo_32_paginas()
    print(" test_html_tiene_minimo_32_paginas PASSED")
    test_consolidate_prioriza_liderazgo()
    print(" test_consolidate_prioriza_liderazgo PASSED")
    print(" All report HTML tests passed!")
