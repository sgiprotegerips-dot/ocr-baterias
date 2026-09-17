/**
 * Asistente de la psicóloga: abrir campaña sobre una empresa ya registrada.
 */

import { abrirCampanaOnboarding, fetchEmpresas, fetchPsicologas } from "../api.js";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

export async function openWizardAbrirCampana(onSuccess) {
  let modal = document.getElementById("wizard-abrir-campana");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "wizard-abrir-campana";
    modal.className = "cmd-palette-backdrop wizard-backdrop";
    document.body.appendChild(modal);
  }

  let empresas = [];
  let psicologas = [];
  try {
    empresas = await fetchEmpresas();
  } catch (e) {
    empresas = [];
  }
  try {
    psicologas = (await fetchPsicologas()).filter((p) => p.rol === "psicologa");
  } catch (e) {
    psicologas = [];
  }

  if (!empresas.length) {
    showToast("No hay empresas registradas. El admin debe dar de alta el cliente primero.", "warning");
    return;
  }

  const year = new Date().getFullYear();
  const data = {
    empresa_id: empresas[0].id,
    anio: year,
    periodo: `Anual ${year}`,
    sede: "Principal",
    trabajadores_esperados: 20,
    psicologa_id: psicologas[0]?.id || "",
  };
  let step = 0;

  const close = () => {
    modal.style.display = "none";
  };

  const render = () => {
    const emp = empresas.find((e) => e.id === data.empresa_id) || empresas[0];
    modal.style.display = "flex";
    modal.innerHTML = `
      <div class="auth-modal-card large-modal wizard-card">
        <div class="modal-head">
          <div class="modal-title-wrap">
            ${svgIcon("target", 20)}
            <div>
              <h3>Abrir nueva campaña</h3>
              <p class="modal-sub">La campaña queda en recolección. El pool de operadores puede cargar cuadernillos.</p>
            </div>
          </div>
          <button type="button" class="btn-close-modal" id="wiz-camp-close" aria-label="Cerrar">${svgIcon("x", 16)}</button>
        </div>
        <ol class="wizard-steps">
          ${["Empresa", "Campaña", "Responsable", "Confirmar"]
            .map(
              (label, i) =>
                `<li class="wizard-step ${i === step ? "active" : ""} ${i < step ? "done" : ""}"><span class="wizard-step-num">${i + 1}</span><span>${label}</span></li>`
            )
            .join("")}
        </ol>
        <form id="wiz-camp-form" class="auth-custom-form">
          ${
            step === 0
              ? `<div class="form-row"><label>Empresa evaluada *</label>
                  <select id="w-emp">${empresas
                    .map(
                      (e) =>
                        `<option value="${e.id}" ${e.id === data.empresa_id ? "selected" : ""}>${esc(e.razon_social)} (NIT ${esc(e.nit)})</option>`
                    )
                    .join("")}</select></div>`
              : ""
          }
          ${
            step === 1
              ? `<div class="form-grid-2col">
                  <div class="form-row"><label>Año *</label><input id="w-anio" type="number" required value="${data.anio}" /></div>
                  <div class="form-row"><label>Periodo *</label><input id="w-periodo" required value="${esc(data.periodo)}" /></div>
                  <div class="form-row"><label>Sede *</label><input id="w-sede" required value="${esc(data.sede)}" /></div>
                  <div class="form-row"><label>Trabajadores esperados</label><input id="w-esp" type="number" min="1" value="${data.trabajadores_esperados}" /></div>
                </div>`
              : ""
          }
          ${
            step === 2
              ? `<div class="form-row"><label>Responsable clínico</label>
                  <select id="w-psico">${psicologas
                    .map(
                      (p) =>
                        `<option value="${p.id}" ${p.id === data.psicologa_id ? "selected" : ""}>${esc(p.nombre_completo)}</option>`
                    )
                    .join("")}</select>
                  <p class="modal-sub">Informativo. Toda psicóloga interna puede auditar la cartera.</p></div>`
              : ""
          }
          ${
            step === 3
              ? `<div class="wizard-confirm">
                  <p><strong>${esc(emp.razon_social)}</strong></p>
                  <p>${esc(data.periodo)} · Sede ${esc(data.sede)} · ${data.trabajadores_esperados} trabajadores esperados</p>
                </div>
                <span id="wiz-camp-error" class="auth-error-hint"></span>`
              : ""
          }
          <div class="form-actions-row modal-footer-row">
            ${step === 0 ? "" : `<button type="button" class="btn-action ghost" id="wiz-camp-back">Anterior</button>`}
            <button type="submit" class="btn-primary">
              ${svgIcon(step === 3 ? "check" : "chevron-right", 16)}
              <span>${step === 3 ? "Abrir campaña" : "Continuar"}</span>
            </button>
          </div>
        </form>
      </div>
    `;
    modal.querySelector("#wiz-camp-close").onclick = close;
    modal.onclick = (e) => {
      if (e.target === modal) close();
    };
    const back = modal.querySelector("#wiz-camp-back");
    if (back) {
      back.onclick = () => {
        collect();
        step -= 1;
        render();
      };
    }
    modal.querySelector("#wiz-camp-form").onsubmit = async (e) => {
      e.preventDefault();
      collect();
      if (step < 3) {
        step += 1;
        render();
        return;
      }
      const errEl = modal.querySelector("#wiz-camp-error");
      try {
        const med = await abrirCampanaOnboarding({
          empresa_id: data.empresa_id,
          anio: Number(data.anio),
          periodo: data.periodo,
          sede: data.sede,
          trabajadores_esperados: Number(data.trabajadores_esperados) || 0,
          psicologa_id: data.psicologa_id || null,
        });
        close();
        showToast(`Campaña ${med.codigo_campana} abierta en recolección.`, "success");
        if (onSuccess) onSuccess(med);
      } catch (err) {
        if (errEl) errEl.textContent = err.message;
      }
    };
  };

  function collect() {
    const val = (id) => modal.querySelector(id)?.value?.trim() || "";
    if (step === 0) data.empresa_id = val("#w-emp") || data.empresa_id;
    if (step === 1) {
      data.anio = Number(val("#w-anio")) || data.anio;
      data.periodo = val("#w-periodo") || data.periodo;
      data.sede = val("#w-sede") || data.sede;
      data.trabajadores_esperados = Number(val("#w-esp")) || 0;
    }
    if (step === 2) data.psicologa_id = val("#w-psico") || data.psicologa_id;
  }

  render();
}
