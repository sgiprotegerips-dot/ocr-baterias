"""Esquema relacional v2: tablas nuevas, catálogo y materialización de scores."""

from sqlalchemy import inspect

from src.bateria.db.migrate_v2 import migrate_v2
from src.bateria.db.models import CatalogoDimension, CasoCuadernillo, ScoreDimension
from src.bateria.db.session import SyncSessionLocal, sync_engine
from src.bateria.score_store import persist_scores
from src.bateria.scoring import score_persona


NUEVAS = {
    "fichas_sociodemograficas",
    "scores_dimension",
    "scores_dominio",
    "scores_total",
    "catalogo_dimensiones",
    "catalogo_baremos",
    "batch_jobs",
}


def test_migrate_v2_crea_tablas_y_es_idempotente():
    info1 = migrate_v2()
    info2 = migrate_v2()
    tablas = set(inspect(sync_engine).get_table_names())
    assert NUEVAS.issubset(tablas)
    assert info1["catalogo_dimensiones"] >= 19
    assert info2["catalogo_dimensiones"] == info1["catalogo_dimensiones"]
    assert info2["catalogo_baremos"] == info1["catalogo_baremos"]


def test_fk_usuario_empresa_en_metadata():
    from src.bateria.db.models import Usuario

    fks = {fk.target_fullname for fk in Usuario.__table__.foreign_keys}
    assert "empresas.id" in fks


def test_catalogo_cubre_forma_a_y_extra():
    from src.bateria.scoring import EXTRALABORAL, FORMA_A

    session = SyncSessionLocal()
    try:
        migrate_v2()
        nombres = {r.nombre for r in session.query(CatalogoDimension).all()}
        for dim in FORMA_A:
            assert dim in nombres, dim
        for dim in EXTRALABORAL:
            assert dim in nombres, dim
        assert "Síntomas de estrés" in nombres
    finally:
        session.close()


def test_persist_scores_forma_a():
    migrate_v2()
    session = SyncSessionLocal()
    try:
        caso = session.query(CasoCuadernillo).first()
        if caso is None:
            return
        intra = {i: 0 for i in range(1, 124)}
        extra = {i: 2 for i in range(1, 32)}
        estres = {i: 3 for i in range(1, 32)}
        original_sc = caso.scoring_villalobos
        original_forma = caso.forma
        caso.scoring_villalobos = score_persona("A", intra, extra, estres)
        caso.forma = "A"
        persist_scores(session, caso)
        session.flush()
        dims = session.query(ScoreDimension).filter_by(caso_id=caso.id, instrumento="intra").all()
        assert len(dims) >= 18
        assert all(d.dimension_codigo.startswith("INTRA_") for d in dims)
        caso.scoring_villalobos = original_sc
        caso.forma = original_forma
        persist_scores(session, caso)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    test_migrate_v2_crea_tablas_y_es_idempotente()
    print(" test_migrate_v2_crea_tablas_y_es_idempotente PASSED")
    test_fk_usuario_empresa_en_metadata()
    print(" test_fk_usuario_empresa_en_metadata PASSED")
    test_catalogo_cubre_forma_a_y_extra()
    print(" test_catalogo_cubre_forma_a_y_extra PASSED")
    test_persist_scores_forma_a()
    print(" test_persist_scores_forma_a PASSED")
    print(" All schema v2 tests passed!")
