/**
 * Home de campañas para la psicóloga SST (cartera completa).
 */

import { fetchAllMediciones, fetchEmpresas } from "../api.js";
import { svgIcon } from "../icons.js";
import { openWizardAbrirCampana } from "./wizardAbrirCampana.js";

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function estadoLabel(estado) {
  switch (estado) {
    case "recoleccion":
      return "Recolección";
    case "auditoria":
      return "Auditoría";
    case "aprobada":
      return "Aprobada";
    case "cerrada":
      return "Sellada 20 años";
    default:
      return estado || "—";
  }
}

export async function renderHomePsico(container, state, callbacks = {}) {
  if (!container) return;
  container.innerHTML = `
    <div class="home-psico-loading">
      ${svgIcon("target", 28)}
      <p>Cargando cartera de campañas...</p>
    </div>
  `;

  let mediciones = [];
  let empresas = [];
  try {
    [mediciones, empresas] = await Promise.all([fetchAllMediciones(), fetchEmpresas()]);
  } catch (err) {
    container.innerHTML = `<div class="admin-error-box">${svgIcon("alert-circle", 28)}<h3>No se pudo cargar la cartera</h3><p>${esc(err.message)}</p></div>`;
    return;
  }

  const empById = Object.fromEntries(empresas.map((e) => [e.id, e]));

  container.innerHTML = `
    <div class="home-psico">
      <header class="home-psico-head">
        <div>
          <span class="badge-admin-corp">${svgIcon("target", 12)} Cartera clínica</span>
          <h2>Campañas de medición psicosocial</h2>
          <p class="admin-sub">Toda la cartera de PROTEGER. Abra una campaña sobre un cliente ya dado de alta por el administrador.</p>
        </div>
        <button type="button" class="btn-primary" id="btn-abrir-campana" ${empresas.length ? "" : "disabled"}>
          ${svgIcon("plus", 15)}
          <span>Abrir nueva campaña</span>
        </button>
      </header>
      ${
        mediciones.length
          ? `<div class="campanas-grid">
              ${mediciones
                .map((m) => {
                  const emp = empById[m.empresa_id];
                  const leidos = m.trabajadores_leidos || 0;
                  const esp = m.trabajadores_esperados || 0;
                  return `
                <button type="button" class="campana-card" data-medicion="${m.id}" data-empresa="${m.empresa_id}">
                  <div class="campana-card-top">
                    <strong>${esc(m.codigo_campana)}</strong>
                    <span class="status-pill">${esc(estadoLabel(m.estado))}</span>
                  </div>
                  <p class="campana-emp">${esc(emp?.razon_social || m.empresa_nombre || "Empresa")}</p>
                  <p class="campana-meta">${esc(m.sede || "Principal")} · ${esc(m.periodo)} · ${leidos}/${esp} leídos</p>
                </button>`;
                })
                .join("")}
            </div>`
          : `<div class="cliente-empty-card">
              <div class="empty-icon-wrap">${svgIcon("target", 32)}</div>
              <h3>No hay campañas abiertas</h3>
              <p>${empresas.length ? "Abra la primera medición para que el pool de operadores pueda digitalizar." : "Espere a que el administrador dé de alta el primer cliente."}</p>
            </div>`
      }
    </div>
  `;

  const cta = container.querySelector("#btn-abrir-campana");
  if (cta) {
    cta.onclick = () =>
      openWizardAbrirCampana((med) => {
        if (callbacks.onCampanaCreated) callbacks.onCampanaCreated(med);
      });
  }
  container.querySelectorAll(".campana-card").forEach((card) => {
    card.onclick = () => {
      if (callbacks.onOpenCampana) {
        callbacks.onOpenCampana(card.dataset.medicion, card.dataset.empresa);
      }
    };
  });
}
