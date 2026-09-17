/**
 * authBar.js - Barra de identidad de usuario y modal de autenticación RBAC.
 * Soporta 4 roles: psicologa, admin, operador, cliente_empresa.
 * Cero emojis. Iconografía técnica vectorial pura.
 */

import { loginUser, logoutUser } from "../api.js?v=2.2";
import { svgIcon } from "../icons.js?v=2.2";
import { setState, state } from "../state.js?v=2.2";
import { getDefaultViewForRole } from "./roleNav.js?v=2.2";
import { showToast } from "./toast.js?v=2.2";

const ROLE_LABELS = {
  admin: "Administrador SST",
  psicologa: "Psicóloga Especialista SST",
  operador: "Operador Digitalizador",
  cliente_empresa: "Cliente Empresa (Gestor SST)",
};

export function renderAuthBar(container, currentUser, onUserChange) {
  if (!container) return;

  const isLogged = Boolean(currentUser);
  const userKey = isLogged
    ? `${currentUser.id || ""}_${currentUser.email || ""}_${currentUser.rol || ""}_${currentUser.nombre_completo || currentUser.nombre || ""}`
    : "anonymous";

  if (container.dataset.renderedUser === userKey) {
    return;
  }
  container.dataset.renderedUser = userKey;

  const roleName = isLogged ? (ROLE_LABELS[currentUser.rol] || currentUser.rol) : "Sin autenticar";
  const userName = isLogged ? (currentUser.nombre_completo || currentUser.nombre) : "Acceso Profesional";
  const licVal = isLogged ? (currentUser.licencia_sst || currentUser.licencia_so) : null;
  const licTag = licVal ? `<span class="user-lic-tag">${licVal}</span>` : "";

  container.innerHTML = `
    <div class="user-session-wrap" style="display: flex; align-items: center; gap: 0.5rem;">
      <button type="button" class="btn-user-session" id="btn-user-menu" title="Perfil y control de acceso">
        <span class="user-avatar-icon">${svgIcon(isLogged ? "shield-check" : "user", 16)}</span>
        <div class="user-session-text">
          <span class="user-name">${userName}</span>
          <span class="user-role">${roleName}</span>
        </div>
        ${licTag}
      </button>
      ${
        isLogged
          ? `
        <button type="button" class="btn-action ghost btn-logout-header" id="btn-header-logout" title="Cerrar sesión en la plataforma">
          ${svgIcon("log-out", 14)}
          <span>Cerrar Sesión</span>
        </button>
      `
          : ""
      }
    </div>
  `;

  const btnMenu = container.querySelector("#btn-user-menu");
  if (btnMenu) {
    btnMenu.onclick = () => openAuthModal(currentUser, onUserChange);
  }

  const btnLogout = container.querySelector("#btn-header-logout");
  if (btnLogout) {
    btnLogout.onclick = async () => {
      try {
        await logoutUser();
      } catch (err) {
        console.error("Error cerrando sesión:", err);
      }
      delete container.dataset.renderedUser;
      setState({ currentUser: null, activeView: "workspace" });
      if (onUserChange) onUserChange(null);
    };
  }
}

export function openAuthModal(currentUser, onUserChange) {
  let modal = document.getElementById("auth-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "auth-modal";
    modal.className = "cmd-palette-backdrop";
    document.body.appendChild(modal);
  }

  const isLogged = Boolean(currentUser);

  modal.innerHTML = `
    <div class="auth-modal-card">
      <div class="modal-head">
        <div class="modal-title-wrap">
          ${svgIcon("shield-check", 20)}
          <div>
            <h3>Control de Acceso y Roles SST</h3>
            <p class="modal-sub">Batería de Riesgo Psicosocial · Resoluciones 2646/2008 y 2764/2022</p>
          </div>
        </div>
        <button type="button" class="btn-close-modal" id="btn-close-auth-modal" aria-label="Cerrar">
          ${svgIcon("x", 16)}
        </button>
      </div>

      ${
        isLogged
          ? `
        <div class="current-user-banner">
          <div class="current-user-info">
            <strong>${currentUser.nombre_completo || currentUser.nombre}</strong>
            <span>${ROLE_LABELS[currentUser.rol] || currentUser.rol} · ${currentUser.email}</span>
            ${currentUser.licencia_sst || currentUser.licencia_so ? `<span class="badge-lic-sst">Licencia SST: ${currentUser.licencia_sst || currentUser.licencia_so}</span>` : ""}
          </div>
          <button type="button" class="btn-action ghost" id="btn-do-logout">
            ${svgIcon("log-out", 15)}
            <span>Cerrar Sesión</span>
          </button>
        </div>
      `
          : ""
      }

      <form id="auth-form" class="auth-custom-form">
        <div class="form-row">
          <label for="auth-email">Correo Electrónico:</label>
          <input type="email" id="auth-email" required placeholder="ejemplo@proteger.com.co" value="${currentUser ? currentUser.email : ""}" />
        </div>
        <div class="form-row">
          <label for="auth-pass">Contraseña:</label>
          <input type="password" id="auth-pass" required placeholder="Contraseña de acceso" />
        </div>
        <div class="form-actions-row">
          <span id="auth-error-msg" class="auth-error-hint"></span>
          <button type="submit" class="btn-primary" id="btn-submit-login">
            ${svgIcon("log-in", 16)}
            <span>Autenticar</span>
          </button>
        </div>
      </form>
    </div>
  `;

  modal.style.display = "flex";

  const closeModal = () => {
    modal.style.display = "none";
  };

  modal.querySelector("#btn-close-auth-modal").onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) closeModal();
  };

  // Logout
  const logoutBtn = modal.querySelector("#btn-do-logout");
  if (logoutBtn) {
    logoutBtn.onclick = async () => {
      await logoutUser();
      setState({ currentUser: null, activeView: "workspace" });
      closeModal();
      showToast("Sesión cerrada correctamente", "info");
      if (onUserChange) onUserChange(null);
    };
  }

  // Form submit
  const form = modal.querySelector("#auth-form");
  const errEl = modal.querySelector("#auth-error-msg");
  form.onsubmit = async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    const email = modal.querySelector("#auth-email").value.trim();
    const pass = modal.querySelector("#auth-pass").value;
    try {
      const user = await loginUser(email, pass);
      const nextView = getDefaultViewForRole(user.rol);
      setState({ currentUser: user, activeView: nextView });
      closeModal();
      showToast(`Sesión iniciada como ${user.nombre_completo || user.nombre}`, "success");
      if (onUserChange) onUserChange(user);
    } catch (err) {
      errEl.textContent = err.message;
      showToast(err.message, "error");
    }
  };
}
