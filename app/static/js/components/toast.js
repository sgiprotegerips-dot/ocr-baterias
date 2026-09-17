/**
 * toast.js - Sistema de notificaciones toast flotantes no intrusivas.
 * Cero emojis. Iconografía SVG vectorial pura.
 */

import { svgIcon } from "../icons.js";

let toastContainer = null;

function ensureToastContainer() {
  if (!toastContainer || !document.body.contains(toastContainer)) {
    toastContainer = document.getElementById("toast-shelf");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.id = "toast-shelf";
      toastContainer.className = "toast-shelf";
      document.body.appendChild(toastContainer);
    }
  }
  return toastContainer;
}

export function showToast(message, type = "info", duration = 3500) {
  const container = ensureToastContainer();

  const toast = document.createElement("div");
  toast.className = `toast-item toast-${type}`;

  let iconName = "check-circle";
  if (type === "error") iconName = "alert-circle";
  else if (type === "warning") iconName = "alert-triangle";
  else if (type === "info") iconName = "shield-check";

  toast.innerHTML = `
    <div class="toast-icon">${svgIcon(iconName, 16)}</div>
    <div class="toast-msg">${escapeHtml(message)}</div>
    <button type="button" class="toast-close" aria-label="Cerrar notificación">${svgIcon("x", 12)}</button>
  `;

  const closeBtn = toast.querySelector(".toast-close");
  const dismiss = () => {
    toast.classList.add("toast-hiding");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 250);
  };

  if (closeBtn) closeBtn.onclick = dismiss;
  toast.onclick = (e) => {
    if (e.target.closest(".toast-close")) return;
    dismiss();
  };

  container.appendChild(toast);

  // Auto-dismiss
  if (duration > 0) {
    setTimeout(dismiss, duration);
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}
