/**
 * caseDetail.js - Workspace del Evaluador: Pestañas de Datos, Doble Chuleado, Visor y Baremos.
 * Cero emojis. Iconografía vectorial SVG pura (Lucide Standard), alto contraste clínico y tipografía técnica.
 */

import { svgIcon } from "../icons.js";

export function renderCaseDetail(container, caso, state, handlers) {
  if (!caso) {
    container.innerHTML = `
      <div class="empty-detail">
        <div class="empty-icon-wrap">${svgIcon("list-checks", 36)}</div>
        <h3>Ningún cuadernillo seleccionado</h3>
        <p>Seleccione un caso en la bandeja lateral para auditar datos demográficos, resolver dobles marcas con trazabilidad o verificar baremos normativos.</p>
      </div>
    `;
    return;
  }

  const { onTabChange, onSaveDatos, onDecideDoble, onDeleteCaso, onPageChange } = handlers;
  const idn = caso.identidad || {};
  const pend = (caso.ambiguos || []).filter((a) => a.decision === null || a.decision === undefined);
  const q = caso.calidad || {};
  const sc = caso.scoring || {};

  const currentTab = state.activeTab || "datos";
  const visorPage = state.visorPage || 1;

  container.innerHTML = `
    <header class="detail-header">
      <div class="detail-title-row">
        <div class="detail-title-block">
          <h2>${escapeHtml(idn.nombre || caso.archivo)}</h2>
          <div class="detail-meta-line">
            <span class="meta-item"><strong>Archivo:</strong> ${escapeHtml(caso.archivo)}</span>
            <span class="meta-sep">·</span>
            <span class="meta-item"><strong>Forma:</strong> <span class="badge-forma-mini">F-${caso.forma}</span></span>
            <span class="meta-sep">·</span>
            <span class="meta-item"><strong>Cédula:</strong> ${escapeHtml(caso.id_documento || idn.id_documento || "Sin ID")}</span>
            <span class="meta-sep">·</span>
            <span class="meta-item"><strong>Calidad OMR:</strong> ${q.intra_leidos || 0}/${q.intra_esperados || (caso.forma === "B" ? 97 : 123)} ítems</span>
          </div>
        </div>
        <div class="detail-actions">
          <a href="/api/casos/${caso.caso_id}/pdf-ordenado" class="btn-action-sm secondary" download title="Descargar cuadernillo reordenado de 1 a 24">
            ${svgIcon("download", 14)}
            <span>PDF Ordenado (1..24)</span>
          </a>
          <a href="/api/casos/${caso.caso_id}/json" class="btn-action-sm ghost" download title="Exportar datos brutos en formato JSON">
            ${svgIcon("file-search", 14)}
            <span>JSON</span>
          </a>
          <button type="button" class="btn-action-sm danger btn-delete-caso" title="Eliminar cuadernillo">
            ${svgIcon("trash", 14)}
            <span>Eliminar</span>
          </button>
        </div>
      </div>

      <nav class="detail-tabs">
        <button type="button" class="tab-btn ${currentTab === "datos" ? "active" : ""}" data-tab="datos">
          ${svgIcon("user", 16)}
          <span>Datos Trabajador</span>
        </button>
        <button type="button" class="tab-btn ${currentTab === "respuestas" ? "active" : ""}" data-tab="respuestas">
          ${svgIcon("list-checks", 16)}
          <span>Respuestas OMR</span>
        </button>
        <button type="button" class="tab-btn ${currentTab === "dobles" ? "active" : ""}" data-tab="dobles">
          ${svgIcon("alert-triangle", 16)}
          <span>Doble Chuleado</span>
          ${pend.length ? `<span class="tab-badge-alert">${pend.length}</span>` : ""}
        </button>
        <button type="button" class="tab-btn ${currentTab === "visor" ? "active" : ""}" data-tab="visor">
          ${svgIcon("file-search", 16)}
          <span>Visor Cuadernillo</span>
        </button>
        <button type="button" class="tab-btn ${currentTab === "baremos" ? "active" : ""}" data-tab="baremos">
          ${svgIcon("bar-chart-3", 16)}
          <span>Baremos Villalobos</span>
        </button>
      </nav>
    </header>

    <div class="detail-body">
      ${currentTab === "datos" ? renderTabDatos(caso) : ""}
      ${currentTab === "respuestas" ? renderTabRespuestas(caso) : ""}
      ${currentTab === "dobles" ? renderTabDobles(caso) : ""}
      ${currentTab === "visor" ? renderTabVisor(caso, visorPage) : ""}
      ${currentTab === "baremos" ? renderTabBaremos(caso) : ""}
    </div>
  `;

  // Bind tab navigation
  container.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.onclick = () => onTabChange(btn.dataset.tab);
  });

  // Bind delete
  const delBtn = container.querySelector(".btn-delete-caso");
  if (delBtn) {
    delBtn.onclick = () => {
      if (confirm(`¿Eliminar definitivamente el caso de ${idn.nombre || caso.archivo}?`)) {
        onDeleteCaso(caso.caso_id);
      }
    };
  }

  // Bind Form Submit
  const form = container.querySelector("#form-datos");
  if (form) {
    form.onsubmit = (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      const data = Object.fromEntries(fd.entries());
      onSaveDatos(caso.caso_id, data);
    };
  }

  // Bind Doble Chuleado Buttons
  container.querySelectorAll(".likert-opt-btn").forEach((btn) => {
    btn.onclick = () => {
      const psicInput = document.getElementById("input-psicologa");
      const currentPsic = state && state.currentUser ? (state.currentUser.nombre_completo || state.currentUser.nombre) : "";
      const psic = (psicInput && psicInput.value.trim()) || currentPsic || caso.psicologa || "";
      if (!psic) {
        alert("Escriba el nombre de la psicóloga responsable antes de registrar la decisión.");
        if (psicInput) psicInput.focus();
        return;
      }
      onDecideDoble(caso.caso_id, btn.dataset.amb, Number(btn.dataset.choice), psic);
    };
  });

  // Bind Visor page buttons
  container.querySelectorAll(".visor-page-pill").forEach((btn) => {
    btn.onclick = () => onPageChange(Number(btn.dataset.page));
  });
}

