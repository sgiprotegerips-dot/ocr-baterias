/** Recuerda la última empresa + campaña del operador / digitalizador. */

function keyFor(user) {
  return `sst_ctx_${user?.email || "anon"}`;
}

export function readSavedContext(user) {
  try {
    return JSON.parse(localStorage.getItem(keyFor(user)) || "null");
  } catch (e) {
    return null;
  }
}

export function saveContext(user, empresaId, medicionId) {
  localStorage.setItem(
    keyFor(user),
    JSON.stringify({ empresaId: empresaId || null, medicionId: medicionId || null })
  );
}
