/**
 * etiquetasView.js - Impresión de QR en etiquetas térmicas 30×20 mm.
 * Importa FICHA DATOS GENERALES o registra 1 a 1 a mano.
 * El sticker se pega solo en la página 1 del cuadernillo.
 */

import {
  createNominaManual,
  deleteNominaRow,
  fetchNomina,
  fetchNominaPrintHtml,
  fetchOneLabelHtml,
  importNominaExcel,
} from "../api.js";
import { svgIcon } from "../icons.js";
import { showToast } from "./toast.js";
import { hasCampaignContext, renderContextPicker } from "./contextPicker.js";

const SEXO_OPTS = ["F", "M"];
const ESTADO_CIVIL_OPTS = [
  "SOLTERO(A)",
  "CASADO(A)",
  "UNION LIBRE",
  "SEPARADO(A)",
  "DIVORCIADO(A)",
  "VIUDO(A)",
];
const ESTUDIOS_OPTS = [
  "NINGUNO",
  "PRIM-INCOMPL",
  "PRIM-COMPL",
  "BACH-INCOMPL",
  "BACH-COMPL",
  "TECN-INCOMPL",
  "TECN-COMPL",
  "PROF-INCOMPL",
  "PROF-COMPL",
  "POSG-INCOMPL",
  "POSG-COMPL",
];
const ESTRATO_OPTS = ["1", "2", "3", "4", "5", "6"];
const VIVIENDA_OPTS = ["PROPIA", "ARRIENDO", "FAMILIAR"];
const TIPO_CARGO_OPTS = [
  "JEFATURA TIENE PERSONAL A CARGO",
  "PROFESIONAL",
  "AUXILIAR",
  "OPERARIO",
];
const TIEMPO_OPTS = ["<1", "1-5", "6-10", ">10"];
const CONTRATO_OPTS = ["T<1", "T>1", "INDEFINIDO", "PRESTACION", "COOPERATIVA", "EST", "APRENDIZAJE"];
const SALARIO_OPTS = ["F", "V", "MIXTO"];

const FORM_FIELDS = [
  { key: "forma", label: "Forma", type: "select", options: ["A", "B"], required: true, group: "Identidad" },
  { key: "cedula", label: "Cédula", required: true, group: "Identidad" },
  { key: "nombre", label: "Nombre completo", required: true, group: "Identidad" },
  { key: "sexo", label: "Sexo", type: "select", options: SEXO_OPTS, group: "Identidad" },
  { key: "fecha_nacimiento", label: "Fecha de nacimiento", type: "date", group: "Identidad" },
  { key: "anio_nacimiento", label: "Año de nacimiento", group: "Identidad" },
  { key: "edad", label: "Edad", group: "Identidad" },
  { key: "estado_civil", label: "Estado civil", type: "select", options: ESTADO_CIVIL_OPTS, group: "Identidad" },
  { key: "nivel_estudios", label: "Nivel de estudios", type: "select", options: ESTUDIOS_OPTS, group: "Identidad" },
  { key: "fecha_aplicacion", label: "Fecha de aplicación", type: "date", group: "Laboral" },
  { key: "cargo", label: "Cargo actual", group: "Laboral" },
  { key: "cargo_ocupacion", label: "Cargo u ocupación", group: "Laboral" },
  { key: "tipo_cargo", label: "Tipo de cargo", type: "select", options: TIPO_CARGO_OPTS, group: "Laboral" },
  { key: "area", label: "Área", group: "Laboral" },
  { key: "tipo_contrato", label: "Tipo de contrato", type: "select", options: CONTRATO_OPTS, group: "Laboral" },
  { key: "horas_diarias", label: "Horas diarias de trabajo", group: "Laboral" },
  { key: "tipo_salario", label: "Tipo de salario", type: "select", options: SALARIO_OPTS, group: "Laboral" },
  { key: "tiempo_empresa", label: "Tiempo en la empresa (años)", type: "select", options: TIEMPO_OPTS, group: "Laboral" },
  { key: "tiempo_cargo", label: "Tiempo en el cargo (años)", type: "select", options: TIEMPO_OPTS, group: "Laboral" },
  { key: "residencia", label: "Residencia actual", group: "Contexto" },
  { key: "departamento", label: "Departamento", group: "Contexto" },
  { key: "estrato", label: "Estrato", type: "select", options: ESTRATO_OPTS, group: "Contexto" },
  { key: "tipo_vivienda", label: "Tipo de vivienda", type: "select", options: VIVIENDA_OPTS, group: "Contexto" },
  { key: "n_dependientes", label: "No. personas que dependen de ud.", group: "Contexto" },
  { key: "lugar_trabajo", label: "Lugar de trabajo actual", group: "Contexto" },
  { key: "dpto_trabajo", label: "Dpto. de trabajo", group: "Contexto" },
];

