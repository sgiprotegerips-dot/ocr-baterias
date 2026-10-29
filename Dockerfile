# ==============================================================================
# Dockerfile de Producción 100% Self-Hosted — Batería de Riesgo Psicosocial (OMR/OCR)
# Compatible con Linux x86_64 y ARM64 (AWS Graviton / EC2 / Debian / Ubuntu)
# 100% Offline: Modelos ONNX pre-empaquetados, Cero llamadas a APIs de pago en la nube
# ==============================================================================

FROM python:3.11-slim as base

# Evitar prompts interactivos durante apt-get y configurar optimización de hilos en CPU
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=2 \
    ONNXRUNTIME_NUM_THREADS=2 \
    OCR_ENGINE=rapidocr

# Instalar dependencias del sistema requeridas para OCR y OpenCV en Linux
# - tesseract-ocr y tesseract-ocr-spa para OCR en español
# - libgl1 y libglib2.0-0 para OpenCV headless
# - poppler-utils para manipulación de PDFs
# - curl para healthchecks del contenedor
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios para ejecución segura
RUN useradd -m -u 1001 -s /bin/bash appuser

WORKDIR /app

# Copiar manifiesto de dependencias e instalar
COPY requirements.txt .

# En entornos de contenedor Linux reemplazamos opencv-python por opencv-python-headless
RUN pip install --upgrade pip setuptools wheel && \
    sed -i 's/opencv-python>=/opencv-python-headless>=/' requirements.txt && \
    pip install -r requirements.txt

# Pre-descargar y pre-calentar los grafos ONNX de RapidOCR en tiempo de build
# Esto asegura que el contenedor arranque 100% offline sin descargas en runtime
RUN python -c "from rapidocr_onnxruntime import RapidOCR; import numpy as np; r = RapidOCR(); r(np.zeros((100, 100, 3), dtype=np.uint8))"

# Copiar código fuente y recursos
ENV OMP_THREAD_LIMIT=1 \
    OMP_NUM_THREADS=1 \
    ONNXRUNTIME_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2 \
    MKL_NUM_THREADS=2
COPY src/ ./src/
COPY app/ ./app/
COPY run.py .

# Crear directorios de datos y salida con permisos para appuser
RUN mkdir -p /app/data/uploads /app/out/casos /app/out/crops /app/out/batches && \
    chown -R appuser:appuser /app

# Cambiar a usuario no root
USER appuser

# Exponer puerto HTTP
EXPOSE 8000

# Healthcheck nativo consultando el endpoint /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio: Uvicorn con ASGI FastAPI
CMD ["python", "run.py"]
