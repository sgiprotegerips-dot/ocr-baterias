/**
 * informeView.js - Vista del Informe Diagnóstico Consolidado y Custodia Legal 20 Años.
 * Conforme a Resolución 2646/2008, 2764/2022 y Decreto 1072/2015 Art. 2.2.4.6.13.
 * Cero emojis. Iconografía vectorial SVG pura y diseño Swiss Modern de alta fidelidad.
 */

import { aprobarSellarInforme, fetchInforme } from "../api.js?v=2.2";
import { svgIcon } from "../icons.js?v=2.2";
import { setState, state } from "../state.js?v=2.2";
import { bindOfficialDocs } from "../downloads.js";


export async function renderInformeView(container, medicionId, onBack) {
  if (!container) return;

  container.innerHTML = `
    <div class="informe-loading">
      ${svgIcon("flask-conical", 28)}
      <p>Consolidando estadísticas psicométricas y baremos normativos oficiales...</p>
    </div>
  `;

  try {
    const data = await fetchInforme(medicionId);
    setState({ activeInforme: data });
    buildInformeDOM(container, data, medicionId, onBack);
  } catch (err) {
    container.innerHTML = `
      <div class="informe-error-box">
        ${svgIcon("alert-triangle", 32)}
        <h3>No se pudo cargar el informe consolidado</h3>
        <p>${err.message}</p>
        <button type="button" class="btn-primary" id="btn-err-back">Volver a Bandeja</button>
      </div>
    `;
    const btn = container.querySelector("#btn-err-back");
    if (btn && onBack) btn.onclick = onBack;
  }
}