const TABLE_COLUMNS = [
  { key: "forma", label: "Forma" },
  { key: "fecha_aplicacion", label: "Fecha aplicación" },
  { key: "cedula", label: "Cédula" },
  { key: "nombre", label: "Nombre completo" },
  { key: "sexo", label: "Sexo" },
  { key: "anio_nacimiento", label: "Año nac." },
  { key: "edad", label: "Edad" },
  { key: "estado_civil", label: "Estado civil" },
  { key: "nivel_estudios", label: "Nivel de estudios" },
  { key: "cargo_ocupacion", label: "Cargo u ocupación" },
  { key: "residencia", label: "Resid. actual" },
  { key: "departamento", label: "Departamento" },
  { key: "estrato", label: "Estrato" },
  { key: "tipo_vivienda", label: "Tipo vivienda" },
  { key: "n_dependientes", label: "Personas a cargo" },
  { key: "lugar_trabajo", label: "Lugar de trabajo" },
  { key: "dpto_trabajo", label: "Dpto. trabajo" },
  { key: "tiempo_empresa", label: "Tiempo empresa" },
  { key: "cargo", label: "Cargo actual" },
  { key: "tipo_cargo", label: "Tipo de cargo" },
  { key: "tiempo_cargo", label: "Tiempo cargo" },
  { key: "area", label: "Área" },
  { key: "tipo_contrato", label: "Tipo contrato" },
  { key: "horas_diarias", label: "Horas diarias" },
  { key: "tipo_salario", label: "Tipo salario" },
  { key: "origen", label: "Origen" },
];

