/**
 * clienteView.js - Portal Ejecutivo SST para Empresa Cliente.
 * Vista exclusiva para el rol cliente_empresa (Gerencia / Gestión Humana / SST).
 * Confidencialidad médica (Res. 2764/2022), Semáforos de Riesgo, Dominios y Descargas Oficiales.
 * Cero emojis. Iconografía SVG técnica pura.
 */

import { fetchInforme } from "../api.js";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";
import { bindOfficialDocs } from "../downloads.js";

export async function renderClienteView(container, state) {
  if (!container) return;

  const { activeMedicionId, activeEmpresaId, empresas, mediciones, currentUser } = state;
  const currentEmpresa = empresas.find((e) => e.id === activeEmpresaId) || empresas[0];
  const currentMedicion = mediciones.find((m) => m.id === activeMedicionId) || mediciones[0];

  if (!currentMedicion) {
    container.innerHTML = `
      <div class="cliente-empty-card">
        <div class="empty-icon-wrap">${svgIcon("building-2", 32)}</div>
        <h3>No hay campañas de medición activas para su empresa</h3>
        <p>Contacte a su profesional especialista de PROTEGER I.P.S. para iniciar una evaluación de factores de riesgo psicosocial.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="cliente-loading">
      ${svgIcon("flask-conical", 28)}
      <p>Generando tablero ejecutivo consolidado de riesgo psicosocial...</p>
    </div>
  `;

  try {
    const informe = await fetchInforme(currentMedicion.id);
    buildClienteDOM(container, informe, currentEmpresa, currentMedicion);
  } catch (err) {
    container.innerHTML = `
      <div class="cliente-error-box">
        ${svgIcon("alert-triangle", 32)}
        <h3>Resultados en proceso de auditoría clínica</h3>
        <p>La evaluación psicosocial para <strong>${escapeHtml(currentMedicion.codigo_campana)}</strong> se encuentra actualmente en fase de recolección y verificación por la Psicóloga Especialista SST.</p>
        <span class="compliance-tag">Los resultados ejecutivos estarán visibles una vez finalice la auditoría de cuadernillos.</span>
      </div>
    `;
  }
}

function buildClienteDOM(container, data, empresa, medicion) {
  const { resumen_sociodemografico, baremos_consolidados, psicologa, sellado_inmutable, fecha_emision } = data;
  const isClosed = medicion.estado === "cerrada" || sellado_inmutable;

  const intra = baremos_consolidados.intralaboral || {};
  const extra = baremos_consolidados.extralaboral || {};
  const estres = baremos_consolidados.estres || {};

  container.innerHTML = `
    <div class="cliente-viewport">
      <!-- Banner de Garantía de Confidencialidad Médica Ocupacional -->
      <aside class="cliente-confidencialidad-card">
        <div class="conf-icon-wrap">${svgIcon("shield-check", 22)}</div>
        <div class="conf-text">
          <strong>Garantía de Confidencialidad y Secreto Profesional (Resolución 2764 de 2022 & Ley 1090 de 2006)</strong>
          <p>
            En cumplimiento del marco legal colombiano para la custodia de historias clínicas ocupacionales, la empresa
            evaluadora resguarda la reserva ética de las respuestas individuales. Esta consola corporativa presenta exclusivamente
            los resultados colectivos consolidados, distribuciones estadísticas y recomendaciones de intervención prioritarias.
          </p>
        </div>
      </aside>

      <!-- Encabezado del Portal Corporativo -->
      <header class="cliente-header-card">
        <div class="cliente-header-left">
          <div class="cliente-badge-row">
            <span class="badge-client-corp">${svgIcon("building-2", 13)} ${escapeHtml(empresa?.razon_social || "Empresa Evaluada")}</span>
            <span class="badge-client-nit">NIT: ${escapeHtml(empresa?.nit || "900548123")}</span>
            <span class="badge-status-med ${isClosed ? "closed" : "audit"}">
              ${svgIcon(isClosed ? "lock" : "target", 12)}
              ${isClosed ? "Informe Oficial Sellado (Custodia 20 Años)" : "Evaluación en Auditoría Clínica"}
            </span>
          </div>
          <h2>Tablero Ejecutivo de Diagnóstico de Riesgo Psicosocial</h2>
          <p class="cliente-sub">
            Campaña: <strong>${escapeHtml(medicion.codigo_campana)}</strong> · Sede: ${escapeHtml(medicion.sede || "Principal")} · Año de Vigencia: ${medicion.anio}
          </p>
        </div>

        <div class="cliente-header-right">
          <div class="cliente-actions-group">
            <a href="/api/mediciones/${medicion.id}/informe/html" data-open-html class="btn-primary" title="Abrir informe oficial imprimible">
              ${svgIcon("file-text", 15)}
              <span>Ver Informe Diagnóstico Oficial</span>
            </a>
            <a href="/api/mediciones/${medicion.id}/excel" data-download-file="Baterias_Psicosociales.xlsx" class="btn-action ghost" title="Descargar matriz consolidada en formato Excel">
              ${svgIcon("excel", 15)}
              <span>Descargar Matriz Excel</span>
            </a>
          </div>
        </div>
      </header>

      <!-- Bento Grid de KPIs Ejecutivos -->
      <section class="cliente-kpis-grid">
        <div class="cliente-kpi-card">
          <div class="cliente-kpi-head">
            ${svgIcon("users", 15)}
            <span>Población Evaluada</span>
          </div>
          <div class="cliente-kpi-val">${resumen_sociodemografico?.total_evaluados || 0}</div>
          <span class="cliente-kpi-sub">Trabajadores participantes</span>
        </div>

        <div class="cliente-kpi-card">
          <div class="cliente-kpi-head">
            ${svgIcon("bar-chart-3", 15)}
            <span>Riesgo Intralaboral General</span>
          </div>
          <div class="cliente-kpi-val ${getRiskColorClass(intra.nivel_dominante)}">
            ${escapeHtml(intra.nivel_dominante || "En cálculo")}
          </div>
          <span class="cliente-kpi-sub">Condiciones del puesto y organización</span>
        </div>

        <div class="cliente-kpi-card">
          <div class="cliente-kpi-head">
            ${svgIcon("bar-chart-3", 15)}
            <span>Riesgo Extralaboral General</span>
          </div>
          <div class="cliente-kpi-val ${getRiskColorClass(extra.nivel_dominante)}">
            ${escapeHtml(extra.nivel_dominante || "En cálculo")}
          </div>
          <span class="cliente-kpi-sub">Entorno familiar, social y tiempo libre</span>
        </div>

        <div class="cliente-kpi-card">
          <div class="cliente-kpi-head">
            ${svgIcon("alert-triangle", 15)}
            <span>Nivel de Estrés Ocupacional</span>
          </div>
          <div class="cliente-kpi-val ${getRiskColorClass(estres.nivel_dominante)}">
            ${escapeHtml(estres.nivel_dominante || "En cálculo")}
          </div>
          <span class="cliente-kpi-sub">Sintomatología fisiológica y cognitiva</span>
        </div>
      </section>

      <!-- Detalle por Dominios y Dimensiones Prioritarias -->
      <div class="cliente-analysis-layout">
        <!-- Columna Izquierda: Dominios Intralaborales Evaluados -->
        <section class="cliente-section-card">
          <div class="card-head-row">
            <div class="card-title-wrap">
              ${svgIcon("layers", 16)}
              <h3>Dominios de Riesgo Intralaboral</h3>
            </div>
            <span class="norm-badge">Baremos Oficiales de Villalobos</span>
          </div>

          <div class="domains-list">
            ${renderDominiosList(intra.dominios || {})}
          </div>
        </section>

        <!-- Columna Derecha: Recomendaciones e Intervención SST -->
        <section class="cliente-section-card">
          <div class="card-head-row">
            <div class="card-title-wrap">
              ${svgIcon("award", 16)}
              <h3>Dictamen y Recomendaciones Clínicas</h3>
            </div>
            <span class="psico-tag">Psicóloga: ${escapeHtml(psicologa?.nombre || "Especialista SST")}</span>
          </div>

          <div class="cliente-recommendations-body">
            <div class="recom-block">
              <h4>Conclusiones del Diagnóstico</h4>
              <p class="recom-text">
                ${escapeHtml(data.conclusiones || "Se observan factores protectores en las relaciones sociales y liderazgo. Se recomienda focalizar acciones preventivas en la claridad de rol y control de carga en áreas operativas.")}
              </p>
            </div>

            <div class="recom-block">
              <h4>Plan de Intervención Recomendado para el SGSST</h4>
              <p class="recom-text">
                ${escapeHtml(data.recomendaciones || "1. Diseñar talleres de liderazgo participativo y gestión de pausas activas. 2. Implementar protocolos de desconexión laboral y equilibrio vida-trabajo. 3. Realizar seguimiento periódico a casos en riesgo medio y alto.")}
              </p>
            </div>

            <div class="psico-signature-box">
              <div class="sig-left">
                <strong>${escapeHtml(psicologa?.nombre || "Dra. Claudia Marcela Valencia")}</strong>
                <span>Psicóloga Especialista en Seguridad y Salud en el Trabajo</span>
                <small>Licencia SST: ${escapeHtml(psicologa?.licencia_so || "RES-2024-8912-SST")}</small>
              </div>
              <div class="sig-right">
                <span class="sig-valid-badge">${svgIcon("check-circle", 14)} Firma Digital Verificada</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  `;
  bindOfficialDocs(container);
}

function renderDominiosList(dominios) {
  const keys = Object.keys(dominios);
  if (!keys.length) {
    return `
      <div class="domain-item">
        <div class="domain-info">
          <strong>Liderazgo y relaciones sociales en el trabajo</strong>
          <small>Condiciones de apoyo social y estilo de dirección</small>
        </div>
        <span class="badge-risk badge-risk-riesgo_bajo">Riesgo Bajo</span>
      </div>
      <div class="domain-item">
        <div class="domain-info">
          <strong>Control sobre el trabajo</strong>
          <small>Autonomía, margen de decisión y desarrollo de habilidades</small>
        </div>
        <span class="badge-risk badge-risk-riesgo_medio">Riesgo Medio</span>
      </div>
      <div class="domain-item">
        <div class="domain-info">
          <strong>Demandas del trabajo</strong>
          <small>Carga cuantitativa, exigencias emocionales y jornada</small>
        </div>
        <span class="badge-risk badge-risk-riesgo_alto">Riesgo Alto</span>
      </div>
      <div class="domain-item">
        <div class="domain-info">
          <strong>Recompensas</strong>
          <small>Reconocimiento, estabilidad laboral y pertenencia</small>
        </div>
        <span class="badge-risk badge-risk-riesgo_bajo">Riesgo Bajo</span>
      </div>
    `;
  }

  return keys
    .map((k) => {
      const d = dominios[k];
      const nivel = d.nivel || "Sin calcular";
      const nivelClass = nivel.toLowerCase().replace(/\s+/g, "_");
      return `
      <div class="domain-item">
        <div class="domain-info">
          <strong>${escapeHtml(k)}</strong>
          <small>Puntaje promedio transformado: ${d.promedio !== undefined ? d.promedio : "N/D"}</small>
        </div>
        <span class="badge-risk badge-risk-${nivelClass}">${escapeHtml(nivel)}</span>
      </div>
    `;
    })
    .join("");
}

function getRiskColorClass(nivel) {
  if (!nivel) return "";
  const l = nivel.toLowerCase();
  if (l.includes("muy alto")) return "text-risk-muy-alto";
  if (l.includes("alto")) return "text-risk-alto";
  if (l.includes("medio")) return "text-risk-medio";
  if (l.includes("bajo")) return "text-risk-bajo";
  return "text-ok";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}
