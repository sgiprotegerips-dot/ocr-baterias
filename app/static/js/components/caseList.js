/**
 * caseList.js - Bandeja inteligente de casos, filtros y paginación técnica.
 * Cero emojis. Iconos SVG vectoriales y píldoras semánticas con status dots.
 */

import { svgIcon } from "../icons.js";

const LABELS_ESTADO = {
  doble_marca: "Doble chuleado",
  faltan_datos: "Faltan datos",
  listo: "Listo",
};

export function renderCaseList(container, state, onSelect) {
  const { casos, activeId, total, page, totalPages } = state;

  if (!casos || casos.length === 0) {
    container.innerHTML = `
      <div class="empty-list">
        <div class="empty-icon-wrap">${svgIcon("search", 24)}</div>
        <p>No se encontraron cuadernillos con los filtros activos.</p>
      </div>
    `;
    return;
  }

  const itemsHtml = casos
    .map((c) => {
      const idn = c.identidad || {};
      const pend = (c.ambiguos || []).filter((a) => a.decision === null || a.decision === undefined).length;
      const isSelected = c.caso_id === activeId;
      const sc = ((c.scoring || {}).intra || {}).total || {};
      const nivelRiesgo = sc.nivel || "Sin tabular";
      const nivelClass = nivelRiesgo.toLowerCase().replace(/\s+/g, "_");

      let statusDotClass = "neutral";
      if (c.estado === "listo") statusDotClass = "ok";
      else if (c.estado === "doble_marca") statusDotClass = "alert";
      else if (c.estado === "faltan_datos") statusDotClass = "warn";

      return `
      <li class="case-item ${isSelected ? "active" : ""}" data-id="${c.caso_id}">
        <div class="case-top">
          <strong class="case-name">${idn.nombre || c.archivo}</strong>
          <span class="badge-forma">F-${c.forma || "A"}</span>
        </div>
        <div class="case-sub">
          <span class="case-id-text">CC ${c.id_documento || idn.id_documento || "Sin ID"}</span>
          <span class="sub-sep">·</span>
          <span class="case-cargo-text">${idn.cargo || "Sin cargo registrado"}</span>
        </div>
        <div class="case-badges">
          <span class="status-pill status-pill-${c.estado}">
            <span class="status-dot ${statusDotClass}"></span>
            ${LABELS_ESTADO[c.estado] || c.estado}${pend ? ` (${pend})` : ""}
          </span>
          ${
            sc.transformado !== undefined && sc.transformado !== null
              ? `<span class="badge-risk badge-risk-${nivelClass}">Intra T: ${sc.transformado}</span>`
              : ""
          }
        </div>
      </li>
    `;
    })
    .join("");

  const paginationHtml = `
    <div class="list-pagination">
      <span class="pagination-info">Pág ${page} de ${totalPages || 1} (${total} casos)</span>
      <div class="page-btns">
        <button type="button" class="page-prev page-btn" ${page <= 1 ? "disabled" : ""} title="Página anterior" aria-label="Página anterior">
          ${svgIcon("chevron-left", 14)}
        </button>
        <button type="button" class="page-next page-btn" ${page >= totalPages ? "disabled" : ""} title="Página siguiente" aria-label="Página siguiente">
          ${svgIcon("chevron-right", 14)}
        </button>
      </div>
    </div>
  `;

  container.innerHTML = `<ul class="case-ul">${itemsHtml}</ul>${paginationHtml}`;

  // Event handlers
  container.querySelectorAll(".case-item").forEach((el) => {
    el.onclick = () => {
      onSelect(el.dataset.id);
    };
  });
}
