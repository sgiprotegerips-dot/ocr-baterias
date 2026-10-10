/**
 * adminView.js - Consola de Administración y Gestión Global SST.
 * Vista exclusiva para el rol de Administrador.
 * Telemetría, Empresas, Campañas, Usuarios y Auditoría Forense.
 * Cero emojis. Iconografía SVG técnica pura.
 */

import {
  createAdminUser,
  createEmpresa,
  fetchAdminAuditLogs,
  fetchAdminStats,
  fetchAdminUsers,
  fetchEmpresas,
  fetchMediciones,
  fetchOcrBenchmark,
  fetchOcrEngines,
  updateAdminUser,
  updateMedicionEstado,
} from "../api.js";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";
import { openWizardAltaCliente } from "./wizardAltaCliente.js";
import { openWizardAbrirCampana } from "./wizardAbrirCampana.js";

const ROLE_LABELS = {
  admin: "Administrador SST",
  psicologa: "Psicóloga Especialista SST",
  operador: "Operador Digitalizador",
  cliente_empresa: "Cliente Empresa (Gestor SST)",
};

export async function renderAdminView(container, onNavigate) {
  if (!container) return;

  container.innerHTML = `
    <div class="admin-loading">
      ${svgIcon("flask-conical", 28)}
      <p>Cargando consola de administración y telemetría...</p>
    </div>
  `;

  try {
    const stats = await fetchAdminStats();
    buildAdminDOM(container, stats, onNavigate);
  } catch (err) {
    container.innerHTML = `
      <div class="admin-error-box">
        ${svgIcon("alert-circle", 32)}
        <h3>Error al cargar la consola de administración</h3>
        <p>${escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

function buildAdminDOM(container, stats, onNavigate) {
  container.innerHTML = `
    <div class="admin-viewport">
      <!-- Encabezado de la Consola -->
      <header class="admin-header">
        <div class="admin-header-title">
          <div class="admin-badge-row">
            <span class="badge-admin-corp">${svgIcon("shield-check", 12)} Consola Global de Administración</span>
            <span class="badge-admin-norm">Auditoría Resoluciones 2646/2008 & 2764/2022</span>
          </div>
          <h2>Panel de Control y Gobierno de Plataforma SST</h2>
          <p class="admin-sub">
            Gestión de empresas evaluadas, asignación de campañas, control de usuarios y registro forense de auditoría.
          </p>
        </div>
      </header>

      <!-- Bento Grid de Métricas Globales -->
      <section class="admin-kpis-grid">
        <div class="admin-kpi-card">
          <div class="admin-kpi-head">
            ${svgIcon("building-2", 15)}
            <span>Empresas Registradas</span>
          </div>
          <div class="admin-kpi-val">${stats.total_empresas || 0}</div>
          <span class="admin-kpi-note">Entidades evaluadas</span>
        </div>

        <div class="admin-kpi-card">
          <div class="admin-kpi-head">
            ${svgIcon("target", 15)}
            <span>Mediciones / Campañas</span>
          </div>
          <div class="admin-kpi-val">${stats.total_mediciones || 0}</div>
          <span class="admin-kpi-note">Baterías abiertas o cerradas</span>
        </div>

        <div class="admin-kpi-card">
          <div class="admin-kpi-head">
            ${svgIcon("list-checks", 15)}
            <span>Cuadernillos Procesados</span>
          </div>
          <div class="admin-kpi-val">${stats.total_cuadernillos || 0}</div>
          <span class="admin-kpi-note">Calificados por OMR</span>
        </div>

        <div class="admin-kpi-card">
          <div class="admin-kpi-head">
            ${svgIcon("lock", 15)}
            <span>Expedientes Sellados</span>
          </div>
          <div class="admin-kpi-val text-ok">${stats.informes_sellados_20_anios || 0}</div>
          <span class="admin-kpi-note">Custodia inmutable 20 años</span>
        </div>

        <div class="admin-kpi-card">
          <div class="admin-kpi-head">
            ${svgIcon("users", 15)}
            <span>Usuarios de Sistema</span>
          </div>
          <div class="admin-kpi-val">${stats.total_usuarios || 0}</div>
          <span class="admin-kpi-note">Roles con acceso RBAC</span>
        </div>
      </section>

      <!-- Navegación de Pestañas de Administración -->
      <nav class="admin-nav-tabs">
        <button type="button" class="admin-tab-btn active" data-tab="telemetria">
          ${svgIcon("cpu", 15)}
          <span>Telemetría y Motores OCR</span>
        </button>
        <button type="button" class="admin-tab-btn" data-tab="empresas">
          ${svgIcon("building-2", 15)}
          <span>Empresas Clientes</span>
        </button>
        <button type="button" class="admin-tab-btn" data-tab="mediciones">
          ${svgIcon("target", 15)}
          <span>Mediciones y Campañas</span>
        </button>
        <button type="button" class="admin-tab-btn" data-tab="usuarios">
          ${svgIcon("users", 15)}
          <span>Usuarios y Credenciales</span>
        </button>
        <button type="button" class="admin-tab-btn" data-tab="auditoria">
          ${svgIcon("shield-check", 15)}
          <span>Registro de Auditoría (Logs)</span>
        </button>
      </nav>

      <!-- Contenedor Dinámico de Pestañas -->
      <div class="admin-tab-content" id="admin-tab-container"></div>
    </div>
  `;

  // Control de cambio de pestañas
  const tabButtons = container.querySelectorAll(".admin-tab-btn");
  const tabContainer = container.querySelector("#admin-tab-container");

  const activateTab = (tabName) => {
    tabButtons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tabName));
    if (tabName === "telemetria") renderTabTelemetria(tabContainer, stats);
    else if (tabName === "empresas") renderTabEmpresas(tabContainer);
    else if (tabName === "mediciones") renderTabMediciones(tabContainer);
    else if (tabName === "usuarios") renderTabUsuarios(tabContainer);
    else if (tabName === "auditoria") renderTabAuditoria(tabContainer);
  };

  tabButtons.forEach((btn) => {
    btn.onclick = () => activateTab(btn.dataset.tab);
  });

  // Cargar pestaña inicial
  activateTab("empresas");
}

async function renderTabTelemetria(container, stats) {
  container.innerHTML = `
    <div class="admin-subpane">
      <div class="pane-header-row">
        <div>
          <h3>Telemetría de Servidor y Motores OCR</h3>
          <p>Detección automática de hardware y rendimiento de extracción de datos manuscritos.</p>
        </div>
        <button type="button" class="btn-action primary-solid" id="btn-run-benchmark">
          ${svgIcon("flask-conical", 14)}
          <span>Ejecutar Benchmark en Vivo</span>
        </button>
      </div>

      <div class="telemetry-grid">
        <div class="telemetry-card">
          <h4>Motor OCR Activo</h4>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Motor Primario:</span>
            <strong class="text-accent">${stats.motores_ocr?.active_engine || "Detectando..."}</strong>
          </div>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Sistema Operativo:</span>
            <span>${stats.motores_ocr?.os || "Desconocido"} (${stats.motores_ocr?.arch || ""})</span>
          </div>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Apple Vision Disponible:</span>
            <span class="status-pill status-pill-${stats.motores_ocr?.apple_vision_available ? "listo" : "faltan_datos"}">
              ${stats.motores_ocr?.apple_vision_available ? "Disponible (Nativo macOS)" : "No disponible"}
            </span>
          </div>
          <div class="telemetry-item-row">
            <span class="telemetry-label">RapidOCR ONNX Disponible:</span>
            <span class="status-pill status-pill-${stats.motores_ocr?.rapid_ocr_available ? "listo" : "faltan_datos"}">
              ${stats.motores_ocr?.rapid_ocr_available ? "Disponible (CPU/Linux)" : "No disponible"}
            </span>
          </div>
        </div>

        <div class="telemetry-card">
          <h4>Capacidad de Cómputo Paralelo</h4>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Núcleos de CPU:</span>
            <strong>${navigator.hardwareConcurrency || "Multi-core"} Cores</strong>
          </div>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Inmunidad a Trasluz:</span>
            <span class="status-pill status-pill-listo">
              <span class="status-dot ok"></span>
              OMR Morfológico Activo
            </span>
          </div>
          <div class="telemetry-item-row">
            <span class="telemetry-label">Reordenamiento ADF:</span>
            <span class="status-pill status-pill-listo">
              <span class="status-dot ok"></span>
              Dúplex Inverso 1..24 Activo
            </span>
          </div>
        </div>
      </div>

      <div id="benchmark-results-box" class="benchmark-box" style="display: none;"></div>
    </div>
  `;

  const btnBenchmark = container.querySelector("#btn-run-benchmark");
  const boxBenchmark = container.querySelector("#benchmark-results-box");
  if (btnBenchmark) {
    btnBenchmark.onclick = async () => {
      btnBenchmark.disabled = true;
      btnBenchmark.innerHTML = `${svgIcon("flask-conical", 14)} <span>Ejecutando prueba OCR...</span>`;
      boxBenchmark.style.display = "block";
      boxBenchmark.innerHTML = `<p class="loading-hint">Procesando muestra estándar y midiendo latencia...</p>`;

      try {
        const res = await fetchOcrBenchmark();
        boxBenchmark.innerHTML = `
          <h4>Resultados del Benchmark en Servidor</h4>
          <div class="bench-metrics-row">
            <div class="bench-metric">
              <span>Motor Evaluado</span>
              <strong>${res.active_engine}</strong>
            </div>
            <div class="bench-metric">
              <span>Tiempo de Ejecución</span>
              <strong class="text-accent">${res.elapsed_ms ? res.elapsed_ms.toFixed(1) + " ms" : "N/A"}</strong>
            </div>
            <div class="bench-metric">
              <span>Caracteres Extraídos</span>
              <strong>${res.extracted_chars || 0} caracteres</strong>
            </div>
          </div>
        `;
        showToast("Benchmark OCR completado con éxito", "success");
      } catch (err) {
        boxBenchmark.innerHTML = `<p class="text-danger">Error: ${escapeHtml(err.message)}</p>`;
        showToast("Error ejecutando benchmark", "error");
      } finally {
        btnBenchmark.disabled = false;
        btnBenchmark.innerHTML = `${svgIcon("flask-conical", 14)} <span>Ejecutar Benchmark en Vivo</span>`;
      }
    };
  }
}

async function renderTabEmpresas(container) {
  container.innerHTML = `<p class="loading-hint">Cargando empresas clientes...</p>`;
  try {
    const empresas = await fetchEmpresas();
    container.innerHTML = `
      <div class="admin-subpane">
        <div class="pane-header-row">
          <div>
            <h3>Directorio de Empresas Evaluadas</h3>
            <p>Empresas base con mediciones psicosociales vigentes o históricas.</p>
          </div>
          <button type="button" class="btn-primary" id="btn-alta-cliente">
            ${svgIcon("plus", 14)}
            <span>Dar de alta cliente</span>
          </button>
        </div>

        <div class="admin-table-wrap">
          <table class="admin-data-table">
            <thead>
              <tr>
                <th>Razón Social</th>
                <th>NIT</th>
                <th>Ciudad</th>
                <th>Sector Económico</th>
                <th>Contacto SST</th>
                <th>Psicóloga</th>
                <th>Campañas</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              ${
                empresas.length
                  ? empresas
                      .map(
                        (e) => `
                    <tr>
                      <td><strong>${escapeHtml(e.razon_social)}</strong></td>
                      <td><code>${escapeHtml(e.nit_completo || e.nit)}</code></td>
                      <td>${escapeHtml(e.ciudad || "N/D")}</td>
                      <td>${escapeHtml(e.sector_economico || "General")}</td>
                      <td>
                        <div class="cell-sub">${escapeHtml(e.contacto_nombre || "No asignado")}</div>
                        <small>${escapeHtml(e.contacto_email || "")}</small>
                      </td>
                      <td>${escapeHtml(e.psicologa_responsable_nombre || "—")}</td>
                      <td><span class="badge-number">${e.mediciones_count || 0}</span></td>
                      <td>
                        <span class="status-pill status-pill-listo">
                          <span class="status-dot ok"></span>
                          Activa
                        </span>
                      </td>
                    </tr>
                  `
                      )
                      .join("")
                  : `<tr><td colspan="8" class="text-center">No hay empresas registradas.</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </div>
    `;
    const altaBtn = container.querySelector("#btn-alta-cliente");
    if (altaBtn) {
      altaBtn.onclick = () =>
        openWizardAltaCliente(async () => {
          showToast("Cliente registrado. La psicóloga ya puede abrir la campaña.", "success");
          renderTabEmpresas(container);
        });
    }
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Error cargando empresas: ${escapeHtml(err.message)}</p>`;
  }
}

async function renderTabMediciones(container) {
  container.innerHTML = `<p class="loading-hint">Cargando campañas de medición...</p>`;
  try {
    const res = await fetch("/api/mediciones");
    const mediciones = await res.json();

    container.innerHTML = `
      <div class="admin-subpane">
        <div class="pane-header-row">
          <div>
            <h3>Campañas de Evaluación Psicosocial</h3>
            <p>Mediciones periódicas asociadas a las empresas clientes.</p>
          </div>
          <button type="button" class="btn-primary" id="btn-admin-abrir-campana">
            ${svgIcon("plus", 14)}
            <span>Abrir nueva campaña</span>
          </button>
        </div>

        <div class="admin-table-wrap">
          <table class="admin-data-table">
            <thead>
              <tr>
                <th>Código Campaña</th>
                <th>Empresa Evaluada</th>
                <th>Periodo</th>
                <th>Psicóloga Responsable</th>
                <th>Cuadernillos</th>
                <th>Estado</th>
                <th>Acción Rápida</th>
              </tr>
            </thead>
            <tbody>
              ${
                mediciones.length
                  ? mediciones
                      .map((m) => {
                        const isClosed = m.estado === "cerrada";
                        return `
                    <tr>
                      <td><strong>${escapeHtml(m.codigo_campana)}</strong></td>
                      <td>${escapeHtml(m.empresa_nombre || "Empresa")}</td>
                      <td>${escapeHtml(m.periodo || "Vigente")} (${m.anio})</td>
                      <td>
                        <div class="cell-sub">${escapeHtml(m.psicologa_nombre || "Sin asignar")}</div>
                        <small>Lic. ${escapeHtml(m.psicologa_licencia || "N/A")}</small>
                      </td>
                      <td>${m.trabajadores_leidos || 0} / ${m.trabajadores_esperados || 0}</td>
                      <td>
                        <span class="status-pill status-pill-${isClosed ? "listo" : "doble_marca"}">
                          <span class="status-dot ${isClosed ? "ok" : "warn"}"></span>
                          ${isClosed ? "Cerrada y Sellada" : m.estado === "auditoria" ? "En Auditoría" : "Recolección"}
                        </span>
                      </td>
                      <td>
                        ${
                          !isClosed
                            ? `
                          <button type="button" class="btn-action-sm ghost btn-change-med-state" data-id="${m.id}" data-current="${m.estado}">
                            ${svgIcon("sliders", 12)}
                            <span>Cambiar Estado</span>
                          </button>
                        `
                            : `<span class="badge-lic-sst">Sellada 20 Años</span>`
                        }
                      </td>
                    </tr>
                  `;
                      })
                      .join("")
                  : `<tr><td colspan="7" class="text-center">No hay campañas registradas.</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </div>
    `;

    const btnAbrirCamp = container.querySelector("#btn-admin-abrir-campana");
    if (btnAbrirCamp) {
      btnAbrirCamp.onclick = () => {
        openWizardAbrirCampana(async () => {
          showToast("Campaña abierta exitosamente.", "success");
          renderTabMediciones(container);
        });
      };
    }

    // Handler para cambio de estado
    container.querySelectorAll(".btn-change-med-state").forEach((btn) => {
      btn.onclick = async () => {
        const medId = btn.dataset.id;
        const current = btn.dataset.current;
        const next = current === "recoleccion" ? "auditoria" : current === "auditoria" ? "aprobada" : "auditoria";
        if (confirm(`¿Cambiar estado de la medición a '${next}'?`)) {
          try {
            await updateMedicionEstado(medId, next);
            showToast(`Estado actualizado a ${next}`, "success");
            renderTabMediciones(container);
          } catch (e) {
            showToast(e.message, "error");
          }
        }
      };
    });
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Error cargando mediciones: ${escapeHtml(err.message)}</p>`;
  }
}

async function renderTabUsuarios(container) {
  container.innerHTML = `<p class="loading-hint">Cargando usuarios y credenciales...</p>`;
  try {
    const users = await fetchAdminUsers();
    const empresas = await fetchEmpresas();

    container.innerHTML = `
      <div class="admin-subpane">
        <div class="pane-header-row">
          <div>
            <h3>Usuarios del Sistema y Control de Acceso RBAC</h3>
            <p>Psicólogas especialistas, administradores, operadores y representantes de empresa.</p>
          </div>
          <button type="button" class="btn-action primary-solid" id="btn-nuevo-usuario">
            ${svgIcon("plus", 14)}
            <span>Nuevo Usuario</span>
          </button>
        </div>

        <div class="admin-table-wrap">
          <table class="admin-data-table">
            <thead>
              <tr>
                <th>Nombre Completo</th>
                <th>Correo Electrónico</th>
                <th>Rol Asignado</th>
                <th>Cédula / Licencia SST</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              ${
                users.length
                  ? users
                      .map(
                        (u) => `
                    <tr>
                      <td><strong>${escapeHtml(u.nombre_completo || u.nombre)}</strong></td>
                      <td><code>${escapeHtml(u.email)}</code></td>
                      <td>
                        <span class="role-tag role-tag-${u.rol}">
                          ${ROLE_LABELS[u.rol] || u.rol}
                        </span>
                      </td>
                      <td>
                        <div>CC: ${escapeHtml(u.cedula || "N/A")}</div>
                        ${u.licencia_sst ? `<small class="badge-lic-sst">Lic: ${escapeHtml(u.licencia_sst)}</small>` : ""}
                      </td>
                      <td>
                        <span class="status-pill status-pill-${u.activo ? "listo" : "faltan_datos"}">
                          <span class="status-dot ${u.activo ? "ok" : "alert"}"></span>
                          ${u.activo ? "Activo" : "Inactivo"}
                        </span>
                      </td>
                      <td>
                        <button type="button" class="btn-action-sm ghost btn-edit-user" data-user='${JSON.stringify(u)}'>
                          ${svgIcon("key", 12)}
                          <span>Editar</span>
                        </button>
                      </td>
                    </tr>
                  `
                      )
                      .join("")
                  : `<tr><td colspan="6" class="text-center">No hay usuarios registrados.</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </div>
    `;

    // Handler Nuevo Usuario
    const btnNuevo = container.querySelector("#btn-nuevo-usuario");
    if (btnNuevo) {
      btnNuevo.onclick = () => openUserModal(null, empresas, () => renderTabUsuarios(container));
    }

    // Handler Editar Usuario
    container.querySelectorAll(".btn-edit-user").forEach((btn) => {
      btn.onclick = () => {
        const u = JSON.parse(btn.dataset.user);
        openUserModal(u, empresas, () => renderTabUsuarios(container));
      };
    });
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Error cargando usuarios: ${escapeHtml(err.message)}</p>`;
  }
}

async function renderTabAuditoria(container) {
  container.innerHTML = `<p class="loading-hint">Cargando registros forenses de auditoría...</p>`;
  try {
    const logs = await fetchAdminAuditLogs(100);

    container.innerHTML = `
      <div class="admin-subpane">
        <div class="pane-header-row">
          <div>
            <h3>Registro Forense de Auditoría (Audit Logs)</h3>
            <p>Trazabilidad inmutable de todas las acciones críticas ejecutadas en el sistema.</p>
          </div>
          <span class="compliance-tag">${logs.length} eventos recientes</span>
        </div>

        <div class="admin-table-wrap">
          <table class="admin-data-table">
            <thead>
              <tr>
                <th>Fecha y Hora (UTC)</th>
                <th>Usuario</th>
                <th>Acción Ejecutada</th>
                <th>Entidad Afectada</th>
                <th>Dirección IP</th>
              </tr>
            </thead>
            <tbody>
              ${
                logs.length
                  ? logs
                      .map(
                        (l) => `
                    <tr>
                      <td><code class="text-muted">${escapeHtml(l.timestamp_utc || "Reciente")}</code></td>
                      <td><strong>${escapeHtml(l.usuario_email || "Sistema")}</strong></td>
                      <td>
                        <span class="action-tag action-tag-${l.accion?.toLowerCase()}">
                          ${escapeHtml(l.accion)}
                        </span>
                      </td>
                      <td>${escapeHtml(l.entidad_tipo || "GENERAL")} ${l.entidad_id ? `<small class="text-muted">(${l.entidad_id.slice(0, 8)})</small>` : ""}</td>
                      <td><code>${escapeHtml(l.ip_address || "127.0.0.1")}</code></td>
                    </tr>
                  `
                      )
                      .join("")
                  : `<tr><td colspan="5" class="text-center">No hay registros de auditoría aún.</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Error cargando logs: ${escapeHtml(err.message)}</p>`;
  }
}

function openUserModal(user, empresas, onSuccess) {
  let modal = document.getElementById("admin-user-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "admin-user-modal";
    modal.className = "cmd-palette-backdrop";
    document.body.appendChild(modal);
  }

  const isEdit = Boolean(user);

  modal.innerHTML = `
    <div class="auth-modal-card large-modal">
      <div class="modal-head">
        <div class="modal-title-wrap">
          ${svgIcon("user", 20)}
          <div>
            <h3>${isEdit ? "Actualizar Usuario" : "Registrar Nuevo Usuario"}</h3>
            <p class="modal-sub">Asigne credenciales y privilegios conforme a la Resolución 2764/2022.</p>
          </div>
        </div>
        <button type="button" class="btn-close-modal" id="btn-close-user-modal" aria-label="Cerrar">${svgIcon("x", 16)}</button>
      </div>

      <form id="form-admin-user" class="empresa-form">
        <div class="form-row-2col">
          <label class="form-field">
            <span class="form-label">Nombre Completo <strong class="req">*</strong></span>
            <input name="nombre_completo" required value="${escapeHtml(user?.nombre_completo || user?.nombre || "")}" placeholder="Ej. Dra. Claudia Marcela Valencia" />
          </label>
          <label class="form-field">
            <span class="form-label">Correo Electrónico <strong class="req">*</strong></span>
            <input type="email" name="email" ${isEdit ? "readonly" : "required"} value="${escapeHtml(user?.email || "")}" placeholder="usuario@proteger.com.co" />
          </label>
        </div>

        <div class="form-row-2col">
          <label class="form-field">
            <span class="form-label">Rol en la Plataforma <strong class="req">*</strong></span>
            <select name="rol" id="select-user-rol" required>
              <option value="psicologa" ${user?.rol === "psicologa" ? "selected" : ""}>Psicóloga Especialista SST (Auditoría & Firma)</option>
              <option value="admin" ${user?.rol === "admin" ? "selected" : ""}>Administrador de Sistema (Gestión Global)</option>
              <option value="operador" ${user?.rol === "operador" ? "selected" : ""}>Operador Digitalizador (Carga y Escaneo)</option>
              <option value="cliente_empresa" ${user?.rol === "cliente_empresa" ? "selected" : ""}>Cliente Empresa (Portal Ejecutivo)</option>
            </select>
          </label>
          <label class="form-field">
            <span class="form-label">Cédula de Ciudadanía</span>
            <input name="cedula" value="${escapeHtml(user?.cedula || "")}" placeholder="Ej. 52891402" />
          </label>
        </div>

        <div class="form-row-2col">
          <label class="form-field">
            <span class="form-label">Licencia en Seguridad y Salud en el Trabajo</span>
            <input name="licencia_sst" value="${escapeHtml(user?.licencia_sst || "")}" placeholder="Ej. RES-2024-8912-SST" />
          </label>
          <label class="form-field">
            <span class="form-label">Tarjeta Profesional</span>
            <input name="tarjeta_profesional" value="${escapeHtml(user?.tarjeta_profesional || "")}" placeholder="Ej. PSI-48201" />
          </label>
        </div>

        <div class="form-row-2col" id="row-empresa-cliente" style="${user?.rol === "cliente_empresa" ? "display: flex;" : "display: none;"}">
          <label class="form-field full-width">
            <span class="form-label">Empresa Asociada</span>
            <select name="empresa_id">
              <option value="">Seleccione empresa...</option>
              ${empresas.map((e) => `<option value="${e.id}" ${user?.empresa_id === e.id ? "selected" : ""}>${escapeHtml(e.razon_social)}</option>`).join("")}
            </select>
          </label>
        </div>

        <div class="form-row-2col">
          <label class="form-field">
            <span class="form-label">${isEdit ? "Cambiar Contraseña (opcional)" : "Contraseña de Acceso *"}</span>
            <input type="password" name="password" ${isEdit ? "" : "required"} placeholder="••••••••••••" />
          </label>
          <label class="form-field">
            <span class="form-label">Estado de la Cuenta</span>
            <select name="activo">
              <option value="true" ${user?.activo !== false ? "selected" : ""}>Activo</option>
              <option value="false" ${user?.activo === false ? "selected" : ""}>Inactivo</option>
            </select>
          </label>
        </div>

        <div class="form-actions-row">
          <button type="button" class="btn-action ghost" id="btn-cancel-user">Cancelar</button>
          <button type="submit" class="btn-primary" id="btn-save-user">
            ${svgIcon("check", 15)}
            <span>${isEdit ? "Guardar Cambios" : "Crear Usuario"}</span>
          </button>
        </div>
      </form>
    </div>
  `;

  modal.style.display = "flex";

  const closeModal = () => {
    modal.style.display = "none";
  };

  modal.querySelector("#btn-close-user-modal").onclick = closeModal;
  modal.querySelector("#btn-cancel-user").onclick = closeModal;

  // Toggle campo empresa cliente según rol
  const rolSelect = modal.querySelector("#select-user-rol");
  const empresaRow = modal.querySelector("#row-empresa-cliente");
  if (rolSelect && empresaRow) {
    rolSelect.onchange = () => {
      empresaRow.style.display = rolSelect.value === "cliente_empresa" ? "flex" : "none";
    };
  }

  // Submit
  const form = modal.querySelector("#form-admin-user");
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const data = Object.fromEntries(fd.entries());
    data.activo = data.activo === "true";

    try {
      if (isEdit) {
        await updateAdminUser(user.id, data);
        showToast("Usuario actualizado exitosamente", "success");
      } else {
        await createAdminUser(data);
        showToast("Usuario registrado exitosamente", "success");
      }
      closeModal();
      if (onSuccess) onSuccess();
    } catch (err) {
      showToast(err.message, "error");
    }
  };
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}
