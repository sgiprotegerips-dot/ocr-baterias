/**
 * operadorView.js - Estación de Digitalización y Control de Calidad de Escaneo.
 * Vista exclusiva para el rol de Operador Digitalizador.
 * Carga masiva de PDFs/ZIPs, monitor SSE y control de calidad OMR/ADF.
 * Cero emojis. Iconografía SVG técnica pura.
 */

import {
  cancelBatch,
  fetchCasos,
  subscribeBatchEvents,
  uploadBatch,
} from "../api.js?v=4.8";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";
import { hasCampaignContext, renderContextPicker } from "./contextPicker.js";

export async function renderOperadorView(container, state, callbacks = {}) {
  if (!container) return;

  const { activeMedicionId, activeEmpresaId, empresas, mediciones } = state;
  const currentEmpresa = empresas.find((e) => e.id === activeEmpresaId) || null;
  const currentMedicion = mediciones.find((m) => m.id === activeMedicionId) || null;
  const ctxReady = hasCampaignContext({ activeEmpresaId, activeMedicionId });

  container.innerHTML = `
    <div class="operador-viewport">
      <!-- Encabezado de la Estación -->
      <header class="operador-header">
        <div class="operador-header-title">
          <div class="operador-badge-row">
            <span class="badge-op-tag">${svgIcon("scan", 12)} Estación de Digitalización y Escaneo Masivo</span>
            <span class="badge-op-norm">Resolución 2764/2022 · ADF Dúplex Inverso 1..24</span>
          </div>
          <h2>Ingesta Masiva y Control de Calidad de Cuadernillos</h2>
          <p class="operador-sub">
            Digitalizador y operador trabajan igual: eligen empresa y campaña, y todo el lote queda en esa medición.
          </p>
        </div>
      </header>

      <div id="op-ctx-picker"></div>

      <!-- Zona de Carga Masiva Droppable -->
      <section class="operador-upload-card" id="op-upload-card">
        <form id="op-upload-form" class="op-drop-zone">
          <div class="op-drop-content">
            <div class="op-icon-circle">
              ${svgIcon("upload", 32)}
            </div>
            <div class="op-drop-text">
              <h3>Arrastre lotes de cuadernillos en PDF o archivo .ZIP sin límite de cantidad</h3>
              <p>
                Los archivos se asignarán a <strong>${currentEmpresa ? escapeHtml(currentEmpresa.razon_social) : "la empresa elegida"}</strong> / campaña <strong>${currentMedicion ? escapeHtml(currentMedicion.codigo_campana) : "(selección pendiente)"}</strong>.
                Transferencia segmentada resistente a cortes de red y procesamiento paralelo multi-hilo con verificación de orientación e inmunidad a trasluz.
              </p>
              <div id="op-selected-summary" style="margin-top: 6px; font-size: 12px; font-weight: 600; color: var(--brand-primary, #2563eb); display: none;"></div>
            </div>
          </div>
          <div class="op-controls-row">
            <input type="file" id="op-file-input" accept="application/pdf,application/zip,.pdf,.zip" multiple />
            <button type="submit" class="btn-primary btn-large" id="btn-op-submit" ${ctxReady ? "" : "disabled"}>
              ${svgIcon("upload", 16)}
              <span>Iniciar Lectura e Ingesta Masiva</span>
            </button>
          </div>
        </form>

        <!-- Contenedor de Progreso SSE en vivo -->
        <div id="op-progress-container" class="op-progress-shelf" style="display: none;"></div>
      </section>

      <!-- Panel de Control de Calidad OMR / ADF -->
      <section class="operador-qc-section">
        <div class="qc-header-row">
          <div class="qc-title-wrap">
            ${svgIcon("list-checks", 18)}
            <div>
              <h3>Control de Calidad de Cuadernillos Escaneados</h3>
              <p>Verificación de completitud de páginas físicas (1..24), código de barras y cédula legible.</p>
            </div>
          </div>
          <button type="button" class="btn-action ghost" id="btn-op-refresh">
            ${svgIcon("refresh-cw", 14)}
            <span>Actualizar Bandeja</span>
          </button>
        </div>

        <div class="admin-table-wrap">
          <table class="admin-data-table">
            <thead>
              <tr>
                <th>Archivo Escaneado</th>
                <th>Cédula / Nombre</th>
                <th>Forma</th>
                <th>Páginas ADF</th>
                <th>Estado Técnico</th>
                <th>Inspección PDF</th>
              </tr>
            </thead>
            <tbody id="op-cases-tbody">
              <tr><td colspan="6" class="text-center">Cargando cuadernillos de la campaña...</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Nota Técnica Deontológica -->
      <aside class="operador-legal-notice">
        <div class="notice-icon">${svgIcon("shield-check", 18)}</div>
        <div class="notice-text">
          <strong>Salvaguarda Deontológica y Separación de Roles (Resolución 2764 de 2022)</strong>
          <p>
            El operador de digitalización se encarga del aseguramiento técnico del escaneo (orientación de hojas, contraste y resolución).
            La resolución de marcas dobles ambiguas y la calificación psicométrica final quedan estrictamente reservadas para la
            Psicóloga Especialista con Licencia en Seguridad y Salud en el Trabajo.
          </p>
        </div>
      </aside>
    </div>
  `;

  renderContextPicker(container.querySelector("#op-ctx-picker"), state, callbacks);

  // Cargar casos de la campaña para control de calidad
  const tbody = container.querySelector("#op-cases-tbody");
  const loadQcCasos = async () => {
    if (!activeMedicionId) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">Seleccione empresa y campaña para ver solo los cuadernillos de esa medición.</td></tr>`;
      return;
    }
    try {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">Cargando cuadernillos...</td></tr>`;
      const res = await fetchCasos({
        medicion_id: activeMedicionId,
        page_size: 50,
      });

      if (!res.casos || !res.casos.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center">No hay cuadernillos cargados en esta medición aún.</td></tr>`;
        return;
      }

      tbody.innerHTML = res.casos
        .map((c) => {
          const idn = c.identidad || {};
          const isListo = c.estado === "listo";
          const isDoble = c.estado === "doble_marca";
          const isFaltan = c.estado === "faltan_datos";
          const pagesCount = (c.paginas || []).length || 24;

          return `
            <tr>
              <td>
                <strong>${escapeHtml(c.archivo)}</strong>
                <div class="cell-sub">ID: ${escapeHtml(c.caso_id?.slice(0, 12) || "")}</div>
              </td>
              <td>
                <div><strong>${escapeHtml(idn.nombre || "No identificado")}</strong></div>
                <small class="text-muted">CC: ${escapeHtml(c.id_documento || idn.id_documento || "Ilegible / Faltante")}</small>
              </td>
              <td><span class="badge-forma-mini">Forma ${c.forma || "A"}</span></td>
              <td>
                <span class="status-pill status-pill-listo">
                  <span class="status-dot ok"></span>
                  ${pagesCount} / 24 págs
                </span>
              </td>
              <td>
                <span class="status-pill status-pill-${c.estado}">
                  <span class="status-dot ${isListo ? "ok" : isDoble ? "alert" : "warn"}"></span>
                  ${isListo ? "Ingesta Correcta" : isDoble ? "Doble Marca (A Psicóloga)" : "Faltan Datos"}
                </span>
              </td>
              <td>
                <a href="/api/casos/${c.caso_id}/pdf-ordenado" target="_blank" class="btn-action-sm ghost" title="Ver PDF reordenado">
                  ${svgIcon("file-search", 13)}
                  <span>Auditar PDF</span>
                </a>
              </td>
            </tr>
          `;
        })
        .join("");
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">Error: ${escapeHtml(e.message)}</td></tr>`;
    }
  };

  await loadQcCasos();

  // Botón Refresh
  const btnRefresh = container.querySelector("#btn-op-refresh");
  if (btnRefresh) btnRefresh.onclick = loadQcCasos;

  // Subida de Archivos con soporte Drag & Drop y progreso de transferencia por bloques
  const formUpload = container.querySelector("#op-upload-form");
  const fileInput = container.querySelector("#op-file-input");
  const progressShelf = container.querySelector("#op-progress-container");
  const btnSubmit = container.querySelector("#btn-op-submit");
  const selectedSummary = container.querySelector("#op-selected-summary");
  let droppedFiles = null;

  const updateSelectedSummary = (fileList) => {
    const arr = Array.from(fileList || []);
    if (!selectedSummary) return;
    if (!arr.length) {
      selectedSummary.style.display = "none";
      selectedSummary.textContent = "";
      return;
    }
    const totalMb = (arr.reduce((acc, f) => acc + (f.size || 0), 0) / (1024 * 1024)).toFixed(1);
    selectedSummary.style.display = "block";
    selectedSummary.textContent = `${arr.length} archivo(s) seleccionado(s) (${totalMb} MB listos para cargar)`;
  };

  if (fileInput) {
    fileInput.onchange = () => {
      droppedFiles = null;
      updateSelectedSummary(fileInput.files);
    };
  }

  if (formUpload) {
    formUpload.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      formUpload.classList.add("drag-active");
    });
    formUpload.addEventListener("dragleave", () => {
      formUpload.classList.remove("drag-active");
    });
    formUpload.addEventListener("drop", (ev) => {
      ev.preventDefault();
      formUpload.classList.remove("drag-active");
      if (ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files.length) {
        droppedFiles = ev.dataTransfer.files;
        try {
          fileInput.files = ev.dataTransfer.files;
        } catch (_e) {}
        updateSelectedSummary(droppedFiles);
      }
    });

    formUpload.onsubmit = async (ev) => {
      ev.preventDefault();
      const files = (droppedFiles && droppedFiles.length) ? droppedFiles : fileInput.files;
      if (!ctxReady || !activeMedicionId) {
        showToast("Seleccione empresa y campaña antes de digitalizar. Los PDF no deben mezclarse.", "error");
        return;
      }
      if (!files || !files.length) {
        showToast("Seleccione al menos un archivo PDF o ZIP para procesar.", "warning");
        return;
      }

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = `${svgIcon("upload", 16)} <span>Subiendo Lote...</span>`;
      progressShelf.style.display = "block";
      progressShelf.innerHTML = `
        <div class="progress-bar-wrap">
          <div class="progress-label-row">
            <span>Subiendo archivos al servidor (0%)...</span>
            <span class="progress-pct">0%</span>
          </div>
          <div class="progress-track"><div class="progress-fill" style="width: 0%;"></div></div>
        </div>
      `;

      try {
        const uploadRes = await uploadBatch(files, activeMedicionId, (upProg) => {
          const upPct = Math.round(upProg.percent || 0);
          progressShelf.innerHTML = `
            <div class="progress-bar-wrap">
              <div class="progress-label-row">
                <span>Subiendo archivos al servidor: ${upProg.filesUploaded} de ${upProg.totalFiles} (${escapeHtml(upProg.currentFileName || "")})</span>
                <span class="progress-pct">${upPct}%</span>
              </div>
              <div class="progress-track"><div class="progress-fill" style="width: ${upPct}%;"></div></div>
            </div>
          `;
        });
        fileInput.value = "";
        droppedFiles = null;
        updateSelectedSummary([]);
        showToast(`Lote iniciado: ${uploadRes.total} cuadernillos en proceso`, "info");

        subscribeBatchEvents(
          uploadRes.job_id,
          (eventData) => {
            const pct = Math.round(eventData.percent || 0);
            progressShelf.innerHTML = `
              <div class="progress-bar-wrap">
                <div class="progress-label-row">
                  <span>Procesando lote: ${eventData.completed || 0} de ${eventData.total || 0} cuadernillos (${eventData.current_file || ""})</span>
                  <span class="progress-pct">${pct}%</span>
                </div>
                <div class="progress-track"><div class="progress-fill" style="width: ${pct}%;"></div></div>
              </div>
            `;
            if (eventData.completed > 0 && eventData.completed % 3 === 0) {
              loadQcCasos();
            }
          },
          () => {
            showToast("Procesamiento de lote finalizado con éxito", "success");
            progressShelf.innerHTML = `
              <div class="progress-complete-msg">
                ${svgIcon("check-circle", 16)}
                <span>Lote procesado exitosamente. Todos los cuadernillos fueron indexados.</span>
              </div>
            `;
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `${svgIcon("upload", 16)} <span>Iniciar Lectura e Ingesta Masiva</span>`;
            loadQcCasos();
          },
          () => {
            showToast("Error o interrupción durante el procesamiento del lote", "error");
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `${svgIcon("upload", 16)} <span>Iniciar Lectura e Ingesta Masiva</span>`;
          }
        );
      } catch (err) {
        showToast("Error iniciando la subida: " + err.message, "error");
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = `${svgIcon("upload", 16)} <span>Iniciar Lectura e Ingesta Masiva</span>`;
      }
    };
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}