function renderTabDatos(caso) {
  const idn = caso.identidad || {};
  return `
    <form id="form-datos" class="tab-pane">
      <div class="section-intro">
        <div class="intro-title-row">
          <h3>Datos Demográficos y de Consentimiento</h3>
          <span class="norm-badge">Resolución 2764 / 2022</span>
        </div>
        <p>Valide o corrija los datos leídos por OCR manuscrito antes de emitir los informes psicolaborales.</p>
      </div>

      <div class="form-grid">
        <label class="form-field">
          <span class="form-label">Nombre del Trabajador <strong class="req">*</strong></span>
          <input name="nombre" value="${escapeHtml(idn.nombre || "")}" required placeholder="Ej. Hugo Andrés Baquero" />
        </label>
        <label class="form-field">
          <span class="form-label">Cédula de Ciudadanía / ID</span>
          <input name="id_documento" value="${escapeHtml(caso.id_documento || idn.id_documento || "")}" placeholder="Ej. 80421154" />
        </label>
        <label class="form-field">
          <span class="form-label">Cargo <strong class="req">*</strong></span>
          <input name="cargo" value="${escapeHtml(idn.cargo || "")}" required placeholder="Ej. Gerente General" />
        </label>
        <label class="form-field">
          <span class="form-label">Área o Dependencia <strong class="req">*</strong></span>
          <input name="dependencia" value="${escapeHtml(idn.dependencia || "")}" required placeholder="Ej. Administrativa" />
        </label>
        <label class="form-field">
          <span class="form-label">Fecha de Aplicación <strong class="req">*</strong></span>
          <input name="fecha" value="${escapeHtml(idn.fecha || "")}" required placeholder="DD/MM/AAAA" />
        </label>
        <label class="form-field">
          <span class="form-label">Psicóloga Especialista SST <strong class="req">*</strong></span>
          <input id="input-psicologa" name="psicologa" value="${escapeHtml(caso.psicologa || "")}" required placeholder="Nombre completo y tarjeta profesional" />
        </label>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-primary">
          ${svgIcon("check", 16)}
          <span>Guardar Cambios y Recalcular Baremos</span>
        </button>
      </div>
    </form>
  `;
}

