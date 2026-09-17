"""Script de inicialización, creación de tablas y sembrado (Seeding) de usuarios y datos base."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import func, inspect, select, text

from ..auth import hash_password
from .models import CasoCuadernillo, Empresa, MarcaAmbigua, Medicion, Usuario
from .session import Base, SyncSessionLocal, sync_engine

REAL_ADMIN_EMAIL = "sgi@protegerips.com"
REAL_ADMIN_NOMBRE = "Orlando Hernández Manrique"
REAL_ADMIN_PASSWORD = "Proteger2026"
DEMO_PSYCHO_EMAIL = "dra.valencia@proteger.com.co"
DEMO_ADMIN_EMAIL = "admin@proteger.com.co"

ROOT = Path(__file__).resolve().parents[3]
CASOS_DIR = ROOT / "out" / "casos"


def init_db():
    """Crea todas las tablas en la base de datos y siembra los datos iniciales."""
    # 1. Crear tablas si no existen y aplicar migración v2 (scores, ficha, catálogos)
    Base.metadata.create_all(bind=sync_engine)
    try:
        cols = {c["name"] for c in inspect(sync_engine).get_columns("empresas")}
        if "psicologa_responsable_id" not in cols:
            with sync_engine.begin() as conn:
                conn.execute(text("ALTER TABLE empresas ADD COLUMN psicologa_responsable_id VARCHAR(36)"))
    except Exception as ex:
        print(f"[WARN] migrate psicologa_responsable_id: {ex}")
    try:
        from .migrate_v2 import migrate_v2

        migrate_v2()
    except Exception as ex:
        print(f"[WARN] migrate_v2: {ex}")

    session = SyncSessionLocal()
    try:
        # 2. Administrador real: Orlando Hernández Manrique
        admin = session.execute(select(Usuario).where(Usuario.email == REAL_ADMIN_EMAIL)).scalar_one_or_none()
        if not admin:
            admin = Usuario(
                email=REAL_ADMIN_EMAIL,
                password_hash=hash_password(REAL_ADMIN_PASSWORD),
                nombre_completo=REAL_ADMIN_NOMBRE,
                rol="admin",
                activo=True,
            )
            session.add(admin)
            session.commit()
            print(f"[OK] Administrador creado: {REAL_ADMIN_EMAIL}")
        else:
            admin.nombre_completo = REAL_ADMIN_NOMBRE
            admin.rol = "admin"
            admin.activo = True
            session.commit()

        demo_admin = session.execute(select(Usuario).where(Usuario.email == DEMO_ADMIN_EMAIL)).scalar_one_or_none()
        if demo_admin and demo_admin.email != REAL_ADMIN_EMAIL:
            demo_admin.activo = False
            session.commit()

        # 3. Retirar psicóloga de demostración (no se vuelve a sembrar)
        psico = session.execute(select(Usuario).where(Usuario.email == DEMO_PSYCHO_EMAIL)).scalar_one_or_none()
        if psico:
            psico.activo = False
            session.commit()
            print(f"[OK] Psicóloga demo desactivada: {DEMO_PSYCHO_EMAIL}")

        # 4. Sembrar Operador Digitalizador
        operador = session.execute(select(Usuario).where(Usuario.email == "operador@proteger.com.co")).scalar_one_or_none()
        if not operador:
            operador = Usuario(
                email="operador@proteger.com.co",
                password_hash=hash_password("Operador2026!"),
                nombre_completo="Carlos Eduardo Méndez (Digitalizador)",
                rol="operador",
                cedula="80123456",
                activo=True,
            )
            session.add(operador)
            session.commit()

        # 5. Sembrar Empresa Demo
        empresa = session.execute(select(Empresa).where(Empresa.nit == "900548123")).scalar_one_or_none()
        if not empresa:
            empresa = Empresa(
                nit="900548123",
                digito_verificacion="4",
                razon_social="PROTEGER I.P.S. S.A.S.",
                sector_economico="Servicios de Salud Ocupacional y SST",
                codigo_ciiu="8699",
                ciudad="Bogotá D.C.",
                direccion="Carrera 15 # 85-30 Oficina 401",
                contacto_nombre="Ing. Diana Carolina Gómez",
                contacto_email="sst@proteger.com.co",
                contacto_telefono="3102345678",
                activo=True,
            )
            session.add(empresa)
            session.commit()
            print("[OK] Empresa Demo creada: PROTEGER I.P.S. S.A.S. (NIT 900.548.123-4)")

        # 5b. Sembrar Usuario Cliente Empresa (Gestor SST)
        cliente = session.execute(select(Usuario).where(Usuario.email == "cliente@proteger.com.co")).scalar_one_or_none()
        if not cliente:
            cliente = Usuario(
                email="cliente@proteger.com.co",
                password_hash=hash_password("Cliente2026!"),
                nombre_completo="Ing. Diana Carolina Gómez (SST)",
                rol="cliente_empresa",
                cedula="1018459203",
                empresa_id=empresa.id,
                activo=True,
            )
            session.add(cliente)
            session.commit()
            print("[OK] Cliente Empresa creado: cliente@proteger.com.co / Cliente2026!")

        # 6. Sembrar Medición Anual Activa para la Empresa Demo
        medicion = (
            session.execute(select(Medicion).where(Medicion.codigo_campana == "MED-2026-001").order_by(Medicion.created_at.asc()))
            .scalars()
            .first()
        )
        if not medicion:
            psico_id = psico.id if psico else admin.id
            medicion = Medicion(
                empresa_id=empresa.id,
                psicologa_id=psico_id,
                codigo_campana="MED-2026-001",
                anio=2026,
                periodo="Anual 2026",
                sede="Sede Principal",
                estado="auditoria",
                fecha_inicio=date(2026, 1, 15),
                trabajadores_esperados=25,
            )
            session.add(medicion)
            session.commit()
            print("[OK] Medición activa creada: MED-2026-001 vinculada a PROTEGER I.P.S.")

        # 7. Migrar casos JSON existentes a la base de datos relacional si la medición no tiene casos
        casos_existentes = session.execute(select(func.count(CasoCuadernillo.id)).where(CasoCuadernillo.medicion_id == medicion.id)).scalar()
        if casos_existentes == 0 and CASOS_DIR.exists():
            migrados = 0
            for json_path in sorted(CASOS_DIR.glob("*.json")):
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    c_uid = data.get("caso_id") or json_path.stem
                    idn = data.get("identidad") or {}

                    caso_obj = CasoCuadernillo(
                        medicion_id=medicion.id,
                        caso_uid=c_uid,
                        archivo_pdf=data.get("archivo") or json_path.name,
                        forma=data.get("forma", "A"),
                        id_documento=data.get("id_documento") or idn.get("id_documento"),
                        nombre_trabajador=idn.get("nombre"),
                        cargo=idn.get("cargo"),
                        area_dependencia=idn.get("dependencia"),
                        fecha_aplicacion=idn.get("fecha"),
                        estado=data.get("estado", "listo"),
                        intra_respuestas=data.get("intra") or {},
                        extra_respuestas=data.get("extra") or {},
                        estres_respuestas=data.get("estres") or {},
                        scoring_villalobos=data.get("scoring") or {},
                        paginas_metadata=data.get("paginas") or [],
                        pdf_ordenado_path=data.get("pdf_ordenado"),
                    )
                    session.add(caso_obj)
                    session.flush()

                    for amb in data.get("ambiguos") or []:
                        marca_obj = MarcaAmbigua(
                            caso_id=caso_obj.id,
                            item_num=amb.get("item", 1),
                            bloque=amb.get("bloque", "intra"),
                            pagina_fisica=amb.get("pagina", 1),
                            opciones_detectadas=amb.get("marcadas") or [],
                            decision=amb.get("decision"),
                            decidido_por=amb.get("decidido_por"),
                            crop_path=amb.get("crop"),
                        )
                        session.add(marca_obj)

                    migrados += 1
                except Exception as ex:
                    print(f"Advertencia al migrar {json_path}: {ex}")

            session.commit()
            if migrados > 0:
                print(f"[OK] {migrados} cuadernillos JSON migrados a la Medición MED-2026-001 en PostgreSQL")

    finally:
        session.close()


if __name__ == "__main__":
    init_db()
