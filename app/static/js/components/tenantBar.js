/**
 * tenantBar.js - Barra de selección de Empresa cliente y Campaña (Medición SST).
 * Permite a la Psicóloga crear una Empresa Base y sus Mediciones para subir cuadernillos.
 * Cero emojis. Iconos vectoriales SVG puros.
 */

import { createEmpresa, createMedicion, fetchEmpresas, fetchPsicologas } from "../api.js?v=4.5";
import { svgIcon } from "../icons.js?v=2.2";
import { setState, state } from "../state.js?v=2.2";
import { openEditarClienteModal } from "./wizardAltaCliente.js?v=4.5";


export function renderTenantBar(container, currentState, callbacks = {}) {
  if (!container) return;

  const { empresas, activeEmpresaId, mediciones, activeMedicionId, currentUser, activeView } = currentState;

  const currentEmpresa = empresas.find((e) => e.id === activeEmpresaId) || empresas[0];
  const currentMedicion = mediciones.find((m) => m.id === activeMedicionId) || mediciones[0];

  const canManage = currentUser && (currentUser.rol === "psicologa" || currentUser.rol === "admin");
  const isInformeView = activeView === "informe";

  container.innerHTML = `
    <div class="tenant-bar-inner">
      <div class="tenant-selector-group">
        <!-- Selector Empresa -->
        <div class="tenant-field">
          <label class="tenant-label">
            ${svgIcon("building-2", 13)}
            <span>Empresa Evaluada:</span>
          </label>
          <div class="tenant-control-wrap">
            <select id="select-empresa" class="tenant-select" title="Seleccione la empresa para aislar cuadernillos y baremos">
              ${
                empresas.length
                  ? empresas
                      .map(
                        (e) =>
                          `<option value="${e.id}" ${currentEmpresa && currentEmpresa.id === e.id ? "selected" : ""}>${e.razon_social} (NIT ${e.nit})</option>`
                      )
                      .join("")
                  : `<option value="">Sin empresas registradas</option>`
              }
            </select>
            ${
              canManage
                ? `
            <button type="button" class="btn-tenant-action" id="btn-editar-empresa" title="Modificar todos los datos del cliente seleccionado" ${!currentEmpresa ? "disabled" : ""}>
              ${svgIcon("sliders", 13)}
              <span>Modificar Cliente</span>
            </button>
            <button type="button" class="btn-tenant-action" id="btn-nueva-empresa" title="Registrar nueva Empresa Base (Psicóloga SST)">
              ${svgIcon("plus", 13)}
              <span>Nueva Empresa</span>
            </button>
            `
                : ""
            }
          </div>
        </div>

        <!-- Selector Medición (Campaña) -->
        <div class="tenant-field">
          <label class="tenant-label">
            ${svgIcon("target", 13)}
            <span>Campaña / Medición:</span>
          </label>
          <div class="tenant-control-wrap">
            <select id="select-medicion" class="tenant-select" title="Seleccione la campaña de evaluación psicosocial" ${!mediciones.length ? "disabled" : ""}>
              ${
                mediciones.length
                  ? mediciones
                      .map(
                        (m) =>
                          `<option value="${m.id}" ${currentMedicion && currentMedicion.id === m.id ? "selected" : ""}>${m.codigo_campana} · ${m.nombre} [${m.estado === "cerrada" ? "Sellada 20 Años" : "En Auditoría"}]</option>`
                      )
                      .join("")
                  : `<option value="">Sin mediciones activas</option>`
              }
            </select>
            ${
              canManage
                ? `
            <button type="button" class="btn-tenant-action" id="btn-nueva-medicion" title="Crear nueva Campaña de Medición" ${!currentEmpresa ? "disabled" : ""}>
              ${svgIcon("plus", 13)}
              <span>Nueva Medición</span>
            </button>
            `
                : ""
            }
          </div>
        </div>
      </div>

      <!-- Acciones Rápidas -->
      <div class="tenant-actions-group">
        <button type="button" class="btn-action ${isInformeView ? "primary-solid" : "ghost"}" id="btn-toggle-informe" title="Ver consolidado estadístico y dictamen legal de la empresa">
          ${svgIcon(isInformeView ? "layers" : "award", 15)}
          <span>${isInformeView ? "Volver a Vista Principal" : "Informe Diagnóstico SST"}</span>
        </button>
      </div>
    </div>
  `;

  // Listener cambio de empresa
  const selEmpresa = container.querySelector("#select-empresa");
  if (selEmpresa) {
    selEmpresa.onchange = (e) => {
      const empId = e.target.value;
      if (callbacks.onSelectEmpresa) callbacks.onSelectEmpresa(empId);
    };
  }

  // Listener cambio de medición
  const selMedicion = container.querySelector("#select-medicion");
  if (selMedicion) {
    selMedicion.onchange = (e) => {
      const medId = e.target.value;
      if (callbacks.onSelectMedicion) callbacks.onSelectMedicion(medId);
    };
  }

  // Botón Modificar Cliente
  const btnEditarEmpresa = container.querySelector("#btn-editar-empresa");
  if (btnEditarEmpresa) {
    btnEditarEmpresa.onclick = () => {
      if (!currentEmpresa) return;
      openEditarClienteModal(currentEmpresa, async () => {
        const updatedList = await fetchEmpresas();
        setState({ empresas: updatedList });
      });
    };
  }

  // Botón Nueva Empresa
  const btnNuevaEmpresa = container.querySelector("#btn-nueva-empresa");
  if (btnNuevaEmpresa) {
    btnNuevaEmpresa.onclick = () => {
      if (!canManage) {
        alert("Atención: Por disposición de la Resolución 2764/2022, la creación de empresas y apertura de baterías requiere el rol de Psicóloga Especialista con Licencia SST vigente o Administrador.");
        return;
      }
      openNuevaEmpresaModal(callbacks.onEmpresaCreated);
    };
  }

  // Botón Nueva Medición
  const btnNuevaMedicion = container.querySelector("#btn-nueva-medicion");
  if (btnNuevaMedicion) {
    btnNuevaMedicion.onclick = () => {
      if (!canManage) {
        alert("Atención: Por disposición de la Resolución 2764/2022, la apertura de campañas requiere el rol de Psicóloga Especialista SST.");
        return;
      }
      if (!currentEmpresa) {
        alert("Debe seleccionar o registrar una empresa primero.");
        return;
      }
      openNuevaMedicionModal(currentEmpresa, callbacks.onMedicionCreated);
    };
  }

  // Botón Toggle Informe
  const btnToggleInforme = container.querySelector("#btn-toggle-informe");
  if (btnToggleInforme) {
    btnToggleInforme.onclick = () => {
      const nextView = isInformeView ? "workspace" : "informe";
      setState({ activeView: nextView });
      if (callbacks.onToggleView) callbacks.onToggleView(nextView);
    };
  }
}