function renderTabRespuestas(caso) {
  const intra = caso.intra || {};
  const extra = caso.extra || {};
  const estres = caso.estres || {};
  const forma = caso.forma || "A";
  const nIntra = forma === "B" ? 97 : 123;

  const LIKERT_5 = ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"];
  const LIKERT_4 = ["Siempre", "Casi siempre", "A veces", "Nunca"];

  function badge(val, isEstres = false) {
    if (val === null || val === undefined) {
      return `<span class="ans-badge blank">Sin respuesta</span>`;
    }
    const tags = isEstres ? LIKERT_4 : LIKERT_5;
    const txt = tags[val] || `Código ${val}`;
    let cls = "intermedio";
    if (val === (isEstres ? 3 : 4)) cls = "nunca";
    else if (val === 0) cls = "siempre";
    return `<span class="ans-badge ${cls}"><strong>${txt}</strong> <small>(Col ${val})</small></span>`;
  }

  function getCounts(answers, nExpected, isEstres = false) {
    const counts = isEstres
      ? { 0: 0, 1: 0, 2: 0, 3: 0, blank: 0 }
      : { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, blank: 0 };
    for (let i = 1; i <= nExpected; i++) {
      const v = answers[String(i)] ?? answers[i];
      if (v === null || v === undefined) {
        counts.blank++;
      } else if (counts[v] !== undefined) {
        counts[v]++;
      }
    }
    return counts;
  }

  const cIntra = getCounts(intra, nIntra, false);
  const cExtra = getCounts(extra, 31, false);
  const cEstres = getCounts(estres, 31, true);

  function renderRows(answers, nExpected, isEstres = false) {
    let rows = "";
    for (let i = 1; i <= nExpected; i++) {
      const v = answers[String(i)] ?? answers[i];
      rows += `
        <div class="ans-item-card">
          <span class="ans-item-num">Ítem ${i}</span>
          ${badge(v, isEstres)}
        </div>
      `;
    }
    return rows;
  }

  return `
    <div class="tab-pane respuestas-pane">
      <div class="section-intro">
        <h3>Auditoría de Respuestas Tabuladas por OMR</h3>
        <p>Verifique la correspondencia de cada ítem con las columnas físicas de la grilla impresa.</p>
        <div class="column-legend">
          <span class="legend-box"><strong>Col 0:</strong> Siempre (izq)</span>
          <span class="legend-box"><strong>Col 1:</strong> Casi siempre</span>
          <span class="legend-box"><strong>Col 2:</strong> Algunas veces / A veces</span>
          <span class="legend-box"><strong>Col 3:</strong> Casi nunca (Nunca en estrés)</span>
          <span class="legend-box highlight-nunca"><strong>Col 4:</strong> Nunca (der)</span>
        </div>
      </div>

      <!-- Bloque Intralaboral -->
      <section class="ans-section">
        <div class="ans-section-header">
          <div class="ans-section-title">
            <span class="section-indicator"></span>
            <h4>Cuestionario Intralaboral (Forma ${forma} · ${nIntra} ítems)</h4>
          </div>
          <div class="ans-summary-pills">
            <span class="pill-badge nunca">Nunca (Col 4): ${cIntra[4]}</span>
            <span class="pill-badge">Casi nunca (Col 3): ${cIntra[3]}</span>
            <span class="pill-badge">Algunas veces (Col 2): ${cIntra[2]}</span>
            <span class="pill-badge">Casi siempre (Col 1): ${cIntra[1]}</span>
            <span class="pill-badge siempre">Siempre (Col 0): ${cIntra[0]}</span>
            ${cIntra.blank > 0 ? `<span class="pill-badge blank">En blanco: ${cIntra.blank}</span>` : ""}
          </div>
        </div>
        <div class="ans-grid">${renderRows(intra, nIntra, false)}</div>
      </section>

      <!-- Bloque Extralaboral -->
      <section class="ans-section">
        <div class="ans-section-header">
          <div class="ans-section-title">
            <span class="section-indicator"></span>
            <h4>Cuestionario Extralaboral (31 ítems)</h4>
          </div>
          <div class="ans-summary-pills">
            <span class="pill-badge nunca">Nunca (Col 4): ${cExtra[4]}</span>
            <span class="pill-badge">Casi nunca (Col 3): ${cExtra[3]}</span>
            <span class="pill-badge">Algunas veces (Col 2): ${cExtra[2]}</span>
            <span class="pill-badge">Casi siempre (Col 1): ${cExtra[1]}</span>
            <span class="pill-badge siempre">Siempre (Col 0): ${cExtra[0]}</span>
            ${cExtra.blank > 0 ? `<span class="pill-badge blank">En blanco: ${cExtra.blank}</span>` : ""}
          </div>
        </div>
        <div class="ans-grid">${renderRows(extra, 31, false)}</div>
      </section>

      <!-- Bloque Estrés -->
      <section class="ans-section">
        <div class="ans-section-header">
          <div class="ans-section-title">
            <span class="section-indicator"></span>
            <h4>Cuestionario de Estrés (3.ª Versión · 31 síntomas)</h4>
          </div>
          <div class="ans-summary-pills">
            <span class="pill-badge nunca">Nunca (Col 3): ${cEstres[3]}</span>
            <span class="pill-badge">A veces (Col 2): ${cEstres[2]}</span>
            <span class="pill-badge">Casi siempre (Col 1): ${cEstres[1]}</span>
            <span class="pill-badge siempre">Siempre (Col 0): ${cEstres[0]}</span>
            ${cEstres.blank > 0 ? `<span class="pill-badge blank">En blanco: ${cEstres.blank}</span>` : ""}
          </div>
        </div>
        <div class="ans-grid">${renderRows(estres, 31, true)}</div>
      </section>
    </div>
  `;
}

