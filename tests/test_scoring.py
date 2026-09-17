from src.bateria.scoring import FORMA_A, FORMA_B, score_persona


def test_forma_a_cubre_123():
    items = set()
    for meta in FORMA_A.values():
        items.update(meta["items"])
    assert items == set(range(1, 124))


def test_forma_b_cubre_97():
    items = set()
    for meta in FORMA_B.values():
        items.update(meta["items"])
    assert items == set(range(1, 98))


def test_score_vacio():
    sc = score_persona("A", {}, {}, {})
    assert sc["intra"]["total"]["n"] == 0
    assert sc["intra"]["total"]["transformado"] is None


def test_score_siempre_riesgo():
    intra = {i: 0 for i in range(1, 124)}  # Siempre = índice 0
    sc = score_persona("A", intra, {}, {})
    assert sc["intra"]["total"]["n"] == 123
    assert sc["intra"]["total"]["transformado"] is not None


def test_score_forma_b():
    intra = {i: 0 for i in range(1, 98)}
    sc = score_persona("B", intra, {}, {})
    assert sc["intra"]["total"]["n"] == 97
    assert sc["intra"]["total"]["transformado"] is not None
    assert sc["intra"]["total"]["nivel"] is not None


def test_score_estres_nunca_y_siempre():
    # En Estrés: Col 3 = Nunca (0 puntos), Col 0 = Siempre (3 puntos)
    estres_nunca = {i: 3 for i in range(1, 32)}
    sc_nunca = score_persona("A", {}, {}, estres_nunca)
    assert sc_nunca["estres"]["total"]["transformado"] == 0.0
    assert sc_nunca["estres"]["total"]["nivel"] == "Sin riesgo"

    estres_siempre = {i: 0 for i in range(1, 32)}
    sc_siempre = score_persona("A", {}, {}, estres_siempre)
    assert sc_siempre["estres"]["total"]["transformado"] == 100.0
    assert sc_siempre["estres"]["total"]["nivel"] == "Riesgo muy alto"


def test_extralaboral_baremos_dimensions():
    from src.bateria.scoring import BAREMOS_EXTRA_DIM_A, nivel_riesgo
    # Verificar los casos exactos reportados por el usuario
    # Desplazamiento: 62.5 -> Riesgo muy alto
    assert nivel_riesgo(62.5, BAREMOS_EXTRA_DIM_A["Desplazamiento vivienda-trabajo-vivienda"]) == "Riesgo muy alto"
    # Características vivienda: 19.4 -> Riesgo alto
    assert nivel_riesgo(19.4, BAREMOS_EXTRA_DIM_A["Características de la vivienda y de su entorno"]) == "Riesgo alto"
    # Tiempo fuera: 12.5 -> Riesgo bajo
    assert nivel_riesgo(12.5, BAREMOS_EXTRA_DIM_A["Tiempo fuera del trabajo"]) == "Riesgo bajo"
    # Comunicación: 5.0 -> Riesgo bajo
    assert nivel_riesgo(5.0, BAREMOS_EXTRA_DIM_A["Comunicación y relaciones interpersonales"]) == "Riesgo bajo"
    # Relaciones familiares: 0.0 -> Sin riesgo
    assert nivel_riesgo(0.0, BAREMOS_EXTRA_DIM_A["Relaciones familiares"]) == "Sin riesgo"
    # Influencia: 25.0 -> Riesgo medio
    assert nivel_riesgo(25.0, BAREMOS_EXTRA_DIM_A["Influencia del entorno extralaboral sobre el trabajo"]) == "Riesgo medio"
    # Situación económica: 25.0 -> Riesgo bajo
    assert nivel_riesgo(25.0, BAREMOS_EXTRA_DIM_A["Situación económica del grupo familiar"]) == "Riesgo bajo"

    # Verificar que score_persona califica todas las dimensiones de Extralaboral sin dejar ninguna en Incompleta o None
    extra_sample = {i: 2 for i in range(1, 32)}
    sc = score_persona("A", {}, extra_sample, {})
    dims = sc["extra"]["dimensiones"]
    assert len(dims) == 7
    for d in dims:
        assert d["n_respondidos"] == d["n_esperados"]
        assert d["incompleta"] is False
        assert d["nivel"] in ("Sin riesgo", "Riesgo bajo", "Riesgo medio", "Riesgo alto", "Riesgo muy alto")
    assert sc["extra"]["total"]["nivel"] is not None


if __name__ == "__main__":
    test_forma_a_cubre_123()
    test_forma_b_cubre_97()
    test_score_vacio()
    test_score_siempre_riesgo()
    test_score_forma_b()
    test_score_estres_nunca_y_siempre()
    test_extralaboral_baremos_dimensions()
    print(" All scoring tests passed!")




