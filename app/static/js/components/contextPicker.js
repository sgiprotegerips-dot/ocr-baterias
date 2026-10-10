/**
 * Selector obligatorio Empresa → Campaña.
 * Las etiquetas y la digitalización quedan aisladas por medición; no se mezclan.
 */

import { svgIcon } from "../icons.js";
import { openWizardAbrirCampana } from "./wizardAbrirCampana.js";

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

export function renderContextPicker(container, state, callbacks = {}) {
  if (!container) return;

  const { empresas = [], mediciones = [], activeEmpresaId, activeMedicionId, currentUser } = state;
  const empresa = empresas.find((e) => e.id === activeEmpresaId) || null;
  const meds = activeEmpresaId
    ? mediciones.filter((m) => !m.empresa_id || m.empresa_id === activeEmpresaId)
    : [];
  const medicion = meds.find((m) => m.id === activeMedicionId) || null;
  const ready = Boolean(empresa && medicion);
  const canOpen = currentUser && (currentUser.rol === "admin" || currentUser.rol === "psicologa");

  container.innerHTML = `
    <section class="ctx-picker ${ready ? "is-ready" : "is-pending"}">
      <div class="ctx-picker-grid">
        <label class="ctx-field">
          <span>${svgIcon("building-2", 13)} Empresa cliente</span>
          <select id="ctx-empresa" ${empresas.length ? "" : "disabled"}>
            <option value="">Seleccione la empresa…</option>
            ${empresas
              .map(
                (e) =>
                  `<option value="${esc(e.id)}" ${e.id === activeEmpresaId ? "selected" : ""}>${esc(e.razon_social)} · NIT ${esc(e.nit_completo || e.nit)}</option>`
              )
              .join("")}
          </select>
        </label>
        <label class="ctx-field">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span>${svgIcon("target", 13)} Campaña / medición</span>
            ${
              canOpen
                ? `<button type="button" class="btn-action ghost" id="btn-ctx-abrir-campana" style="padding:2px 8px;font-size:11px;cursor:pointer;" title="Abrir nueva campaña para esta empresa">${svgIcon("plus", 11)} <span>Abrir Campaña</span></button>`
                : ""
            }
          </div>
          <select id="ctx-medicion" ${empresa ? "" : "disabled"}>
            <option value="">${empresa ? "Seleccione la campaña…" : "Primero elija empresa"}</option>
            ${meds
              .map(
                (m) =>
                  `<option value="${esc(m.id)}" ${m.id === activeMedicionId ? "selected" : ""}>${esc(m.codigo_campana)} · ${esc(m.sede || "Sede")} · ${esc(m.estado)}</option>`
              )
              .join("")}
          </select>
        </label>
      </div>
      <p class="ctx-status ${ready ? "ok" : "warn"}">
        ${
          ready
            ? `Trabajando en <strong>${esc(empresa.razon_social)}</strong> · campaña <strong>${esc(medicion.codigo_campana)}</strong>. Las etiquetas y los PDF de esta sesión no se mezclan con otras empresas.`
            : "Elija empresa y campaña antes de importar Excel, imprimir etiquetas o subir cuadernillos. Cada nómina QR pertenece a una sola medición."
        }
      </p>
    </section>
  `;

  const selEmp = container.querySelector("#ctx-empresa");
  const selMed = container.querySelector("#ctx-medicion");
  if (selEmp) {
    selEmp.onchange = () => {
      const id = selEmp.value || null;
      if (callbacks.onSelectEmpresa) callbacks.onSelectEmpresa(id);
    };
  }
  if (selMed) {
    selMed.onchange = () => {
      const id = selMed.value || null;
      if (callbacks.onSelectMedicion) callbacks.onSelectMedicion(id);
    };
  }

  const btnAbrir = container.querySelector("#btn-ctx-abrir-campana");
  if (btnAbrir) {
    btnAbrir.onclick = () => {
      openWizardAbrirCampana((med) => {
        if (callbacks.onSelectEmpresa) callbacks.onSelectEmpresa(med.empresa_id);
        if (callbacks.onSelectMedicion) callbacks.onSelectMedicion(med.id);
      });
    };
  }
}

export function hasCampaignContext(state) {
  return Boolean(state?.activeEmpresaId && state?.activeMedicionId);
}