function buildInformeDOM(container, data, medicionId, onBack) {
  const { empresa, medicion, psicologa, resumen_sociodemografico, baremos_consolidados, hash_sha256, sellado_inmutable, fecha_emision } = data;

  const isClosed = medicion.estado === "cerrada" || sellado_inmutable;
  const intra = baremos_consolidados.intralaboral || {};
  const extra = baremos_consolidados.extralaboral || {};
  const estres = baremos_consolidados.estres || {};

  container.innerHTML = `
    <div class="informe-container">
      <!-- Barra superior de navegación y acciones -->
      <div class="informe-topbar">
        <button type="button" class="btn-action ghost" id="btn-informe-back">
          ${svgIcon("chevron-left", 16)}
          <span>Volver a Cuadernillos</span>
        </button>

        <div class="informe-top-actions">
          <a href="/api/mediciones/${medicionId}/informe/html" data-open-html class="btn-action ghost" title="Ver informe oficial en pestaña imprimible">
            ${svgIcon("file-text", 15)}
            <span>Documento oficial imprimible (32–40 pág.)</span>
          </a>
          <a href="/api/mediciones/${medicionId}/excel" data-download-file="Baterias_Psicosociales.xlsx" class="btn-action ghost" title="Descargar matriz consolidada de esta medición en formato Excel">
            ${svgIcon("excel", 15)}
            <span>Excel de la Medición</span>
          </a>
        </div>
      </div>

      <!-- Encabezado Clínico Institucional -->
      <header class="informe-header-card">
        <div class="informe-header-left">
          <div class="informe-badge-row">
            <span class="badge-tenant-corp">${svgIcon("building-2", 12)} ${empresa.razon_social}</span>
            <span class="badge-tenant-nit">NIT: ${empresa.nit}</span>
            <span class="badge-status-med ${isClosed ? "closed" : "audit"}">
              ${svgIcon(isClosed ? "lock" : "target", 12)}
              ${isClosed ? "Expediente Sellado (Custodia 20 Años)" : "Fase de Auditoría Clínica"}
            </span>
          </div>
          <h2>Informe Diagnóstico Consolidado de Riesgo Psicosocial</h2>
          <p class="informe-sub">
            Campaña: <strong>${medicion.codigo_campana} · ${medicion.nombre}</strong> · Sede: ${medicion.sede || "Principal"} · Periodo: ${medicion.periodo || "Vigente"}
          </p>
        </div>

        <div class="informe-header-right">
          <div class="psico-credential-card">
            <div class="psico-icon">${svgIcon("award", 22)}</div>
            <div class="psico-meta">
              <span class="psico-title">Psicóloga Especialista Responsable</span>
              <strong>${psicologa.nombre}</strong>
              <span class="psico-lic">Licencia SST: ${psicologa.licencia_so || "Pendiente"}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Bento Grid Resumen Poblacional -->
      <section class="informe-bento-grid">
        <div class="bento-card-kpi">
          <div class="bento-kpi-head">
            ${svgIcon("users", 16)}
            <span>Muestra Total</span>
          </div>
          <div class="bento-kpi-value">${resumen_sociodemografico.total_evaluados}</div>
          <span class="bento-kpi-sub">Cuadernillos procesados</span>
        </div>

        <div class="bento-card-kpi">
          <div class="bento-kpi-head">
            ${svgIcon("file-search", 16)}
            <span>Segmentación de Formas</span>
          </div>
          <div class="bento-kpi-split">
            <div><strong>${resumen_sociodemografico.forma_a_conteo}</strong><span>Forma A (Jefes/Prof.)</span></div>
            <div class="split-divider"></div>
            <div><strong>${resumen_sociodemografico.forma_b_conteo}</strong><span>Forma B (Aux./Oper.)</span></div>
          </div>
        </div>

        <div class="bento-card-kpi">
          <div class="bento-kpi-head">
            ${svgIcon("check-circle", 16)}
            <span>Estado de Auditoría</span>
          </div>
          <div class="bento-kpi-split">
            <div><strong class="text-ok">${resumen_sociodemografico.completos_conteo}</strong><span>Completos</span></div>
            <div class="split-divider"></div>
            <div><strong class="${resumen_sociodemografico.ambiguos_pendientes > 0 ? "text-warn" : "text-ok"}">${resumen_sociodemografico.ambiguos_pendientes}</strong><span>Dobles Pend.</span></div>
          </div>
        </div>
      </section>

      <!-- Distribución General de Riesgo (Intralaboral, Extralaboral, Estrés) -->
      <section class="informe-section">
        <div class="section-title-row">
          ${svgIcon("bar-chart-3", 18)}
          <h3>Niveles Generales de Riesgo Psicosocial</h3>
        </div>

        <div class="risk-cards-grid">
          <!-- Intralaboral General -->
          <div class="risk-card">
            <h4>Cuestionario Intralaboral (General)</h4>
            <div class="risk-bars-stack">
              ${renderRiskBars(intra.general?.distribucion || {})}
            </div>
          </div>

          <!-- Extralaboral General -->
          <div class="risk-card">
            <h4>Cuestionario Extralaboral (General)</h4>
            <div class="risk-bars-stack">
              ${renderRiskBars(extra.general?.distribucion || {})}
            </div>
          </div>

          <!-- Estrés General -->
          <div class="risk-card">
            <h4>Cuestionario de Estrés (General)</h4>
            <div class="risk-bars-stack">
              ${renderRiskBars(estres.distribucion || {})}
            </div>
          </div>
        </div>
      </section>

      <!-- Tabla Detallada de Dominios y Dimensiones Intralaborales -->
      <section class="informe-section">
        <div class="section-title-row">
          ${svgIcon("list-checks", 18)}
          <h3>Desglose Intralaboral por Dominios y Dimensiones (Villalobos)</h3>
        </div>
        <div class="table-responsive-wrap">
          <table class="clinical-table-full">
            <thead>
              <tr>
                <th>Factor / Dimensión Psicosocial</th>
                <th>Sin Riesgo</th>
                <th>Riesgo Bajo</th>
                <th>Riesgo Medio</th>
                <th>Riesgo Alto</th>
                <th>Riesgo Muy Alto</th>
              </tr>
            </thead>
            <tbody>
              ${renderDimensionRows(intra.dimensiones || {})}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Tabla Detallada de Dimensiones Extralaborales -->
      <section class="informe-section">
        <div class="section-title-row">
          ${svgIcon("list-checks", 18)}
          <h3>Desglose Extralaboral por Dimensiones</h3>
        </div>
        <div class="table-responsive-wrap">
          <table class="clinical-table-full">
            <thead>
              <tr>
                <th>Dimensión Extralaboral</th>
                <th>Sin Riesgo</th>
                <th>Riesgo Bajo</th>
                <th>Riesgo Medio</th>
                <th>Riesgo Alto</th>
                <th>Riesgo Muy Alto</th>
              </tr>
            </thead>
            <tbody>
              ${renderDimensionRows(extra.dimensiones || {})}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Conclusiones y Recomendaciones Profesionales -->
      <section class="informe-section">
        <div class="section-title-row">
          ${svgIcon("award", 18)}
          <h3>Concepto Clínico y Recomendaciones SST</h3>
        </div>

        <div class="conclusiones-card">
          <div class="form-row">
            <label for="txt-conclusiones"><strong>Conclusiones Diagnósticas del Especialista:</strong></label>
            <textarea id="txt-conclusiones" rows="4" placeholder="Escriba las conclusiones clínicas según los baremos observados..." ${isClosed ? "readonly" : ""}>${data.conclusiones || "La evaluación realizada sobre la población evaluada muestra los patrones de riesgo especificados en las matrices de Villalobos adjuntas."}</textarea>
          </div>

          <div class="form-row" style="margin-top: 14px;">
            <label for="txt-recomendaciones"><strong>Medidas de Intervención y Recomendaciones:</strong></label>
            <textarea id="txt-recomendaciones" rows="4" placeholder="Escriba las recomendaciones de prevención e intervención de SST..." ${isClosed ? "readonly" : ""}>${data.recomendaciones || "Implementar programa de vigilancia epidemiológica para los factores de riesgo identificados en niveles Alto y Muy Alto."}</textarea>
          </div>
        </div>
      </section>

      <!-- Custodia Legal 20 Años y Sellado Digital -->
      <section class="custodia-seal-section ${isClosed ? "is-sealed" : "pending-seal"}">
        ${
          isClosed
            ? `
          <div class="seal-box sealed">
            <div class="seal-icon-box">${svgIcon("shield-check", 32)}</div>
            <div class="seal-content">
              <span class="seal-title">DICTAMEN PSICOLÓGICO SELLADO Y CUSTODIADO A 20 AÑOS</span>
              <p class="seal-law">Inmutable según Resolución 2764/2022 y Decreto 1072/2015 Artículo 2.2.4.6.13.</p>
              <div class="seal-hashes">
                <div><span>Huella Criptográfica SHA-256:</span> <code>${hash_sha256}</code></div>
                <div><span>Firmado Digitalmente por:</span> <strong>${psicologa.nombre}</strong> (Lic. SST: ${psicologa.licencia_so})</div>
                <div><span>Bóveda Fría de Seguridad:</span> <code>out/custodia/${empresa.nit}/${medicion.codigo_campana}_custodia_20y.zip</code></div>
              </div>
            </div>
            <div class="seal-actions">
              <a href="/api/mediciones/${medicionId}/informe/html" data-open-html class="btn-primary">
                ${svgIcon("file-text", 16)}
                <span>Ver Informe Oficial Firmado</span>
              </a>
            </div>
          </div>
        `
            : `
          <div class="seal-box unsealed">
            <div class="seal-icon-box">${svgIcon("lock", 28)}</div>
            <div class="seal-content">
              <span class="seal-title">Aprobación de Dictamen y Cierre de Medición</span>
              <p class="seal-warning">
                Atención: Al sellar con la Licencia SST de la Psicóloga, la medición pasará a estado <strong>Cerrada</strong>, se generará la huella SHA-256 inmutable y se creará el paquete de custodia legal por 20 años en bóveda protegida.
              </p>
            </div>
            <div class="seal-actions">
              <button type="button" class="btn-seal-primary" id="btn-sellar-medicion">
                ${svgIcon("shield-check", 16)}
                <span>Aprobar y Sellar Dictamen SST</span>
              </button>
            </div>
          </div>
        `
        }
      </section>
    </div>
  `;

  // Listener volver
  const btnBack = container.querySelector("#btn-informe-back");
  if (btnBack && onBack) btnBack.onclick = onBack;

  // Listener sellar medición
  const btnSellar = container.querySelector("#btn-sellar-medicion");
  if (btnSellar) {
    btnSellar.onclick = async () => {
      const user = state.currentUser;
      if (!user || (user.rol !== "psicologa" && user.rol !== "admin")) {
        alert("Atención: Solo la Psicóloga Especialista SST asignada o el Administrador pueden sellar legalmente el informe.");
        return;
      }

      const conf = confirm(
        `¿Confirma el sellado e inmutabilización oficial de la campaña ${medicion.codigo_campana} para la empresa ${empresa.razon_social}?\n\nEsta acción generará la huella SHA-256 y activará la custodia legal de 20 años.`
      );
      if (!conf) return;

      const conclusiones = container.querySelector("#txt-conclusiones")?.value || "";
      const recomendaciones = container.querySelector("#txt-recomendaciones")?.value || "";

      try {
        btnSellar.disabled = true;
        btnSellar.innerHTML = `${svgIcon("flask-conical", 16)} <span>Sellando y Archivando a 20 Años...</span>`;

        await aprobarSellarInforme(medicionId, { conclusiones, recomendaciones });
        alert("Informe diagnóstico sellado con éxito. Se ha generado la huella inmutable SHA-256 y archivado el paquete de custodia legal.");
        renderInformeView(container, medicionId, onBack);
      } catch (err) {
        alert("Error al sellar informe: " + err.message);
        btnSellar.disabled = false;
        btnSellar.innerHTML = `${svgIcon("shield-check", 16)} <span>Aprobar y Sellar Dictamen SST</span>`;
      }
    };
  }

  bindOfficialDocs(container);
}

