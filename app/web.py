from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import fitz
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from bateria.auth import (
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    hash_password,
    require_role,
    verify_password,
)
from bateria.batch_manager import batch_manager
from bateria.db.init_db import init_db
from bateria.db.models import (
    AuditLog,
    CasoCuadernillo,
    Empresa,
    HistoricoCustodia,
    InformeDiagnostico,
    MarcaAmbigua,
    Medicion,
    TrabajadorNomina,
    Usuario,
)
from bateria.nomina import ficha_to_worker_kwargs, parse_ficha_excel, render_labels_html
from bateria.db.session import SyncSessionLocal, get_db
from bateria.export import export_workbook
from bateria.pipeline import generate_ordered_pdf, process_pdf
from bateria.report_template import generate_printable_report_html
from bateria.reporting import compute_report_hash, consolidate_medicion_report
from bateria.scoring import score_persona
from bateria.onboarding import abrir_campana, alta_cliente
from bateria.storage import ensure_campaign_dirs, save_upload
from bateria.store import aplicar_decision, estado, get_caso, load_all, save_caso

UPLOAD = ROOT / "data" / "uploads"
OUT = ROOT / "out"
CASOS = OUT / "casos"
CROPS = OUT / "crops"
CUSTODIA = OUT / "custodia"
STATIC = Path(__file__).resolve().parent / "static"

UPLOAD.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
CASOS.mkdir(parents=True, exist_ok=True)
CROPS.mkdir(parents=True, exist_ok=True)
CUSTODIA.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización de esquemas relacionales y sembrado de datos en startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Advertencia inicializando base de datos en startup: {e}")
    yield


app = FastAPI(
    title="Sala de Lectura Masiva · Batería Psicosocial (Resolución 2764 / 2646)",
    version="3.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount("/media", StaticFiles(directory=OUT), name="media")



# -----------------------------------------------------------------------------
# DTOs / Schemas Pydantic
# -----------------------------------------------------------------------------
class LoginIn(BaseModel):
    email: str
    password: str


class EmpresaIn(BaseModel):
    nit: str
    digito_verificacion: Optional[str] = None
    razon_social: str
    sector_economico: Optional[str] = None
    sector: Optional[str] = None
    actividad_economica: Optional[str] = None
    codigo_ciiu: Optional[str] = None
    ciudad: Optional[str] = "Bogotá D.C."
    direccion: Optional[str] = None
    representante_legal: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_email: Optional[str] = None
    email_contacto: Optional[str] = None
    contacto_telefono: Optional[str] = None
    telefono: Optional[str] = None


class MedicionIn(BaseModel):
    empresa_id: Optional[str] = None
    codigo_campana: Optional[str] = None
    nombre: Optional[str] = None
    psicologa_id: Optional[str] = None
    anio: Optional[int] = 2026
    periodo: Optional[str] = "2026-1"
    sede: Optional[str] = "Principal"
    trabajadores_esperados: Optional[int] = 20
    fecha_inicio: Optional[str] = None


class EstadoMedicionIn(BaseModel):
    estado: str  # recoleccion, auditoria, aprobada, cerrada


class AprobarInformeIn(BaseModel):
    conclusiones: Optional[str] = None
    recomendaciones: Optional[str] = None


class DatosIn(BaseModel):
    nombre: str
    cargo: str
    fecha: str
    dependencia: str
    id_documento: Optional[str] = None
    psicologa: str


class UserCreateIn(BaseModel):
    email: str
    password: str
    nombre_completo: str
    rol: str = "psicologa"
    cedula: Optional[str] = None
    tarjeta_profesional: Optional[str] = None
    licencia_sst: Optional[str] = None
    dpto_licencia_sst: Optional[str] = None
    empresa_id: Optional[str] = None
    activo: bool = True


class UserUpdateIn(BaseModel):
    nombre_completo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    cedula: Optional[str] = None
    tarjeta_profesional: Optional[str] = None
    licencia_sst: Optional[str] = None
    empresa_id: Optional[str] = None
    activo: Optional[bool] = None


class DecisionIn(BaseModel):
    amb_id: str
    choice: int
    psicologa: str


class PortalUserIn(BaseModel):
    nombre_completo: str
    email: str
    password: str


class OnboardingClienteIn(BaseModel):
    empresa: EmpresaIn
    psicologa_id: Optional[str] = None
    portal: PortalUserIn


class OnboardingCampanaIn(BaseModel):
    empresa_id: str
    codigo_campana: Optional[str] = None
    psicologa_id: Optional[str] = None
    anio: Optional[int] = 2026
    periodo: Optional[str] = "Anual"
    sede: Optional[str] = "Principal"
    trabajadores_esperados: Optional[int] = 20


AuthUser = Annotated[Usuario, Depends(get_current_user)]
AdminUser = Annotated[Usuario, Depends(require_role(["admin"]))]
PsicoUser = Annotated[Usuario, Depends(require_role(["psicologa"]))]
StaffUser = Annotated[Usuario, Depends(require_role(["admin", "psicologa"]))]
CargaUser = Annotated[Usuario, Depends(require_role(["admin", "psicologa", "operador"]))]
ClinicoUser = Annotated[Usuario, Depends(require_role(["admin", "psicologa"]))]
InformeUser = Annotated[Usuario, Depends(require_role(["admin", "psicologa", "cliente_empresa"]))]


def _scope_empresa_query(query, user: Usuario):
    if user.rol == "cliente_empresa" and user.empresa_id:
        return query.filter_by(id=user.empresa_id)
    return query


def _scope_medicion_query(query, user: Usuario):
    if user.rol == "cliente_empresa" and user.empresa_id:
        return query.filter_by(empresa_id=user.empresa_id)
    if user.rol == "operador":
        return query.filter(Medicion.estado.in_(("recoleccion", "auditoria")))
    return query


def _assert_medicion_visible(med: Medicion, user: Usuario) -> None:
    if user.rol == "cliente_empresa" and user.empresa_id != med.empresa_id:
        raise HTTPException(status_code=403, detail="Acceso denegado a esta empresa.")
    if user.rol == "operador" and med.estado not in ("recoleccion", "auditoria"):
        raise HTTPException(status_code=403, detail="La campaña no está abierta a digitalización.")


class FichaNominaIn(BaseModel):
    forma: Optional[str] = "B"
    fecha_aplicacion: Optional[str] = None
    cedula: str
    nombre: Optional[str] = None
    nombre_completo: Optional[str] = None
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    anio_nacimiento: Optional[str] = None
    edad: Optional[str] = None
    estado_civil: Optional[str] = None
    nivel_estudios: Optional[str] = None
    cargo_ocupacion: Optional[str] = None
    residencia: Optional[str] = None
    departamento: Optional[str] = None
    estrato: Optional[str] = None
    tipo_vivienda: Optional[str] = None
    n_dependientes: Optional[str] = None
    lugar_trabajo: Optional[str] = None
    dpto_trabajo: Optional[str] = None
    tiempo_empresa: Optional[str] = None
    cargo: Optional[str] = None
    tipo_cargo: Optional[str] = None
    tiempo_cargo: Optional[str] = None
    area: Optional[str] = None
    tipo_contrato: Optional[str] = None
    horas_diarias: Optional[str] = None
    tipo_salario: Optional[str] = None


class PrintNominaIn(BaseModel):
    cedulas: Optional[List[str]] = None
    forma: Optional[str] = None


# -----------------------------------------------------------------------------
# Rutas Principales y Salud
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    """Endpoint de estado para AWS Application Load Balancers (ALB) y monitoreo."""
    from bateria.ocr_engine import get_available_engines

    return {
        "status": "healthy",
        "engines": get_available_engines(),
        "active_jobs": len(batch_manager.jobs),
        "workers": batch_manager.max_workers,
        "cpu_count": os.cpu_count() or 1,
    }


@app.get("/api/ocr/engines")
def api_ocr_engines():
    """Retorna los motores de OCR disponibles en el servidor (RapidOCR, Tesseract, AWS Textract, etc.)."""
    from bateria.ocr_engine import get_available_engines

    return get_available_engines()


@app.get("/api/ocr/benchmark")
def api_ocr_benchmark():
    """Ejecuta una prueba comparativa de rendimiento en los motores de OCR disponibles."""
    from bateria.ocr_engine import benchmark_ocr_engines

    return benchmark_ocr_engines()



# -----------------------------------------------------------------------------
# Módulo de Autenticación y RBAC
# -----------------------------------------------------------------------------
@app.post("/api/auth/login")
def api_auth_login(body: LoginIn, response: Response):
    """Inicia sesión y emite token JWT en cookie HttpOnly segura."""
    session = SyncSessionLocal()
    try:
        user = session.query(Usuario).filter_by(email=body.email.strip().lower(), activo=True).first()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas. Verifique su correo o contraseña.",
            )

        token_data = {
            "sub": user.id,
            "email": user.email,
            "rol": user.rol,
            "nombre": user.nombre_completo,
        }
        token = create_access_token(token_data)

        # Set HttpOnly Cookie segura
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,  # Permitir HTTP en redes locales/docker
            max_age=60 * 480,  # 8 horas
        )

        return {
            "success": True,
            "user": user.to_dict(),
            "token": token,
        }
    finally:
        session.close()


