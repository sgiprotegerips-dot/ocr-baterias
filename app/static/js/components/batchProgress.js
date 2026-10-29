/**
 * batchProgress.js - Barra de progreso en tiempo real (SSE) con shimmer angular direccional.
 * Cero emojis. Iconos vectoriales y aceleración por GPU.
 */

import { svgIcon } from "../icons.js";

export function renderBatchProgress(container, jobState, onCancel) {
  if (!jobState) {
    container.innerHTML = "";
    container.style.display = "none";
    return;
  }

  container.style.display = "block";
  const { total = 0, completed = 0, failed = 0, current_file = "", percent = 0, status = "processing", elapsed_seconds = 0 } = jobState;

  const isDone = status === "completed" || status === "cancelled" || status === "error";

  let statusTitle = "Procesando lote masivo...";
  let statusIcon = "cpu";
  if (status === "uploading") {
    statusTitle = "Subiendo archivos al servidor...";
    statusIcon = "upload";
  } else if (status === "completed") {
    statusTitle = "Lectura masiva completada exitosamente";
    statusIcon = "check-circle";
  } else if (status === "cancelled") {
    statusTitle = "Procesamiento cancelado por el operador";
    statusIcon = "alert-triangle";
  } else if (status === "error") {
    statusTitle = "Error durante el procesamiento del lote";
    statusIcon = "alert-circle";
  }

  const detailText =
    status === "uploading"
      ? `${completed} de ${total} archivo(s) en transferencia (${percent}%)`
      : `${completed} de ${total} cuadernillos leídos ${failed > 0 ? `(${failed} fallos)` : ""} · ${elapsed_seconds}s transcurridos`;

  container.innerHTML = `
    <div class="batch-card ${status}">
      <div class="batch-info-row">
        <div class="batch-title-block">
          <div class="batch-status-icon-row">
            <span class="batch-icon-wrap">${svgIcon(statusIcon, 16)}</span>
            <strong>${statusTitle}</strong>
          </div>
          <span class="batch-detail">${detailText}</span>
        </div>
        ${!isDone && status !== "uploading" ? `<button type="button" class="btn-cancel-batch btn-sm ghost">Detener Lote</button>` : ""}
      </div>

      <div class="progress-track">
        <div class="progress-bar ${isDone ? "done" : "active-shimmer"}" style="width: ${percent}%;"></div>
      </div>

      <div class="batch-current-file">
        ${!isDone && current_file ? `<span>${status === "uploading" ? "Transfiriendo archivo" : "Página actual en lectura"}: <em>${current_file}</em> (${percent}%)</span>` : ""}
      </div>
    </div>
  `;

  const cancelBtn = container.querySelector(".btn-cancel-batch");
  if (cancelBtn) {
    cancelBtn.onclick = onCancel;
  }
}
