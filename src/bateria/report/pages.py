"""Capítulos del informe diagnóstico (cada función retorna HTML interior de 1..n hojas)."""

from __future__ import annotations

import html
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .catalog_narratives import ORDEN_DOMINIOS, ORDEN_EXTRA, ORDEN_INTRA, narrativa
from .svg_charts import hbar_critico, legend_html, stacked_bar

NIVELES = ["Sin riesgo", "Riesgo bajo", "Riesgo medio", "Riesgo alto", "Riesgo muy alto"]
Page = Tuple[str, str]  # (titulo_toc, inner_html)


def esc(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


def _dist(block: Optional[Mapping], *keys: str) -> Dict[str, Any]:
    cur: Any = block or {}
    for k in keys:
        cur = (cur or {}).get(k) or {}
    return cur if isinstance(cur, dict) else {}


def _pct(dist: Mapping, nivel: str) -> float:
    val = dist.get(nivel)
    if isinstance(val, dict):
        return float(val.get("porcentaje") or 0)
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _qty(dist: Mapping, nivel: str) -> int:
    val = dist.get(nivel)
    if isinstance(val, dict):
        return int(val.get("cantidad") or 0)
    return 0


def risk_table(rows: Sequence[Tuple[str, Mapping]], compact: bool = False) -> str:
    body = []
    for name, dist in rows:
        pa, pma = _pct(dist, "Riesgo alto"), _pct(dist, "Riesgo muy alto")
        critico = (pa + pma) >= 35
        badge = '<span class="badge-critico">PRIORIDAD</span>' if critico else ""
        body.append(
            f'<tr class="{"critico" if critico else ""}">'
            f'<td class="dim-name">{esc(name)} {badge}</td>'
            f'<td class="num val-none">{_pct(dist, "Sin riesgo"):.1f}%</td>'
            f'<td class="num val-low">{_pct(dist, "Riesgo bajo"):.1f}%</td>'
            f'<td class="num val-med">{_pct(dist, "Riesgo medio"):.1f}%</td>'
            f'<td class="num val-high">{pa:.1f}%</td>'
            f'<td class="num val-vhigh">{pma:.1f}%</td>'
            f"</tr>"
        )
    cls = "data-table table-compact" if compact else "data-table"
    return f"""
    <table class="{cls}">
      <thead><tr>
        <th class="dim-col">Factor / dimensión</th>
        <th>Sin riesgo</th><th>Bajo</th><th>Medio</th><th>Alto</th><th>Muy alto</th>
      </tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table>"""


def _media(baremos: Mapping, key: str) -> str:
    st = ((baremos.get("medias") or {}).get(key) or {})
    m = st.get("media")
    return f"{m:.1f}" if isinstance(m, (int, float)) else "s.d."


def page_portada(ctx: Dict[str, Any]) -> List[Page]:
    e, m, p, socio = ctx["empresa"], ctx["medicion"], ctx["psicologa"], ctx["socio"]
    sello = "DICTAMEN OFICIAL · CUSTODIA 20 AÑOS" if ctx["is_sealed"] else "BORRADOR DE AUDITORÍA CLÍNICA"
    inner = f"""
    <div class="cover">
      <div>
        <div class="cover-kicker">PROTEGER I.P.S. S.A.S. · Seguridad y Salud en el Trabajo</div>
        <h1>Informe diagnóstico de factores de riesgo psicosocial</h1>
        <h2>{esc(e.get("razon_social") or "Empresa evaluada")}</h2>
        <p class="cover-meta">
          NIT {esc(e.get("nit") or "N/A")}{'-' + esc(e.get("digito_verificacion")) if e.get("digito_verificacion") else ''}<br>
          Actividad: {esc(e.get("sector_economico") or "Servicios")} · CIIU {esc(e.get("codigo_ciiu") or "N/A")}<br>
          Sede: {esc(m.get("sede") or "Principal")} · {esc(e.get("ciudad") or "Colombia")}<br>
          Campaña {esc(m.get("codigo_campana") or "MED")} · {esc(m.get("periodo") or "Anual")} ({esc(m.get("anio") or "")})<br>
          Muestra: {esc(ctx.get("total_evaluados") or 0)} trabajadores
          (Forma A: {esc(socio.get("forma_a_conteo") or 0)} · Forma B: {esc(socio.get("forma_b_conteo") or 0)})
        </p>
      </div>
      <div>
        <div class="cover-stamp">{sello}</div>
        <p class="cover-meta" style="margin-top:16px">
          Psicóloga especialista SST responsable<br>
          <strong>{esc(p.get("nombre_completo") or p.get("nombre") or "Especialista SST")}</strong><br>
          T.P. {esc(p.get("tarjeta_profesional") or "s.d.")} ·
          Licencia SST {esc(p.get("licencia_sst") or p.get("licencia_so") or "s.d.")}<br>
          {esc(p.get("dpto_licencia_sst") or "")}
        </p>
        <p class="muted" style="margin-top:18px">
          Resolución 2646 de 2008 · Resolución 2764 de 2022 · Decreto 1072 de 2015 art. 2.2.4.6.13<br>
          Batería de Instrumentos para la Evaluación de Factores de Riesgo Psicosocial
          (Ministerio de la Protección Social / Pontificia Universidad Javeriana).
        </p>
      </div>
    </div>"""
    return [("Portada institucional", inner)]


def page_control(ctx: Dict[str, Any]) -> List[Page]:
    e, m = ctx["empresa"], ctx["medicion"]
    inner = f"""
    <div class="section-hdr">Control documental y confidencialidad</div>
    <table class="table-meta">
      <tr><td class="label">Tipo documental</td><td>Informe diagnóstico epidemiológico de riesgo psicosocial (organizacional)</td></tr>
      <tr><td class="label">Código de medición</td><td>{esc(m.get("codigo_campana"))}</td></tr>
      <tr><td class="label">Versión</td><td>{"Sellada" if ctx["is_sealed"] else "Borrador de auditoría"} · SHA-256 {esc(ctx["hash_sha"][:16])}…</td></tr>
      <tr><td class="label">Destinatarios</td><td>Responsable del SG-SST de {esc(e.get("razon_social"))}; psicóloga especialista firmante; autoridad de inspección cuando sea requerida.</td></tr>
      <tr><td class="label">Custodia</td><td>Veinte (20) años, art. 2.2.4.6.13 Decreto 1072 de 2015 y art. 14 Resolución 2764 de 2022.</td></tr>
      <tr><td class="label">Clasificación</td><td>Reservado. No contiene cédulas ni nombres de trabajadores (Ley 1581 de 2012).</td></tr>
    </table>
    <div class="section-hdr">Alcance y limitaciones</div>
    <div class="prose">
      <p>Este informe consolida resultados <strong>colectivos</strong> de la Batería de Instrumentos aplicada
      a la población evaluada. No sustituye concepto clínico individual ni dictamen de origen de enfermedad laboral.
      Los baremos son los publicados para Forma A (jefes, profesionales y técnicos) y Forma B (auxiliares y operarios).</p>
      <p>La ficha de datos generales (págs. 2–5 del cuadernillo) se estructura en base de datos; cuando un campo
      sociodemográfico no fue leído por OMR, el capítulo correspondiente declara la limitación y no inventa valores.</p>
      <p>Las marcas ambiguas (doble chuleado) se resuelven por la psicóloga en la sala de lectura antes del sellado.
      Ítems no respondidos no se imputan: la dimensión se califica sobre ítems contestados y se marca incompleta si falta alguno esperado.</p>
    </div>
    <div class="section-hdr">Huella criptográfica</div>
    <span class="custody-hash-code">{esc(ctx["hash_sha"])}</span>
    """
    return [("Control documental y confidencialidad", inner)]


def page_intro(ctx: Dict[str, Any]) -> List[Page]:
    e = ctx["empresa"]
    inner = f"""
    <div class="section-hdr">1. Introducción</div>
    <div class="prose">
      <p>La evaluación de factores de riesgo psicosocial es una obligación del Sistema de Gestión de Seguridad
      y Salud en el Trabajo. Permite identificar condiciones de origen laboral y extralaboral, y la sintomatología
      de estrés asociada, para orientar el Programa de Vigilancia Epidemiológica (PVE) y las intervenciones
      primarias, secundarias y terciarias.</p>
      <p>PROTEGER I.P.S. S.A.S. aplicó la Batería de Instrumentos del Ministerio de la Protección Social y la
      Pontificia Universidad Javeriana a la población de <strong>{esc(e.get("razon_social") or "la empresa")}</strong>,
      digitalizó los cuadernillos mediante OMR morfológico inmune a trasluz y calificó los puntajes transformados
      con los baremos oficiales de Villalobos.</p>
      <p>El presente documento entrega el diagnóstico organizacional: ficha técnica, caracterización disponible,
      resultados por instrumento, dominio y dimensión, cruces por forma y área, priorización y recomendaciones
      de intervención. Los resultados individuales permanecen en la sala de lectura clínica, fuera de este entregable.</p>
    </div>
    <div class="section-hdr">Contexto de la organización evaluada</div>
    <table class="table-meta">
      <tr><td class="label">Razón social</td><td>{esc(e.get("razon_social"))}</td>
          <td class="label">NIT</td><td>{esc(e.get("nit"))}</td></tr>
      <tr><td class="label">Sector</td><td>{esc(e.get("sector_economico") or "s.d.")}</td>
          <td class="label">CIIU</td><td>{esc(e.get("codigo_ciiu") or "s.d.")}</td></tr>
      <tr><td class="label">Ciudad</td><td>{esc(e.get("ciudad") or "s.d.")}</td>
          <td class="label">Dirección</td><td>{esc(e.get("direccion") or "s.d.")}</td></tr>
    </table>
    """
    return [("Introducción", inner)]


def page_objetivos(ctx: Dict[str, Any]) -> List[Page]:
    inner = """
    <div class="section-hdr">2. Objetivos</div>
    <div class="section-hdr sub">2.1 Objetivo general</div>
    <div class="prose">
      <p>Diagnosticar el nivel de riesgo psicosocial de la población trabajadora evaluada, mediante la Batería
      de Instrumentos oficial, para fundamentar el Programa de Vigilancia Epidemiológica y las acciones del SG-SST.</p>
    </div>
    <div class="section-hdr sub">2.2 Objetivos específicos</div>
    <ol class="ol-legal">
      <li>Caracterizar la muestra según forma de aplicación (A / B), cargo y área, y declarar las limitaciones de la ficha sociodemográfica.</li>
      <li>Calificar el cuestionario de factores de riesgo psicosocial <strong>intralaboral</strong> (total, 4 dominios y dimensiones).</li>
      <li>Calificar el cuestionario <strong>extralaboral</strong> (total y 7 dimensiones, Tablas 17 y 18).</li>
      <li>Calificar el cuestionario de <strong>estrés</strong> (3.ª versión, 31 síntomas, escala 0–3).</li>
      <li>Identificar las dimensiones con mayor concentración en riesgo alto y muy alto para priorizar el PVE.</li>
      <li>Formular recomendaciones de intervención primaria, secundaria y terciaria, trazables a cada dimensión crítica.</li>
      <li>Dejar constancia de custodia documental por veinte años y de la huella SHA-256 del dictamen.</li>
    </ol>
    <div class="section-hdr sub">2.3 Usuarios del informe</div>
    <div class="prose">
      <p>Responsable del SG-SST, alta dirección, COPASST o vigía, comité de convivencia laboral y la psicóloga
      especialista firmante. No está destinado a publicación masiva ni a inclusión en hojas de vida de los evaluados.</p>
    </div>
    """
    return [("Objetivos", inner)]


def page_marco_legal(ctx: Dict[str, Any]) -> List[Page]:
    p1 = """
    <div class="section-hdr">3. Marco legal y técnico</div>
    <div class="prose">
      <p>La evaluación se apoya en el siguiente marco, citado de forma no exhaustiva:</p>
    </div>
    <div class="section-hdr sub">3.1 Resolución 2646 de 2008</div>
    <div class="prose">
      <p>Estableció disposiciones para la identificación, evaluación, prevención, intervención y monitoreo
      permanente de la exposición a factores de riesgo psicosocial en el trabajo, y para la determinación
      del origen de las patologías causadas por estrés ocupacional. Obligó a los empleadores a evaluar
      factores intralaborales, extralaborales y individuales, y a contar con un programa de vigilancia.</p>
    </div>
    <div class="section-hdr sub">3.2 Resolución 2764 de 2022</div>
    <div class="prose">
      <p>Actualizó los instrumentos y adoptó la Batería de la Universidad Javeriana / Ministerio de la Protección
      Social como referente técnico, precisó la periodicidad, la competencia del psicólogo con posgrado y
      licencia en SST, y el deber de conservar soportes. El artículo 14 se articula con la custodia de veinte años.</p>
    </div>
    <div class="section-hdr sub">3.3 Decreto 1072 de 2015, artículo 2.2.4.6.13</div>
    <div class="prose">
      <p>El empleador debe conservar los registros y documentos que soportan el SG-SST. Los resultados de
      evaluaciones de condiciones de salud y de riesgos se resguardan por un término no inferior a veinte (20) años.</p>
    </div>
    """
    p2 = """
    <div class="section-hdr">3. Marco legal (continuación)</div>
    <div class="section-hdr sub">3.4 Ley 1616 de 2013 — Salud mental</div>
    <div class="prose">
      <p>Reconoce la salud mental como derecho y ordena acciones de promoción y prevención en el entorno laboral.
      El PVE de factores psicosociales es una de las herramientas con las que el empleador materializa ese deber.</p>
    </div>
    <div class="section-hdr sub">3.5 Ley 1010 de 2006 — Acoso laboral</div>
    <div class="prose">
      <p>Cuando el dominio de liderazgo o las relaciones sociales concentran riesgo alto, el informe recomienda
      fortalecer el comité de convivencia y los protocolos de prevención de acoso, sin que el baremo por sí solo
      constituya prueba de acoso en un caso particular.</p>
    </div>
    <div class="section-hdr sub">3.6 Ley 1581 de 2012 — Protección de datos</div>
    <div class="prose">
      <p>Los datos de salud son sensibles. Este entregable es <strong>agregado y no nominativo</strong>.
      Las matrices individuales (ítem a ítem) se conservan en la bóveda de custodia y en la sala de lectura,
      con acceso restringido a la especialista y al personal autorizado.</p>
    </div>
    <div class="section-hdr sub">3.7 Ley 1090 de 2006 — Código deontológico del psicólogo</div>
    <div class="prose">
      <p>El consentimiento informado del cuadernillo (página 1) y la reserva de la información clínica
      rigen la práctica. El sellado del dictamen es un acto profesional de la psicóloga con tarjeta profesional
      y licencia SST, no un acto administrativo de la empresa evaluada.</p>
    </div>
    """
    return [("Marco legal y técnico (I)", p1), ("Marco legal y técnico (II)", p2)]


def page_marco_conceptual(ctx: Dict[str, Any]) -> List[Page]:
    inner = """
    <div class="section-hdr">4. Marco conceptual (modelo Villalobos)</div>
    <div class="prose">
      <p>La batería opera con <strong>puntaje bruto</strong> (suma de ítems, con inversión de los protectores) y
      <strong>puntaje transformado</strong> = (bruto / (n × máximo de escala)) × 100. Intra y extra usan escala 0–4;
      estrés usa 0–3. El transformado se compara con cortes de cinco niveles: sin riesgo, bajo, medio, alto y muy alto.</p>
    </div>
    <div class="section-hdr sub">4.1 Intralaboral — cuatro dominios</div>
    <ol class="ol-legal">
      <li><strong>Liderazgo y relaciones sociales en el trabajo</strong> — jefe, pares, retroalimentación.</li>
      <li><strong>Control sobre el trabajo</strong> — claridad de rol, autonomía, participación, capacitación, habilidades.</li>
      <li><strong>Demandas del trabajo</strong> — carga, jornada, ambiente, emociones, consistencia, interferencia con la vida.</li>
      <li><strong>Recompensas</strong> — reconocimiento, compensación y pertenencia.</li>
    </ol>
    <div class="section-hdr sub">4.2 Extralaboral — siete dimensiones</div>
    <div class="prose">
      <p>Tiempo fuera del trabajo, relaciones familiares, comunicación interpersonal, situación económica,
      vivienda y entorno, influencia del entorno sobre el trabajo, y desplazamiento vivienda–trabajo–vivienda.
      Los cortes difieren entre jefes/profesionales (Tabla 17) y auxiliares/operarios (Tabla 18).</p>
    </div>
    <div class="section-hdr sub">4.3 Estrés</div>
    <div class="prose">
      <p>31 síntomas. Ningún ítem se invierte: «Siempre» es máximo riesgo. Un total alto obliga a ruta de atención
      y a intervenir las dimensiones intra/extra que lo alimentan; no equivale a diagnóstico psiquiátrico.</p>
    </div>
    """
    return [("Marco conceptual (Villalobos)", inner)]


def page_metodologia(ctx: Dict[str, Any]) -> List[Page]:
    p1 = """
    <div class="section-hdr">5. Metodología</div>
    <div class="section-hdr sub">5.1 Instrumentos</div>
    <div class="prose">
      <p>Se aplicó el cuadernillo físico de 24 páginas: consentimiento (pág. 1), ficha de datos generales (2–5),
      cuestionario intralaboral Forma A (123 ítems) o Forma B (97 ítems), cuestionario extralaboral (31 ítems)
      y cuestionario de estrés 3.ª versión (31 ítems).</p>
    </div>
    <div class="section-hdr sub">5.2 Forma A y Forma B</div>
    <div class="prose">
      <p><strong>Forma A</strong> se aplica a jefes, profesionales y técnicos. Incluye dimensiones de
      responsabilidad del cargo, consistencia del rol y relación con colaboradores (esta última solo si hay personal a cargo).
      <strong>Forma B</strong> se aplica a auxiliares y operarios. Los baremos no son intercambiables.</p>
    </div>
    <div class="section-hdr sub">5.3 Captura OMR</div>
    <div class="prose">
      <p>Las respuestas Likert no se leen por OCR de la palabra «Siempre». Se segmenta la grilla, se mide densidad
      de tinta oscura (píxel &lt; 150) con margen interno, y se rechaza el trasluz del reverso del papel bond.
      El doble chuleado queda como marca ambigua: la psicóloga decide en recorte visual; el motor no desempató.</p>
    </div>
    """
    p2 = """
    <div class="section-hdr">5. Metodología (continuación)</div>
    <div class="section-hdr sub">5.4 Reordenamiento ADF</div>
    <div class="prose">
      <p>Los escáneres dúplex con alimentador suelen entregar el reverso en orden inverso. Antes de tabular,
      se identifica el número de página impreso (1 a 24) y se reconstruye el cuadernillo. No se asume que el PDF
      llegue correlativo.</p>
    </div>
    <div class="section-hdr sub">5.5 Criterios de calidad psicométrica</div>
    <ol class="ol-legal">
      <li>Una dimensión se declara incompleta solo si n_respondidos &lt; n_esperados.</li>
      <li>Los ítems opcionales de jefatura o clientes no contestados no se tratan como faltantes.</li>
      <li>El puntaje transformado usa únicamente ítems respondidos (no se imputa la media).</li>
      <li>Los baremos extralaborales aplican Tabla 17 (Forma A) o Tabla 18 (Forma B) de forma obligatoria.</li>
    </ol>
    <div class="section-hdr sub">5.6 Unidad de análisis</div>
    <div class="prose">
      <p>La unidad es el trabajador-cuadernillo. El informe presenta distribuciones porcentuales sobre el n
      de casos con nivel calificable en cada factor. Las medias de puntaje transformado acompañan a los porcentajes
      para no confundir «muchos en alto» con «media extrema».</p>
    </div>
    """
    return [("Metodología (I)", p1), ("Metodología (II)", p2)]


def page_ficha_tecnica(ctx: Dict[str, Any]) -> List[Page]:
    e, m, p, socio = ctx["empresa"], ctx["medicion"], ctx["psicologa"], ctx["socio"]
    inner = f"""
    <div class="section-hdr">6. Ficha técnica de la medición</div>
    <table class="table-meta">
      <tr><td class="label">Empresa</td><td>{esc(e.get("razon_social"))}</td>
          <td class="label">NIT</td><td>{esc(e.get("nit"))}</td></tr>
      <tr><td class="label">Periodo</td><td>{esc(m.get("periodo"))} ({esc(m.get("anio"))})</td>
          <td class="label">Código</td><td>{esc(m.get("codigo_campana"))}</td></tr>
      <tr><td class="label">Sede</td><td>{esc(m.get("sede"))}</td>
          <td class="label">Fecha de inicio</td><td>{esc(m.get("fecha_inicio"))}</td></tr>
      <tr><td class="label">Trabajadores esperados</td><td>{esc(m.get("trabajadores_esperados") or 0)}</td>
          <td class="label">Evaluados</td><td><strong>{esc(ctx.get("total_evaluados") or 0)}</strong></td></tr>
      <tr><td class="label">Cobertura</td><td>{esc(socio.get("cobertura_porcentaje"))}%</td>
          <td class="label">Completos / ambiguos pend.</td>
          <td>{esc(socio.get("completos_conteo"))} / {esc(socio.get("ambiguos_pendientes"))}</td></tr>
      <tr><td class="label">Forma A</td><td>{esc(socio.get("forma_a_conteo"))} (jefes / profesionales / técnicos)</td>
          <td class="label">Forma B</td><td>{esc(socio.get("forma_b_conteo"))} (auxiliares / operarios)</td></tr>
      <tr><td class="label">Especialista</td><td>{esc(p.get("nombre_completo") or p.get("nombre"))}</td>
          <td class="label">Licencia SST</td><td>{esc(p.get("licencia_sst") or p.get("licencia_so"))}</td></tr>
    </table>
    <div class="kpi-row">
      <div class="kpi"><div class="k">Muestra</div><div class="v">{esc(ctx.get("total_evaluados") or 0)}</div></div>
      <div class="kpi"><div class="k">Cobertura</div><div class="v">{esc(socio.get("cobertura_porcentaje"))}%</div></div>
      <div class="kpi"><div class="k">Forma A</div><div class="v">{esc(socio.get("forma_a_conteo") or 0)}</div></div>
      <div class="kpi"><div class="k">Forma B</div><div class="v">{esc(socio.get("forma_b_conteo") or 0)}</div></div>
    </div>
    <div class="prose">
      <p>La cobertura se calcula sobre los trabajadores esperados declarados en la campaña. Si ese dato es 0,
      el denominador es el n de cuadernillos leídos. Un ambiguo pendiente no impide calificar el resto de ítems,
      pero sí debe resolverse antes del sellado legal.</p>
    </div>
    """
    return [("Ficha técnica de la medición", inner)]


def _kv_table(title: str, data: Mapping[str, Any], empty: str) -> str:
    if not data:
        return f'<p class="muted">{esc(empty)}</p>'
    rows = "".join(
        f"<tr><td>{esc(k)}</td><td class='num'>{esc(v)}</td></tr>" for k, v in list(data.items())[:12]
    )
    return f"""
    <div class="section-hdr sub">{esc(title)}</div>
    <table class="data-table"><thead><tr><th class="dim-col">Categoría</th><th>n</th></tr></thead>
    <tbody>{rows}</tbody></table>"""


def page_sociodemografico(ctx: Dict[str, Any]) -> List[Page]:
    socio = ctx["socio"]
    p1 = f"""
    <div class="section-hdr">7. Caracterización sociodemográfica</div>
    <div class="prose">
      <p>La ficha oficial (preguntas 1 a 24) contempla sexo, nacimiento, estado civil, escolaridad, ocupación,
      residencia, estrato, vivienda, personas a cargo, antigüedad, tipo de cargo, contrato, horas y salario.
      En esta medición se estructuró la tabla relacional; los campos aún no leídos por OMR de casillas de ficha
      <strong>no se imputan</strong>. Se reporta lo disponible: forma, cargo y área provenientes del consentimiento y de la clasificación A/B.</p>
    </div>
    {_kv_table("7.1 Distribución por forma de aplicación", socio.get("distribucion_forma") or {}, "Sin datos de forma.")}
    {_kv_table("7.2 Cargos con mayor participación", socio.get("cargos_principales") or {}, "Cargos no leídos en el consentimiento; se declara limitación.")}
    """
    p2 = f"""
    <div class="section-hdr">7. Caracterización (continuación)</div>
    {_kv_table("7.3 Áreas / dependencias", socio.get("areas_principales") or {}, "Áreas no leídas; se declara limitación.")}
    <div class="section-hdr sub">7.4 Limitación metodológica</div>
    <div class="prose">
      <p>Mientras no se complete la lectura OMR de las casillas de la ficha (motor distinto a la grilla Likert
      de 5 columnas), no se publican pirámides de sexo, edad, escolaridad ni tipo de contrato. Inventar esas
      cifras violaría el principio de evidencia del dictamen. El esquema de base de datos ya reserva los campos
      para cuando esa captura exista o se complete de forma manual por la especialista.</p>
      <p>Los cruces de riesgo de este informe se hacen con las variables disponibles: forma A/B, cargo y área.</p>
    </div>
    """
    return [("Caracterización sociodemográfica (I)", p1), ("Caracterización sociodemográfica (II)", p2)]


def page_globales(ctx: Dict[str, Any]) -> List[Page]:
    b = ctx["baremos"]
    rows = [
        ("1. Factor intralaboral (total)", b.get("intralaboral_total") or {}),
        ("2. Factor extralaboral (total)", b.get("extralaboral_total") or {}),
        ("3. Síntomas de estrés (total)", b.get("estres_total") or {}),
        ("4. Riesgo general (intra + extra)", b.get("general_total") or {}),
    ]
    inner = f"""
    <div class="section-hdr">8. Resultados globales de los tres instrumentos</div>
    <p class="muted">Distribución porcentual según baremos transformados oficiales. Medias de puntaje transformado:
    Intra {_media(b, "intralaboral_total")} · Extra {_media(b, "extralaboral_total")} ·
    Estrés {_media(b, "estres_total")} · General {_media(b, "general_total")}.</p>
    {legend_html()}
    {risk_table(rows)}
    <div class="section-hdr sub">Lectura ejecutiva</div>
    <div class="prose">
      <p>El total general combina intra y extra (Tabla 34) y no incluye estrés: el estrés es un desenlace,
      no un factor. Un total intra elevado con estrés alto refuerza la hipótesis de que las demandas y el
      bajo control ya se expresan en síntomas; un extra alto con intra moderado orienta a conciliación,
      desplazamiento o red de apoyo, más que a rediseño del puesto.</p>
    </div>
    {stacked_bar(b.get("intralaboral_total") or {})}
    <p class="muted">Barra apilada: Intralaboral total.</p>
    {stacked_bar(b.get("extralaboral_total") or {})}
    <p class="muted">Barra apilada: Extralaboral total.</p>
    {stacked_bar(b.get("estres_total") or {})}
    <p class="muted">Barra apilada: Estrés total.</p>
    """
    return [("Resultados globales de los instrumentos", inner)]


def page_intra_total(ctx: Dict[str, Any]) -> List[Page]:
    b = ctx["baremos"]
    dist = b.get("intralaboral_total") or {}
    inner = f"""
    <div class="section-hdr">9. Cuestionario intralaboral — total</div>
    <div class="prose">
      <p>El total intralaboral resume las condiciones de origen laboral. Se califica con los cortes de la
      Tabla 33 (Forma A) o su equivalente Forma B. Media transformada: <strong>{_media(b, "intralaboral_total")}</strong>.</p>
    </div>
    {legend_html()}
    {risk_table([("Total intralaboral", dist)])}
    {stacked_bar(dist)}
    <div class="clinical-prose">Un porcentaje elevado en riesgo alto o muy alto en el total, más que en una
dimensión aislada, indica que el problema no es un «pico» local sino un patrón de condiciones de trabajo.
El PVE debe entonces combinar liderazgo, control y demandas, no un taller genérico de estrés.</div>
    """
    return [("Intralaboral — total", inner)]


def page_dominios(ctx: Dict[str, Any]) -> List[Page]:
    dmap = ctx["baremos"].get("dominios_intralaborales") or {}
    pages: List[Page] = []
    ordered = [n for n in ORDEN_DOMINIOS if n in dmap] + [n for n in dmap if n not in ORDEN_DOMINIOS]
    # 2 dominios por hoja
    for i in range(0, max(len(ordered), 1), 2):
        chunk = ordered[i : i + 2] or ["Demandas del trabajo"]
        blocks = []
        for name in chunk:
            dist = dmap.get(name) or {}
            nav = narrativa(name)
            blocks.append(f"""
            <div class="dim-block">
              <h3>{esc(name)}</h3>
              <p class="prose">{esc(nav.get("definicion"))}</p>
              {stacked_bar(dist)}
              {risk_table([(name, dist)], compact=True)}
              <p class="prose">{esc(dist.get("lectura") or nav.get("interpretacion_alto"))}</p>
              <p class="muted"><strong>Intervención primaria:</strong> {esc(nav.get("intervencion_primaria"))}</p>
            </div>""")
        pages.append((f"Dominios intralaborales ({i // 2 + 1})", f'<div class="section-hdr">10. Dominios intralaborales</div>{"".join(blocks)}'))
    return pages


def _dim_block(name: str, dist: Mapping) -> str:
    nav = narrativa(name)
    media = dist.get("media_transformado")
    media_txt = f"{media:.1f}" if isinstance(media, (int, float)) else "s.d."
    n_eval = dist.get("n_eval") or 0
    return f"""
    <div class="dim-block">
      <h3>{esc(name)}</h3>
      <p class="muted">Dominio: {esc(dist.get("dominio") or nav.get("dominio") or "—")} ·
      n evaluados: {esc(n_eval)} · media T: {media_txt}</p>
      <p class="prose">{esc(nav.get("definicion"))}</p>
      {stacked_bar(dist)}
      {risk_table([(name, dist)], compact=True)}
      <p class="prose">{esc(dist.get("lectura") or interpolar_fallback(name, dist))}</p>
      <p class="muted"><strong>Primaria:</strong> {esc(nav.get("intervencion_primaria"))}<br>
      <strong>Secundaria:</strong> {esc(nav.get("intervencion_secundaria"))}</p>
    </div>"""


def interpolar_fallback(name: str, dist: Mapping) -> str:
    from .catalog_narratives import interpolar_lectura

    return interpolar_lectura(
        name,
        float(dist.get("porcentaje_critico") or 0),
        int(dist.get("n_critico") or 0),
        int(dist.get("n_eval") or 0),
        dist.get("media_transformado"),
    )


def _pages_dimensiones(titulo_seccion: str, orden: Sequence[str], dmap: Mapping[str, Any], prefijo_toc: str) -> List[Page]:
    names = [n for n in orden if True]  # siempre emitir el catálogo oficial
    pages: List[Page] = []
    for i in range(0, len(names), 2):
        chunk = names[i : i + 2]
        blocks = [_dim_block(n, dmap.get(n) or {}) for n in chunk]
        pages.append(
            (
                f"{prefijo_toc} ({i // 2 + 1})",
                f'<div class="section-hdr">{esc(titulo_seccion)}</div>{"".join(blocks)}',
            )
        )
    return pages


def page_dims_intra(ctx: Dict[str, Any]) -> List[Page]:
    dmap = ctx["baremos"].get("dimensiones_intralaborales") or {}
    return _pages_dimensiones("11. Dimensiones intralaborales", ORDEN_INTRA, dmap, "Dimensiones intra")


def page_extra(ctx: Dict[str, Any]) -> List[Page]:
    b = ctx["baremos"]
    tot = b.get("extralaboral_total") or {}
    dmap = b.get("dimensiones_extralaborales") or {}
    first = f"""
    <div class="section-hdr">12. Cuestionario extralaboral</div>
    <div class="prose">
      <p>Siete dimensiones, Tablas 17 (Forma A) y 18 (Forma B). Media transformada total:
      <strong>{_media(b, "extralaboral_total")}</strong>. El extralaboral no se «corrige» con un taller de
      motivación: varias de sus dimensiones son estructurales (ingreso, trayecto, vivienda).</p>
    </div>
    {legend_html()}
    {risk_table([("Total extralaboral", tot)])}
    {stacked_bar(tot)}
    """
    pages = [("Extralaboral — total", first)]
    pages.extend(_pages_dimensiones("12. Dimensiones extralaborales", ORDEN_EXTRA, dmap, "Dimensiones extra"))
    return pages


def page_estres(ctx: Dict[str, Any]) -> List[Page]:
    b = ctx["baremos"]
    dist = b.get("estres_total") or {}
    nav = narrativa("Síntomas de estrés")
    p1 = f"""
    <div class="section-hdr">13. Cuestionario para la evaluación del estrés</div>
    <div class="prose"><p>{esc(nav.get("definicion"))}</p></div>
    {legend_html()}
    {risk_table([("Sintomatología general de estrés", dist)])}
    {stacked_bar(dist)}
    <p class="muted">Media transformada: {_media(b, "estres_total")}.</p>
    <div class="clinical-prose">{esc(dist.get("lectura") or nav.get("interpretacion_alto"))}</div>
    """
    p2 = f"""
    <div class="section-hdr">13. Estrés — intervención y lectura clínica</div>
    <div class="prose">
      <p>Los 31 ítems cubren cuatro grupos de malestar: fisiológicos (sueño, digestión, tensión muscular,
      palpitaciones), de comportamiento social (irritabilidad, aislamiento), intelectuales (olvido, dificultad
      de concentración) y psicoemocionales (ánimo, ansiedad). El informe organizacional no desagrega síntoma
      a síntoma para no reidentificar personas; esa matriz queda en la sala de lectura.</p>
    </div>
    <div class="section-hdr sub">Intervención</div>
    <ol class="ol-legal">
      <li><strong>Primaria:</strong> {esc(nav.get("intervencion_primaria"))}</li>
      <li><strong>Secundaria:</strong> {esc(nav.get("intervencion_secundaria"))}</li>
      <li><strong>Terciaria:</strong> {esc(nav.get("intervencion_terciaria") or "Reincorporación protegida y ajuste de puesto cuando exista cuadro clínico documentado.")}</li>
    </ol>
    <div class="prose">
      <p>La ruta de atención es voluntaria y confidencial. Un total poblacional alto no autoriza citar a
      toda la planta a psicología: se ofrece el servicio, se interviene el origen laboral y se prioriza a
      quienes consultan o son detectados por el PVE con consentimiento.</p>
    </div>
    """
    return [("Estrés — resultados", p1), ("Estrés — intervención clínica", p2)]


def page_cruces(ctx: Dict[str, Any]) -> List[Page]:
    cruces = ctx.get("cruces") or {}
    forma = cruces.get("forma") or {}

    def forma_block(letra: str) -> str:
        bloq = forma.get(letra) or {}
        rows = [
            (f"Forma {letra} · Intra", bloq.get("intra") or {}),
            (f"Forma {letra} · Extra", bloq.get("extra") or {}),
            (f"Forma {letra} · Estrés", bloq.get("estres") or {}),
        ]
        return risk_table(rows, compact=True)

    areas = cruces.get("areas_intralaboral") or {}
    area_rows = [(k, v) for k, v in list(areas.items())[:8]]
    cargos = cruces.get("cargos_intralaboral") or {}
    cargo_rows = [(k, v) for k, v in list(cargos.items())[:8]]
    inner = f"""
    <div class="section-hdr">14. Análisis cruzado</div>
    <div class="prose">
      <p>Se cruza el nivel de riesgo de los totales con las variables disponibles (forma, área, cargo).
      Un área con n muy pequeño no debe leerse como «la peor de la empresa»: se informa el porcentaje y el n.</p>
    </div>
    <div class="section-hdr sub">14.1 Forma A frente a Forma B</div>
    {forma_block("A")}
    {forma_block("B")}
    <div class="section-hdr sub">14.2 Áreas — total intralaboral</div>
    {risk_table(area_rows, compact=True) if area_rows else '<p class="muted">Sin áreas leídas.</p>'}
    <div class="section-hdr sub">14.3 Cargos — total intralaboral</div>
    {risk_table(cargo_rows, compact=True) if cargo_rows else '<p class="muted">Sin cargos leídos.</p>'}
    """
    return [("Análisis cruzado (forma, área, cargo)", inner)]


def page_priorizacion(ctx: Dict[str, Any]) -> List[Page]:
    prios = ctx.get("prioritarias") or []
    ranking = {p["dimension"]: float(p.get("porcentaje_critico") or 0) for p in prios[:12]}
    rows = []
    for i, p in enumerate(prios[:12], 1):
        rows.append(
            f"<tr><td>{i}</td><td>{esc(p.get('dimension'))}</td><td>{esc(p.get('tipo'))}</td>"
            f"<td class='num'>{float(p.get('porcentaje_critico') or 0):.1f}%</td>"
            f"<td class='num'>{esc(p.get('n_critico'))}/{esc(p.get('n_eval'))}</td>"
            f"<td class='num'>{p.get('media_transformado') if p.get('media_transformado') is not None else 's.d.'}</td></tr>"
        )
    inner = f"""
    <div class="section-hdr">15. Priorización para el PVE</div>
    <div class="prose">
      <p>Se ordenan las dimensiones por la suma de porcentajes en riesgo alto y muy alto. Ese criterio
      privilegia la <em>extensión</em> del problema en la planta. La media transformada se muestra para
      detectar dimensiones con pocos casos extremos pero media alta.</p>
    </div>
    {hbar_critico(ranking)}
    <table class="data-table">
      <thead><tr><th>#</th><th class="dim-col">Dimensión</th><th>Tipo</th><th>% crítico</th><th>n crítico / n</th><th>Media T</th></tr></thead>
      <tbody>{''.join(rows) or '<tr><td colspan="6">Sin dimensiones en riesgo alto o muy alto.</td></tr>'}</tbody>
    </table>
    """
    return [("Priorización de dimensiones críticas", inner)]


def page_conclusiones(ctx: Dict[str, Any]) -> List[Page]:
    txt = ctx.get("conclusiones") or "Sin conclusiones registradas."
    inner = f"""
    <div class="section-hdr">16. Conclusiones diagnósticas</div>
    <div class="clinical-prose">{esc(txt)}</div>
    <div class="prose">
      <p>Las conclusiones son responsabilidad de la psicóloga especialista firmante. El texto automático
      de apoyo se genera interpolando las tres dimensiones con mayor % crítico; puede ser sustituido
      antes del sellado en la sala de lectura.</p>
    </div>
    """
    return [("Conclusiones diagnósticas", inner)]


def page_pve(ctx: Dict[str, Any]) -> List[Page]:
    prios = (ctx.get("prioritarias") or [])[:6]
    reco = ctx.get("recomendaciones") or ""
    lis = []
    for p in prios:
        nav = narrativa(p.get("dimension") or "")
        lis.append(
            f"<li><strong>{esc(p.get('dimension'))}</strong> ({esc(p.get('tipo'))}, "
            f"{float(p.get('porcentaje_critico') or 0):.1f}% crítico).<br>"
            f"<em>Primaria:</em> {esc(nav.get('intervencion_primaria'))}<br>"
            f"<em>Secundaria:</em> {esc(nav.get('intervencion_secundaria'))}</li>"
        )
    p1 = f"""
    <div class="section-hdr">17. Recomendaciones — PVE de factores psicosociales</div>
    <div class="prose">
      <p>El Programa de Vigilancia Epidemiológica debe ser específico, medible y anclado a las dimensiones
      priorizadas. Se organiza en tres niveles clásicos de prevención.</p>
    </div>
    <div class="section-hdr sub">17.1 Intervención primaria (fuente)</div>
    <div class="prose">
      <p>Rediseño de condiciones de trabajo: jornada, carga, autonomía, liderazgo, claridad de rol,
      desconexión y equidad. Es el nivel de mayor impacto poblacional.</p>
    </div>
    <div class="section-hdr sub">17.2 Intervención secundaria (detección temprana)</div>
    <div class="prose">
      <p>Formación de jefes, grupos de apoyo, tamizaje voluntario de síntomas y canales de denuncia
      protegidos (convivencia / acoso).</p>
    </div>
    <div class="section-hdr sub">17.3 Intervención terciaria (daño)</div>
    <div class="prose">
      <p>Atención psicológica/médica ocupacional, reincorporación, ajuste de puesto y seguimiento de casos.
      No reemplaza la intervención primaria.</p>
    </div>
    <div class="clinical-prose">{esc(reco)}</div>
    """
    p2 = f"""
    <div class="section-hdr">17. Recomendaciones por dimensión prioritaria</div>
    <ol class="ol-legal">{''.join(lis) or '<li>No se identificaron dimensiones en riesgo alto o muy alto. Mantener monitoreo anual y acciones de promoción.</li>'}</ol>
    <div class="section-hdr sub">Indicadores de seguimiento sugeridos</div>
    <ol class="ol-legal">
      <li>Porcentaje de trabajadores en riesgo alto+muy alto en las tres dimensiones cabeza de lista (meta: descenso en la siguiente medición).</li>
      <li>Resolución del 100% de marcas ambiguas antes de cada sellado.</li>
      <li>Cobertura de la batería vs. planta objeto (≥ de la muestra planificada).</li>
      <li>Ausentismo por causa médica y denuncias al comité de convivencia, leídos como contexto, no como prueba causal única.</li>
    </ol>
    """
    return [("PVE — niveles de intervención", p1), ("PVE — acciones por dimensión", p2)]


def page_anexos_baremos(ctx: Dict[str, Any]) -> List[Page]:
    from ..scoring import (
        BAREMOS_DIM_A,
        BAREMOS_ESTRES_AUX,
        BAREMOS_ESTRES_JEFES,
        BAREMOS_EXTRA_DIM_A,
        BAREMOS_EXTRA_DIM_B,
        BAREMOS_TOTAL_A,
        BAREMOS_TOTAL_B,
        BAREMOS_TOTAL_GENERAL_A,
        BAREMOS_TOTAL_GENERAL_B,
    )

    def cortes_rows(mapa: Mapping[str, tuple]) -> str:
        body = []
        for nom, c in mapa.items():
            body.append(
                f"<tr><td>{esc(nom)}</td><td class='num'>{c[0]}</td><td class='num'>{c[1]}</td>"
                f"<td class='num'>{c[2]}</td><td class='num'>{c[3]}</td><td class='num'>&gt; {c[3]}</td></tr>"
            )
        return "".join(body)

    inner = f"""
    <div class="section-hdr">18. Anexo — cortes de baremos (transparencia metodológica)</div>
    <p class="muted">Los cuatro números son los techos de sin riesgo, bajo, medio y alto. Por encima del cuarto corte: muy alto.</p>
    <div class="section-hdr sub">Totales</div>
    <table class="data-table table-compact">
      <thead><tr><th class="dim-col">Instrumento</th><th>Sin</th><th>Bajo</th><th>Medio</th><th>Alto</th><th>Muy alto</th></tr></thead>
      <tbody>
        <tr><td>Intra total Forma A (T33)</td><td class="num">{BAREMOS_TOTAL_A[0]}</td><td class="num">{BAREMOS_TOTAL_A[1]}</td>
            <td class="num">{BAREMOS_TOTAL_A[2]}</td><td class="num">{BAREMOS_TOTAL_A[3]}</td><td class="num">&gt; {BAREMOS_TOTAL_A[3]}</td></tr>
        <tr><td>Intra total Forma B</td><td class="num">{BAREMOS_TOTAL_B[0]}</td><td class="num">{BAREMOS_TOTAL_B[1]}</td>
            <td class="num">{BAREMOS_TOTAL_B[2]}</td><td class="num">{BAREMOS_TOTAL_B[3]}</td><td class="num">&gt; {BAREMOS_TOTAL_B[3]}</td></tr>
        <tr><td>General A (T34)</td><td class="num">{BAREMOS_TOTAL_GENERAL_A[0]}</td><td class="num">{BAREMOS_TOTAL_GENERAL_A[1]}</td>
            <td class="num">{BAREMOS_TOTAL_GENERAL_A[2]}</td><td class="num">{BAREMOS_TOTAL_GENERAL_A[3]}</td><td class="num">&gt; {BAREMOS_TOTAL_GENERAL_A[3]}</td></tr>
        <tr><td>General B (T34)</td><td class="num">{BAREMOS_TOTAL_GENERAL_B[0]}</td><td class="num">{BAREMOS_TOTAL_GENERAL_B[1]}</td>
            <td class="num">{BAREMOS_TOTAL_GENERAL_B[2]}</td><td class="num">{BAREMOS_TOTAL_GENERAL_B[3]}</td><td class="num">&gt; {BAREMOS_TOTAL_GENERAL_B[3]}</td></tr>
        <tr><td>Estrés jefes</td><td class="num">{BAREMOS_ESTRES_JEFES[0]}</td><td class="num">{BAREMOS_ESTRES_JEFES[1]}</td>
            <td class="num">{BAREMOS_ESTRES_JEFES[2]}</td><td class="num">{BAREMOS_ESTRES_JEFES[3]}</td><td class="num">&gt; {BAREMOS_ESTRES_JEFES[3]}</td></tr>
        <tr><td>Estrés auxiliares</td><td class="num">{BAREMOS_ESTRES_AUX[0]}</td><td class="num">{BAREMOS_ESTRES_AUX[1]}</td>
            <td class="num">{BAREMOS_ESTRES_AUX[2]}</td><td class="num">{BAREMOS_ESTRES_AUX[3]}</td><td class="num">&gt; {BAREMOS_ESTRES_AUX[3]}</td></tr>
      </tbody>
    </table>
    <div class="section-hdr sub">Dimensiones extra Forma A (Tabla 17)</div>
    <table class="data-table table-compact">
      <thead><tr><th class="dim-col">Dimensión</th><th>Sin</th><th>Bajo</th><th>Medio</th><th>Alto</th><th>Muy alto</th></tr></thead>
      <tbody>{cortes_rows(BAREMOS_EXTRA_DIM_A)}</tbody>
    </table>
    <p class="muted">Forma B (Tabla 18) aplica cortes propios en comunicación, situación económica, vivienda e influencia.
    Dimensiones intra Forma A (extracto): liderazgo {BAREMOS_DIM_A.get("Características del liderazgo")}.</p>
    """
    return [("Anexo de baremos oficiales", inner)]


def page_firmas(ctx: Dict[str, Any]) -> List[Page]:
    e, m, p = ctx["empresa"], ctx["medicion"], ctx["psicologa"]
    inner = f"""
    <div class="section-hdr">19. Firmas y certificado de custodia (20 años)</div>
    <div class="prose">
      <p>El dictamen queda firmado por la psicóloga especialista en SST responsable de la medición.
      El representante del SG-SST de la empresa acusa recibo del informe organizacional, no de las matrices individuales.</p>
    </div>
    <div class="signatures-grid">
      <div class="sig-box">
        <strong>{esc(p.get("nombre_completo") or p.get("nombre") or "Psicóloga especialista SST")}</strong>
        Psicóloga especialista en Seguridad y Salud en el Trabajo<br>
        T.P. No. {esc(p.get("tarjeta_profesional") or "s.d.")} · Colpsic<br>
        Licencia SST No. {esc(p.get("licencia_sst") or p.get("licencia_so") or "s.d.")}
      </div>
      <div class="sig-box">
        <strong>{esc(e.get("contacto_nombre") or "Responsable del SG-SST")}</strong>
        Líder de Seguridad y Salud en el Trabajo / Talento humano<br>
        {esc(e.get("razon_social"))}<br>
        NIT {esc(e.get("nit"))}
      </div>
    </div>
    <div class="custody-certificate">
      <h4>Certificado oficial de custodia y conservación legal (20 años)</h4>
      <p>Conforme al <strong>artículo 2.2.4.6.13 del Decreto 1072 de 2015</strong> y el
      <strong>artículo 14 de la Resolución 2764 de 2022</strong>, este informe diagnóstico, sus matrices
      psicométricas y las firmas profesionales quedan sellados e inmutabilizados por un término mínimo de veinte (20) años.</p>
      <span class="custody-hash-code">HUELLA SHA-256: {esc(ctx["hash_sha"])}</span>
      <p style="margin-top:6px">Bóveda:
      <code>out/custodia/{esc(e.get("nit") or "empresa")}/{esc(m.get("codigo_campana") or "MED")}_custodia_20y.zip</code></p>
    </div>
    """
    return [("Firmas y custodia de 20 años", inner)]


def assemble_content_pages(ctx: Dict[str, Any]) -> List[Page]:
    """Todas las hojas salvo TOC (el builder lo inserta en la posición 3)."""
    pages: List[Page] = []
    for fn in (
        page_portada,
        page_control,
        page_intro,
        page_objetivos,
        page_marco_legal,
        page_marco_conceptual,
        page_metodologia,
        page_ficha_tecnica,
        page_sociodemografico,
        page_globales,
        page_intra_total,
        page_dominios,
        page_dims_intra,
        page_extra,
        page_estres,
        page_cruces,
        page_priorizacion,
        page_conclusiones,
        page_pve,
        page_anexos_baremos,
        page_firmas,
    ):
        pages.extend(fn(ctx))
    return pages
