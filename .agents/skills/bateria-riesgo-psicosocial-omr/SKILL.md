---
name: bateria-riesgo-psicosocial-omr
description: >-
  Pipeline especializado en visión por computador (OMR) y OCR para la Batería de Instrumentos
  de Factores de Riesgo Psicosocial (Ministerio de la Protección Social de Colombia / Universidad Javeriana).
  Usa esta skill para procesar PDF escaneados, reordenar páginas duplex de escáneres ADF, segmentar tablas
  Likert de 4 y 5 columnas, detectar marcas manuscritas rechazando bleed-through de papel traslúcido, extraer
  cédula y datos demográficos, y tabular puntajes transformados (Villalobos).
---

# Pipeline OMR/OCR — Batería de Riesgo Psicosocial (Colombia)

Esta guía documenta la lógica y arquitectura para la extracción precisa y sin falsos positivos de baterías de riesgo psicosocial diligenciadas a mano.

## 1. Estructura Estándar del Cuadernillo (24 Páginas)

Toda batería física completa aplicada en Colombia bajo la resolución oficial consta de 24 páginas correlativas:
- **Pág 1**: Consentimiento Informado (Nombre, Cargo, Área, Cédula, Fecha).
- **Págs 2–5**: Ficha de Datos Generales (Preguntas 1 a 24).
- **Pág 6**: Portada Cuestionario Intralaboral + Recuadro Cédula/ID respondiente + Fecha.
- **Pág 7**: Instrucciones Intralaboral (declara FORMA A o FORMA B).
- **Págs 8–16**: Ítems Intralaborales (Forma A: ítems 1–105; Forma B: ítems 1–88).
- **Pág 17**: Sección Jefatura / Clientes (Forma A: ítems 106–123; Forma B: servicio clientes / fin).
- **Pág 18**: Portada Cuestionario Extralaboral + Recuadro ID respondiente + Fecha.
- **Pág 19**: Instrucciones Extralaboral.
- **Págs 20–22**: Ítems Extralaborales (31 ítems en 5 opciones Likert).
- **Pág 23**: Portada Cuestionario de Estrés (3.ª versión) + Recuadro ID + Fecha.
- **Pág 24**: Cuestionario de Estrés (31 síntomas en 4 opciones Likert).

## 2. Reordenamiento de Páginas (Escáner ADF Dúplex)

Los escáneres con alimentador automático (ADF) frecuentemente generan PDF donde el reverso viene en orden inverso (`1..12` y `24..13`).
**Procedimiento**:
1. Leer el número de página impreso (`printed_page`) en el pie de página o mediante coincidencia con plantillas de encabezado.
2. Reindexar el documento en memoria para asegurar que se procesa en el orden 1..24.
3. Si faltan páginas en el escaneo, reportar la página física faltante de forma explícita.

## 3. Algoritmo OMR Anti-Bleed-through (OpenCV)

1. **Aislamiento de la tabla**:
   - Detección de contornos con kernel adaptativo según resolución DPI (200 DPI recomendado).
2. **Proyección y segmentación de filas**:
   - Kernel horizontal `(w * 0.1, 1)`. Los picos en la proyección horizontal marcan los límites superior e inferior de cada ítem de forma exacta.
3. **Proyección de columnas Likert**:
   - Kernel vertical `(1, 15)` en el cuadrante derecho. Detecta las 6 líneas divisorias de las 5 opciones Likert (o 5 líneas para Estrés).
4. **Cálculo de densidad de tinta (Rechazo de trasluz)**:
   - Prohibido Otsu local por casilla: el texto del reverso (~220 gris) genera falsos positivos masivos.
   - Umbral de tinta oscura: `cell < 150` (la tinta de esfero baja a 15–90; el papel traslúcido queda en > 210).
   - Margen de seguridad interno (`pad_x = 0.10`, `pad_y = 0.10`) para ignorar las líneas negras de la grilla.
   - Si una celda tiene `fill >= 0.012` (1.2% de tinta oscura) y supera por al menos 2.5x a las demás, se clasifica como marcada (`OK`).
   - Si 2 casillas tienen marcas notables: registrar como `status: "ambiguo"` y guardar recorte para validación de la psicóloga.

## 4. Extracción de Identidad y Cédula (OCR)

- **Cédula / ID**: Aislar por contorno el recuadro negro junto a `Número de identificación del respondiente (ID): [ 80421154 ]` en páginas 2, 6, 18 o 23. Aplicar OCR filtrado estrictamente a dígitos `0123456789`.
- **Campos de Texto**: Extraer los renglones manuscritos de Fecha, Cargo y Dependencia en Consentimiento Informado.

## 5. Puntuación y Baremos Normativos Extralaborales (Tablas 17 y 18)

Para las 7 dimensiones extralaborales, los cortes para clasificar en (Sin riesgo, Bajo, Medio, Alto, Muy alto) son:
- **Jefatura y Profesionales (Forma A)**:
  - Tiempo fuera del trabajo: `(6.3, 25.0, 37.5, 50.0)`
  - Relaciones familiares: `(8.3, 25.0, 33.3, 50.0)`
  - Comunicación y relaciones interpersonales: `(0.9, 10.0, 20.0, 30.0)`
  - Situación económica del grupo familiar: `(8.3, 25.0, 33.3, 50.0)`
  - Características de la vivienda y de su entorno: `(5.6, 11.1, 13.9, 22.2)`
  - Influencia del entorno extralaboral sobre el trabajo: `(8.3, 16.7, 25.0, 41.7)`
  - Desplazamiento vivienda-trabajo-vivienda: `(0.9, 12.5, 25.0, 43.8)`
  - Puntaje Total Extralaboral: `(11.3, 16.9, 22.6, 29.0)`

- **Auxiliares y Operarios (Forma B)**:
  - Tiempo fuera del trabajo: `(6.3, 25.0, 37.5, 50.0)`
  - Relaciones familiares: `(8.3, 25.0, 33.3, 50.0)`
  - Comunicación y relaciones interpersonales: `(5.0, 15.0, 25.0, 35.0)`
  - Situación económica del grupo familiar: `(16.7, 25.0, 41.7, 50.0)`
  - Características de la vivienda y de su entorno: `(5.6, 11.1, 16.7, 27.8)`
  - Influencia del entorno extralaboral sobre el trabajo: `(0.9, 16.7, 25.0, 41.7)`
  - Desplazamiento vivienda-trabajo-vivienda: `(0.9, 12.5, 25.0, 43.8)`
  - Puntaje Total Extralaboral: `(12.9, 17.7, 24.2, 32.3)`

