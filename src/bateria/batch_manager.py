"""Gestor asíncrono de procesamiento por lotes (Batch Manager) para lectura masiva.

Permite procesar de 1 a 1000 cuadernillos en segundo plano con control de concurrencia,
reporte de progreso en tiempo real mediante Server-Sent Events (SSE), reintentos y
cancelación segura.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Callable, Dict, List, Optional

from .export import export_workbook
from .pipeline import process_pdf
from .store import load_all, save_caso

logger = logging.getLogger("bateria.batch")


@dataclass
class BatchJob:
    job_id: str
    file_paths: List[Path]
    out_dir: Path
    casos_dir: Path
    total: int
    completed: int = 0
    failed: int = 0
    current_file: str = ""
    percent: float = 0.0
    status: str = "queued"  # queued, processing, completed, cancelled, error
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    results: List[dict] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)
    cancelled: bool = False
    medicion_id: Optional[str] = None
    _listeners: List[asyncio.Queue] = field(default_factory=list)


import gc
import os
import threading


class BatchManager:
    """Singleton para gestionar colas de procesamiento masivo en segundo plano."""

    def __init__(self, max_workers: Optional[int] = None):
        if max_workers is None:
            env_w = os.getenv("BATCH_MAX_WORKERS") or os.getenv("WORKERS")
            if env_w:
                try:
                    self.max_workers = max(1, int(env_w))
                except ValueError:
                    self.max_workers = 4
            else:
                self.max_workers = min(8, max(2, (os.cpu_count() or 2)))
        else:
            self.max_workers = max_workers

        self.jobs: Dict[str, BatchJob] = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(2, self.max_workers), thread_name_prefix="bateria-batch"
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()

    def create_batch(
        self,
        file_paths: List[Path],
        out_dir: Path,
        casos_dir: Path,
        medicion_id: Optional[str] = None,
    ) -> BatchJob:
        """Crea e inicializa un nuevo lote de procesamiento masivo."""
        job_id = uuid.uuid4().hex[:12]
        job = BatchJob(
            job_id=job_id,
            file_paths=file_paths,
            out_dir=out_dir,
            casos_dir=casos_dir,
            total=len(file_paths),
            medicion_id=medicion_id,
        )
        self.jobs[job_id] = job
        return job

    def start_batch_async(self, job: BatchJob, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Inicia la ejecución del lote en el pool de subprocesos."""
        self._loop = loop
        job.status = "processing"
        self._notify_listeners(job)
        self.executor.submit(self._run_batch, job)

    def _notify_listeners(self, job: BatchJob):
        """Envía el estado actual a todos los clientes SSE suscritos."""
        if not job._listeners:
            return

        payload = self.get_job_status(job.job_id)
        msg = json.dumps(payload, ensure_ascii=False)

        for q in list(job._listeners):
            try:
                if self._loop and not self._loop.is_closed() and self._loop.is_running():
                    self._loop.call_soon_threadsafe(q.put_nowait, msg)
                else:
                    q.put_nowait(msg)
            except Exception:
                pass

    def _run_batch(self, job: BatchJob):
        """Ejecuta el procesamiento masivo concurrente en paralelo sobre los CPUs del servidor."""
        logger.info(
            f"Iniciando lote {job.job_id} con {job.total} archivos en paralelo (workers={self.max_workers})."
        )

        batches_dir = job.out_dir / "batches"
        batches_dir.mkdir(parents=True, exist_ok=True)

        def _process_single(pdf_path: Path):
            if job.cancelled:
                return ("cancelled", pdf_path.name, None)
            try:
                raw_res = process_pdf(pdf_path, out_dir=job.out_dir)
                raw_res["psicologa"] = ""
                if job.medicion_id:
                    raw_res["medicion_id"] = job.medicion_id
                saved = save_caso(job.casos_dir, raw_res)
                return ("ok", pdf_path.name, saved)
            except Exception as e:
                logger.exception(f"Error procesando {pdf_path.name}: {e}")
                return ("error", pdf_path.name, str(e))

        # Procesar con ThreadPoolExecutor paralelo para aprovechar todos los núcleos de CPU en EC2
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="bateria-file-worker"
        ) as file_pool:
            future_to_file = {file_pool.submit(_process_single, p): p for p in job.file_paths}

            for future in concurrent.futures.as_completed(future_to_file):
                pdf_p = future_to_file[future]
                if job.cancelled:
                    break

                try:
                    status, fname, data = future.result()
                except Exception as e:
                    status, fname, data = ("error", pdf_p.name, str(e))

                with self._lock:
                    job.current_file = fname
                    if status == "ok":
                        job.results.append(data)
                        job.completed += 1
                    elif status == "error":
                        job.errors.append({"archivo": fname, "error": str(data)})
                        job.failed += 1

                    processed = job.completed + job.failed
                    job.percent = round((processed / max(1, job.total)) * 100.0, 1)

                self._notify_listeners(job)

        job.end_time = time.time()
        if not job.cancelled:
            job.status = "completed"
        job.current_file = ""
        job.percent = 100.0

        # Auto-actualizar libro maestro de Excel al finalizar lote
        try:
            excel_path = job.out_dir / "respuestas.xlsx"
            export_workbook(load_all(job.casos_dir), excel_path)
        except Exception as e:
            logger.error(f"Error exportando Excel maestro: {e}")

        # Persistir estado final del lote en disco
        try:
            status_payload = self.get_job_status(job.job_id)
            if status_payload:
                (batches_dir / f"{job.job_id}.json").write_text(
                    json.dumps(status_payload, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception as e:
            logger.error(f"Error guardando estado de lote: {e}")

        # Limpieza de memoria explícita para lotes masivos de 1000 PDFs en servidores
        gc.collect()

        self._notify_listeners(job)
        logger.info(f"Lote {job.job_id} finalizado: {job.completed} exitosos, {job.failed} errores.")

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Obtiene una instantánea JSON del estado del lote (memoria o disco)."""
        job = self.jobs.get(job_id)
        if job:
            elapsed = (job.end_time or time.time()) - job.start_time
            return {
                "job_id": job.job_id,
                "status": job.status,
                "total": job.total,
                "completed": job.completed,
                "failed": job.failed,
                "current_file": job.current_file,
                "percent": job.percent,
                "elapsed_seconds": round(elapsed, 1),
                "cancelled": job.cancelled,
                "n_results": len(job.results),
                "n_errors": len(job.errors),
            }

        # Intentar cargar desde disco
        b_file = Path("out/batches") / f"{job_id}.json"
        if b_file.exists():
            try:
                return json.loads(b_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def cancel_batch(self, job_id: str) -> bool:
        """Cancela un lote en curso."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        job.cancelled = True
        job.status = "cancelled"
        self._notify_listeners(job)
        return True

    async def stream_events(self, job_id: str) -> AsyncGenerator[str, None]:
        """Generador asíncrono para streaming de eventos SSE hacia la UI."""
        job = self.jobs.get(job_id)
        if not job:
            yield json.dumps({"error": "Lote no encontrado"})
            return

        q = asyncio.Queue()
        job._listeners.append(q)

        # Enviar estado inicial inmediato
        yield json.dumps(self.get_job_status(job_id))

        try:
            while True:
                data = await q.get()
                yield data
                parsed = json.loads(data)
                if parsed.get("status") in ("completed", "cancelled", "error"):
                    break
        finally:
            if q in job._listeners:
                job._listeners.remove(q)


# Instancia global del gestor de lotes
batch_manager = BatchManager()