function cellValue(t, key) {
  const ficha = t.ficha || {};
  if (key === "forma") return t.forma || ficha.forma || "";
  if (key === "cedula") return t.cedula || "";
  if (key === "nombre") return t.nombre || t.nombre_completo || ficha.nombre || "";
  if (key === "origen") return t.origen === "manual" ? "Manual" : "Excel";
  if (key === "anio_nacimiento") {
    return ficha.anio_nacimiento || t.anio_nacimiento || (ficha.fecha_nacimiento || t.fecha_nacimiento || "").slice(0, 4);
  }
  return ficha[key] || t[key] || "";
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function emptyForm() {
  const data = {};
  FORM_FIELDS.forEach((f) => {
    data[f.key] = f.key === "forma" ? "B" : "";
  });
  return data;
}

async function openPrintHtmlAsync(fetchPromise, labelCount = 0) {
  const countStr = labelCount > 0 ? `${labelCount} etiqueta${labelCount > 1 ? "s" : ""}` : "etiquetas";
  showToast(`Preparando ${countStr} para impresión...`, "info");
  try {
    const html = await fetchPromise;
    
    let iframe = document.getElementById('print-iframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'print-iframe';
      // Hide visually but keep in render tree so print works across all browsers
      iframe.style.position = 'fixed';
      iframe.style.right = '0';
      iframe.style.bottom = '0';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.style.border = '0';
      document.body.appendChild(iframe);
    }
    
    iframe.contentWindow.document.open();
    iframe.contentWindow.document.write(html);
    iframe.contentWindow.document.close();

    // Disparo explícito y confiable para que nunca falle la llamada a print()
    setTimeout(() => {
      try {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (e) {
        console.error("Error al invocar print() en iframe:", e);
      }
    }, 350);
  } catch (err) {
    showToast(err.message, "error");
  }
}

export async function renderEtiquetasView(container, state, callbacks = {}) {
  if (!container) return;

  const { activeMedicionId, activeEmpresaId, empresas, mediciones } = state;
  const currentEmpresa = empresas.find((e) => e.id === activeEmpresaId) || null;
  const currentMedicion = mediciones.find((m) => m.id === activeMedicionId) || null;
  const medicionId = currentMedicion?.id || null;
  const ctxReady = hasCampaignContext({ activeEmpresaId, activeMedicionId: medicionId });

  container.innerHTML = `
    <div class="etq-viewport">
      <header class="operador-header">
        <div class="operador-header-title">
          <div class="operador-badge-row">
            <span class="badge-op-tag">${svgIcon("qr-code", 12)} Etiquetas QR térmicas 30 × 20 mm</span>
            <span class="badge-op-norm">Sticker solo en página 1 · Consentimiento informado</span>
          </div>
          <h2>Nómina y impresión de identificación automática</h2>
          <p class="operador-sub">
            Las etiquetas QR pertenecen a <strong>una empresa y una campaña</strong>. Elíjalas abajo antes de importar o imprimir.
            La plantilla Excel trae los <strong>25 campos oficiales</strong> de la FICHA DATOS GENERALES; todo entra al QR 30×20 mm.
          </p>
        </div>
      </header>

      <div id="etq-ctx-picker"></div>

      <section class="etq-toolbar">
        <a class="btn-action ghost" href="/static/plantillas/importador_etiquetas_qr.xlsx" download="importador_etiquetas_qr.xlsx" title="Excel oficial: 25 columnas de la FICHA DATOS GENERALES">
          ${svgIcon("excel", 14)}
          <span>Plantilla Excel</span>
        </a>
        <label class="btn-action primary-solid etq-import-btn ${ctxReady ? "" : "is-disabled"}">
          ${svgIcon("upload", 14)}
          <span>Importar nómina</span>
          <input type="file" id="etq-excel-input" accept=".xlsx,.xlsm" hidden ${ctxReady ? "" : "disabled"} />
        </label>
        
        <div class="etq-filter-group">
          <button type="button" class="etq-chip is-active" id="etq-chip-all" data-forma="">Todas (<span id="etq-cnt-all">0</span>)</button>
          <button type="button" class="etq-chip" id="etq-chip-a" data-forma="A">Forma A (<span id="etq-cnt-a">0</span>)</button>
          <button type="button" class="etq-chip" id="etq-chip-b" data-forma="B">Forma B (<span id="etq-cnt-b">0</span>)</button>
        </div>

        <div class="etq-search-wrap">
          <input type="text" id="etq-search-input" placeholder="Buscar cédula o nombre..." autocomplete="off" />
        </div>

        <div class="etq-actions-right">
          <button type="button" class="btn-action ghost" id="etq-select-batch50" title="Selecciona hasta 50 trabajadores para imprimir en rollo" ${ctxReady ? "" : "disabled"}>
            ${svgIcon("check-square", 14)}
            <span>Sel. 50</span>
          </button>
          <button type="button" class="btn-action ghost" id="etq-print-selected" disabled>
            ${svgIcon("file-text", 14)}
            <span id="etq-lbl-print-sel">Imprimir seleccionadas</span>
          </button>
          <button type="button" class="btn-action primary-solid" id="etq-print-all" ${ctxReady ? "" : "disabled"}>
            ${svgIcon("layers", 14)}
            <span id="etq-lbl-print-all">Imprimir toda la nómina</span>
          </button>
        </div>
      </section>

      <div class="etq-layout">
        <section class="etq-table-card">
          <div class="qc-header-row">
            <div class="qc-title-wrap">
              ${svgIcon("users", 18)}
              <div>
                <h3>Trabajadores de la campaña</h3>
                <p>Tabla completa de la ficha (desplace a la derecha). Clic en una fila para editar o imprimir. Si no hay Excel, registre a mano a la derecha.</p>
              </div>
            </div>
          </div>
          <div class="admin-table-wrap etq-table-scroll">
            <table class="admin-data-table etq-ficha-table">
              <thead>
                <tr>
                  <th class="etq-sticky-check"><input type="checkbox" id="etq-check-all" /></th>
                  ${TABLE_COLUMNS.map((c) => `<th>${escapeHtml(c.label)}</th>`).join("")}
                </tr>
              </thead>
              <tbody id="etq-tbody">
                <tr><td colspan="${TABLE_COLUMNS.length + 1}" class="text-center">Cargando nómina...</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <aside class="etq-side">
          <div class="etq-preview-card">
            <h3>Vista previa 30 × 20 mm</h3>
            <iframe id="etq-preview" class="etq-preview-frame" title="Vista previa de etiqueta"></iframe>
            <button type="button" class="btn-primary" id="etq-print-one" disabled>
              ${svgIcon("qr-code", 14)}
              <span>Imprimir esta etiqueta</span>
            </button>
          </div>

          <form id="etq-form" class="etq-form-card" autocomplete="off">
            <h3 id="etq-form-title">Registrar a mano e imprimir 1 a 1</h3>
            <p class="etq-form-hint">Todos los campos de la FICHA DATOS GENERALES. Obligatorios: forma, cédula y nombre.</p>
            <div id="etq-form-fields"></div>
            <div class="etq-form-actions">
              <button type="submit" class="btn-primary" id="etq-save">
                ${svgIcon("plus", 14)}
                <span>Guardar e imprimir esta persona</span>
              </button>
              <button type="button" class="btn-action ghost" id="etq-reset">Nueva ficha vacía</button>
            </div>
          </form>
        </aside>
      </div>
    </div>
  `;

  const fieldsRoot = container.querySelector("#etq-form-fields");
  const groups = [...new Set(FORM_FIELDS.map((f) => f.group))];
  fieldsRoot.innerHTML = groups
    .map((group) => {
      const fields = FORM_FIELDS.filter((f) => f.group === group);
      return `
        <fieldset class="etq-fieldset">
          <legend>${escapeHtml(group)}</legend>
          <div class="etq-fields-grid">
            ${fields
              .map((f) => {
                if (f.type === "select") {
                  const optionLabel = (o) => (f.key === "forma" ? `FORMA ${o}` : o);
                  const empty = f.required ? "" : `<option value=""></option>`;
                  return `
                    <label class="etq-field">
                      <span>${escapeHtml(f.label)}${f.required ? " *" : ""}</span>
                      <select name="${f.key}">
                        ${empty}
                        ${f.options.map((o) => `<option value="${o}">${optionLabel(o)}</option>`).join("")}
                      </select>
                    </label>`;
                }
                return `
                  <label class="etq-field">
                    <span>${escapeHtml(f.label)}${f.required ? " *" : ""}</span>
                    <input name="${f.key}" type="${f.type || "text"}" ${f.required ? "required" : ""} />
                  </label>`;
              })
              .join("")}
          </div>
        </fieldset>`;
    })
    .join("");

  renderContextPicker(container.querySelector("#etq-ctx-picker"), state, callbacks);

  const form = container.querySelector("#etq-form");
  const tbody = container.querySelector("#etq-tbody");
  const preview = container.querySelector("#etq-preview");
  const btnPrintOne = container.querySelector("#etq-print-one");
  let currentCedula = null;
  let nomina = [];

  const fillForm = (data) => {
    const src = data || emptyForm();
    FORM_FIELDS.forEach((f) => {
      const el = form.elements[f.key];
      if (!el) return;
      const val = src[f.key] || src.ficha?.[f.key] || (f.key === "forma" ? "B" : "");
      if (el.tagName === "SELECT" && val && ![...el.options].some((o) => o.value === val)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = val;
        el.appendChild(opt);
      }
      el.value = val;
    });
    if (src.nombre_completo && !form.elements.nombre.value) {
      form.elements.nombre.value = src.nombre_completo;
    }
  };

  const readForm = () => {
    const data = {};
    FORM_FIELDS.forEach((f) => {
      data[f.key] = (form.elements[f.key]?.value || "").trim();
    });
    if (data.fecha_nacimiento && !data.anio_nacimiento) {
      data.anio_nacimiento = data.fecha_nacimiento.slice(0, 4);
    }
    return data;
  };

  let activeFormaFilter = "";
  let searchQuery = "";

  const selectedCedulas = () =>
    [...container.querySelectorAll(".etq-row-check:checked")].map((el) => el.value);

  const getFilteredNomina = () => {
    return nomina.filter((t) => {
      const forma = (t.forma || t.ficha?.forma || "").toUpperCase();
      if (activeFormaFilter && forma !== activeFormaFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const ced = (t.cedula || "").toLowerCase();
        const nom = (t.nombre_completo || t.nombre || t.ficha?.nombre || "").toLowerCase();
        const car = (t.cargo || t.ficha?.cargo || "").toLowerCase();
        if (!ced.includes(q) && !nom.includes(q) && !car.includes(q)) return false;
      }
      return true;
    });
  };

  const updateToolbarCounts = () => {
    const total = nomina.length;
    const cntA = nomina.filter((t) => (t.forma || t.ficha?.forma || "").toUpperCase() === "A").length;
    const cntB = nomina.filter((t) => (t.forma || t.ficha?.forma || "").toUpperCase() === "B").length;

    const elAll = container.querySelector("#etq-cnt-all");
    const elA = container.querySelector("#etq-cnt-a");
    const elB = container.querySelector("#etq-cnt-b");
    if (elAll) elAll.textContent = total;
    if (elA) elA.textContent = cntA;
    if (elB) elB.textContent = cntB;

    const lblAll = container.querySelector("#etq-lbl-print-all");
    if (lblAll) {
      if (activeFormaFilter === "A") {
        lblAll.textContent = `Imprimir Forma A (${cntA})`;
      } else if (activeFormaFilter === "B") {
        lblAll.textContent = `Imprimir Forma B (${cntB})`;
      } else {
        lblAll.textContent = `Imprimir toda la nómina (${total})`;
      }
    }
  };

  const updateSelectionState = () => {
    const ceds = selectedCedulas();
    const btnSel = container.querySelector("#etq-print-selected");
    const lblSel = container.querySelector("#etq-lbl-print-sel");
    if (btnSel && lblSel) {
      btnSel.disabled = ceds.length === 0;
      lblSel.textContent = ceds.length > 0 ? `Imprimir seleccionadas (${ceds.length})` : "Imprimir seleccionadas";
    }
  };

  const showPreview = async (cedula) => {
    if (!medicionId || !cedula) return;
    try {
      const html = await fetchOneLabelHtml(medicionId, cedula);
      preview.srcdoc = html.replace(/window\.print\(\);?/g, "");
      currentCedula = cedula;
      btnPrintOne.disabled = false;
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const renderRows = () => {
    updateToolbarCounts();
    const filtered = getFilteredNomina();
    const colCount = TABLE_COLUMNS.length + 1;
    if (!filtered.length) {
      const msg = nomina.length === 0
        ? "Nómina vacía. Importe el Excel o registre a mano la primera persona."
        : "No hay trabajadores que coincidan con el filtro o búsqueda actual.";
      tbody.innerHTML = `<tr><td colspan="${colCount}" class="text-center">${msg}</td></tr>`;
      updateSelectionState();
      return;
    }
    tbody.innerHTML = filtered
      .map((t) => {
        const cells = TABLE_COLUMNS.map((c) => {
          const val = cellValue(t, c.key);
          const shown = c.key === "forma" && val ? `FORMA ${val}` : val || "—";
          const strong = c.key === "nombre" ? `<strong>${escapeHtml(shown)}</strong>` : escapeHtml(shown);
          return `<td>${strong}</td>`;
        }).join("");
        return `
          <tr data-cedula="${escapeHtml(t.cedula)}" class="${currentCedula === t.cedula ? "is-active" : ""}">
            <td class="etq-sticky-check"><input type="checkbox" class="etq-row-check" value="${escapeHtml(t.cedula)}" /></td>
            ${cells}
          </tr>`;
      })
      .join("");
    updateSelectionState();
  };

  const reload = async () => {
    if (!medicionId) {
      tbody.innerHTML = `<tr><td colspan="${TABLE_COLUMNS.length + 1}" class="text-center">Seleccione empresa y campaña. La nómina de etiquetas es exclusiva de esa medición.</td></tr>`;
      return;
    }
    const res = await fetchNomina(medicionId);
    nomina = res.trabajadores || [];
    renderRows();
  };

  fillForm(emptyForm());
  try {
    await reload();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="${TABLE_COLUMNS.length + 1}" class="text-center">${escapeHtml(err.message)}</td></tr>`;
  }

  tbody.addEventListener("click", async (ev) => {
    const tr = ev.target.closest("tr[data-cedula]");
    if (!tr) return;
    if (ev.target.classList.contains("etq-row-check")) {
      updateSelectionState();
      return;
    }
    const ced = tr.dataset.cedula;
    const row = nomina.find((t) => t.cedula === ced);
    if (row) fillForm({ ...row, ...(row.ficha || {}) });
    currentCedula = ced;
    renderRows();
    await showPreview(ced);
  });

  tbody.addEventListener("change", (ev) => {
    if (ev.target.classList.contains("etq-row-check")) {
      updateSelectionState();
    }
  });

  container.querySelectorAll(".etq-chip").forEach((chip) => {
    chip.onclick = () => {
      container.querySelectorAll(".etq-chip").forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      activeFormaFilter = chip.dataset.forma || "";
      renderRows();
    };
  });

  const searchInput = container.querySelector("#etq-search-input");
  if (searchInput) {
    searchInput.oninput = (ev) => {
      searchQuery = ev.target.value.trim();
      renderRows();
    };
  }

  container.querySelector("#etq-check-all").onchange = (ev) => {
    container.querySelectorAll(".etq-row-check").forEach((c) => {
      c.checked = ev.target.checked;
    });
    updateSelectionState();
  };

  const btnBatch50 = container.querySelector("#etq-select-batch50");
  if (btnBatch50) {
    btnBatch50.onclick = () => {
      const checks = [...container.querySelectorAll(".etq-row-check")];
      if (!checks.length) return;
      checks.forEach((c, idx) => {
        c.checked = idx < 50;
      });
      updateSelectionState();
      const count = Math.min(50, checks.length);
      showToast(`${count} trabajadores seleccionados para imprimir rollo.`, "info");
    };
  }

  container.querySelector("#etq-excel-input").onchange = async (ev) => {
    const file = ev.target.files?.[0];
    ev.target.value = "";
    if (!file) return;
    if (!medicionId) {
      showToast("Seleccione empresa y campaña antes de importar. Así las etiquetas no se mezclan.", "error");
      return;
    }
    try {
      const res = await importNominaExcel(medicionId, file);
      showToast(`Importados ${res.imported} trabajadores (${res.created} nuevos).`, "info");
      await reload();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  container.querySelector("#etq-print-all").onclick = () => {
    if (!medicionId) return;
    const cnt = activeFormaFilter === "A"
      ? nomina.filter((t) => (t.forma || t.ficha?.forma || "").toUpperCase() === "A").length
      : activeFormaFilter === "B"
      ? nomina.filter((t) => (t.forma || t.ficha?.forma || "").toUpperCase() === "B").length
      : nomina.length;

    if (cnt === 0) {
      showToast("No hay trabajadores para imprimir.", "error");
      return;
    }

    const desc = activeFormaFilter ? `FORMA ${activeFormaFilter} (${cnt} etiquetas)` : `toda la nómina (${cnt} etiquetas)`;
    if (cnt > 30) {
      if (!confirm(`Se van a preparar ${desc} para la impresora térmica Zebra. ¿Desea continuar?`)) {
        return;
      }
    }
    openPrintHtmlAsync(fetchNominaPrintHtml(medicionId, null, activeFormaFilter || null), cnt).catch(err => {
      showToast(err.message, "error");
    });
  };

  container.querySelector("#etq-print-selected").onclick = () => {
    const ceds = selectedCedulas();
    if (!ceds.length) {
      showToast("Seleccione al menos una fila.", "error");
      return;
    }
    openPrintHtmlAsync(fetchNominaPrintHtml(medicionId, ceds), ceds.length).catch(err => {
      showToast(err.message, "error");
    });
  };

  btnPrintOne.onclick = () => {
    if (!currentCedula || !medicionId) return;
    openPrintHtmlAsync(fetchOneLabelHtml(medicionId, currentCedula)).catch(err => {
      showToast(err.message, "error");
    });
  };

  container.querySelector("#etq-reset").onclick = () => {
    currentCedula = null;
    fillForm(emptyForm());
    btnPrintOne.disabled = true;
    preview.srcdoc = "";
    renderRows();
  };

  form.onsubmit = async (ev) => {
    ev.preventDefault();
    if (!medicionId) {
      showToast("Seleccione una campaña antes de guardar.", "error");
      return;
    }
    const data = readForm();
    if (!data.cedula || !data.nombre) {
      showToast("Cédula y nombre son obligatorios.", "error");
      return;
    }

    try {
      showToast("Guardando persona...", "info");
      const saved = await createNominaManual(medicionId, data);
      showToast(`Guardado ${saved.nombre}. Imprimiendo etiqueta 30×20 mm.`, "info");
      await reload();
      currentCedula = saved.cedula;
      await showPreview(saved.cedula);
      
      const html = await fetchOneLabelHtml(medicionId, saved.cedula);
      
      let iframe = document.getElementById('print-iframe');
      if (!iframe) {
        iframe = document.createElement('iframe');
        iframe.id = 'print-iframe';
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';
        document.body.appendChild(iframe);
      }
      
      iframe.contentWindow.document.open();
      iframe.contentWindow.document.write(html);
      iframe.contentWindow.document.close();
    } catch (err) {
      showToast(err.message, "error");
    }
  };
}
