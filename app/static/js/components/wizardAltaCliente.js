/**
 * Asistente guiado de alta de cliente (rol admin).
 * Pasos: empresa → contacto SST → psicóloga → portal → confirmación.
 */

import { altaClienteOnboarding, fetchPsicologas, updateEmpresa } from "../api.js?v=4.5";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";

const STEPS = [
  { id: "empresa", label: "Empresa" },
  { id: "contacto", label: "Contacto SST" },
  { id: "psico", label: "Psicóloga" },
  { id: "portal", label: "Usuario portal" },
  { id: "confirm", label: "Confirmar" },
];

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

export async function openWizardAltaCliente(onSuccess) {
  let modal = document.getElementById("wizard-alta-cliente");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "wizard-alta-cliente";
    modal.className = "cmd-palette-backdrop wizard-backdrop";
    document.body.appendChild(modal);
  }

  let psicologas = [];
  try {
    psicologas = await fetchPsicologas();
  } catch (e) {
    psicologas = [];
  }

  const data = {
    nit: "",
    razon_social: "",
    sector_economico: "Servicios",
    codigo_ciiu: "",
    ciudad: "",
    direccion: "",
    contacto_nombre: "",
    contacto_email: "",
    contacto_telefono: "",
    psicologa_id: psicologas[0]?.id || "",
    portal_nombre: "",
    portal_email: "",
    portal_password: "",
  };

  let step = 0;

  const close = () => {
    modal.style.display = "none";
  };

  const render = () => {
    modal.style.display = "flex";
    modal.innerHTML = `
      <div class="auth-modal-card large-modal wizard-card">
        <div class="modal-head">
          <div class="modal-title-wrap">
            ${svgIcon("building-2", 20)}
            <div>
              <h3>Dar de alta cliente</h3>
              <p class="modal-sub">Empresa + psicóloga responsable + acceso al portal SST</p>
            </div>
          </div>
          <button type="button" class="btn-close-modal" id="wiz-alta-close" aria-label="Cerrar">${svgIcon("x", 16)}</button>
        </div>
        <ol class="wizard-steps" aria-label="Pasos del alta">
          ${STEPS.map(
            (s, i) => `
            <li class="wizard-step ${i === step ? "active" : ""} ${i < step ? "done" : ""}">
              <span class="wizard-step-num">${i + 1}</span>
              <span>${s.label}</span>
            </li>`
          ).join("")}
        </ol>
        <form id="wiz-alta-form" class="auth-custom-form">${renderStep()}</form>
      </div>
    `;

    modal.querySelector("#wiz-alta-close").onclick = close;
    modal.onclick = (e) => {
      if (e.target === modal) close();
    };
    bindForm();
  };

  function renderStep() {
    if (step === 0) {
      return `
        <div class="form-grid-2col">
          <div class="form-row"><label>Razón social *</label><input id="w-razon" required value="${esc(data.razon_social)}" /></div>
          <div class="form-row"><label>NIT *</label><input id="w-nit" required value="${esc(data.nit)}" placeholder="900.123.456-7" /></div>
          <div class="form-row"><label>Sector</label>
            <select id="w-sector">
              ${["Servicios", "Industrial / Manufactura", "Comercio", "Salud", "Educación", "Financiero", "Transporte", "Construcción"]
                .map((s) => `<option ${s === data.sector_economico ? "selected" : ""}>${s}</option>`)
                .join("")}
            </select>
          </div>
          <div class="form-row"><label>CIIU</label><input id="w-ciiu" value="${esc(data.codigo_ciiu)}" /></div>
          <div class="form-row"><label>Ciudad</label><input id="w-ciudad" value="${esc(data.ciudad)}" /></div>
          <div class="form-row"><label>Dirección</label><input id="w-dir" value="${esc(data.direccion)}" /></div>
        </div>
        ${navBtns(true, false)}`;
    }
    if (step === 1) {
      return `
        <div class="form-grid-2col">
          <div class="form-row"><label>Nombre de contacto SST *</label><input id="w-cnom" required value="${esc(data.contacto_nombre)}" /></div>
          <div class="form-row"><label>Email de contacto *</label><input id="w-cmail" type="email" required value="${esc(data.contacto_email)}" /></div>
          <div class="form-row"><label>Teléfono</label><input id="w-ctel" value="${esc(data.contacto_telefono)}" /></div>
        </div>
        ${navBtns()}`;
    }
    if (step === 2) {
      return `
        <div class="form-row">
          <label>Psicóloga responsable (informativa)</label>
          <select id="w-psico">
            ${psicologas
              .filter((p) => p.rol === "psicologa")
              .map(
                (p) =>
                  `<option value="${p.id}" ${p.id === data.psicologa_id ? "selected" : ""}>${esc(p.nombre_completo)}</option>`
              )
              .join("")}
          </select>
          <p class="modal-sub">No restringe el acceso: cualquier psicóloga de PROTEGER puede operar la cartera.</p>
        </div>
        ${navBtns()}`;
    }
    if (step === 3) {
      return `
        <div class="form-grid-2col">
          <div class="form-row"><label>Nombre del gestor SST *</label><input id="w-pnom" required value="${esc(data.portal_nombre || data.contacto_nombre)}" /></div>
          <div class="form-row"><label>Email de acceso *</label><input id="w-pmail" type="email" required value="${esc(data.portal_email || data.contacto_email)}" /></div>
          <div class="form-row"><label>Contraseña inicial *</label><input id="w-ppass" type="password" required minlength="8" value="${esc(data.portal_password)}" /></div>
        </div>
        ${navBtns()}`;
    }
    return `
      <div class="wizard-confirm">
        <p><strong>${esc(data.razon_social)}</strong> · NIT ${esc(data.nit)}</p>
        <p>Contacto: ${esc(data.contacto_nombre)} · ${esc(data.contacto_email)}</p>
        <p>Portal: ${esc(data.portal_email)}</p>
      </div>
      <span id="wiz-alta-error" class="auth-error-hint"></span>
      ${navBtns(false, true)}`;
  }

  function navBtns(first = false, last = false) {
    return `
      <div class="form-actions-row modal-footer-row">
        ${first ? "" : `<button type="button" class="btn-action ghost" id="wiz-back">Anterior</button>`}
        <button type="submit" class="btn-primary" id="wiz-next">
          ${svgIcon(last ? "check" : "chevron-right", 16)}
          <span>${last ? "Crear cliente" : "Continuar"}</span>
        </button>
      </div>`;
  }

  function collect() {
    const val = (id) => modal.querySelector(id)?.value?.trim() || "";
    if (step === 0) {
      data.razon_social = val("#w-razon");
      data.nit = val("#w-nit");
      data.sector_economico = val("#w-sector");
      data.codigo_ciiu = val("#w-ciiu");
      data.ciudad = val("#w-ciudad");
      data.direccion = val("#w-dir");
    } else if (step === 1) {
      data.contacto_nombre = val("#w-cnom");
      data.contacto_email = val("#w-cmail");
      data.contacto_telefono = val("#w-ctel");
    } else if (step === 2) {
      data.psicologa_id = val("#w-psico");
    } else if (step === 3) {
      data.portal_nombre = val("#w-pnom");
      data.portal_email = val("#w-pmail");
      data.portal_password = val("#w-ppass");
    }
  }

  function bindForm() {
    const form = modal.querySelector("#wiz-alta-form");
    const back = modal.querySelector("#wiz-back");
    if (back) {
      back.onclick = () => {
        collect();
        step -= 1;
        render();
      };
    }
    form.onsubmit = async (e) => {
      e.preventDefault();
      collect();
      if (step < STEPS.length - 1) {
        step += 1;
        render();
        return;
      }
      const errEl = modal.querySelector("#wiz-alta-error");
      try {
        const created = await altaClienteOnboarding({
          empresa: {
            nit: data.nit,
            razon_social: data.razon_social,
            sector_economico: data.sector_economico,
            codigo_ciiu: data.codigo_ciiu,
            ciudad: data.ciudad,
            direccion: data.direccion,
            contacto_nombre: data.contacto_nombre,
            contacto_email: data.contacto_email,
            contacto_telefono: data.contacto_telefono,
          },
          psicologa_id: data.psicologa_id || null,
          portal: {
            nombre_completo: data.portal_nombre,
            email: data.portal_email,
            password: data.portal_password,
          },
        });
        close();
        showToast("Cliente dado de alta. Copie las credenciales del portal.", "success");
        if (onSuccess) onSuccess(created);
      } catch (err) {
        if (errEl) errEl.textContent = err.message;
      }
    };
  }

  render();
}

