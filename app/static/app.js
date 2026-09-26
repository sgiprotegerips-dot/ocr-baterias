/**
 * app.js - Orquestador principal de la aplicación web moderna.
 * Arquitectura Bespoke Frontend: Swiss Modern + Bento Grid + Frosted Glass.
 * Soporta RBAC (4 roles), Empresa Base, Campañas (Medición), Cuadernillos e Informe Custodia 20 Años.
 * Cero emojis. Iconos SVG puros y paleta de comandos (Cmd+K).
 */

import {
  cancelBatch,
  createDemoCaso,
  decideDoble,
  deleteCaso,
  fetchCaso,
  fetchCasos,
  fetchEmpresas,
  fetchMe,
  fetchMediciones,
  fetchOcrEngines,
  loginUser,
  logoutUser,
  saveDatos,
  subscribeBatchEvents,
  uploadBatch,
} from "./js/api.js?v=2.3";
import { renderAuthBar } from "./js/components/authBar.js?v=3.1";
import { renderBatchProgress } from "./js/components/batchProgress.js?v=2.2";
import { renderCaseDetail } from "./js/components/caseDetail.js?v=2.2";
import { renderCaseList } from "./js/components/caseList.js?v=2.2";
import { renderInformeView } from "./js/components/informeView.js?v=3.2";
import { renderStats } from "./js/components/stats.js?v=2.2";
import { getDefaultViewForRole, renderRoleNav } from "./js/components/roleNav.js?v=3.0";
import { renderAdminView } from "./js/components/adminView.js?v=3.0";
import { renderOperadorView } from "./js/components/operadorView.js?v=3.5";
import { renderEtiquetasView } from "./js/components/etiquetasView.js?v=3.8";
import { readSavedContext, saveContext } from "./js/contextStore.js?v=3.5";
import { renderClienteView } from "./js/components/clienteView.js?v=3.2";
import { renderHomePsico } from "./js/components/homePsico.js?v=3.0";
import { bindOfficialDocs, downloadOfficialFile } from "./js/downloads.js?v=3.2";
import { showToast } from "./js/components/toast.js?v=2.2";
import { setState, state, subscribeState } from "./js/state.js?v=2.2";


// Elementos DOM de Plataforma y Login
const domLoginViewport = document.getElementById("login-viewport");
const domAppShell = document.getElementById("app-shell");
const domLoginForm = document.getElementById("login-main-form");
const domLoginEmail = document.getElementById("input-login-email");
const domLoginPass = document.getElementById("input-login-pass");
const domLoginErrorBox = document.getElementById("login-error-box");
const domLoginErrorText = document.getElementById("login-error-text");
const domBtnLoginSubmit = document.getElementById("btn-login-submit");
const domBtnLoginText = document.getElementById("btn-login-text");
const domBtnTogglePass = document.getElementById("btn-toggle-pass");
const domIconEyeOpen = document.getElementById("icon-eye-open");
const domIconEyeClosed = document.getElementById("icon-eye-closed");
const domBtnLoginTheme = document.getElementById("btn-login-theme");
const domDemoRolePills = document.querySelectorAll(".demo-role-pill");
const domCheckRememberMe = document.getElementById("check-remember-me");

const domUserAuth = document.getElementById("user-auth-container");
const domRoleNav = document.getElementById("role-nav-container");
const domTenant = document.getElementById("tenant-container");
const domWorkspaceView = document.getElementById("workspace-view");
const domInformeView = document.getElementById("informe-container");
const domAdminView = document.getElementById("admin-container");
const domOperadorView = document.getElementById("operador-container");
const domEtiquetasView = document.getElementById("etiquetas-container");
const domClienteView = document.getElementById("cliente-container");
const domCampanasView = document.getElementById("campanas-container");

const domStats = document.getElementById("stats-container");
const domCaseList = document.getElementById("casos-container");
const domCaseDetail = document.getElementById("detail-container");
const domBatchProgress = document.getElementById("batch-progress-container");
const domSearch = document.getElementById("search-input");
const domFilterBtns = document.querySelectorAll(".filter-pill");
const domUploadForm = document.getElementById("upload-form");
const domFileInput = document.getElementById("files-input");
const domDemoBtn = document.getElementById("btn-demo");
const domThemeBtn = document.getElementById("btn-theme");
const domUploadPanel = document.getElementById("upload-panel");

// Command Palette Elements
const domCmdPalette = document.getElementById("cmd-palette");
const domBtnOpenCmd = document.getElementById("btn-open-cmd");
const domBtnCloseCmd = document.getElementById("btn-close-cmd");
const domCmdSearchInput = document.getElementById("cmd-search-input");
const domCmdResults = document.getElementById("cmd-results");

