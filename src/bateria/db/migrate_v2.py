"""Migración idempotente v2: tablas de scores, ficha, catálogos y lotes."""

from __future__ import annotations

from sqlalchemy import inspect, text

from ..report.catalog_narratives import baremos_para_siembra, catalogo_para_siembra
from .models import (
    BatchJob,
    CatalogoBaremo,
    CatalogoDimension,
    CasoCuadernillo,
    FichaSociodemografica,
    ScoreDimension,
)
from .session import Base, SyncSessionLocal, sync_engine
from ..score_store import persist_scores, upsert_ficha_minima


NUEVAS_TABLAS = (
    "fichas_sociodemograficas",
    "scores_dimension",
    "scores_dominio",
    "scores_total",
    "catalogo_dimensiones",
    "catalogo_baremos",
    "batch_jobs",
)


def _ensure_column(conn, table: str, column: str, ddl: str) -> None:
    try:
        cols = {c["name"] for c in inspect(sync_engine).get_columns(table)}
    except Exception:
        return
    if column in cols:
        return
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def _ensure_indexes(conn) -> None:
    _ensure_column(conn, "empresas", "psicologa_responsable_id", "psicologa_responsable_id VARCHAR(36)")
    statements = [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_medicion_empresa_campana ON mediciones (empresa_id, codigo_campana)",
        "CREATE INDEX IF NOT EXISTS ix_medicion_estado ON mediciones (estado)",
        "CREATE INDEX IF NOT EXISTS ix_caso_medicion_estado ON casos_cuadernillos (medicion_id, estado)",
        "CREATE INDEX IF NOT EXISTS ix_caso_medicion_forma ON casos_cuadernillos (medicion_id, forma)",
    ]
    for sql in statements:
        try:
            conn.execute(text(sql))
        except Exception:
            pass


def seed_catalogos(session) -> None:
    existentes = {row.codigo for row in session.query(CatalogoDimension).all()}
    for fila in catalogo_para_siembra():
        if fila["codigo"] in existentes:
            continue
        session.add(CatalogoDimension(**fila))
        existentes.add(fila["codigo"])
    session.flush()

    baremo_existentes = {
        (b.dimension_codigo, b.forma) for b in session.query(CatalogoBaremo).all()
    }
    dim_ok = {row.codigo for row in session.query(CatalogoDimension).all()}
    for codigo, forma, cortes in baremos_para_siembra():
        if codigo not in dim_ok:
            continue
        if (codigo, forma) in baremo_existentes:
            continue
        session.add(
            CatalogoBaremo(
                dimension_codigo=codigo,
                forma=forma,
                corte_sin=cortes[0],
                corte_bajo=cortes[1],
                corte_medio=cortes[2],
                corte_alto=cortes[3],
            )
        )
        baremo_existentes.add((codigo, forma))


def backfill_casos(session) -> int:
    """Vuelca scoring JSON → tablas y crea ficha mínima. Idempotente (delete+insert por caso)."""
    n = 0
    casos = session.query(CasoCuadernillo).all()
    for caso in casos:
        persist_scores(session, caso)
        upsert_ficha_minima(session, caso)
        n += 1
    return n


def migrate_v2() -> dict:
    Base.metadata.create_all(bind=sync_engine)
    with sync_engine.begin() as conn:
        _ensure_indexes(conn)

    session = SyncSessionLocal()
    try:
        seed_catalogos(session)
        n_casos = backfill_casos(session)
        session.commit()
        insp = inspect(sync_engine)
        tablas = set(insp.get_table_names())
        return {
            "ok": True,
            "tablas_nuevas": [t for t in NUEVAS_TABLAS if t in tablas],
            "casos_materializados": n_casos,
            "catalogo_dimensiones": session.query(CatalogoDimension).count(),
            "catalogo_baremos": session.query(CatalogoBaremo).count(),
            "scores_dimension": session.query(ScoreDimension).count(),
            "fichas": session.query(FichaSociodemografica).count(),
            "batch_jobs": session.query(BatchJob).count(),
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    info = migrate_v2()
    print("[OK] migrate_v2", info)
