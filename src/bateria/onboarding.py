"""Alta transaccional de cliente y apertura de campaña de medición."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from .auth import hash_password
from .db.models import AuditLog, Empresa, Medicion, Usuario
from .storage import ensure_campaign_dirs, sanitize_nit


def parse_nit(raw: str, dv_fallback: Optional[str] = None) -> Tuple[str, str]:
    raw_nit = (raw or "").replace(".", "").strip()
    if "-" in raw_nit:
        parts = raw_nit.split("-", 1)
        clean = parts[0].strip()
        dv = parts[1].strip() or "0"
        return clean, dv
    return raw_nit, ((dv_fallback or "0").strip() or "0")


def next_codigo_campana(session: Session, empresa_id: str, anio: int) -> str:
    prefix = f"MED-{anio}-"
    existentes = (
        session.query(Medicion)
        .filter(Medicion.empresa_id == empresa_id, Medicion.codigo_campana.like(f"{prefix}%"))
        .all()
    )
    nums = []
    for med in existentes:
        tail = med.codigo_campana[len(prefix) :]
        if tail.isdigit():
            nums.append(int(tail))
    return f"{prefix}{max(nums, default=0) + 1:03d}"


def alta_cliente(
    session: Session,
    actor: Usuario,
    empresa_data: Dict[str, Any],
    portal_data: Dict[str, Any],
    psicologa_id: Optional[str] = None,
) -> Dict[str, Any]:
    clean_nit, dv = parse_nit(
        empresa_data.get("nit") or "",
        empresa_data.get("digito_verificacion"),
    )
    if not clean_nit or not (empresa_data.get("razon_social") or "").strip():
        raise ValueError("NIT y razón social son obligatorios.")

    if session.query(Empresa).filter_by(nit=clean_nit).first():
        raise ValueError(f"Ya existe una empresa registrada con el NIT {clean_nit}")

    portal_email = (portal_data.get("email") or "").strip().lower()
    if not portal_email or not (portal_data.get("password") or "").strip():
        raise ValueError("El usuario portal requiere correo y contraseña.")
    if session.query(Usuario).filter_by(email=portal_email).first():
        raise ValueError("Ya existe un usuario registrado con este correo electrónico.")

    psico = None
    if psicologa_id:
        psico = session.query(Usuario).filter_by(id=psicologa_id, rol="psicologa", activo=True).first()
        if not psico:
            raise ValueError("La psicóloga responsable no existe o no está activa.")

    empresa = Empresa(
        nit=clean_nit,
        digito_verificacion=dv,
        razon_social=empresa_data["razon_social"].strip(),
        sector_economico=empresa_data.get("sector_economico") or empresa_data.get("sector"),
        codigo_ciiu=empresa_data.get("codigo_ciiu") or empresa_data.get("actividad_economica"),
        ciudad=empresa_data.get("ciudad") or "Bogotá D.C.",
        direccion=empresa_data.get("direccion"),
        contacto_nombre=empresa_data.get("contacto_nombre") or empresa_data.get("representante_legal") or portal_data.get("nombre_completo"),
        contacto_email=empresa_data.get("contacto_email") or empresa_data.get("email_contacto") or portal_email,
        contacto_telefono=empresa_data.get("contacto_telefono") or empresa_data.get("telefono"),
        psicologa_responsable_id=psico.id if psico else None,
        activo=True,
    )
    session.add(empresa)
    session.flush()

    portal = Usuario(
        email=portal_email,
        password_hash=hash_password(portal_data["password"].strip()),
        nombre_completo=(portal_data.get("nombre_completo") or "").strip() or empresa.contacto_nombre or "Gestor SST",
        rol="cliente_empresa",
        empresa_id=empresa.id,
        activo=True,
    )
    session.add(portal)
    session.flush()

    session.add(
        AuditLog(
            usuario_id=actor.id,
            accion="ALTA_CLIENTE",
            entidad_tipo="EMPRESA",
            entidad_id=empresa.id,
            datos_nuevos={
                "nit": empresa.nit,
                "razon_social": empresa.razon_social,
                "portal_email": portal.email,
                "psicologa_responsable_id": empresa.psicologa_responsable_id,
            },
        )
    )
    session.commit()
    session.refresh(empresa)
    session.refresh(portal)
    return {"empresa": empresa.to_dict(), "portal": portal.to_dict()}


def abrir_campana(
    session: Session,
    actor: Usuario,
    empresa_id: str,
    anio: int,
    periodo: str,
    sede: str,
    trabajadores_esperados: int,
    psicologa_id: Optional[str] = None,
    codigo_campana: Optional[str] = None,
) -> Dict[str, Any]:
    empresa = session.query(Empresa).filter_by(id=empresa_id, activo=True).first()
    if not empresa:
        raise ValueError("Empresa no encontrada")

    responsable_id = actor.id
    if psicologa_id:
        alt = session.query(Usuario).filter_by(id=psicologa_id, rol="psicologa", activo=True).first()
        if alt:
            responsable_id = alt.id
    responsable = session.query(Usuario).filter_by(id=responsable_id, activo=True).first()
    if not responsable or responsable.rol not in ("psicologa", "admin"):
        raise ValueError("Debe asignar una psicóloga responsable de la campaña.")

    codigo = (codigo_campana or "").strip() or next_codigo_campana(session, empresa.id, anio)
    dup = (
        session.query(Medicion)
        .filter_by(empresa_id=empresa.id, codigo_campana=codigo)
        .first()
    )
    if dup:
        raise ValueError(f"Ya existe una campaña {codigo} para esta empresa.")

    medicion = Medicion(
        empresa_id=empresa.id,
        psicologa_id=responsable.id,
        codigo_campana=codigo,
        anio=anio,
        periodo=periodo or "Anual",
        sede=sede or "Principal",
        estado="recoleccion",
        fecha_inicio=date.today(),
        trabajadores_esperados=trabajadores_esperados or 0,
    )

    session.add(medicion)
    session.flush()
    ensure_campaign_dirs(empresa.nit, medicion.codigo_campana)
    session.add(
        AuditLog(
            usuario_id=actor.id,
            accion="ABRIR_CAMPANA",
            entidad_tipo="MEDICION",
            entidad_id=medicion.id,
            datos_nuevos={"codigo": medicion.codigo_campana, "empresa": empresa.razon_social},
        )
    )
    session.commit()
    session.refresh(medicion)
    return medicion.to_dict()