// Carga de datos con filtro de campaña/medición
async function reloadData() {
  try {
    if (state.currentUser?.rol === "cliente_empresa") {
      return;
    }
    const res = await fetchCasos({
      q: state.searchQuery,
      estado: state.filterEstado,
      forma: state.filterForma,
      medicion_id: state.activeMedicionId || undefined,
      page: state.page,
      page_size: state.pageSize,
    });

    setState({
      casos: res.casos,
      total: res.total,
      totalPages: res.total_pages,
      stats: res.stats,
    });

    // Si hay un caso activo, refrescar su detalle
    if (state.activeId) {
      const active = await fetchCaso(state.activeId);
      setState({ activeCaso: active });
    } else if (res.casos.length > 0) {
      // Auto-seleccionar primer caso
      const first = await fetchCaso(res.casos[0].caso_id);
      setState({ activeId: first.caso_id, activeCaso: first });
    } else {
      setState({ activeId: null, activeCaso: null });
    }
  } catch (err) {
    console.error("Error recargando datos:", err);
  }
}

function contextCallbacks() {
  return {
    onSelectEmpresa: async (empId) => {
      let meds = [];
      if (empId) {
        try {
          meds = await fetchMediciones(empId);
        } catch (err) {
          showToast(err.message, "error");
        }
      }
      setState({
        activeEmpresaId: empId || null,
        mediciones: meds,
        activeMedicionId: null,
        page: 1,
      });
      saveContext(state.currentUser, empId || null, null);
    },
    onSelectMedicion: async (medId) => {
      setState({ activeMedicionId: medId || null, page: 1 });
      saveContext(state.currentUser, state.activeEmpresaId, medId || null);
      await reloadData();
    },
  };
}

// Suscripción al estado reactivo para re-renderizado
subscribeState((currentState) => {
  // 1. Barra de Usuario / Auth
  renderAuthBar(domUserAuth, currentState.currentUser, async (updatedUser) => {
    if (!updatedUser) {
      showLoginScreen();
    } else {
      await reloadData();
    }
  });

  // 2. Barra de Navegación Contextual por Rol (Role Nav Bar)
  renderRoleNav(domRoleNav, currentState.currentUser, currentState.activeView, (nextView) => {
    setState({ activeView: nextView });
  });

  // 3. Contexto empresa/campaña vive en cada home; se oculta la barra global.
  if (domTenant) {
    domTenant.style.display = "none";
    domTenant.innerHTML = "";
  }

  // 4. Conmutador de Vistas: Ocultar todas primero
  const allViews = [
    domWorkspaceView,
    domInformeView,
    domAdminView,
    domOperadorView,
    domEtiquetasView,
    domClienteView,
    domCampanasView,
  ];
  allViews.forEach((el) => {
    if (el) el.style.display = "none";
  });

  const activeView = currentState.activeView || "workspace";

  if (activeView === "campanas") {
    if (domCampanasView) {
      domCampanasView.style.display = "block";
      renderHomePsico(domCampanasView, currentState, {
        onCampanaCreated: async (med) => {
          const emps = await fetchEmpresas();
          const meds = med.empresa_id ? await fetchMediciones(med.empresa_id) : currentState.mediciones;
          setState({
            empresas: emps,
            mediciones: meds,
            activeEmpresaId: med.empresa_id,
            activeMedicionId: med.id,
            activeView: "workspace",
          });
          await reloadData();
        },
        onOpenCampana: async (medicionId, empresaId) => {
          setState({
            activeEmpresaId: empresaId,
            activeMedicionId: medicionId,
            activeView: "workspace",
            page: 1,
          });
          await reloadData();
        },
      });
    }
    return;
  }

  // Vista Admin
  if (activeView === "admin") {
    if (domAdminView) {
      domAdminView.style.display = "block";
      renderAdminView(domAdminView, (v) => setState({ activeView: v }));
    }
    return;
  }

  // Vista Operador
  if (activeView === "operador") {
    if (domOperadorView) {
      domOperadorView.style.display = "block";
      renderOperadorView(domOperadorView, currentState, contextCallbacks());
    }
    return;
  }

  // Vista Etiquetas QR 30×20 mm
  if (activeView === "etiquetas") {
    if (domEtiquetasView) {
      domEtiquetasView.style.display = "block";
      renderEtiquetasView(domEtiquetasView, currentState, contextCallbacks());
    }
    return;
  }

  // Vista Cliente Empresa
  if (activeView === "cliente") {
    if (domClienteView) {
      domClienteView.style.display = "block";
      renderClienteView(domClienteView, currentState);
    }
    return;
  }

  // Vista Informe Diagnóstico
  if (activeView === "informe") {
    if (domInformeView) {
      domInformeView.style.display = "block";
      if (currentState.activeMedicionId) {
        renderInformeView(domInformeView, currentState.activeMedicionId, () => {
          setState({ activeView: getDefaultViewForRole(currentState.currentUser?.rol) });
        });
      }
    }
    return;
  }

  // Vista Workspace (Auditoría clínica de cuadernillos)
  if (domWorkspaceView) {
    domWorkspaceView.style.display = "block";
  }

  renderStats(domStats, currentState.stats);

  renderCaseList(domCaseList, currentState, async (selectedId) => {
    try {
      const caso = await fetchCaso(selectedId);
      setState({ activeId: selectedId, activeCaso: caso, visorPage: 1 });
    } catch (e) {
      showToast("Error al cargar caso", "error");
    }
  });

  renderCaseDetail(domCaseDetail, currentState.activeCaso, currentState, {
    onTabChange: (tab) => setState({ activeTab: tab }),
    onPageChange: (page) => setState({ visorPage: page }),
    onSaveDatos: async (casoId, data) => {
      const updated = await saveDatos(casoId, data);
      setState({ activeCaso: updated });
      showToast("Datos demográficos guardados", "success");
      reloadData();
    },
    onDecideDoble: async (casoId, ambId, choice, psicologa) => {
      const updated = await decideDoble(casoId, ambId, choice, psicologa);
      setState({ activeCaso: updated });
      showToast("Decisión de doble chuleado guardada con trazabilidad", "success");
      reloadData();
    },
    onDeleteCaso: async (casoId) => {
      await deleteCaso(casoId);
      setState({ activeId: null, activeCaso: null });
      showToast("Cuadernillo eliminado", "info");
      reloadData();
    },
  });

  renderBatchProgress(domBatchProgress, currentState.activeJob, async () => {
    if (currentState.activeJob) {
      await cancelBatch(currentState.activeJob.job_id);
      showToast("Lote cancelado", "warning");
    }
  });
});

