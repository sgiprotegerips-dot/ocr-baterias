/**
 * api.js - Capa de comunicación HTTP y eventos SSE con el backend FastAPI.
 */

export async function fetchCasos(params = {}) {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.estado && params.estado !== "todos") query.set("estado", params.estado);
  if (params.forma && params.forma !== "todas") query.set("forma", params.forma);
  if (params.medicion_id) query.set("medicion_id", params.medicion_id);
  if (params.page) query.set("page", params.page);
  if (params.page_size) query.set("page_size", params.page_size);

  const res = await fetch(`/api/casos?${query.toString()}`);
  if (!res.ok) throw new Error("Error cargando lista de casos");
  return await res.json();
}

export async function fetchCaso(casoId) {
  const res = await fetch(`/api/casos/${casoId}`);
  if (!res.ok) throw new Error("Error cargando detalle del caso");
  return await res.json();
}

export async function uploadBatch(fileList, medicionId = null) {
  const fd = new FormData();
  for (const f of fileList) {
    fd.append("files", f);
  }
  if (medicionId) {
    fd.append("medicion_id", medicionId);
  }
  const res = await fetch("/api/upload", {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error en la subida" }));
    throw new Error(err.detail || "Error en la subida de archivos");
  }
  return await res.json();
}

// ---------------------------------------------------------------------------
// Autenticación y Usuarios
// ---------------------------------------------------------------------------
export async function fetchMe() {
  const res = await fetch("/api/auth/me");
  if (!res.ok) return null;
  const data = await res.json();
  if (data.authenticated && data.user) return data.user;
  return null;
}

export async function loginUser(email, password) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Credenciales inválidas" }));
    throw new Error(err.detail || "Error en inicio de sesión");
  }
  const data = await res.json();
  return data.user || data;
}

export async function logoutUser() {
  const res = await fetch("/api/auth/logout", { method: "POST" });
  return await res.json();
}

export async function fetchPsicologas() {
  const res = await fetch("/api/auth/psicologas");
  if (!res.ok) return [];
  return await res.json();
}

// ---------------------------------------------------------------------------
// Empresas y Mediciones (Campañas SST)
// ---------------------------------------------------------------------------
export async function fetchEmpresas() {
  const res = await fetch("/api/empresas");
  if (!res.ok) throw new Error("Error cargando empresas");
  return await res.json();
}

export async function createEmpresa(data) {
  const res = await fetch("/api/empresas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error registrando empresa" }));
    throw new Error(err.detail || "Error registrando empresa");
  }
  return await res.json();
}

export async function fetchMediciones(empresaId) {
  const res = await fetch(`/api/empresas/${empresaId}/mediciones`);
  if (!res.ok) throw new Error("Error cargando mediciones de la empresa");
  return await res.json();
}

export async function altaClienteOnboarding(data) {
  const res = await fetch("/api/onboarding/cliente", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error en el alta de cliente" }));
    throw new Error(err.detail || "Error en el alta de cliente");
  }
  return await res.json();
}

export async function abrirCampanaOnboarding(data) {
  const res = await fetch("/api/onboarding/campana", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error abriendo la campaña" }));
    throw new Error(err.detail || "Error abriendo la campaña");
  }
  return await res.json();
}

export async function fetchAllMediciones() {
  const res = await fetch("/api/mediciones");
  if (!res.ok) throw new Error("Error cargando campañas");
  return await res.json();
}

export async function createMedicion(empresaId, data) {
  const res = await fetch(`/api/empresas/${empresaId}/mediciones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error creando medición" }));
    throw new Error(err.detail || "Error creando medición");
  }
  return await res.json();
}

// ---------------------------------------------------------------------------
// Informe Diagnóstico y Custodia Legal 20 Años
// ---------------------------------------------------------------------------
export async function fetchInforme(medicionId) {
  const res = await fetch(`/api/mediciones/${medicionId}/informe`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error cargando informe" }));
    throw new Error(err.detail || "Error calculando informe diagnóstico");
  }
  return await res.json();
}

export async function aprobarSellarInforme(medicionId, data) {
  const res = await fetch(`/api/mediciones/${medicionId}/informe/aprobar-sellar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error aprobando informe" }));
    throw new Error(err.detail || "Error aprobando y sellando informe");
  }
  return await res.json();
}

export async function cancelBatch(jobId) {
  const res = await fetch(`/api/batch/${jobId}/cancel`, { method: "POST" });
  return await res.json();
}

