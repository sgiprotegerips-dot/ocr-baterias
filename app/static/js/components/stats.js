/**
 * stats.js - Tarjetas de métricas y telemetría de lote con arquitectura Bento Grid.
 * Cero emojis. Iconografía vectorial SVG pura y status dots calibrados.
 */

import { svgIcon } from "../icons.js";

export function renderStats(container, stats = {}) {
  const { total = 0, listos = 0, faltan_datos = 0, doble_marca = 0, riesgo_dist = {} } = stats;
  const altoMuyAlto = (riesgo_dist["Riesgo alto"] || 0) + (riesgo_dist["Riesgo muy alto"] || 0);
  const pctListos = total > 0 ? Math.round((listos / total) * 100) : 0;

  container.innerHTML = `
    <div class="stat-card stat-total">
      <div class="stat-card-header">
        <span class="stat-icon-wrap neutral">${svgIcon("layers", 18)}</span>
        <span class="stat-label">Total Baterías</span>
      </div>
      <div class="stat-value-row">
        <span class="stat-num">${total}</span>
      </div>
      <div class="stat-footer">
        <span class="stat-sub">Cuadernillos cargados</span>
      </div>
    </div>

    <div class="stat-card stat-ok">
      <div class="stat-card-header">
        <span class="stat-icon-wrap ok">${svgIcon("check-circle", 18)}</span>
        <span class="stat-label">Listos para Informe</span>
      </div>
      <div class="stat-value-row">
        <span class="stat-num">${listos}</span>
        <span class="stat-meter-badge ok">${pctListos}%</span>
      </div>
      <div class="stat-footer">
        <span class="status-indicator-inline">
          <span class="status-dot ok"></span>
          <span class="stat-sub">100% validados sin errores</span>
        </span>
      </div>
    </div>

    <div class="stat-card stat-alert">
      <div class="stat-card-header">
        <span class="stat-icon-wrap alert">${svgIcon("alert-triangle", 18)}</span>
        <span class="stat-label">Doble Chuleado</span>
      </div>
      <div class="stat-value-row">
        <span class="stat-num">${doble_marca}</span>
        ${doble_marca > 0 ? `<span class="stat-meter-badge alert">Acción</span>` : ""}
      </div>
      <div class="stat-footer">
        <span class="status-indicator-inline">
          <span class="status-dot alert ${doble_marca > 0 ? "pulse" : ""}"></span>
          <span class="stat-sub">Decisión manual psicóloga</span>
        </span>
      </div>
    </div>

    <div class="stat-card stat-warn">
      <div class="stat-card-header">
        <span class="stat-icon-wrap warn">${svgIcon("alert-circle", 18)}</span>
        <span class="stat-label">Faltan Datos</span>
      </div>
      <div class="stat-value-row">
        <span class="stat-num">${faltan_datos}</span>
      </div>
      <div class="stat-footer">
        <span class="status-indicator-inline">
          <span class="status-dot warn"></span>
          <span class="stat-sub">Nombre, cargo o cédula</span>
        </span>
      </div>
    </div>

    <div class="stat-card stat-danger">
      <div class="stat-card-header">
        <span class="stat-icon-wrap danger">${svgIcon("warning", 18)}</span>
        <span class="stat-label">Riesgo Alto / Muy Alto</span>
      </div>
      <div class="stat-value-row">
        <span class="stat-num">${altoMuyAlto}</span>
      </div>
      <div class="stat-footer">
        <span class="status-indicator-inline">
          <span class="status-dot danger"></span>
          <span class="stat-sub">Prioridad de vigilancia SST</span>
        </span>
      </div>
    </div>
  `;
}
