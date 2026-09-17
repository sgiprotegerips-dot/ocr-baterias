"""Materializa puntajes Villalobos y ficha mínima en tablas relacionales."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .db.models import CasoCuadernillo, FichaSociodemografica, ScoreDimension, ScoreDominio, ScoreTotal
from .report.catalog_narratives import codigo_de


def _tipo_cargo_desde_forma(forma: Optional[str]) -> str:
    return "auxiliar_operario" if (forma or "A").upper() == "B" else "profesional_jefatura"


def persist_scores(session: Session, caso: CasoCuadernillo) -> None:
    """Reescribe scores de un caso a partir de scoring_villalobos (JSON)."""
    sc: Dict[str, Any] = caso.scoring_villalobos or {}
    forma = (caso.forma or sc.get("forma") or "A").upper()
    medicion_id = caso.medicion_id

    session.query(ScoreDimension).filter_by(caso_id=caso.id).delete()
    session.query(ScoreDominio).filter_by(caso_id=caso.id).delete()
    session.query(ScoreTotal).filter_by(caso_id=caso.id).delete()

    intra = sc.get("intra") or {}
    for d in intra.get("dimensiones") or []:
        nombre = d.get("nombre") or ""
        session.add(
            ScoreDimension(
                caso_id=caso.id,
                medicion_id=medicion_id,
                instrumento="intra",
                dimension_codigo=codigo_de(nombre, "intra"),
                dimension_nombre=nombre,
                dominio_nombre=d.get("dominio"),
                n_items=int(d.get("n_esperados") or 0),
                n_respondidos=int(d.get("n_respondidos") or d.get("n") or 0),
                bruto=d.get("bruto"),
                transformado=d.get("transformado"),
                nivel=d.get("nivel"),
                incompleta=bool(d.get("incompleta")),
                forma=forma,
            )
        )
    for dom in intra.get("dominios") or []:
        session.add(
            ScoreDominio(
                caso_id=caso.id,
                medicion_id=medicion_id,
                dominio_nombre=dom.get("nombre") or "",
                n_items=int(dom.get("n") or 0),
                bruto=dom.get("bruto"),
                transformado=dom.get("transformado"),
                nivel=dom.get("nivel"),
                forma=forma,
            )
        )

    extra = sc.get("extra") or {}
    for d in extra.get("dimensiones") or []:
        nombre = d.get("nombre") or ""
        session.add(
            ScoreDimension(
                caso_id=caso.id,
                medicion_id=medicion_id,
                instrumento="extra",
                dimension_codigo=codigo_de(nombre, "extra"),
                dimension_nombre=nombre,
                dominio_nombre=d.get("dominio") or "Extralaboral",
                n_items=int(d.get("n_esperados") or 0),
                n_respondidos=int(d.get("n_respondidos") or d.get("n") or 0),
                bruto=d.get("bruto"),
                transformado=d.get("transformado"),
                nivel=d.get("nivel"),
                incompleta=bool(d.get("incompleta")),
                forma=forma,
            )
        )

    def _add_total(instrumento: str, block: Dict[str, Any]) -> None:
        tot = (block or {}).get("total") if instrumento != "general" else (block or {})
        if not tot:
            return
        session.add(
            ScoreTotal(
                caso_id=caso.id,
                medicion_id=medicion_id,
                instrumento=instrumento,
                n_items=int(tot.get("n") or 0),
                n_esperados=int(tot.get("esperados") or tot.get("n") or 0),
                transformado=tot.get("transformado"),
                nivel=tot.get("nivel"),
                forma=forma,
            )
        )

    _add_total("intra", intra)
    _add_total("extra", extra)
    _add_total("estres", sc.get("estres") or {})
    _add_total("general", sc.get("general") or {})


def upsert_ficha_minima(session: Session, caso: CasoCuadernillo) -> FichaSociodemografica:
    ficha = session.query(FichaSociodemografica).filter_by(caso_id=caso.id).first()
    tipo = _tipo_cargo_desde_forma(caso.forma)
    area = caso.area_dependencia
    ocupacion = caso.cargo
    if not ficha:
        ficha = FichaSociodemografica(
            caso_id=caso.id,
            tipo_cargo=tipo,
            area_trabajo=area,
            ocupacion=ocupacion,
            fuente="ocr_parcial",
        )
        session.add(ficha)
        return ficha
    if not ficha.tipo_cargo:
        ficha.tipo_cargo = tipo
    if area and not ficha.area_trabajo:
        ficha.area_trabajo = area
    if ocupacion and not ficha.ocupacion:
        ficha.ocupacion = ocupacion
    return ficha