function renderTabDobles(caso) {
  const ambs = caso.ambiguos || [];
  if (!ambs.length) {
    return `
      <div class="tab-pane empty-pane">
        <div class="ok-icon-wrap">${svgIcon("check-circle", 32)}</div>
        <p class="ok-msg">No se detectaron marcas dobles o ambiguas en este cuadernillo.</p>
        <span class="ok-sub">Todos los ítems leídos presentan marcas unívocas validadas.</span>
      </div>
    `;
  }

  const cardsHtml = ambs
    .map((a) => {
      const isDone = a.decision !== null && a.decision !== undefined;
      const tags = a.etiquetas || ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"];
      const hotSet = new Set(a.marcadas || []);

      const btnsHtml = tags
        .map((lab, i) => {
          const isChosen = isDone && a.decision === i;
          const isDetected = hotSet.has(i);
          return `
          <button type="button" 
                  class="likert-opt-btn ${isChosen ? "picked" : ""} ${isDetected ? "hot" : ""}" 
                  data-amb="${a.id}" 
                  data-choice="${i}">
            ${lab}
          </button>
        `;
        })
        .join("");

      const cropHtml = a.crop
        ? `<div class="crop-container"><img src="/media/${a.crop}" alt="Recorte de celda manuscrita" /></div>`
        : `<p class="no-crop">Recorte visual no disponible</p>`;
      const hasAiHint = !isDone && (a.ia_motivo || (a.ia_sugerencia !== null && a.ia_sugerencia !== undefined));
      const sugLabel = a.ia_sugerencia !== null && a.ia_sugerencia !== undefined && tags[a.ia_sugerencia] ? `Posible opción limpia: <strong>${escapeHtml(tags[a.ia_sugerencia])}</strong>.` : "";
      const aiHintHtml = hasAiHint ? `<div class="amb-ai-hint" style="display:flex;align-items:flex-start;gap:8px;padding:8px 10px;margin:6px 0;border-radius:6px;background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.22);font-size:0.82rem;line-height:1.35;"><span style="flex-shrink:0;margin-top:1px;">${svgIcon("cpu", 14)}</span><span><strong>Apoyo IA (no vinculante):</strong> ${escapeHtml(a.ia_motivo || "Revisión visual de trazos.")} ${sugLabel} <em>Confirme manualmente abajo.</em></span></div>` : "";

      return `
      <article class="amb-card ${isDone ? "resolved" : "pending"}">
        <div class="amb-header">
          <div class="amb-title">
            <span class="amb-status-dot ${isDone ? "resolved" : "pending"}"></span>
            <strong>Ítem ${a.item} (${a.bloque.toUpperCase()})</strong>
          </div>
          <span class="amb-page">Pág física ${a.pagina}</span>
        </div>
        ${
          isDone
            ? `<div class="amb-audit">${svgIcon("check", 14)} <span>Resuelto por <strong>${escapeHtml(a.decidido_por)}</strong>: <em>${tags[a.decision]}</em></span></div>`
            : `<div class="amb-alert">El respondiente marcó varias casillas. Seleccione la opción válida:</div>`
        }
        ${aiHintHtml}
        ${cropHtml}
        <div class="likert-btn-group">${btnsHtml}</div>
      </article>
    `;
    })
    .join("");

  return `
    <div class="tab-pane">
      <div class="section-intro">
        <div class="intro-title-row">
          <h3>Resolución de Dobles Chuleados</h3>
          <span class="norm-badge">Auditoría Clínica</span>
        </div>
        <p>Por invariante ético y legal, el motor OMR jamás desempata automáticamente. La psicóloga dictamina la opción con trazabilidad completa.</p>
      </div>
      <div class="amb-grid">${cardsHtml}</div>
    </div>
  `;
}

