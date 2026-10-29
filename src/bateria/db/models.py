"""Modelos relacionales SQLAlchemy 2.0 para la plataforma de Baterías de Riesgo Psicosocial.
Cumplimiento normativo: Resoluciones 2646 de 2008 y 2764 de 2022 del Ministerio del Trabajo.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base

ROLES = ("admin", "psicologa", "operador", "cliente_empresa")
ESTADOS_MEDICION = ("recoleccion", "auditoria", "aprobada", "cerrada")
FORMAS = ("A", "B")
INSTRUMENTOS = ("intra", "extra", "estres", "general")
FUENTES_FICHA = ("ocr_parcial", "manual", "omr_ficha")


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False, default="psicologa")  # admin, psicologa, operador, cliente_empresa
    cedula: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tarjeta_profesional: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    licencia_sst: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dpto_licencia_sst: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    empresa_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("empresas.id", ondelete="SET NULL", use_alter=True, name="fk_usuarios_empresa_id"),
        nullable=True,
        index=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    mediciones: Mapped[List[Medicion]] = relationship("Medicion", back_populates="psicologa", foreign_keys="Medicion.psicologa_id")
    empresa: Mapped[Optional["Empresa"]] = relationship(
        "Empresa", back_populates="usuarios_cliente", foreign_keys=[empresa_id]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "nombre": self.nombre_completo,
            "nombre_completo": self.nombre_completo,
            "rol": self.rol,
            "cedula": self.cedula,
            "tarjeta_profesional": self.tarjeta_profesional,
            "licencia_so": self.licencia_sst,
            "licencia_sst": self.licencia_sst,
            "dpto_licencia_sst": self.dpto_licencia_sst,
            "empresa_id": self.empresa_id,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    nit: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    digito_verificacion: Mapped[str] = mapped_column(String(2), nullable=False)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    sector_economico: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    codigo_ciiu: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contacto_nombre: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contacto_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contacto_telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    psicologa_responsable_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mediciones: Mapped[List[Medicion]] = relationship("Medicion", back_populates="empresa", cascade="all, delete-orphan", lazy="selectin")
    usuarios_cliente: Mapped[List["Usuario"]] = relationship(
        "Usuario", back_populates="empresa", foreign_keys="Usuario.empresa_id", lazy="selectin"
    )
    psicologa_responsable: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[psicologa_responsable_id], lazy="selectin"
    )

    def to_dict(self) -> Dict[str, Any]:
        portal_user = self.usuarios_cliente[0] if self.usuarios_cliente else None
        return {
            "id": self.id,
            "nit": self.nit,
            "digito_verificacion": self.digito_verificacion,
            "nit_completo": f"{self.nit}-{self.digito_verificacion}",
            "razon_social": self.razon_social,
            "sector_economico": self.sector_economico,
            "codigo_ciiu": self.codigo_ciiu,
            "ciudad": self.ciudad,
            "direccion": self.direccion,
            "contacto_nombre": self.contacto_nombre,
            "contacto_email": self.contacto_email,
            "contacto_telefono": self.contacto_telefono,
            "psicologa_responsable_id": self.psicologa_responsable_id,
            "psicologa_responsable_nombre": (
                self.psicologa_responsable.nombre_completo if self.psicologa_responsable else None
            ),
            "portal_user_id": portal_user.id if portal_user else None,
            "portal_nombre": portal_user.nombre_completo if portal_user else None,
            "portal_email": portal_user.email if portal_user else None,
            "portal_activo": portal_user.activo if portal_user else True,
            "activo": self.activo,
            "mediciones_count": len(self.mediciones) if self.mediciones else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Medicion(Base):
    __tablename__ = "mediciones"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo_campana", name="uq_medicion_empresa_campana"),
        Index("ix_medicion_estado", "estado"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    empresa_id: Mapped[str] = mapped_column(String(36), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True)
    psicologa_id: Mapped[str] = mapped_column(String(36), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    codigo_campana: Mapped[str] = mapped_column(String(50), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(50), default="Anual")
    sede: Mapped[str] = mapped_column(String(150), default="Principal")
    estado: Mapped[str] = mapped_column(String(50), default="recoleccion")  # recoleccion, auditoria, aprobada, cerrada
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cierre: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    trabajadores_esperados: Mapped[int] = mapped_column(Integer, default=0)
    hash_integridad_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    empresa: Mapped[Empresa] = relationship("Empresa", back_populates="mediciones", lazy="selectin")
    psicologa: Mapped[Usuario] = relationship("Usuario", back_populates="mediciones", foreign_keys=[psicologa_id], lazy="selectin")
    casos: Mapped[List[CasoCuadernillo]] = relationship("CasoCuadernillo", back_populates="medicion", cascade="all, delete-orphan", lazy="selectin")
    nomina: Mapped[List["TrabajadorNomina"]] = relationship("TrabajadorNomina", back_populates="medicion", cascade="all, delete-orphan", lazy="selectin")
    informe: Mapped[Optional[InformeDiagnostico]] = relationship("InformeDiagnostico", back_populates="medicion", uselist=False, lazy="selectin")
    lotes: Mapped[List["BatchJob"]] = relationship("BatchJob", back_populates="medicion", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "empresa_nombre": self.empresa.razon_social if self.empresa else None,
            "empresa_nit": f"{self.empresa.nit}-{self.empresa.digito_verificacion}" if self.empresa else None,
            "psicologa_id": self.psicologa_id,
            "psicologa_nombre": self.psicologa.nombre_completo if self.psicologa else None,
            "psicologa_licencia": self.psicologa.licencia_sst if self.psicologa else None,
            "codigo_campana": self.codigo_campana,
            "nombre": f"{self.codigo_campana} · {self.periodo}",
            "anio": self.anio,
            "periodo": self.periodo,
            "sede": self.sede,
            "estado": self.estado,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_cierre": self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            "trabajadores_esperados": self.trabajadores_esperados,
            "trabajadores_leidos": len(self.casos) if self.casos else 0,
            "nomina_count": len(self.nomina) if self.nomina else 0,
            "hash_integridad_sha256": self.hash_integridad_sha256,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CasoCuadernillo(Base):
    __tablename__ = "casos_cuadernillos"
    __table_args__ = (
        Index("ix_caso_medicion_estado", "medicion_id", "estado"),
        Index("ix_caso_medicion_forma", "medicion_id", "forma"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True)
    caso_uid: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    archivo_pdf: Mapped[str] = mapped_column(String(255), nullable=False)
    forma: Mapped[str] = mapped_column(String(5), default="A")
    id_documento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    nombre_trabajador: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cargo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    area_dependencia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fecha_aplicacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estado: Mapped[str] = mapped_column(String(50), default="listo", index=True)  # listo, doble_marca, faltan_datos
    intra_respuestas: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    extra_respuestas: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    estres_respuestas: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    scoring_villalobos: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    paginas_metadata: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    pdf_ordenado_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    medicion: Mapped[Medicion] = relationship("Medicion", back_populates="casos", lazy="selectin")
    ambiguos: Mapped[List[MarcaAmbigua]] = relationship("MarcaAmbigua", back_populates="caso", cascade="all, delete-orphan", lazy="selectin")
    ficha: Mapped[Optional["FichaSociodemografica"]] = relationship(
        "FichaSociodemografica", back_populates="caso", uselist=False, cascade="all, delete-orphan"
    )
    scores_dim: Mapped[List["ScoreDimension"]] = relationship(
        "ScoreDimension", back_populates="caso", cascade="all, delete-orphan"
    )
    scores_dom: Mapped[List["ScoreDominio"]] = relationship(
        "ScoreDominio", back_populates="caso", cascade="all, delete-orphan"
    )
    scores_tot: Mapped[List["ScoreTotal"]] = relationship(
        "ScoreTotal", back_populates="caso", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caso_id": self.caso_uid,
            "medicion_id": self.medicion_id,
            "archivo": self.archivo_pdf,
            "forma": self.forma,
            "id_documento": self.id_documento,
            "identidad": {
                "nombre": self.nombre_trabajador,
                "cargo": self.cargo,
                "dependencia": self.area_dependencia,
                "fecha": self.fecha_aplicacion,
                "id_documento": self.id_documento,
            },
            "estado": self.estado,
            "intra": self.intra_respuestas,
            "extra": self.extra_respuestas,
            "estres": self.estres_respuestas,
            "scoring": self.scoring_villalobos,
            "paginas": self.paginas_metadata,
            "pdf_ordenado": self.pdf_ordenado_path,
            "ambiguos": [a.to_dict() for a in self.ambiguos] if self.ambiguos else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MarcaAmbigua(Base):
    __tablename__ = "marcas_ambiguas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    caso_id: Mapped[str] = mapped_column(String(36), ForeignKey("casos_cuadernillos.id", ondelete="CASCADE"), nullable=False, index=True)
    item_num: Mapped[int] = mapped_column(Integer, nullable=False)
    bloque: Mapped[str] = mapped_column(String(20), nullable=False)  # intra, extra, estres
    pagina_fisica: Mapped[int] = mapped_column(Integer, nullable=False)
    opciones_detectadas: Mapped[List[int]] = mapped_column(JSON, default=list)
    decision: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decidido_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fecha_decision: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    crop_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    caso: Mapped[CasoCuadernillo] = relationship("CasoCuadernillo", back_populates="ambiguos")

    @property
    def resuelta(self) -> bool:
        return self.decision is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item": self.item_num,
            "bloque": self.bloque,
            "pagina": self.pagina_fisica,
            "marcadas": self.opciones_detectadas,
            "decision": self.decision,
            "resuelta": self.resuelta,
            "decidido_por": self.decidido_por,
            "fecha_decision": self.fecha_decision.isoformat() if self.fecha_decision else None,
            "crop": self.crop_path,
        }


class InformeDiagnostico(Base):
    __tablename__ = "informes_diagnostico"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("mediciones.id", ondelete="RESTRICT"), unique=True, nullable=False)
    psicologa_id: Mapped[str] = mapped_column(String(36), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    resumen_sociodemografico: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    baremos_consolidados: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    conclusiones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recomendaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_informe_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    excel_maestro_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sellado_inmutable: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    medicion: Mapped[Medicion] = relationship("Medicion", back_populates="informe")
    psicologa: Mapped[Usuario] = relationship("Usuario")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "medicion_id": self.medicion_id,
            "psicologa_id": self.psicologa_id,
            "psicologa_nombre": self.psicologa.nombre_completo if self.psicologa else None,
            "psicologa_licencia": self.psicologa.licencia_sst if self.psicologa else None,
            "psicologa_tp": self.psicologa.tarjeta_profesional if self.psicologa else None,
            "version": self.version,
            "resumen_sociodemografico": self.resumen_sociodemografico,
            "baremos_consolidados": self.baremos_consolidados,
            "conclusiones": self.conclusiones,
            "recomendaciones": self.recomendaciones,
            "pdf_informe_path": self.pdf_informe_path,
            "excel_maestro_path": self.excel_maestro_path,
            "hash_sha256": self.hash_sha256,
            "sellado_inmutable": self.sellado_inmutable,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
        }


class HistoricoCustodia(Base):
    __tablename__ = "historico_custodia"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    informe_id: Mapped[str] = mapped_column(String(36), ForeignKey("informes_diagnostico.id", ondelete="RESTRICT"), nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    snapshot_completo_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    archivo_zip_path: Mapped[str] = mapped_column(String(255), nullable=False)
    firmado_por_licencia: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp_sellado: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    usuario_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    datos_anteriores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    datos_nuevos: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    usuario: Mapped[Optional[Usuario]] = relationship("Usuario")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "usuario_email": self.usuario.email if self.usuario else "Sistema",
            "accion": self.accion,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "ip_address": self.ip_address,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
        }


class FichaSociodemografica(Base):
    """Ficha de Datos Generales (págs. 2–5). 1:1 con el cuadernillo."""

    __tablename__ = "fichas_sociodemograficas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    caso_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("casos_cuadernillos.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    sexo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    anio_nacimiento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    edad_calculada: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estado_civil: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nivel_estudios: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    ocupacion: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    lugar_residencia_depto: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    lugar_residencia_mpio: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    estrato: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tipo_vivienda: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    personas_a_cargo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lugar_trabajo_ciudad: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    lugar_trabajo_depto: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    antiguedad_empresa_anios: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    antiguedad_cargo_anios: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tipo_cargo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    area_trabajo: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    tipo_contrato: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    horas_diarias: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tipo_salario: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    fuente: Mapped[str] = mapped_column(String(20), default="ocr_parcial", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    caso: Mapped[CasoCuadernillo] = relationship("CasoCuadernillo", back_populates="ficha")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caso_id": self.caso_id,
            "sexo": self.sexo,
            "anio_nacimiento": self.anio_nacimiento,
            "edad_calculada": self.edad_calculada,
            "estado_civil": self.estado_civil,
            "nivel_estudios": self.nivel_estudios,
            "ocupacion": self.ocupacion,
            "lugar_residencia_depto": self.lugar_residencia_depto,
            "lugar_residencia_mpio": self.lugar_residencia_mpio,
            "estrato": self.estrato,
            "tipo_vivienda": self.tipo_vivienda,
            "personas_a_cargo": self.personas_a_cargo,
            "lugar_trabajo_ciudad": self.lugar_trabajo_ciudad,
            "lugar_trabajo_depto": self.lugar_trabajo_depto,
            "antiguedad_empresa_anios": self.antiguedad_empresa_anios,
            "antiguedad_cargo_anios": self.antiguedad_cargo_anios,
            "tipo_cargo": self.tipo_cargo,
            "area_trabajo": self.area_trabajo,
            "tipo_contrato": self.tipo_contrato,
            "horas_diarias": self.horas_diarias,
            "tipo_salario": self.tipo_salario,
            "fuente": self.fuente,
        }


class ScoreDimension(Base):
    __tablename__ = "scores_dimension"
    __table_args__ = (
        Index("ix_score_dim_medicion_instrumento_nivel", "medicion_id", "instrumento", "nivel"),
        Index("ix_score_dim_caso", "caso_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    caso_id: Mapped[str] = mapped_column(String(36), ForeignKey("casos_cuadernillos.id", ondelete="CASCADE"), nullable=False)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True)
    instrumento: Mapped[str] = mapped_column(String(20), nullable=False)
    dimension_codigo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    dimension_nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    dominio_nombre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    n_items: Mapped[int] = mapped_column(Integer, default=0)
    n_respondidos: Mapped[int] = mapped_column(Integer, default=0)
    bruto: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transformado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nivel: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    incompleta: Mapped[bool] = mapped_column(Boolean, default=False)
    forma: Mapped[str] = mapped_column(String(5), default="A")

    caso: Mapped[CasoCuadernillo] = relationship("CasoCuadernillo", back_populates="scores_dim")


class ScoreDominio(Base):
    __tablename__ = "scores_dominio"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    caso_id: Mapped[str] = mapped_column(String(36), ForeignKey("casos_cuadernillos.id", ondelete="CASCADE"), nullable=False, index=True)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True)
    dominio_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    n_items: Mapped[int] = mapped_column(Integer, default=0)
    bruto: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transformado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nivel: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    forma: Mapped[str] = mapped_column(String(5), default="A")

    caso: Mapped[CasoCuadernillo] = relationship("CasoCuadernillo", back_populates="scores_dom")


class ScoreTotal(Base):
    __tablename__ = "scores_total"
    __table_args__ = (
        UniqueConstraint("caso_id", "instrumento", name="uq_score_total_caso_instrumento"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    caso_id: Mapped[str] = mapped_column(String(36), ForeignKey("casos_cuadernillos.id", ondelete="CASCADE"), nullable=False, index=True)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True)
    instrumento: Mapped[str] = mapped_column(String(20), nullable=False)
    n_items: Mapped[int] = mapped_column(Integer, default=0)
    n_esperados: Mapped[int] = mapped_column(Integer, default=0)
    transformado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nivel: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    forma: Mapped[str] = mapped_column(String(5), default="A")

    caso: Mapped[CasoCuadernillo] = relationship("CasoCuadernillo", back_populates="scores_tot")


class CatalogoDimension(Base):
    __tablename__ = "catalogo_dimensiones"

    codigo: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    instrumento: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    dominio: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    definicion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    interpretacion_alto: Mapped[str] = mapped_column(Text, nullable=False, default="")
    intervencion_primaria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    intervencion_secundaria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    orden: Mapped[int] = mapped_column(Integer, default=0)


class CatalogoBaremo(Base):
    __tablename__ = "catalogo_baremos"
    __table_args__ = (
        UniqueConstraint("dimension_codigo", "forma", name="uq_baremo_dim_forma"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    dimension_codigo: Mapped[str] = mapped_column(
        String(40), ForeignKey("catalogo_dimensiones.codigo", ondelete="CASCADE"), nullable=False
    )
    forma: Mapped[str] = mapped_column(String(5), nullable=False)
    corte_sin: Mapped[float] = mapped_column(Float, nullable=False)
    corte_bajo: Mapped[float] = mapped_column(Float, nullable=False)
    corte_medio: Mapped[float] = mapped_column(Float, nullable=False)
    corte_alto: Mapped[float] = mapped_column(Float, nullable=False)


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    medicion_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("mediciones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    estado: Mapped[str] = mapped_column(String(30), default="pendiente", index=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    procesados: Mapped[int] = mapped_column(Integer, default=0)
    fallidos: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    medicion: Mapped[Optional[Medicion]] = relationship("Medicion", back_populates="lotes")


class TrabajadorNomina(Base):
    """Nómina previa a la aplicación: fuente de etiquetas QR 30×20 mm.

    Independiente de FichaSociodemografica (esa va 1:1 con el cuadernillo ya escaneado).
    """

    __tablename__ = "trabajadores_nomina"
    __table_args__ = (
        UniqueConstraint("medicion_id", "cedula", name="uq_nomina_medicion_cedula"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    medicion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cedula: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    forma: Mapped[str] = mapped_column(String(5), default="B")
    cargo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fecha_aplicacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fecha_nacimiento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    anio_nacimiento: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    sexo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ficha_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    payload_qr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    origen: Mapped[str] = mapped_column(String(20), default="excel")  # excel | manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    medicion: Mapped[Medicion] = relationship("Medicion", back_populates="nomina")

    def to_dict(self) -> Dict[str, Any]:
        ficha = dict(self.ficha_json or {})
        ficha.update(
            {
                "cedula": self.cedula,
                "nombre": self.nombre_completo,
                "forma": self.forma,
                "cargo": self.cargo or ficha.get("cargo") or "",
                "area": self.area or ficha.get("area") or "",
                "fecha_aplicacion": self.fecha_aplicacion or ficha.get("fecha_aplicacion") or "",
                "fecha_nacimiento": self.fecha_nacimiento or ficha.get("fecha_nacimiento") or "",
                "anio_nacimiento": self.anio_nacimiento or ficha.get("anio_nacimiento") or "",
                "sexo": self.sexo or ficha.get("sexo") or "",
            }
        )
        return {
            "id": self.id,
            "medicion_id": self.medicion_id,
            "cedula": self.cedula,
            "nombre": self.nombre_completo,
            "nombre_completo": self.nombre_completo,
            "forma": self.forma,
            "cargo": self.cargo,
            "area": self.area,
            "fecha_aplicacion": self.fecha_aplicacion,
            "fecha_nacimiento": self.fecha_nacimiento,
            "anio_nacimiento": self.anio_nacimiento,
            "sexo": self.sexo,
            "origen": self.origen,
            "payload_qr": self.payload_qr,
            "ficha": ficha,
        }