function renderRiskBars(distribucion) {
  const levels = [
    { key: "Sin riesgo", cls: "risk-none", label: "Sin" },
    { key: "Riesgo bajo", cls: "risk-low", label: "Bajo" },
    { key: "Riesgo medio", cls: "risk-med", label: "Medio" },
    { key: "Riesgo alto", cls: "risk-high", label: "Alto" },
    { key: "Riesgo muy alto", cls: "risk-vhigh", label: "Muy Alto" },
  ];

  return levels
    .map((lvl) => {
      const pct = distribucion[lvl.key] || 0;
      return `
      <div class="risk-bar-row">
        <div class="risk-bar-label"><span>${lvl.label}</span></div>
        <div class="risk-bar-track">
          <div class="risk-bar-fill ${lvl.cls}" style="width: ${pct}%"></div>
        </div>
        <div class="risk-bar-pct"><span>${pct}%</span></div>
      </div>
    `;
    })
    .join("");
}

function renderDimensionRows(dimensiones) {
  const keys = Object.keys(dimensiones);
  if (!keys.length) {
    return `<tr><td colspan="6" class="text-muted text-center">No hay datos procesados para estas dimensiones</td></tr>`;
  }

  return keys
    .map((k) => {
      const item = dimensiones[k] || {};
      const d = item.distribucion || {};
      return `
      <tr>
        <td class="td-dim-name"><strong>${k}</strong></td>
        <td class="td-pct">${d["Sin riesgo"] || 0}%</td>
        <td class="td-pct">${d["Riesgo bajo"] || 0}%</td>
        <td class="td-pct">${d["Riesgo medio"] || 0}%</td>
        <td class="td-pct text-high">${d["Riesgo alto"] || 0}%</td>
        <td class="td-pct text-vhigh"><strong>${d["Riesgo muy alto"] || 0}%</strong></td>
      </tr>
    `;
    })
    .join("");
}