function renderTabVisor(caso, currentPage) {
  const totalPages = caso.n_paginas || 24;
  const pillsHtml = Array.from({ length: totalPages }, (_, i) => i + 1)
    .map(
      (p) =>
        `<button type="button" class="visor-page-pill ${p === currentPage ? "active" : ""}" data-page="${p}">Pág ${p}</button>`
    )
    .join("");

  const pageInfo = (caso.paginas || []).find((p) => p.physical_page === currentPage);
  const scanIdx = pageInfo ? pageInfo.scan_index : currentPage;
  const kindLabel = pageInfo ? pageInfo.kind || "" : "";
  const nRows = pageInfo ? pageInfo.n_likert_rows || 0 : 0;

  const KIND_TITLES = {
    consentimiento: "Consentimiento Informado",
    ficha: "Ficha de Datos Generales",
    intra_portada: "Portada Cuestionario Intralaboral",
    intra_instrucciones: "Instrucciones Intralaboral",
    intra_items: `Cuestionario Intralaboral (${nRows} preguntas)`,
    extra_portada: "Portada Cuestionario Extralaboral",
    extra_instrucciones: "Instrucciones Extralaboral",
    extra_items: `Cuestionario Extralaboral (${nRows} preguntas)`,
    estres_portada: "Portada Evaluación del Estrés",
    estres_items: `Cuestionario de Estrés (${nRows} síntomas)`,
    otra: "Sección General",
  };
  const sectionTitle = KIND_TITLES[kindLabel] || kindLabel;

  return `
    <div class="tab-pane visor-pane">
      <div class="visor-nav">
        <span class="visor-nav-label">Navegación por página física:</span>
        <div class="visor-pills">${pillsHtml}</div>
      </div>
      <div class="visor-page-info">
        <div>
          <span>Página Física Oficial:</span> <strong>Pág ${currentPage} de ${totalPages}</strong>
          ${sectionTitle ? ` · <em class="section-title-tag">${sectionTitle}</em>` : ""}
        </div>
        <div class="visor-scan-ref">
          <small>Escaneo original: #${scanIdx} (ADF)</small>
        </div>
      </div>
      <div class="visor-stage">
        <img src="/api/casos/${caso.caso_id}/pagina/${currentPage}" alt="Página ${currentPage} del PDF" loading="lazy" />
      </div>
    </div>
  `;
}

