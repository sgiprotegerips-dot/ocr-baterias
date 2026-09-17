/**
 * state.js - Estado centralizado reactivo de la aplicación.
 */

export const state = {
  casos: [],
  total: 0,
  page: 1,
  pageSize: 50,
  totalPages: 1,
  activeId: null,
  activeCaso: null,
  activeTab: "datos", // datos, dobles, visor, baremos
  visorPage: 1,
  searchQuery: "",
  filterEstado: "todos",
  filterForma: "todas",
  stats: {
    total: 0,
    listos: 0,
    faltan_datos: 0,
    doble_marca: 0,
    riesgo_dist: {},
  },
  currentUser: null,
  empresas: [],
  activeEmpresaId: null,
  mediciones: [],
  activeMedicionId: null,
  activeMedicion: null,
  psicologas: [],
  activeView: "workspace", // "workspace" | "informe"
  activeInforme: null,
  activeJob: null,
  activeEventSource: null,
  listeners: [],
};

export function setState(patch) {
  Object.assign(state, patch);
  for (const fn of state.listeners) {
    try {
      fn(state);
    } catch (e) {
      console.error("Error en listener de estado", e);
    }
  }
}

export function subscribeState(fn) {
  state.listeners.push(fn);
  return () => {
    state.listeners = state.listeners.filter((l) => l !== fn);
  };
}
