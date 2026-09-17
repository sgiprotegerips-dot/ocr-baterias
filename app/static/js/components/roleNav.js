/**
 * roleNav.js - Barra de navegación contextual adaptada al rol en sesión.
 * Cero emojis. Iconografía SVG técnica pura (Lucide Standard).
 */

import { svgIcon } from "../icons.js";

const NAV_CONFIG = {
  admin: [
    { id: "admin", label: "Consola de Administración", icon: "shield-check" },
    { id: "workspace", label: "Auditoría de Cuadernillos", icon: "list-checks" },
    { id: "etiquetas", label: "Etiquetas QR", icon: "qr-code" },
    { id: "informe", label: "Informe Diagnóstico SST", icon: "award" },
  ],
  psicologa: [
    { id: "campanas", label: "Campañas", icon: "target" },
    { id: "workspace", label: "Auditoría de Cuadernillos", icon: "list-checks" },
    { id: "etiquetas", label: "Etiquetas QR", icon: "qr-code" },
    { id: "informe", label: "Informe Diagnóstico & Custodia 20 Años", icon: "award" },
  ],
  operador: [
    { id: "operador", label: "Estación de Digitalización", icon: "scan" },
    { id: "etiquetas", label: "Etiquetas QR", icon: "qr-code" },
  ],
  cliente_empresa: [
    { id: "cliente", label: "Portal Ejecutivo SST", icon: "building-2" },
    { id: "informe", label: "Informe Diagnóstico Oficial", icon: "file-text" },
  ],
};

const DEFAULT_VIEWS = {
  admin: "admin",
  psicologa: "campanas",
  operador: "operador",
  cliente_empresa: "cliente",
};

export function getDefaultViewForRole(role) {
  return DEFAULT_VIEWS[role] || "workspace";
}

export function renderRoleNav(container, currentUser, activeView, onViewChange) {
  if (!container) return;

  if (!currentUser) {
    container.innerHTML = "";
    container.style.display = "none";
    return;
  }

  const role = currentUser.rol || "psicologa";
  const tabs = NAV_CONFIG[role] || NAV_CONFIG.psicologa;

  container.style.display = "flex";
  container.innerHTML = `
    <div class="role-nav-inner">
      <div class="role-nav-tabs">
        ${tabs
          .map(
            (t) => `
          <button type="button" class="role-nav-btn ${activeView === t.id ? "active" : ""}" data-view="${t.id}">
            ${svgIcon(t.icon, 15)}
            <span>${t.label}</span>
          </button>
        `
          )
          .join("")}
      </div>

      <div class="role-nav-context">
        <span class="role-indicator-badge role-tag-${role}">
          <span class="status-dot ok"></span>
          <span>Modo: ${getRoleLabel(role)}</span>
        </span>
      </div>
    </div>
  `;

  container.querySelectorAll(".role-nav-btn").forEach((btn) => {
    btn.onclick = () => {
      const view = btn.dataset.view;
      if (onViewChange) onViewChange(view);
    };
  });
}

function getRoleLabel(role) {
  switch (role) {
    case "admin":
      return "Administrador Global";
    case "psicologa":
      return "Psicóloga Especialista SST";
    case "operador":
      return "Operador de Escáner";
    case "cliente_empresa":
      return "Cliente Empresa";
    default:
      return role;
  }
}