export async function openEditarClienteModal(empresa, onSuccess) {
  if (!empresa || !empresa.id) return;

  let modal = document.getElementById("modal-editar-cliente");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "modal-editar-cliente";
    modal.className = "cmd-palette-backdrop";
    document.body.appendChild(modal);
  }

  let psicologas = [];
  try {
    psicologas = await fetchPsicologas();
  } catch (e) {
    psicologas = [];
  }

  const baseSectors = [
    "Servicios",
    "Servicios de Salud Ocupacional y SST",
    "Industrial / Manufactura",
    "Comercio",
    "Salud",
    "Educación",
    "Financiero",
    "Transporte",
    "Construcción",
  ];
  const currentSector = empresa.sector_economico || "Servicios";
  if (currentSector && !baseSectors.includes(currentSector)) {
    baseSectors.unshift(currentSector);
  }

  const nitDisplay = empresa.nit_completo || (empresa.digito_verificacion ? `${empresa.nit}-${empresa.digito_verificacion}` : empresa.nit || "");

  modal.innerHTML = `
    <div class="auth-modal-card large-modal" style="max-width: 720px; max-height: 90vh; overflow-y: auto;">
      <div class="modal-head">
        <div class="modal-title-wrap">
          ${svgIcon("building-2", 20)}
          <div>
            <h3>Modificar Datos Totales del Cliente</h3>
            <p class="modal-sub">Actualice identificación tributaria, ubicación, contacto SST, psicóloga y acceso al portal cliente.</p>
          </div>
        </div>
        <button type="button" class="btn-close-modal" id="btn-close-edit-cliente" aria-label="Cerrar">${svgIcon("x", 16)}</button>
      </div>

      <form id="form-edit-cliente" class="empresa-form" autocomplete="off">
        <fieldset class="etq-fieldset" style="margin-bottom: 0.85rem;">
          <legend>1. Datos Tributarios y Ubicación de la Empresa</legend>
          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Razón Social <strong class="req">*</strong></span>
              <input name="razon_social" required value="${esc(empresa.razon_social)}" placeholder="Ej. PROTEGER I.P.S. S.A.S." />
            </label>
            <label class="form-field">
              <span class="form-label">NIT (con Dígito de Verificación) <strong class="req">*</strong></span>
              <input name="nit" required value="${esc(nitDisplay)}" placeholder="Ej. 900548123-4" />
            </label>
          </div>

          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Sector Económico</span>
              <select name="sector_economico">
                ${baseSectors
                  .map((s) => `<option value="${esc(s)}" ${s === currentSector ? "selected" : ""}>${esc(s)}</option>`)
                  .join("")}
              </select>
            </label>
            <label class="form-field">
              <span class="form-label">Código CIIU / Actividad</span>
              <input name="codigo_ciiu" value="${esc(empresa.codigo_ciiu || "")}" placeholder="Ej. 8699" />
            </label>
          </div>

          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Ciudad / Municipio</span>
              <input name="ciudad" value="${esc(empresa.ciudad || "")}" placeholder="Ej. Bogotá D.C." />
            </label>
            <label class="form-field">
              <span class="form-label">Dirección Sede Principal</span>
              <input name="direccion" value="${esc(empresa.direccion || "")}" placeholder="Ej. Carrera 15 # 85-30" />
            </label>
          </div>
        </fieldset>

        <fieldset class="etq-fieldset" style="margin-bottom: 0.85rem;">
          <legend>2. Contacto SST y Asignación Clínica</legend>
          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Nombre de Contacto SST / Representante</span>
              <input name="contacto_nombre" value="${esc(empresa.contacto_nombre || "")}" placeholder="Ej. Ing. Diana Carolina Gómez" />
            </label>
            <label class="form-field">
              <span class="form-label">Correo Electrónico de Contacto SST</span>
              <input type="email" name="contacto_email" value="${esc(empresa.contacto_email || "")}" placeholder="sst@empresa.com" />
            </label>
          </div>

          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Teléfono de Contacto</span>
              <input name="contacto_telefono" value="${esc(empresa.contacto_telefono || "")}" placeholder="Ej. 3102345678" />
            </label>
            <label class="form-field">
              <span class="form-label">Psicóloga Responsable</span>
              <select name="psicologa_responsable_id">
                <option value="">Sin psicóloga específica (Cartera general)</option>
                ${psicologas
                  .map(
                    (p) =>
                      `<option value="${esc(p.id)}" ${p.id === empresa.psicologa_responsable_id ? "selected" : ""}>${esc(p.nombre_completo || p.nombre)} (${esc(p.rol)})</option>`
                  )
                  .join("")}
              </select>
            </label>
          </div>

          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Estado de la Empresa Cliente</span>
              <select name="activo">
                <option value="true" ${empresa.activo !== false ? "selected" : ""}>Activa</option>
                <option value="false" ${empresa.activo === false ? "selected" : ""}>Inactiva</option>
              </select>
            </label>
          </div>
        </fieldset>

        <fieldset class="etq-fieldset" style="margin-bottom: 0.85rem;">
          <legend>3. Credenciales del Portal Ejecutivo del Cliente (Rol Cliente Empresa)</legend>
          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Nombre del Gestor SST (Portal)</span>
              <input name="portal_nombre" value="${esc(empresa.portal_nombre || empresa.contacto_nombre || "")}" placeholder="Nombre del usuario del portal" />
            </label>
            <label class="form-field">
              <span class="form-label">Correo de Acceso al Portal (Login)</span>
              <input type="email" name="portal_email" value="${esc(empresa.portal_email || "")}" placeholder="cliente@empresa.com" />
            </label>
          </div>

          <div class="form-row-2col">
            <label class="form-field">
              <span class="form-label">Nueva Contraseña del Portal (opcional)</span>
              <input type="password" name="portal_password" placeholder="Dejar en blanco para conservar la actual" />
            </label>
            <label class="form-field">
              <span class="form-label">Estado del Usuario Portal</span>
              <select name="portal_activo">
                <option value="true" ${empresa.portal_activo !== false ? "selected" : ""}>Activo</option>
                <option value="false" ${empresa.portal_activo === false ? "selected" : ""}>Inactivo</option>
              </select>
            </label>
          </div>
        </fieldset>

        <span id="edit-cliente-error" class="auth-error-hint"></span>

        <div class="form-actions-row">
          <button type="button" class="btn-action ghost" id="btn-cancel-edit-cliente">Cancelar</button>
          <button type="submit" class="btn-primary" id="btn-save-edit-cliente">
            ${svgIcon("check", 15)}
            <span>Guardar Todos los Cambios</span>
          </button>
        </div>
      </form>
    </div>
  `;

  modal.style.display = "flex";

  const closeModal = () => {
    modal.style.display = "none";
  };

  modal.querySelector("#btn-close-edit-cliente").onclick = closeModal;
  modal.querySelector("#btn-cancel-edit-cliente").onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) closeModal();
  };

  const form = modal.querySelector("#form-edit-cliente");
  const errEl = modal.querySelector("#edit-cliente-error");

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (errEl) errEl.textContent = "";
    const fd = new FormData(form);
    const payload = Object.fromEntries(fd.entries());
    payload.activo = payload.activo === "true";
    payload.portal_activo = payload.portal_activo === "true";

    const btnSave = modal.querySelector("#btn-save-edit-cliente");
    if (btnSave) btnSave.disabled = true;

    try {
      const updated = await updateEmpresa(empresa.id, payload);
      showToast(`Datos del cliente "${updated.razon_social}" actualizados correctamente.`, "success");
      closeModal();
      if (onSuccess) onSuccess(updated);
    } catch (err) {
      if (errEl) errEl.textContent = err.message;
      showToast(err.message, "error");
    } finally {
      if (btnSave) btnSave.disabled = false;
    }
  };
}