// Eventos de Búsqueda y Filtros
let debounceTimer = null;
if (domSearch) {
  domSearch.oninput = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      setState({ searchQuery: domSearch.value.trim(), page: 1 });
      reloadData();
    }, 250);
  };
}

domFilterBtns.forEach((btn) => {
  btn.onclick = () => {
    domFilterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    setState({ filterEstado: btn.dataset.estado, page: 1 });
    reloadData();
  };
});

// Subida de Lote y SSE asociada a la campaña activa
if (domUploadForm) {
  domUploadForm.onsubmit = async (ev) => {
    ev.preventDefault();
    const files = domFileInput.files;
    if (!files || !files.length) return;

    try {
      const uploadRes = await uploadBatch(files, state.activeMedicionId);
      domFileInput.value = "";

      setState({
        activeJob: {
          job_id: uploadRes.job_id,
          total: uploadRes.total,
          status: "processing",
          percent: 0,
          completed: 0,
        },
      });

      subscribeBatchEvents(
        uploadRes.job_id,
        (eventData) => {
          setState({ activeJob: eventData });
          if (eventData.completed > 0) {
            reloadData();
          }
        },
        () => {
          reloadData();
        },
        () => {
          reloadData();
        }
      );
    } catch (e) {
      alert("Error iniciando subida masiva: " + e.message);
    }
  };
}

// Cargar Caso Demo
if (domDemoBtn) {
  domDemoBtn.onclick = async () => {
    const c = await createDemoCaso();
    await reloadData();
    setState({ activeId: c.caso_id, activeCaso: c, activeTab: "dobles" });
  };
}

// Paginación en lista
document.addEventListener("click", (e) => {
  const prevBtn = e.target.closest(".page-prev");
  const nextBtn = e.target.closest(".page-next");
  if (prevBtn) {
    if (state.page > 1) {
      setState({ page: state.page - 1 });
      reloadData();
    }
  } else if (nextBtn) {
    if (state.page < state.totalPages) {
      setState({ page: state.page + 1 });
      reloadData();
    }
  }
});

// Theme Toggle (Dark / Light) con persistencia
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("app-theme", next);
}

if (domThemeBtn) {
  domThemeBtn.onclick = toggleTheme;
}

