/**
 * Apertura/descarga de documentos con la cookie de sesión.
 * Los <a target=_blank> y <a download> nativos no siempre envían HttpOnly
 * (Safari / pestaña nueva) y el Excel no se guarda.
 */

import { showToast } from "./components/toast.js";

export async function openOfficialHtml(url) {
  const win = window.open("", "_blank", "noopener");
  if (!win) {
    showToast("Permita ventanas emergentes para visualizar los informes.", "error");
    return;
  }
  win.document.open();
  win.document.write(`
    <!doctype html><html lang="es"><head><meta charset="utf-8"><title>Cargando informe...</title>
    <style>body{font-family:sans-serif;padding:20px;text-align:center;}</style></head>
    <body><h3>Cargando documento...</h3><p>Espere por favor.</p></body></html>
  `);
  win.document.close();

  try {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
      throw new Error(err.detail || "No se pudo abrir el documento oficial");
    }
    const html = await res.text();
    win.document.open();
    win.document.write(html);
    win.document.close();
  } catch (err) {
    win.close();
    throw err;
  }
}

export async function downloadOfficialFile(url, fallbackName) {
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
    throw new Error(err.detail || "No se pudo descargar el archivo");
  }
  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  const match = /filename\*?=(?:UTF-8''|")?([^\";]+)"?/i.exec(cd);
  const name = match ? decodeURIComponent(match[1].replace(/"/g, "")) : fallbackName;
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 4000);
}

export function bindOfficialDocs(container) {
  if (!container) return;
  container.querySelectorAll("a[data-open-html]").forEach((el) => {
    el.addEventListener("click", async (ev) => {
      ev.preventDefault();
      try {
        await openOfficialHtml(el.getAttribute("href"));
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  });
  container.querySelectorAll("a[data-download-file]").forEach((el) => {
    el.addEventListener("click", async (ev) => {
      ev.preventDefault();
      try {
        await downloadOfficialFile(el.getAttribute("href"), el.dataset.downloadFile || "documento.xlsx");
        showToast("Descarga iniciada", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  });
}