export function openNuevaEmpresaModal(onSuccess) {
  let modal = document.getElementById("empresa-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "empresa-modal";
    modal.className = "cmd-palette-backdrop";
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="auth-modal-card large-modal">
      <div class="modal-head">
        <div class="modal-title-wrap">
          ${svgIcon("building-2", 20)}
          <div>
            <h3>Registrar Empresa Base para Batería Psicosocial</h3>
            <p class="modal-sub">Estructuración de custodia legal a 20 años · Decreto 1072/2015 Art. 2.2.4.6.13</p>
          </div>
        </div>
        <button type="button" class="btn-close-modal" id="btn-close-empresa-modal" aria-label="Cerrar">
          ${svgIcon("x", 16)}
        </button>
      </div>

      <form id="empresa-form" class="auth-custom-form">
        <div class="form-grid-2col">
          <div class="form-row">
            <label for="emp-razon">Razón Social *:</label>
            <input type="text" id="emp-razon" required placeholder="Ej. ACME COLOMBIA S.A.S." />
          </div>
          <div class="form-row">
            <label for="emp-nit">NIT / Identificación Tributaria *:</label>
            <input type="text" id="emp-nit" required placeholder="Ej. 900.123.456-7" />
          </div>
          <div class="form-row">
            <label for="emp-actividad">Actividad Económica:</label>
            <input type="text" id="emp-actividad" placeholder="Ej. Servicios de Tecnología / Salud" />
          </div>
          <div class="form-row">
            <label for="emp-sector">Sector Económico:</label>
            <select id="emp-sector">
              <option value="Servicios">Servicios</option>
              <option value="Industrial / Manufactura">Industrial / Manufactura</option>
              <option value="Comercio">Comercio</option>
              <option value="Salud">Salud</option>
              <option value="Educación">Educación</option>
              <option value="Financiero">Financiero</option>
              <option value="Transporte">Transporte</option>
              <option value="Construcción">Construcción</option>
            </select>
          </div>
          <div class="form-row">
            <label for="emp-ciudad">Ciudad / Municipio:</label>
            <input type="text" id="emp-ciudad" placeholder="Ej. Bogotá D.C." />
          </div>
          <div class="form-row">
            <label for="emp-direccion">Dirección Sede Principal:</label>
            <input type="text" id="emp-direccion" placeholder="Ej. Calle 100 # 15-20" />
          </div>
          <div class="form-row">
            <label for="emp-rep">Representante Legal:</label>
            <input type="text" id="emp-rep" placeholder="Nombre completo" />
          </div>
          <div class="form-row">
            <label for="emp-email">Email de Contacto SST:</label>
            <input type="email" id="emp-email" placeholder="sst@empresa.com" />
          </div>
        </div>

        <div class="form-actions-row modal-footer-row">
          <span id="emp-error-msg" class="auth-error-hint"></span>
          <button type="submit" class="btn-primary" id="btn-save-empresa">
            ${svgIcon("check", 16)}
            <span>Crear Empresa Base</span>
          </button>
        </div>
      </form>
    </div>
  `;

  modal.style.display = "flex";

  const closeModal = () => {
    modal.style.display = "none";
  };
  modal.querySelector("#btn-close-empresa-modal").onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) closeModal();
  };

  const form = modal.querySelector("#empresa-form");
  const errEl = modal.querySelector("#emp-error-msg");

  form.onsubmit = async (e) => {
    e.preventDefault();
    errEl.textContent = "";

    const payload = {
      razon_social: modal.querySelector("#emp-razon").value.trim(),
      nit: modal.querySelector("#emp-nit").value.trim(),
      actividad_economica: modal.querySelector("#emp-actividad").value.trim() || null,
      sector: modal.querySelector("#emp-sector").value,
      ciudad: modal.querySelector("#emp-ciudad").value.trim() || null,
      direccion: modal.querySelector("#emp-direccion").value.trim() || null,
      representante_legal: modal.querySelector("#emp-rep").value.trim() || null,
      email_contacto: modal.querySelector("#emp-email").value.trim() || null,
    };

    try {
      const nueva = await createEmpresa(payload);
      closeModal();
      if (onSuccess) onSuccess(nueva);
    } catch (err) {
      errEl.textContent = err.message;
    }
  };
}

export async function openNuevaMedicionModal(empresa, onSuccess) {
  let modal = document.getElementById("medicion-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "medicion-modal";
    modal.className = "cmd-palette-backdrop";
    document.body.appendChild(modal);
  }

  let psicologas = [];
  try {
    psicologas = await fetchPsicologas();
  } catch (e) {
    console.warn("No se pudieron listar psicólogas:", e);
  }

  const currentYear = new Date().getFullYear();
  const defaultCode = `MED-${currentYear}-${String(Math.floor(Math.random() * 900) + 100)}`;

  modal.innerHTML = `
    <div class="auth-modal-card">
      <div class="modal-head">
        <div class="modal-title-wrap">
          ${svgIcon("target", 20)}
          <div>
            <h3>Nueva Campaña de Medición Psicosocial</h3>
            <p class="modal-sub">Asociada a: <strong>${empresa.razon_social}</strong> (NIT ${empresa.nit})</p>
          </div>
        </div>
        <button type="button" class="btn-close-modal" id="btn-close-medicion-modal" aria-label="Cerrar">
          ${svgIcon("x", 16)}
        </button>
      </div>

      <form id="medicion-form" class="auth-custom-form">
        <div class="form-row">
          <label for="med-codigo">Código Oficial de Campaña *:</label>
          <input type="text" id="med-codigo" required value="${defaultCode}" />
        </div>
        <div class="form-row">
          <label for="med-nombre">Nombre de la Medición *:</label>
          <input type="text" id="med-nombre" required value="Evaluación Batería de Riesgo Psicosocial ${currentYear}" />
        </div>
        <div class="form-grid-2col">
          <div class="form-row">
            <label for="med-periodo">Periodo:</label>
            <input type="text" id="med-periodo" value="${currentYear}-1" />
          </div>
          <div class="form-row">
            <label for="med-sede">Sede / Ubicación:</label>
            <input type="text" id="med-sede" placeholder="Ej. Principal / Planta" />
          </div>
        </div>
        <div class="form-row">
          <label for="med-psicologa">Psicóloga SST Responsable *:</label>
          <select id="med-psicologa" required>
            ${
              psicologas.length
                ? psicologas
                    .map(
                      (p) =>
                        `<option value="${p.id}">${p.nombre} (Lic. ${p.licencia_so || "SST"})</option>`
                    )
                    .join("")
                : `<option value="">Sin psicólogas registradas</option>`
            }
          </select>
        </div>

        <div class="form-actions-row modal-footer-row">
          <span id="med-error-msg" class="auth-error-hint"></span>
          <button type="submit" class="btn-primary" id="btn-save-medicion">
            ${svgIcon("check", 16)}
            <span>Habilitar Campaña para Carga</span>
          </button>
        </div>
      </form>
    </div>
  `;

  modal.style.display = "flex";

  const closeModal = () => {
    modal.style.display = "none";
  };
  modal.querySelector("#btn-close-medicion-modal").onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) closeModal();
  };

  const form = modal.querySelector("#medicion-form");
  const errEl = modal.querySelector("#med-error-msg");

  form.onsubmit = async (e) => {
    e.preventDefault();
    errEl.textContent = "";

    const payload = {
      codigo_campana: modal.querySelector("#med-codigo").value.trim(),
      nombre: modal.querySelector("#med-nombre").value.trim(),
      periodo: modal.querySelector("#med-periodo").value.trim() || null,
      sede: modal.querySelector("#med-sede").value.trim() || null,
      psicologa_id: modal.querySelector("#med-psicologa").value || null,
    };

    try {
      const nueva = await createMedicion(empresa.id, payload);
      closeModal();
      if (onSuccess) onSuccess(nueva);
    } catch (err) {
      errEl.textContent = err.message;
    }
  };
}