// Spotlight cursor effect en panel de carga
if (domUploadPanel) {
  domUploadPanel.onmousemove = (e) => {
    const rect = domUploadPanel.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    domUploadPanel.style.setProperty("--mouse-x", `${x}px`);
    domUploadPanel.style.setProperty("--mouse-y", `${y}px`);
  };
}

// Command Palette (Cmd + K)
function openCommandPalette() {
  if (!domCmdPalette) return;
  domCmdPalette.style.display = "flex";
  if (domCmdSearchInput) {
    domCmdSearchInput.value = "";
    domCmdSearchInput.focus();
  }
}

function closeCommandPalette() {
  if (!domCmdPalette) return;
  domCmdPalette.style.display = "none";
}

if (domBtnOpenCmd) domBtnOpenCmd.onclick = openCommandPalette;
if (domBtnCloseCmd) domBtnCloseCmd.onclick = closeCommandPalette;
if (domCmdPalette) {
  domCmdPalette.onclick = (e) => {
    if (e.target === domCmdPalette) closeCommandPalette();
  };
}

// Atajos globales de teclado
window.addEventListener("keydown", (e) => {
  // Cmd+K o Ctrl+K -> Command Palette
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (domCmdPalette && domCmdPalette.style.display === "flex") {
      closeCommandPalette();
    } else {
      openCommandPalette();
    }
  }
  // Escape -> cerrar Command Palette
  if (e.key === "Escape" && domCmdPalette && domCmdPalette.style.display === "flex") {
    closeCommandPalette();
  }
  // Cmd+T -> Alternar tema
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "t") {
    e.preventDefault();
    toggleTheme();
  }
  // Cmd+E -> Descargar Excel
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "e") {
    const excelBtn = document.querySelector(".btn-excel");
    if (excelBtn) {
      e.preventDefault();
      excelBtn.click();
    }
  }
});

// Acciones dentro de Command Palette
if (domCmdResults) {
  domCmdResults.addEventListener("click", async (e) => {
    const item = e.target.closest(".cmd-item");
    if (!item) return;
    const action = item.dataset.action;
    closeCommandPalette();

    if (action === "export-excel") {
      downloadOfficialFile("/api/excel", "Baterias_Psicosociales_Maestro.xlsx").catch((err) =>
        showToast(err.message, "error")
      );
    } else if (action === "filter-dobles") {
      const btn = document.querySelector('.filter-pill[data-estado="doble_marca"]');
      if (btn) btn.click();
    } else if (action === "load-demo") {
      if (domDemoBtn) domDemoBtn.click();
    } else if (action === "toggle-theme") {
      toggleTheme();
    }
  });
}

// Inicialización del badge de motor OCR
async function initOcrBadge() {
  const labelEl = document.getElementById("ocr-engine-label");
  const badgeEl = document.getElementById("ocr-engine-badge");
  if (!labelEl) return;
  try {
    const info = await fetchOcrEngines();
    const active = info.active_engine;
    let label = "Motor: ";
    if (active === "apple_vision") {
      label += "Apple Vision (macOS)";
    } else if (active === "rapid_ocr_onnx") {
      label += "RapidOCR ONNX (Linux / EC2)";
    } else if (active === "aws_textract") {
      label += "AWS Textract (Cloud EC2)";
    } else if (active === "easy_ocr") {
      label += "EasyOCR (PyTorch)";
    } else if (active === "tesseract") {
      label += "Tesseract 5 (spa)";
    } else {
      label += active;
    }
    labelEl.textContent = label;
    if (badgeEl) {
      badgeEl.title = `SO: ${info.os} (${info.arch}) · Preferencia configurada: ${info.configured_preference}`;
    }
  } catch (e) {
    labelEl.textContent = "Motor OCR Activo";
  }
}

// --------------------------------------------------------------------------
// Lógica de Autenticación y Control de la Pantalla de Login Obligatoria
// --------------------------------------------------------------------------
function showLoginScreen() {
  if (domAppShell) domAppShell.style.display = "none";
  if (domLoginViewport) {
    domLoginViewport.classList.remove("fade-out");
    domLoginViewport.style.display = "flex";
  }
  if (domLoginErrorBox) domLoginErrorBox.style.display = "none";
  if (domLoginPass) domLoginPass.value = "";
  if (domBtnLoginSubmit) domBtnLoginSubmit.disabled = false;
  if (domBtnLoginText) domBtnLoginText.textContent = "Iniciar Sesión";
}

function hideLoginScreen() {
  if (domLoginViewport) {
    domLoginViewport.classList.add("fade-out");
    domLoginViewport.style.display = "none";
  }
  if (domAppShell) {
    domAppShell.style.display = "block";
  }
}

