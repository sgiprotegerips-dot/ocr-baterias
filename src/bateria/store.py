"""Módulo de persistencia híbrida (JSON Local + Base de Datos Relacional PostgreSQL)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .scoring import score_persona

DATOS = ("nombre", "cargo", "fecha", "dependencia")


def estado(caso: dict) -> str:
    ident = caso.get("identidad") or {}
    datos_ok = all(str(ident.get(k) or "").strip() for k in DATOS)
    pendientes = [
        a for a in caso.get("ambiguos") or [] if isinstance(a, dict) and a.get("decision") is None
    ]
    if pendientes:
        return "doble_marca"
    if not datos_ok:
        return "faltan_datos"
    return "listo"


def load_all(casos_dir: Path) -> List[dict]:
    casos_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(casos_dir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def sync_caso_to_db(caso: dict):
    """Sincroniza el caso con la base de datos relacional PostgreSQL / SQLite."""
    try:
        from .db.models import AuditLog, CasoCuadernillo, MarcaAmbigua, Medicion
        from .db.session import SyncSessionLocal

        session = SyncSessionLocal()
        try:
            c_uid = caso.get("caso_id")
            if not c_uid:
                return

            # Buscar o asociar a la medición activa
            med_id = caso.get("medicion_id")
            if not med_id:
                active_med = session.query(Medicion).order_by(Medicion.created_at.desc()).first()
                if active_med:
                    med_id = active_med.id
                    caso["medicion_id"] = med_id

            if not med_id:
                return

            caso_db = session.query(CasoCuadernillo).filter_by(caso_uid=c_uid).first()
            idn = caso.get("identidad") or {}

            if not caso_db:
                caso_db = CasoCuadernillo(
                    medicion_id=med_id,
                    caso_uid=c_uid,
                    archivo_pdf=caso.get("archivo", "desconocido.pdf"),
                    forma=caso.get("forma", "A"),
                    id_documento=caso.get("id_documento") or idn.get("id_documento"),
                    nombre_trabajador=idn.get("nombre"),
                    cargo=idn.get("cargo"),
                    area_dependencia=idn.get("dependencia"),
                    fecha_aplicacion=idn.get("fecha"),
                    estado=caso.get("estado", "listo"),
                    intra_respuestas=caso.get("intra") or {},
                    extra_respuestas=caso.get("extra") or {},
                    estres_respuestas=caso.get("estres") or {},
                    scoring_villalobos=caso.get("scoring") or {},
                    paginas_metadata=caso.get("paginas") or [],
                    pdf_ordenado_path=caso.get("pdf_ordenado"),
                )
                session.add(caso_db)
                session.flush()
            else:
                caso_db.forma = caso.get("forma", caso_db.forma)
                caso_db.id_documento = caso.get("id_documento") or idn.get("id_documento") or caso_db.id_documento
                caso_db.nombre_trabajador = idn.get("nombre") or caso_db.nombre_trabajador
                caso_db.cargo = idn.get("cargo") or caso_db.cargo
                caso_db.area_dependencia = idn.get("dependencia") or caso_db.area_dependencia
                caso_db.fecha_aplicacion = idn.get("fecha") or caso_db.fecha_aplicacion
                caso_db.estado = caso.get("estado", caso_db.estado)
                caso_db.intra_respuestas = caso.get("intra") or caso_db.intra_respuestas
                caso_db.extra_respuestas = caso.get("extra") or caso_db.extra_respuestas
                caso_db.estres_respuestas = caso.get("estres") or caso_db.estres_respuestas
                caso_db.scoring_villalobos = caso.get("scoring") or caso_db.scoring_villalobos
                caso_db.paginas_metadata = caso.get("paginas") or caso_db.paginas_metadata
                caso_db.pdf_ordenado_path = caso.get("pdf_ordenado") or caso_db.pdf_ordenado_path

            # Sincronizar marcas ambiguas
            for amb in caso.get("ambiguos") or []:
                amb_id_str = str(amb.get("item", 1))
                bloque = amb.get("bloque", "intra")
                marca_db = session.query(MarcaAmbigua).filter_by(
                    caso_id=caso_db.id,
                    item_num=amb.get("item", 1),
                    bloque=bloque
                ).first()

                if not marca_db:
                    marca_db = MarcaAmbigua(
                        caso_id=caso_db.id,
                        item_num=amb.get("item", 1),
                        bloque=bloque,
                        pagina_fisica=amb.get("pagina", 1),
                        opciones_detectadas=amb.get("marcadas") or [],
                        decision=amb.get("decision"),
                        decidido_por=amb.get("decidido_por"),
                        crop_path=amb.get("crop"),
                    )
                    session.add(marca_db)
                else:
                    marca_db.decision = amb.get("decision", marca_db.decision)
                    marca_db.decidido_por = amb.get("decidido_por", marca_db.decidido_por)
                    if amb.get("decision") is not None and not marca_db.fecha_decision:
                        marca_db.fecha_decision = datetime.now(timezone.utc)

            try:
                from .score_store import persist_scores, upsert_ficha_minima

                persist_scores(session, caso_db)
                upsert_ficha_minima(session, caso_db)
            except Exception:
                pass

            session.commit()
        finally:
            session.close()
    except Exception as ex:
        # Fallback silencioso para no bloquear en ambientes sin DB
        pass


def save_caso(casos_dir: Path, caso: dict) -> dict:
    casos_dir.mkdir(parents=True, exist_ok=True)
    if not caso.get("caso_id"):
        caso["caso_id"] = uuid.uuid4().hex[:12]
    caso["estado"] = estado(caso)
    path = casos_dir / f"{caso['caso_id']}.json"
    path.write_text(json.dumps(caso, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_caso_to_db(caso)
    return caso


def get_caso(casos_dir: Path, caso_id: str) -> Optional[dict]:
    p = casos_dir / f"{caso_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def aplicar_decision(caso: dict, amb_id: str, choice: int, psicologa: str) -> dict:
    for a in caso.get("ambiguos") or []:
        if a.get("id") != amb_id:
            continue
        a["decision"] = int(choice)
        a["decidido_por"] = psicologa
        bloque = a.get("bloque")
        item = str(a.get("item"))
        if bloque in ("intra", "extra", "estres"):
            caso.setdefault(bloque, {})[item] = int(choice)
        break
    forma = caso.get("forma") or "A"
    intra = {int(k): v for k, v in (caso.get("intra") or {}).items() if v is not None}
    extra = {int(k): v for k, v in (caso.get("extra") or {}).items() if v is not None}
    estres = {int(k): v for k, v in (caso.get("estres") or {}).items() if v is not None}
    caso["scoring"] = score_persona(
        forma, intra, extra, estres, grupo="jefes" if forma != "B" else "auxiliares"
    )
    caso["estado"] = estado(caso)

    # Registrar en auditoría forense
    try:
        from .db.models import AuditLog
        from .db.session import SyncSessionLocal
        s = SyncSessionLocal()
        try:
            log = AuditLog(
                accion="DECIDIR_DOBLE_CHULEADO",
                entidad_tipo="CASO",
                entidad_id=caso.get("caso_id"),
                datos_nuevos={"amb_id": amb_id, "choice": choice, "psicologa": psicologa},
            )
            s.add(log)
            s.commit()
        finally:
            s.close()
    except Exception:
        pass

    sync_caso_to_db(caso)
    return caso
