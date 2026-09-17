# Reglas del Proyecto — OCR/OMR Batería de Riesgo Psicosocial

1. **Separación Estricta OMR vs OCR**:
   - Las respuestas a las preguntas Likert (Intralaboral, Extralaboral, Estrés) se procesan estrictamente mediante OMR morfológico en OpenCV (coordenadas de celdas, límites de tabla y densidad de tinta).
   - NUNCA intentar hacer OCR para leer las palabras impresas de las opciones ("Siempre", "Nunca") para tabular respuestas.

2. **Invariante Anti-Bleed-Through (Papel Traslúcido)**:
   - Queda prohibido el uso de Otsu local o binarización adaptativa global dentro de celdas Likert individuales sin verificación de tinta oscura, ya que el papel bond escaneado a doble cara trasluce el texto del reverso.
   - El umbral de detección de bolígrafo debe verificar intensidad oscura (`pixel < 150` ante papel blanco > 240) y un umbral de área entre 1.2% y 5.0%.

3. **Invariante de Reordenamiento ADF (Dúplex Inverso)**:
   - Nunca procesar un PDF asumiendo que las páginas escaneadas están en orden físico correlativo. Se debe identificar la página impresa oficial (1..24) y reordenar el cuadernillo antes de asociar ítems y tablas.

4. **Tratamiento de Ambigüedades (Doble Chuleado)**:
   - Si un respondiente marcó dos opciones en un ítem, el motor jamás debe desempatar automáticamente ni asumir una respuesta. Debe registrarse como `status: "ambiguo"`, generar el recorte visual (`crops/`) y requerir la resolución manual de la psicóloga en la interfaz web.

5. **Invariante Psicométrico de Baremos y Completitud**:
   - Una dimensión o cuestionario NUNCA debe marcarse ni mostrarse como "INCOMPLETA" si todos sus ítems esperados fueron respondidos (`n_respondidos == n_esperados`). La etiqueta "Incompleta" se reserva estrictamente para cuando faltan respuestas físicas (`n_respondidos < n_esperados`).
   - Toda calificación de dimensiones extralaborales debe aplicar obligatoriamente los baremos oficiales normativos:
     * **Jefes / Profesionales / Técnicos (Forma A)**: Tabla 17 (Tiempo fuera, Relaciones familiares, Comunicación, Situación económica, Vivienda, Influencia extralaboral, Desplazamiento).
     * **Auxiliares / Operarios (Forma B)**: Tabla 18.
   - En el Cuestionario de Estrés, los 31 ítems corresponden a malestares (riesgo directo). El índice OMR de la columna 3 (*Nunca*) otorga 0 puntos de riesgo, y la columna 0 (*Siempre*) otorga 3 puntos de riesgo (`_raw(choice_index, invert=False, vmax=3)`). Jamás utilizar el índice de columna directo como puntaje sin invertir.