async function performLogin(email, password) {
  if (!email || !password) return;
  if (domBtnLoginSubmit) {
    domBtnLoginSubmit.disabled = true;
    if (domBtnLoginText) domBtnLoginText.textContent = "Autenticando...";
  }
  if (domLoginErrorBox) domLoginErrorBox.style.display = "none";

  try {
    const user = await loginUser(email, password);

    // Recordar credenciales si la casilla está marcada
    if (domCheckRememberMe && domCheckRememberMe.checked) {
      localStorage.setItem("sst_remember_email", email);
    } else {
      localStorage.removeItem("sst_remember_email");
    }

    const nextView = getDefaultViewForRole(user.rol);
    setState({ currentUser: user, activeView: nextView });
    hideLoginScreen();
    showToast(`Bienvenido/a, ${user.nombre_completo || user.nombre}`, "success");
    await loadInitialPlatformData();
  } catch (err) {
    if (domLoginErrorBox) {
      domLoginErrorBox.style.display = "flex";
      if (domLoginErrorText) {
        domLoginErrorText.textContent = err.message || "Credenciales incorrectas. Verifique su correo o contraseña.";
      }
    }
    showToast(err.message || "Credenciales incorrectas", "error");
  } finally {
    if (domBtnLoginSubmit) {
      domBtnLoginSubmit.disabled = false;
      if (domBtnLoginText) domBtnLoginText.textContent = "Iniciar Sesión";
    }
  }
}

// Carga completa de entidades, mediciones y cuadernillos una vez autenticado
async function loadInitialPlatformData() {
  try {
    const emps = await fetchEmpresas();
    const saved = readSavedContext(state.currentUser);
    const savedEmpOk = Boolean(saved?.empresaId && emps.some((e) => e.id === saved.empresaId));
    const activeEmpId = savedEmpOk ? saved.empresaId : null;
    let meds = [];
    let activeMedId = null;

    if (activeEmpId) {
      meds = await fetchMediciones(activeEmpId);
      if (saved?.medicionId && meds.some((m) => m.id === saved.medicionId)) {
        activeMedId = saved.medicionId;
      }
    }

    setState({
      empresas: emps,
      activeEmpresaId: activeEmpId,
      mediciones: meds,
      activeMedicionId: activeMedId,
    });

    await initOcrBadge();
    await reloadData();
  } catch (err) {
    console.error("Error cargando datos de plataforma:", err);
    await reloadData();
  }
}

// Inicialización de la aplicación completa con verificación estricta de sesión
async function initApp() {
  // Pre-llenar correo recordado si existe
  const remembered = localStorage.getItem("sst_remember_email");
  if (remembered && domLoginEmail) {
    domLoginEmail.value = remembered;
    if (domCheckRememberMe) domCheckRememberMe.checked = true;
  }

  try {
    const me = await fetchMe();
    if (me) {
      const nextView = getDefaultViewForRole(me.rol);
      setState({ currentUser: me, activeView: nextView });
      hideLoginScreen();
      await loadInitialPlatformData();
    } else {
      setState({ currentUser: null });
      showLoginScreen();
    }
  } catch (err) {
    console.error("Error verificando sesión inicial:", err);
    setState({ currentUser: null });
    showLoginScreen();
  }
}

// Listeners del formulario de Login y Acceso Rápido Demo
if (domLoginForm) {
  domLoginForm.onsubmit = async (e) => {
    e.preventDefault();
    const email = domLoginEmail ? domLoginEmail.value.trim() : "";
    const pass = domLoginPass ? domLoginPass.value : "";
    await performLogin(email, pass);
  };
}

if (domDemoRolePills) {
  domDemoRolePills.forEach((pill) => {
    pill.onclick = async () => {
      const email = pill.dataset.email;
      const pass = pill.dataset.pass;
      if (domLoginEmail) domLoginEmail.value = email;
      if (domLoginPass) domLoginPass.value = pass;
      await performLogin(email, pass);
    };
  });
}

if (domBtnTogglePass && domLoginPass) {
  domBtnTogglePass.onclick = () => {
    const isPass = domLoginPass.type === "password";
    domLoginPass.type = isPass ? "text" : "password";
    if (domIconEyeOpen && domIconEyeClosed) {
      domIconEyeOpen.style.display = isPass ? "none" : "block";
      domIconEyeClosed.style.display = isPass ? "block" : "none";
    }
  };
}

if (domBtnLoginTheme) {
  domBtnLoginTheme.onclick = toggleTheme;
}

const mastActions = document.querySelector(".mast-actions");
if (mastActions) bindOfficialDocs(mastActions);

initApp();