function renderTabBaremos(caso) {
  const sc = caso.scoring || {};
  const intraTotal = (sc.intra || {}).total || {};
  const extraTotal = (sc.extra || {}).total || {};
  const estresTotal = (sc.estres || {}).total || {};

  return `
    <div class="tab-pane baremos-pane">
      <div class="scoring-cards">
        <div class="score-card">
          <div class="score-card-header">
            <h4>Intralaboral Forma ${caso.forma || "A"}</h4>
            <span class="forma-badge-mini">Forma ${caso.forma || "A"}</span>
          </div>
          <div class="score-main">
            <span class="score-t">T: ${intraTotal.transformado ?? "--"}</span>
            <span class="score-badge risk-${(intraTotal.nivel || "").toLowerCase().replace(/\s+/g, "_")}">${intraTotal.nivel || "Incompleto"}</span>
          </div>
          <div class="score-footer-meta">
            <span>Puntaje Bruto: ${intraTotal.bruto ?? 0}</span>
            <span>·</span>
            <span>Respondidos: ${intraTotal.n ?? 0}/${caso.forma === "B" ? 97 : 123}</span>
          </div>
        </div>

        <div class="score-card">
          <div class="score-card-header">
            <h4>Extralaboral</h4>
            <span class="forma-badge-mini">31 Ítems</span>
          </div>
          <div class="score-main">
            <span class="score-t">T: ${extraTotal.transformado ?? "--"}</span>
            <span class="score-badge risk-${(extraTotal.nivel || "").toLowerCase().replace(/\s+/g, "_")}">${extraTotal.nivel || "Incompleto"}</span>
          </div>
          <div class="score-footer-meta">
            <span>Puntaje Bruto: ${extraTotal.bruto ?? 0}</span>
            <span>·</span>
            <span>Respondidos: ${extraTotal.n ?? 0}/31</span>
          </div>
        </div>

        <div class="score-card">
          <div class="score-card-header">
            <h4>Estrés Laboral</h4>
            <span class="forma-badge-mini">3.ª Versión</span>
          </div>
          <div class="score-main">
            <span class="score-t">T: ${estresTotal.transformado ?? "--"}</span>
            <span class="score-badge risk-${(estresTotal.nivel || "").toLowerCase().replace(/\s+/g, "_")}">${estresTotal.nivel || "Incompleto"}</span>
          </div>
          <div class="score-footer-meta">
            <span>Puntaje Bruto: ${estresTotal.bruto ?? 0}</span>
            <span>·</span>
            <span>Respondidos: ${estresTotal.n ?? 0}/31</span>
          </div>
        </div>
      </div>

      <div class="section-intro">
        <div class="intro-title-row">
          <h3>Desglose Normativo por Dominios y Dimensiones</h3>
          <span class="norm-badge">Baremos Villalobos</span>
        </div>
      </div>
      ${renderDimensionTable(sc)}
    </div>
  `;
}

function renderDimensionTable(sc) {
  const dimsIntra = (sc.intra || {}).dimensiones || [];
  const dimsExtra = (sc.extra || {}).dimensiones || [];
  const allDims = [...dimsIntra, ...dimsExtra];

  if (!allDims.length) {
    return `<p class="meta">No hay dimensiones calculadas aún (faltan ítems).</p>`;
  }

  const rows = allDims
    .map((d) => {
      const isIncompleta = Boolean(d.incompleta);
      const nivelText = isIncompleta ? "Incompleta" : d.nivel || "--";
      const nivelKey = (d.nivel || (isIncompleta ? "incompleta" : "sin_riesgo")).toLowerCase().replace(/\s+/g, "_");
      return `
    <tr>
      <td><strong>${escapeHtml(d.nombre || "")}</strong></td>
      <td><span class="domain-tag">${escapeHtml(d.dominio || "General")}</span></td>
      <td class="num-cell">${d.n_respondidos}/${d.n_esperados}</td>
      <td class="num-cell highlight">${d.transformado !== null ? d.transformado : "--"}</td>
      <td><span class="badge badge-risk badge-risk-${nivelKey}">${escapeHtml(nivelText)}</span></td>
    </tr>
  `;
    })
    .join("");

  return `
    <div class="table-responsive">
      <table class="dim-table">
        <thead>
          <tr>
            <th>Dimensión Evaluada</th>
            <th>Dominio</th>
            <th>Resp / Esp</th>
            <th>Puntaje T</th>
            <th>Nivel de Riesgo Normativo</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}
