# Sala de Lectura Masiva — OCR/OMR Batería de Riesgo Psicosocial (Colombia)

Plataforma de alta precisión para el procesamiento masivo de la Batería de Instrumentos para la Evaluación de Factores de Riesgo Psicosocial del Ministerio de la Protección Social / Universidad Javeriana (Resolución 2646 de 2008 y Resolución 2764 de 2022).

Capaz de procesar lotes de **hasta 1000 cuadernillos físicos escaneados** en segundo plano con control de concurrencia, reporte de progreso en tiempo real (Server-Sent Events) y una interfaz web clínica para validación psicométrica.

---

##  Arquitectura y Tecnologías Incorporadas

1. **Motor OCR Multimodelo de Alta Velocidad**:
   - **Apple Vision Framework (Nativo macOS arm64)**: Máxima velocidad y precisión en manuscritos en español (nombres, cargos, fechas, firmas).
   - **RapidOCR (ONNX Runtime - Redes Neuronales Profundas DBNet + SVTR + Clasificador Direccional)**: OCR local, offline y multiplataforma sin requerir GPU pesada.
   - **Tesseract OCR (v5.x)**: Con listas blancas numéricas para lectura de casillas de identificación.
2. **Normalización Automática de Orientación (Anti-Dúplex Invertido 180° y Apaisado)**:
   - Detección automática y enderezamiento de páginas que los alimentadores ADF escanean de cabeza o en reversa.
3. **Reordenamiento Físico ADF (Invariante 24 Páginas)**:
   - Identifica el número de página impreso oficial (1..24) en el pie de página y los encabezados institucionales para reconstruir el cuadernillo en orden correlativo antes de leer las tablas.
4. **OMR Morfológico Inmune a Trasluz (OpenCV)**:
   - Medición estricta de densidad de tinta de bolígrafo (`pixel < 150`), descartando el texto traslúcido del reverso del papel bond.
5. **Gestor de Procesamiento Masivo Asíncrono (Batch Manager)**:
   - `ThreadPoolExecutor` con control de concurrencia para procesar cientos de PDFs sin saturar CPU ni memoria.
   - Streaming SSE (`/api/batch/{job_id}/events`) para visualización fluida de la barra de progreso en el navegador.
6. **Workspace Web para la Psicóloga Evaluadora**:
   - **Métricas Globales (KPIs)**: Total baterías, listos, pendientes de datos, dobles marcas, alertas de riesgo alto/muy alto.
   - **Bandeja Inteligente**: Búsqueda por cédula/nombre/cargo, filtros rápidos y paginación.
   - **Resolución de Dobles Chuleados**: Recortes visuales de alta resolución (`crops/`) para decisión manual con auditoría obligatoria.
   - **Visor Interactivo del Cuadernillo**: Inspección en pantalla de cualquiera de las 24 páginas del PDF original.
   - **Baremos Villalobos**: Cálculo automático de puntajes brutos, transformados (T) y baremos cualitativos por dominio y dimensión.
   - **Excel Maestro**: Generación de libro XLSX con 6 hojas (Resumen, Items Intra, Items Extra, Items Estrés, Dimensiones y Páginas).

---

##  Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

# 2. Tesseract con modelo español (Homebrew en Mac):
# brew install tesseract tesseract-lang
```

---

##  Inicio de la Aplicación Web

```bash
.venv/bin/python run.py
# o mediante uvicorn directamente:
.venv/bin/uvicorn app.web:app --host 127.0.0.1 --port 8000 --reload
```

Abra su navegador en **http://127.0.0.1:8000**.

---

## ️ Uso por CLI (Lotes por Consola)

```bash
# Procesar una carpeta con cientos de PDFs:
.venv/bin/python -m src.bateria.cli "/ruta/a/carpeta_pdfs" -o out

# O un solo archivo:
.venv/bin/python -m src.bateria.cli "baterias de prueba/orlando20260912_13042032.pdf" -o out
```

---

##  Pruebas Automatizadas

```bash
PYTHONPATH=. .venv/bin/python tests/test_pipeline_and_web.py
```