export async function saveDatos(casoId, datos) {
  const res = await fetch(`/api/casos/${casoId}/datos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  return await res.json();
}

export async function decideDoble(casoId, ambId, choice, psicologa) {
  const res = await fetch(`/api/casos/${casoId}/decidir`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amb_id: ambId, choice, psicologa }),
  });
  return await res.json();
}

export async function deleteCaso(casoId) {
  const res = await fetch(`/api/casos/${casoId}`, { method: "DELETE" });
  return await res.json();
}

export async function createDemoCaso() {
  const res = await fetch("/api/demo", { method: "POST" });
  return await res.json();
}

export function subscribeBatchEvents(jobId, onMessage, onComplete, onError) {
  const es = new EventSource(`/api/batch/${jobId}/events`);

  es.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      onMessage(data);
      if (data.status === "completed" || data.status === "cancelled" || data.status === "error") {
        es.close();
        if (onComplete) onComplete(data);
      }
    } catch (e) {
      console.error("Error parseando evento SSE", e);
    }
  };

  es.onerror = (err) => {
    console.warn("Evento SSE cerrado o error de red", err);
    es.close();
    if (onError) onError(err);
  };

  return es;
}

export async function fetchNomina(medicionId) {
  const res = await fetch(`/api/mediciones/${medicionId}/nomina`);
  if (!res.ok) throw new Error("Error cargando nómina de la campaña");
  return await res.json();
}

export async function createNominaManual(medicionId, data) {
  const res = await fetch(`/api/mediciones/${medicionId}/nomina`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error guardando ficha" }));
    throw new Error(err.detail || "Error guardando ficha");
  }
  return await res.json();
}

export async function importNominaExcel(medicionId, file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`/api/mediciones/${medicionId}/nomina/import`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error importando Excel" }));
    throw new Error(err.detail || "Error importando Excel");
  }
  return await res.json();
}

export async function fetchNominaPrintHtml(medicionId, cedulas = null) {
  const res = await fetch(`/api/mediciones/${medicionId}/nomina/print-html`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cedulas }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error generando etiquetas" }));
    throw new Error(err.detail || "Error generando etiquetas");
  }
  return await res.text();
}

export async function fetchOneLabelHtml(medicionId, cedula) {
  const res = await fetch(`/api/mediciones/${medicionId}/nomina/${encodeURIComponent(cedula)}/etiqueta.html`);
  if (!res.ok) throw new Error("Error generando la etiqueta");
  return await res.text();
}

export async function deleteNominaRow(medicionId, cedula) {
  const res = await fetch(`/api/mediciones/${medicionId}/nomina/${encodeURIComponent(cedula)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Error eliminando de la nómina");
  return await res.json();
}

export async function fetchOcrEngines() {
  const res = await fetch("/api/ocr/engines");
  if (!res.ok) throw new Error("Error consultando motores OCR");
  return await res.json();
}

export async function fetchOcrBenchmark() {
  const res = await fetch("/api/ocr/benchmark");
  if (!res.ok) throw new Error("Error ejecutando benchmark OCR");
  return await res.json();
}

// ---------------------------------------------------------------------------
// Administración de Plataforma, Usuarios y Auditoría
// ---------------------------------------------------------------------------
export async function fetchAdminUsers() {
  const res = await fetch("/api/admin/users");
  if (!res.ok) throw new Error("Error consultando usuarios");
  return await res.json();
}

export async function createAdminUser(data) {
  const res = await fetch("/api/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error creando usuario" }));
    throw new Error(err.detail || "Error registrando usuario");
  }
  return await res.json();
}

export async function updateAdminUser(userId, data) {
  const res = await fetch(`/api/admin/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error actualizando usuario" }));
    throw new Error(err.detail || "Error actualizando usuario");
  }
  return await res.json();
}

export async function fetchAdminAuditLogs(limit = 100) {
  const res = await fetch(`/api/admin/audit-logs?limit=${limit}`);
  if (!res.ok) throw new Error("Error consultando logs de auditoría");
  return await res.json();
}

export async function fetchAdminStats() {
  const res = await fetch("/api/admin/stats");
  if (!res.ok) throw new Error("Error consultando estadísticas del sistema");
  return await res.json();
}

export async function updateMedicionEstado(medicionId, estado) {
  const res = await fetch(`/api/mediciones/${medicionId}/estado`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ estado }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error actualizando estado de medición" }));
    throw new Error(err.detail || "Error actualizando estado de medición");
  }
  return await res.json();
}