@app.post("/api/auth/logout")
def api_auth_logout(response: Response):
    """Cierra la sesión y elimina la cookie de autenticación."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"success": True, "message": "Sesión cerrada exitosamente"}


@app.get("/api/auth/me")
def api_auth_me(current_user: Optional[Usuario] = Depends(get_current_user_optional)):
    """Retorna la información del usuario en sesión actual o estado anónimo."""
    if not current_user:
        return {"authenticated": False, "user": None}

    return {"authenticated": True, "user": current_user.to_dict()}


@app.get("/api/auth/psicologas")
def api_auth_psicologas(current_user: StaffUser):
    """Retorna la lista de psicólogas especialistas SST registradas."""
    session = SyncSessionLocal()
    try:
        psicos = session.query(Usuario).filter(Usuario.rol.in_(["psicologa", "admin"]), Usuario.activo.is_(True)).all()
        return [p.to_dict() for p in psicos]
    finally:
        session.close()


@app.post("/api/onboarding/cliente")
def api_onboarding_cliente(body: OnboardingClienteIn, current_user: AdminUser):
    """Asistente de alta: empresa + psicóloga informativa + usuario portal del cliente."""
    session = SyncSessionLocal()
    try:
        emp_payload = body.empresa.model_dump() if hasattr(body.empresa, "model_dump") else body.empresa.dict()
        portal_payload = body.portal.model_dump() if hasattr(body.portal, "model_dump") else body.portal.dict()
        return alta_cliente(
            session,
            current_user,
            emp_payload,
            portal_payload,
            psicologa_id=body.psicologa_id,
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        session.close()


@app.post("/api/onboarding/campana")
def api_onboarding_campana(body: OnboardingCampanaIn, current_user: PsicoUser):
    """Asistente de la psicóloga: abre una medición sobre una empresa ya registrada."""
    session = SyncSessionLocal()
    try:
        return abrir_campana(
            session,
            current_user,
            empresa_id=body.empresa_id,
            anio=body.anio or date.today().year,
            periodo=body.periodo or "Anual",
            sede=body.sede or "Principal",
            trabajadores_esperados=body.trabajadores_esperados or 0,
            psicologa_id=body.psicologa_id,
            codigo_campana=body.codigo_campana,
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Módulo de Empresas y Mediciones (Multi-Tenancy)
# -----------------------------------------------------------------------------
@app.get("/api/empresas")
def api_get_empresas(current_user: AuthUser):
    """Retorna las empresas visibles según el rol en sesión."""
    session = SyncSessionLocal()
    try:
        query = _scope_empresa_query(session.query(Empresa).filter_by(activo=True), current_user)
        empresas = query.order_by(Empresa.razon_social).all()
        return [e.to_dict() for e in empresas]
    finally:
        session.close()


@app.post("/api/empresas")
def api_create_empresa(body: EmpresaIn, current_user: AdminUser):
    """Crea una nueva empresa evaluada."""
    session = SyncSessionLocal()
    try:
        raw_nit = body.nit.replace(".", "").strip()
        if "-" in raw_nit:
            parts = raw_nit.split("-", 1)
            clean_nit = parts[0].strip()
            dv = parts[1].strip() or "0"
        else:
            clean_nit = raw_nit
            dv = (body.digito_verificacion or "0").strip()

        existing = session.query(Empresa).filter_by(nit=clean_nit).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe una empresa registrada con el NIT {clean_nit}")

        empresa = Empresa(
            nit=clean_nit,
            digito_verificacion=dv,
            razon_social=body.razon_social.strip(),
            sector_economico=body.sector_economico or body.sector,
            codigo_ciiu=body.codigo_ciiu or body.actividad_economica,
            ciudad=body.ciudad or "Bogotá D.C.",
            direccion=body.direccion,
            contacto_nombre=body.contacto_nombre or body.representante_legal,
            contacto_email=body.contacto_email or body.email_contacto,
            contacto_telefono=body.contacto_telefono or body.telefono,
        )
        session.add(empresa)
        session.flush()

        # Log de auditoría
        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="CREAR_EMPRESA",
            entidad_tipo="EMPRESA",
            entidad_id=empresa.id,
            datos_nuevos={"nit": empresa.nit, "razon_social": empresa.razon_social},
        )
        session.add(log)
        session.commit()
        return empresa.to_dict()
    finally:
        session.close()


@app.get("/api/empresas/{empresa_id}")
def api_get_empresa(empresa_id: str, current_user: AuthUser):
    session = SyncSessionLocal()
    try:
        empresa = session.query(Empresa).filter_by(id=empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        if current_user.rol == "cliente_empresa" and current_user.empresa_id != empresa.id:
            raise HTTPException(status_code=403, detail="Acceso denegado a esta empresa.")
        return empresa.to_dict()
    finally:
        session.close()


@app.get("/api/empresas/{empresa_id}/mediciones")
def api_get_empresa_mediciones(empresa_id: str, current_user: AuthUser):
    session = SyncSessionLocal()
    try:
        if current_user.rol == "cliente_empresa" and current_user.empresa_id != empresa_id:
            raise HTTPException(status_code=403, detail="Acceso denegado a esta empresa.")
        query = session.query(Medicion).filter_by(empresa_id=empresa_id)
        query = _scope_medicion_query(query, current_user)
        mediciones = query.order_by(Medicion.created_at.desc()).all()
        return [m.to_dict() for m in mediciones]
    finally:
        session.close()


@app.post("/api/empresas/{empresa_id}/mediciones")
def api_create_medicion(
    empresa_id: str,
    body: MedicionIn,
    current_user: PsicoUser,
):
    """Crea una nueva campaña de medición para una empresa."""
    session = SyncSessionLocal()
    try:
        empresa = session.query(Empresa).filter_by(id=empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        psico_id = body.psicologa_id
        if not psico_id and current_user:
            psico_id = current_user.id
        if not psico_id:
            default_psico = session.query(Usuario).filter_by(rol="psicologa").first()
            if default_psico:
                psico_id = default_psico.id
            else:
                raise HTTPException(status_code=400, detail="Debe asignar una psicóloga responsable.")

        codigo_campana = body.codigo_campana or f"MED-{body.anio or 2026}-{empresa.nit[:4]}-{uuid.uuid4().hex[:4].upper()}"
        nombre = body.nombre or f"Evaluación Batería de Riesgo Psicosocial {body.anio or 2026}"

        medicion = Medicion(
            empresa_id=empresa_id,
            psicologa_id=psico_id,
            codigo_campana=codigo_campana,
            anio=body.anio or 2026,
            periodo=body.periodo or "2026-1",
            sede=body.sede or "Principal",
            estado="recoleccion",
            fecha_inicio=date.today(),
            trabajadores_esperados=body.trabajadores_esperados or 20,
        )
        session.add(medicion)
        session.flush()

        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="CREAR_MEDICION",
            entidad_tipo="MEDICION",
            entidad_id=medicion.id,
            datos_nuevos={"codigo": codigo_campana, "empresa": empresa.razon_social},
        )
        session.add(log)
        session.commit()
        ensure_campaign_dirs(empresa.nit, medicion.codigo_campana)
        return medicion.to_dict()
    finally:
        session.close()


@app.get("/api/mediciones")
def api_get_mediciones(current_user: AuthUser):
    """Retorna las mediciones visibles según el rol en sesión."""
    session = SyncSessionLocal()
    try:
        query = _scope_medicion_query(session.query(Medicion), current_user)
        meds = query.order_by(Medicion.created_at.desc()).all()
        return [m.to_dict() for m in meds]
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Módulo de Administración de Plataforma y Usuarios (RBAC)
# -----------------------------------------------------------------------------
@app.get("/api/admin/users")
def api_admin_get_users(current_user: AdminUser):
    """Lista todos los usuarios del sistema para la Consola de Administración."""
    session = SyncSessionLocal()
    try:
        users = session.query(Usuario).order_by(Usuario.created_at.desc()).all()
        return [u.to_dict() for u in users]
    finally:
        session.close()


@app.post("/api/admin/users")
def api_admin_create_user(
    body: UserCreateIn,
    current_user: AdminUser,
):
    """Crea un nuevo usuario en la plataforma."""
    session = SyncSessionLocal()
    try:
        clean_email = body.email.strip().lower()
        existing = session.query(Usuario).filter_by(email=clean_email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un usuario registrado con este correo electrónico.")

        user = Usuario(
            email=clean_email,
            password_hash=hash_password(body.password),
            nombre_completo=body.nombre_completo.strip(),
            rol=body.rol,
            cedula=body.cedula.strip() if body.cedula else None,
            tarjeta_profesional=body.tarjeta_profesional.strip() if body.tarjeta_profesional else None,
            licencia_sst=body.licencia_sst.strip() if body.licencia_sst else None,
            dpto_licencia_sst=body.dpto_licencia_sst.strip() if body.dpto_licencia_sst else None,
            empresa_id=body.empresa_id if body.rol == "cliente_empresa" else None,
            activo=body.activo,
        )
        session.add(user)
        session.flush()

        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="CREAR_USUARIO",
            entidad_tipo="USUARIO",
            entidad_id=user.id,
            datos_nuevos={"email": user.email, "rol": user.rol, "nombre": user.nombre_completo},
        )
        session.add(log)
        session.commit()
        return user.to_dict()
    finally:
        session.close()


@app.put("/api/admin/users/{user_id}")
def api_admin_update_user(
    user_id: str,
    body: UserUpdateIn,
    current_user: AdminUser,
):
    """Actualiza datos o credenciales de un usuario existente."""
    session = SyncSessionLocal()
    try:
        user = session.query(Usuario).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if body.nombre_completo is not None:
            user.nombre_completo = body.nombre_completo.strip()
        if body.rol is not None:
            user.rol = body.rol
        if body.cedula is not None:
            user.cedula = body.cedula.strip()
        if body.tarjeta_profesional is not None:
            user.tarjeta_profesional = body.tarjeta_profesional.strip()
        if body.licencia_sst is not None:
            user.licencia_sst = body.licencia_sst.strip()
        if body.empresa_id is not None:
            user.empresa_id = body.empresa_id
        if body.activo is not None:
            user.activo = body.activo
        if body.password and body.password.strip():
            user.password_hash = hash_password(body.password.strip())

        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="ACTUALIZAR_USUARIO",
            entidad_tipo="USUARIO",
            entidad_id=user.id,
            datos_nuevos={"email": user.email, "rol": user.rol, "activo": user.activo},
        )
        session.add(log)
        session.commit()
        return user.to_dict()
    finally:
        session.close()


@app.get("/api/admin/audit-logs")
def api_admin_get_audit_logs(
    current_user: AdminUser,
    limit: int = Query(100, ge=10, le=500),
):
    """Retorna los registros cronológicos de auditoría del sistema."""
    session = SyncSessionLocal()
    try:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp_utc.desc()).limit(limit).all()
        return [l.to_dict() for l in logs]
    finally:
        session.close()


@app.get("/api/admin/stats")
def api_admin_get_stats(current_user: AdminUser):
    """Retorna métricas y telemetría consolidadas de la plataforma."""
    from bateria.ocr_engine import get_available_engines
    session = SyncSessionLocal()
    try:
        u_count = session.query(Usuario).count()
        e_count = session.query(Empresa).count()
        m_count = session.query(Medicion).count()
        c_count = session.query(CasoCuadernillo).count()
        i_count = session.query(InformeDiagnostico).filter_by(sellado_inmutable=True).count()
        return {
            "total_usuarios": u_count,
            "total_empresas": e_count,
            "total_mediciones": m_count,
            "total_cuadernillos": c_count,
            "informes_sellados_20_anios": i_count,
            "motores_ocr": get_available_engines(),
        }
    finally:
        session.close()



@app.get("/api/mediciones/{medicion_id}")
def api_get_medicion(medicion_id: str, current_user: AuthUser):
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        _assert_medicion_visible(med, current_user)
        return med.to_dict()
    finally:
        session.close()


@app.put("/api/mediciones/{medicion_id}/estado")
def api_update_medicion_estado(
    medicion_id: str,
    body: EstadoMedicionIn,
    current_user: ClinicoUser,
):
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")

        if med.estado == "cerrada":
            raise HTTPException(status_code=400, detail="La medición se encuentra sellada y cerrada legalmente. No es editable.")

        prev_estado = med.estado
        med.estado = body.estado
        if body.estado in ("aprobada", "cerrada") and not med.fecha_cierre:
            med.fecha_cierre = date.today()

        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="CAMBIAR_ESTADO_MEDICION",
            entidad_tipo="MEDICION",
            entidad_id=med.id,
            datos_anteriores={"estado": prev_estado},
            datos_nuevos={"estado": med.estado},
        )
        session.add(log)
        session.commit()
        return med.to_dict()
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Nómina + etiquetas QR térmicas 30×20 mm (sticker solo en pág. 1)
# -----------------------------------------------------------------------------
def _upsert_nomina_row(session, medicion_id: str, ficha: Dict[str, Any], origen: str) -> TrabajadorNomina:
    kwargs = ficha_to_worker_kwargs(ficha, origen=origen)
    if not kwargs["cedula"] or not kwargs["nombre_completo"]:
        raise HTTPException(status_code=400, detail="Cédula y nombre son obligatorios.")
    row = (
        session.query(TrabajadorNomina)
        .filter_by(medicion_id=medicion_id, cedula=kwargs["cedula"])
        .first()
    )
    if row:
        for key, value in kwargs.items():
            setattr(row, key, value)
        return row
    row = TrabajadorNomina(medicion_id=medicion_id, **kwargs)
    session.add(row)
    return row


def _nomina_fichas(
    session,
    medicion_id: str,
    cedulas: Optional[List[str]] = None,
    forma: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = session.query(TrabajadorNomina).filter_by(medicion_id=medicion_id)
    if forma and str(forma).strip():
        q = q.filter(TrabajadorNomina.forma == str(forma).strip().upper())
    if cedulas:
        wanted = {str(c).strip() for c in cedulas if str(c).strip()}
        q = q.filter(TrabajadorNomina.cedula.in_(wanted))
    rows = q.order_by(TrabajadorNomina.forma.asc(), TrabajadorNomina.nombre_completo.asc()).all()
    return [r.to_dict()["ficha"] for r in rows]


@app.get("/api/mediciones/{medicion_id}/nomina")
def api_list_nomina(medicion_id: str, current_user: CargaUser):
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        rows = (
            session.query(TrabajadorNomina)
            .filter_by(medicion_id=medicion_id)
            .order_by(TrabajadorNomina.forma.asc(), TrabajadorNomina.nombre_completo.asc())
            .all()
        )
        return {
            "medicion_id": medicion_id,
            "total": len(rows),
            "forma_a": sum(1 for r in rows if r.forma == "A"),
            "forma_b": sum(1 for r in rows if r.forma == "B"),
            "trabajadores": [r.to_dict() for r in rows],
        }
    finally:
        session.close()


@app.post("/api/mediciones/{medicion_id}/nomina")
def api_create_nomina_manual(
    medicion_id: str,
    body: FichaNominaIn,
    current_user: CargaUser,
):
    """Alta 1 a 1 sin Excel: guarda ficha completa y deja lista la etiqueta."""
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        data = body.model_dump()
        data["nombre"] = (data.get("nombre") or data.get("nombre_completo") or "").strip()
        if not data.get("cedula") or not data.get("nombre"):
            raise HTTPException(status_code=400, detail="Cédula y nombre son obligatorios.")
        row = _upsert_nomina_row(session, medicion_id, data, origen="manual")
        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="NOMINA_ALTA_MANUAL",
            entidad_tipo="NOMINA",
            entidad_id=medicion_id,
            datos_nuevos={"cedula": row.cedula, "nombre": row.nombre_completo},
        )
        session.add(log)
        session.commit()
        session.refresh(row)
        return row.to_dict()
    finally:
        session.close()


@app.post("/api/mediciones/{medicion_id}/nomina/import")
async def api_import_nomina_excel(
    medicion_id: str,
    current_user: CargaUser,
    file: UploadFile = File(...),
):
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        raw = await file.read()
        tmp = ROOT / "data" / "uploads" / f"nomina_{uuid.uuid4().hex[:10]}.xlsx"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(raw)
        try:
            fichas = parse_ficha_excel(tmp)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"No se pudo leer la FICHA DATOS GENERALES: {exc}") from exc
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass
        if not fichas:
            raise HTTPException(status_code=400, detail="El Excel no contiene filas de FICHA DATOS GENERALES.")
        created = 0
        updated = 0
        for ficha in fichas:
            existing = (
                session.query(TrabajadorNomina)
                .filter_by(medicion_id=medicion_id, cedula=ficha["cedula"])
                .first()
            )
            _upsert_nomina_row(session, medicion_id, ficha, origen="excel")
            if existing:
                updated += 1
            else:
                created += 1
        log = AuditLog(
            usuario_id=current_user.id if current_user else None,
            accion="NOMINA_IMPORT_EXCEL",
            entidad_tipo="NOMINA",
            entidad_id=medicion_id,
            datos_nuevos={"created": created, "updated": updated, "total": len(fichas)},
        )
        session.add(log)
        session.commit()
        return {"imported": len(fichas), "created": created, "updated": updated}
    finally:
        session.close()


@app.post("/api/mediciones/{medicion_id}/nomina/print-html", response_class=HTMLResponse)
def api_print_nomina_html(
    medicion_id: str,
    current_user: CargaUser,
    body: Optional[PrintNominaIn] = None,
):
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        cedulas = body.cedulas if body else None
        forma = body.forma if body else None
        fichas = _nomina_fichas(session, medicion_id, cedulas=cedulas, forma=forma)
        if not fichas:
            raise HTTPException(status_code=404, detail="No hay trabajadores para imprimir.")
        return HTMLResponse(render_labels_html(fichas))
    finally:
        session.close()


@app.get("/api/mediciones/{medicion_id}/nomina/{cedula}/etiqueta.html", response_class=HTMLResponse)
def api_print_one_label(
    medicion_id: str,
    cedula: str,
    current_user: CargaUser,
):
    session = SyncSessionLocal()
    try:
        row = (
            session.query(TrabajadorNomina)
            .filter_by(medicion_id=medicion_id, cedula=cedula)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado en la nómina")
        return HTMLResponse(render_labels_html([row.to_dict()["ficha"]]))
    finally:
        session.close()


@app.delete("/api/mediciones/{medicion_id}/nomina/{cedula}")
def api_delete_nomina_row(
    medicion_id: str,
    cedula: str,
    current_user: CargaUser,
):
    session = SyncSessionLocal()
    try:
        row = (
            session.query(TrabajadorNomina)
            .filter_by(medicion_id=medicion_id, cedula=cedula)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado en la nómina")
        session.delete(row)
        session.commit()
        return {"ok": True, "cedula": cedula}
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Módulo de Informes Diagnósticos y Custodia Legal (20 Años)
# -----------------------------------------------------------------------------
@app.get("/api/mediciones/{medicion_id}/informe")
def api_get_informe_medicion(medicion_id: str, current_user: InformeUser):
    """Calcula y retorna la consolidación estadística completa del informe diagnóstico."""
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        _assert_medicion_visible(med, current_user)
        if current_user.rol == "cliente_empresa":
            inf = session.query(InformeDiagnostico).filter_by(medicion_id=medicion_id).first()
            if not inf:
                raise HTTPException(status_code=403, detail="El informe aún está en auditoría clínica.")

        casos = session.query(CasoCuadernillo).filter_by(medicion_id=medicion_id).all()
        report_data = consolidate_medicion_report(med, casos, med.psicologa)
        report_hash = compute_report_hash(report_data)
        report_data["hash_sha256"] = report_hash
        return report_data
    finally:
        session.close()


@app.get("/api/mediciones/{medicion_id}/informe/html", response_class=HTMLResponse)
def api_get_informe_html(medicion_id: str, current_user: InformeUser):
    """Genera el informe diagnóstico oficial imprimible en formato HTML de alta fidelidad."""
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")
        _assert_medicion_visible(med, current_user)

        casos = session.query(CasoCuadernillo).filter_by(medicion_id=medicion_id).all()
        report_data = consolidate_medicion_report(med, casos, med.psicologa)
        report_hash = compute_report_hash(report_data)
        report_data["hash_sha256"] = report_hash

        return generate_printable_report_html(report_data)
    finally:
        session.close()


@app.post("/api/mediciones/{medicion_id}/informe/aprobar-sellar")
def api_aprobar_sellar_informe(
    medicion_id: str,
    body: AprobarInformeIn,
    current_user: PsicoUser,
):
    """Firma digitalmente por la psicóloga, genera hash SHA-256 inmutable y sella la medición a 20 años."""
    session = SyncSessionLocal()
    try:
        med = session.query(Medicion).filter_by(id=medicion_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medición no encontrada")

        if med.estado == "cerrada":
            raise HTTPException(status_code=400, detail="Esta medición ya fue sellada e inmutabilizada previamente.")

        casos = session.query(CasoCuadernillo).filter_by(medicion_id=medicion_id).all()
        if not casos:
            raise HTTPException(status_code=400, detail="No se pueden sellar mediciones sin cuadernillos leídos.")

        psicologa = current_user

        report_data = consolidate_medicion_report(med, casos, psicologa)
        if body.conclusiones:
            report_data["conclusiones"] = body.conclusiones
        if body.recomendaciones:
            report_data["recomendaciones"] = body.recomendaciones

        report_hash = compute_report_hash(report_data)
        report_data["hash_sha256"] = report_hash

        # Guardar o actualizar registro de InformeDiagnostico
        informe = session.query(InformeDiagnostico).filter_by(medicion_id=medicion_id).first()
        if not informe:
            informe = InformeDiagnostico(
                medicion_id=medicion_id,
                psicologa_id=psicologa.id,
                resumen_sociodemografico=report_data["resumen_sociodemografico"],
                baremos_consolidados=report_data["baremos_consolidados"],
                conclusiones=report_data.get("conclusiones"),
                recomendaciones=report_data.get("recomendaciones"),
                hash_sha256=report_hash,
                sellado_inmutable=True,
                fecha_emision=datetime.now(timezone.utc),
            )
            session.add(informe)
        else:
            informe.resumen_sociodemografico = report_data["resumen_sociodemografico"]
            informe.baremos_consolidados = report_data["baremos_consolidados"]
            informe.conclusiones = report_data.get("conclusiones")
            informe.recomendaciones = report_data.get("recomendaciones")
            informe.hash_sha256 = report_hash
            informe.sellado_inmutable = True
            informe.fecha_emision = datetime.now(timezone.utc)

        session.flush()

        # Empaquetar archivo frío .ZIP de custodia 20 años
        empresa_folder = CUSTODIA / f"{med.empresa.nit if med.empresa else 'empresa'}"
        empresa_folder.mkdir(parents=True, exist_ok=True)
        zip_path = empresa_folder / f"{med.codigo_campana}_custodia_20y.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Reporte JSON
            zf.writestr("informe_diagnostico.json", json.dumps(report_data, ensure_ascii=False, indent=2))
            # 2. HTML oficial
            zf.writestr("informe_oficial_firmado.html", generate_printable_report_html(report_data))
            # 3. Manifiesto
            manifest = {
                "codigo_campana": med.codigo_campana,
                "empresa": med.empresa.razon_social if med.empresa else "",
                "nit": med.empresa.nit if med.empresa else "",
                "psicologa_responsable": psicologa.nombre_completo,
                "licencia_sst": psicologa.licencia_sst,
                "tarjeta_profesional": psicologa.tarjeta_profesional,
                "total_trabajadores": len(casos),
                "hash_sha256_integridad": report_hash,
                "normativa": "Resolución 2764 de 2022 / Decreto 1072 de 2015 Art. 2.2.4.6.13",
                "fecha_sello_utc": datetime.now(timezone.utc).isoformat(),
            }
            zf.writestr("manifest_custodia.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        # Registrar en HistoricoCustodia
        custodia_rec = HistoricoCustodia(
            informe_id=informe.id,
            hash_sha256=report_hash,
            snapshot_completo_json=report_data,
            archivo_zip_path=str(zip_path.relative_to(OUT)),
            firmado_por_licencia=f"{psicologa.nombre_completo} ({psicologa.licencia_sst})",
        )
        session.add(custodia_rec)

        # Cerrar medición
        med.estado = "cerrada"
        med.hash_integridad_sha256 = report_hash
        med.fecha_cierre = date.today()

        log = AuditLog(
            usuario_id=psicologa.id,
            accion="SELLAR_INFORME_CUSTODIA_20Y",
            entidad_tipo="MEDICION",
            entidad_id=med.id,
            datos_nuevos={"hash_sha256": report_hash, "zip": str(zip_path.name)},
        )
        session.add(log)
        session.commit()

        return {
            "success": True,
            "hash_sha256": report_hash,
            "estado": "cerrada",
            "archivo_zip": str(zip_path.name),
            "mensaje": f"Medición {med.codigo_campana} sellada e inmutabilizada exitosamente bajo custodia legal de 20 años.",
        }
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Módulo de Casos, OMR y Cuadernillos
# -----------------------------------------------------------------------------
@app.get("/api/casos")
def api_casos(
    current_user: CargaUser,
    q: Optional[str] = Query(None, description="Búsqueda por nombre, cédula o cargo"),
    estado_filtro: Optional[str] = Query(None, alias="estado", description="Filtro por estado"),
    forma_filtro: Optional[str] = Query(None, alias="forma", description="Filtro por Forma A o B"),
    medicion_id: Optional[str] = Query(None, description="Filtro por ID de medición"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=5, le=500),
):
    """Retorna la lista paginada y filtrable de casos con métricas globales del lote."""
    # Primero intentar leer desde la base de datos relacional
    session = SyncSessionLocal()
    all_casos = []
    try:
        query = session.query(CasoCuadernillo)
        if medicion_id:
            query = query.filter_by(medicion_id=medicion_id)
        db_casos = query.order_by(CasoCuadernillo.created_at.desc()).all()
        if db_casos:
            all_casos = [c.to_dict() for c in db_casos]
    except Exception:
        pass
    finally:
        session.close()

    if not all_casos:
        # Fallback a archivos JSON locales
        all_casos = load_all(CASOS)
        for c in all_casos:
            c["estado"] = estado(c)

    # Métricas agregadas
    total_casos = len(all_casos)
    listos = sum(1 for c in all_casos if c["estado"] == "listo")
    faltan_datos = sum(1 for c in all_casos if c["estado"] == "faltan_datos")
    doble_marca = sum(1 for c in all_casos if c["estado"] == "doble_marca")

    riesgo_dist = {"Sin riesgo": 0, "Riesgo bajo": 0, "Riesgo medio": 0, "Riesgo alto": 0, "Riesgo muy alto": 0}
    for c in all_casos:
        sc = ((c.get("scoring") or {}).get("intra") or {}).get("total") or {}
        nv = sc.get("nivel")
        if nv in riesgo_dist:
            riesgo_dist[nv] += 1

    # Filtrado en memoria
    filtrados = all_casos
    if estado_filtro and estado_filtro != "todos":
        filtrados = [c for c in filtrados if c.get("estado") == estado_filtro]
    if forma_filtro and forma_filtro != "todas":
        filtrados = [c for c in filtrados if (c.get("forma") or "A").upper() == forma_filtro.upper()]
    if q and q.strip():
        term = q.strip().lower()

        def match(c):
            idn = c.get("identidad") or {}
            nom = (idn.get("nombre") or "").lower()
            doc = (c.get("id_documento") or idn.get("id_documento") or "").lower()
            car = (idn.get("cargo") or "").lower()
            arc = (c.get("archivo") or "").lower()
            return term in nom or term in doc or term in car or term in arc

        filtrados = [c for c in filtrados if match(c)]

    total_filtrados = len(filtrados)
    total_pages = max(1, (total_filtrados + page_size - 1) // page_size)
    start = (page - 1) * page_size
    page_items = filtrados[start : start + page_size]

    return {
        "casos": page_items,
        "total": total_filtrados,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "stats": {
            "total": total_casos,
            "listos": listos,
            "faltan_datos": faltan_datos,
            "doble_marca": doble_marca,
            "riesgo_dist": riesgo_dist,
        },
    }


@app.get("/api/casos/{caso_id}")
def api_caso_detalle(caso_id: str):
    c = get_caso(CASOS, caso_id)
    if not c:
        # Intentar desde DB
        session = SyncSessionLocal()
        try:
            caso_db = session.query(CasoCuadernillo).filter_by(caso_uid=caso_id).first()
            if caso_db:
                return caso_db.to_dict()
        finally:
            session.close()
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    c["estado"] = estado(c)
    return c


@app.get("/api/casos/{caso_id}/pagina/{page_num}")
def api_caso_pagina_render(caso_id: str, page_num: int):
    """Renderiza al vuelo la página escaneada correspondiente a la página física."""
    c = get_caso(CASOS, caso_id)
    if not c:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    # 1. Si existe el PDF reordenado oficial (1..24), renderizar directamente de él
    ordered_filename = c.get("pdf_ordenado") or f"{Path(c.get('archivo', 'cuadernillo')).stem}_ordenado.pdf"
    ordered_path = None
    if c.get("pdf_ordenado_path") and Path(c["pdf_ordenado_path"]).exists():
        ordered_path = Path(c["pdf_ordenado_path"])
    else:
        for folder in [CASOS, OUT, UPLOAD, ROOT]:
            cand = folder / ordered_filename
            if cand.exists():
                ordered_path = cand
                break

    if ordered_path and ordered_path.exists():
        try:
            doc = fitz.open(ordered_path)
            if 1 <= page_num <= len(doc):
                page = doc[page_num - 1]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("jpeg")
                doc.close()
                return Response(content=img_bytes, media_type="image/jpeg")
            doc.close()
        except Exception as e:
            logger.warning(f"Fallback desde pdf_ordenado falló: {e}")

    # 2. Fallback: buscar en el PDF original con scan_index y rot_angle
    paginas = c.get("paginas", [])
    scan_idx = page_num
    rot_angle = 0
    for p in paginas:
        if p.get("physical_page") == page_num:
            scan_idx = p.get("scan_index", page_num)
            rot_angle = p.get("rot_angle", 0)
            break

    pdf_filename = c.get("archivo")
    pdf_path = None
    if c.get("archivo_path") and Path(c["archivo_path"]).exists():
        pdf_path = Path(c["archivo_path"])
    elif pdf_filename:
        for folder in [UPLOAD, ROOT / "baterias de prueba", ROOT, CASOS, OUT]:
            cand = folder / pdf_filename
            if cand.exists():
                pdf_path = cand
                break

    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Archivo PDF original no encontrado")

    try:
        doc = fitz.open(pdf_path)
        if scan_idx < 1 or scan_idx > len(doc):
            doc.close()
            raise HTTPException(status_code=400, detail=f"Página fuera de rango (1..{len(doc)})")
        page = doc[scan_idx - 1]
        if rot_angle != 0:
            page.set_rotation((page.rotation + rot_angle) % 360)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("jpeg")
        doc.close()
        return Response(content=img_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renderizando página: {e}")



@app.post("/api/upload")
async def api_upload(
    current_user: CargaUser,
    files: List[UploadFile] = File(...),
    medicion_id: Optional[str] = Form(None),
):
    """Carga masiva de cuadernillos asociada a una Medición de Empresa."""
    if len(files) > 1000:
        return {"error": "Máximo 1000 archivos por lote"}

    nit = None
    codigo = None
    if medicion_id:
        session = SyncSessionLocal()
        try:
            med = session.query(Medicion).filter_by(id=medicion_id).first()
            if not med:
                raise HTTPException(status_code=404, detail="Medición no encontrada")
            _assert_medicion_visible(med, current_user)
            if med.estado not in ("recoleccion", "auditoria"):
                raise HTTPException(status_code=403, detail="La campaña no admite carga de cuadernillos.")
            nit = med.empresa.nit if med.empresa else None
            codigo = med.codigo_campana
        finally:
            session.close()

    saved_paths: List[Path] = []
    for f in files:
        fname = f.filename or f"upload_{uuid.uuid4().hex[:8]}.pdf"
        content = await f.read()

        if fname.lower().endswith(".zip"):
            zip_target_dir = (
                ensure_campaign_dirs(nit, codigo) / "uploads" / f"zip_{uuid.uuid4().hex[:8]}"
                if nit and codigo
                else UPLOAD / f"zip_{uuid.uuid4().hex[:8]}"
            )
            zip_target_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for z_info in zf.infolist():
                    if z_info.is_dir():
                        continue
                    safe_name = os.path.basename(z_info.filename)
                    if safe_name.lower().endswith(".pdf") and not safe_name.startswith("."):
                        extracted_dest = zip_target_dir / safe_name
                        with zf.open(z_info) as src, open(extracted_dest, "wb") as dst:
                            dst.write(src.read())
                        saved_paths.append(extracted_dest)
        else:
            if nit and codigo:
                dest = save_upload(nit, codigo, fname, content)
            else:
                safe_name = os.path.basename(fname)
                dest = UPLOAD / (safe_name if safe_name.lower().endswith(".pdf") else f"{safe_name}.pdf")
                dest.write_bytes(content)
            saved_paths.append(dest)

    if not saved_paths:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron archivos PDF válidos en los elementos cargados.",
        )

    job = batch_manager.create_batch(
        saved_paths, out_dir=OUT, casos_dir=CASOS, medicion_id=medicion_id
    )
    loop = asyncio.get_event_loop()
    batch_manager.start_batch_async(job, loop)

    return {
        "job_id": job.job_id,
        "total": len(saved_paths),
        "medicion_id": medicion_id,
        "message": f"Iniciado procesamiento masivo de {len(saved_paths)} cuadernillos",
    }


@app.get("/api/batch/{job_id}/events")
async def api_batch_events(job_id: str):
    """Streaming de eventos SSE con la barra de progreso en tiempo real del lote."""
    return EventSourceResponse(batch_manager.stream_events(job_id))


@app.get("/api/batch/{job_id}/status")
def api_batch_status(job_id: str):
    st = batch_manager.get_job_status(job_id)
    if not st:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return st


@app.post("/api/batch/{job_id}/cancel")
def api_batch_cancel(job_id: str):
    ok = batch_manager.cancel_batch(job_id)
    return {"cancelled": ok}


@app.post("/api/casos/{caso_id}/datos")
def api_datos(caso_id: str, body: DatosIn, current_user: ClinicoUser):
    c = get_caso(CASOS, caso_id)
    if not c:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    ident = c.setdefault("identidad", {})
    ident["nombre"] = body.nombre.strip()
    ident["cargo"] = body.cargo.strip()
    ident["fecha"] = body.fecha.strip()
    ident["dependencia"] = body.dependencia.strip()
    if body.id_documento:
        ident["id_documento"] = body.id_documento.strip()
        c["id_documento"] = ident["id_documento"]

    c["psicologa"] = body.psicologa.strip()
    saved = save_caso(CASOS, c)

    try:
        export_workbook(load_all(CASOS), OUT / "respuestas.xlsx")
    except Exception:
        pass

    return saved


@app.post("/api/casos/{caso_id}/decidir")
def api_decidir(caso_id: str, body: DecisionIn, current_user: PsicoUser):
    c = get_caso(CASOS, caso_id)
    if not c:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if not body.psicologa.strip():
        raise HTTPException(status_code=400, detail="Debe indicar el nombre de la psicóloga que decide.")

    c["psicologa"] = body.psicologa.strip()
    c = aplicar_decision(c, body.amb_id, body.choice, body.psicologa.strip())
    saved = save_caso(CASOS, c)

    try:
        export_workbook(load_all(CASOS), OUT / "respuestas.xlsx")
    except Exception:
        pass

    return saved


@app.delete("/api/casos/{caso_id}")
def api_delete_caso(caso_id: str):
    p = CASOS / f"{caso_id}.json"
    if p.exists():
        p.unlink()

    session = SyncSessionLocal()
    try:
        c_db = session.query(CasoCuadernillo).filter_by(caso_uid=caso_id).first()
        if c_db:
            session.delete(c_db)
            session.commit()
    except Exception:
        pass
    finally:
        session.close()

    try:
        export_workbook(load_all(CASOS), OUT / "respuestas.xlsx")
    except Exception:
        pass

    return {"deleted": True, "caso_id": caso_id}


@app.post("/api/demo")
def api_demo(current_user: ClinicoUser, medicion_id: Optional[str] = Query(None)):
    """Genera un caso demostrativo con ambigüedad real vinculado a la medición activa."""
    session = SyncSessionLocal()
    target_med_id = medicion_id
    try:
        if not target_med_id:
            first_med = session.query(Medicion).order_by(Medicion.created_at.desc()).first()
            if first_med:
                target_med_id = first_med.id
    finally:
        session.close()

    caso = {
        "caso_id": f"demo_{uuid.uuid4().hex[:8]}",
        "medicion_id": target_med_id,
        "archivo": "ejemplo_doble_chuleado.pdf",
        "forma": "A",
        "n_paginas": 24,
        "identidad": {
            "nombre": "Carolina Gómez Ospina",
            "cargo": "Analista de Talento Humano",
            "fecha": "12/09/2026",
            "dependencia": "Gestión Humana",
            "id_documento": "52841930",
        },
        "id_documento": "52841930",
        "psicologa": "Dra. Claudia Marcela Valencia",
        "intra": {"1": 0, "2": 1, "3": 2, "4": 1, "5": 0, "6": 2, "7": 3, "8": 1, "9": 0, "10": 1, "11": 2, "12": 0},
        "extra": {str(i): (i % 5) for i in range(1, 32)},
        "estres": {str(i): (i % 4) for i in range(1, 32)},
        "faltantes": {"intra": list(range(15, 124)), "extra": [], "estres": []},
        "calidad": {"intra_leidos": 12, "intra_esperados": 123, "extra_leidos": 31, "estres_leidos": 31},
        "ambiguos": [
            {
                "id": "I013",
                "bloque": "intra",
                "item": 13,
                "pagina": 9,
                "fills": [0.31, 0.02, 0.29, 0.01, 0.0],
                "marcadas": [0, 2],
                "etiquetas": ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"],
                "crop": None,
                "decision": None,
                "decidido_por": None,
            },
            {
                "id": "I014",
                "bloque": "intra",
                "item": 14,
                "pagina": 9,
                "fills": [0.02, 0.28, 0.27, 0.01, 0.0],
                "marcadas": [1, 2],
                "etiquetas": ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"],
                "crop": None,
                "decision": None,
                "decidido_por": None,
            },
        ],
    }
    intra_num = {int(k): v for k, v in caso["intra"].items()}
    extra_num = {int(k): v for k, v in caso["extra"].items()}
    estres_num = {int(k): v for k, v in caso["estres"].items()}
    caso["scoring"] = score_persona("A", intra_num, extra_num, estres_num)
    saved = save_caso(CASOS, caso)
    export_workbook(load_all(CASOS), OUT / "respuestas.xlsx")
    return saved


def export_casos_to_excel(medicion_id: Optional[str] = None) -> tuple[Path, str]:
    """Genera al vuelo el libro Excel consolidado o filtrado por medición con baremos de Villalobos."""
    session = SyncSessionLocal()
    casos = []
    med_code = "Maestro"
    try:
        query = session.query(CasoCuadernillo)
        if medicion_id:
            query = query.filter_by(medicion_id=medicion_id)
            med = session.query(Medicion).filter_by(id=medicion_id).first()
            if med:
                med_code = med.codigo_campana
        db_casos = query.all()
        if db_casos:
            casos = [c.to_dict() for c in db_casos]
    except Exception:
        pass
    finally:
        session.close()

    if not casos:
        all_local = load_all(CASOS)
        if medicion_id:
            casos = [c for c in all_local if c.get("medicion_id") == medicion_id]
        else:
            casos = all_local

    for c in casos:
        if "calidad" not in c or not c["calidad"]:
            c["calidad"] = {
                "intra_leidos": len(c.get("intra") or {}),
                "intra_esperados": 97 if c.get("forma") == "B" else 123,
                "extra_leidos": len(c.get("extra") or {}),
                "estres_leidos": len(c.get("estres") or {}),
            }

    OUT.mkdir(parents=True, exist_ok=True)
    if medicion_id:
        clean_code = "".join(ch for ch in med_code if ch.isalnum() or ch in ("-", "_"))
        target_path = OUT / f"respuestas_{clean_code}.xlsx"
        filename = f"Baterias_Psicosociales_Medicion_{clean_code}.xlsx"
    else:
        target_path = OUT / "respuestas_consolidado_maestro.xlsx"
        filename = "Baterias_Psicosociales_Maestro_Consolidado.xlsx"

    export_workbook(casos, target_path)

    # Mantener sincronizado respuestas.xlsx genérico para retrocompatibilidad
    try:
        if not medicion_id:
            import shutil
            shutil.copyfile(target_path, OUT / "respuestas.xlsx")
    except Exception:
        pass

    return target_path, filename


@app.get("/api/excel")
def api_excel(medicion_id: Optional[str] = Query(None)):
    """Descarga la matriz de respuestas y baremos consolidados en formato Excel (.xlsx)."""
    target_path, filename = export_casos_to_excel(medicion_id)
    return FileResponse(
        target_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/mediciones/{medicion_id}/excel")
def api_medicion_excel(medicion_id: str):
    """Descarga la matriz de respuestas y baremos de una Medición específica en Excel (.xlsx)."""
    target_path, filename = export_casos_to_excel(medicion_id)
    return FileResponse(
        target_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/casos/{caso_id}/json")
def api_caso_json(caso_id: str):
    p = CASOS / f"{caso_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return FileResponse(p, filename=f"caso_{caso_id}.json", media_type="application/json")


@app.get("/api/casos/{caso_id}/pdf-ordenado")
def api_caso_pdf_ordenado(caso_id: str):
    """Descarga el cuadernillo de 24 páginas reordenado físicamente en orden 1..24."""
    c = get_caso(CASOS, caso_id)
    if not c:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    ordered_filename = c.get("pdf_ordenado") or f"{Path(c.get('archivo', 'cuadernillo')).stem}_ordenado.pdf"
    ordered_path = None
    for folder in [CASOS, OUT, UPLOAD]:
        cand = folder / ordered_filename
        if cand.exists():
            ordered_path = cand
            break

    if not ordered_path or not ordered_path.exists():
        pdf_filename = c.get("archivo")
        raw_path = None
        for folder in [UPLOAD, ROOT / "baterias de prueba", ROOT]:
            cand = folder / pdf_filename
            if cand.exists():
                raw_path = cand
                break
        if raw_path and raw_path.exists():
            dest = CASOS / ordered_filename
            generate_ordered_pdf(raw_path, c.get("paginas", []), dest)
            ordered_path = dest
            c["pdf_ordenado"] = ordered_filename
            save_caso(CASOS, c)

    if not ordered_path or not ordered_path.exists():
        raise HTTPException(status_code=404, detail="No se encontró ni se pudo generar el PDF ordenado")

    safe_name = f"{Path(c.get('archivo', 'cuadernillo')).stem}_ordenado_1_24.pdf"
    return FileResponse(ordered_path, filename=safe_name, media_type="application/pdf")
