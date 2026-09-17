# Matriz de Diagnóstico y Consulta por Tipo de Negocio

Antes de escribir una sola línea de código CSS, Tailwind o JSX, el agente o diseñador DEBE consultar y determinar el tipo de negocio y su arquetipo proyectado.

---

## 1. El Cuestionario de Diagnóstico Obligatorio (4 Preguntas Clave)

Cuando un usuario solicite crear o rediseñar una interfaz, ejecuta este diagnóstico:

### Pregunta 1: Densidad y Frecuencia de Lectura de Datos
- **Alta / Crítica (Telemetry / Cyber / Mission Control)**: Operadores, ingenieros, analistas financieros o personal de salud que monitorean decenas de métricas simultáneas en tiempo real. Cero espacio para márgenes excesivos o elementos decorativos grandes.
- **Media / Equilibrada (Swiss Modern / Bento Grid)**: Administradores B2B, gestores de proyectos, directores de RRHH o SST. Requieren equilibrio entre visualización de KPIs, tablas paginadas y acciones directas.
- **Baja / Contemplativa (Dark Luxury / Spatial UI / Glassmorphism)**: Portafolios ejecutivos, e-commerce de alta gama, presentaciones a inversores, dashboards ejecutivos C-Level.

### Pregunta 2: Consecuencia del Error en la Acción del Usuario
- **Riesgo Vital o Financiero Irreversible**: (Ej. emisión de órdenes de compra millonarias, diagnóstico médico, activación de maquinaria pesada).
  - *Regla*: Prohibido el uso de Glassmorphism en botones de confirmación. Requiere contrastes absolutos (WCAG AAA), estados explícitos de foco y diálogos de doble paso con texto monoespaciado de verificación.
- **Riesgo Operativo Moderado**: (Ej. reclasificación de encuestas, edición de registros de clientes, configuración de permisos).
  - *Regla*: Diálogos modales con fondo oscurecido, micro-animaciones de confirmación no destructivas, botones con jerarquía primaria/secundaria/peligro claramente codificada.
- **Riesgo Bajo / Exploratorio**: (Ej. navegación de contenido, dashboards de lectura, visualización de tendencias).
  - *Regla*: Alta libertad para transiciones fluidas, Bento Grid interactivo, tarjetas con spotlight dinámico.

### Pregunta 3: Postura de Marca y Personalidad Visual
- **Confianza Institucional / Solidez Corporativa** → *Swiss Modern / Bento Grid*.
- **Vanguardia Tecnológica / DevTools / Ciberdefensa** → *High-Density Cyber / Telemetry*.
- **Exclusividad / Sofisticación Silenciosa** → *Dark Luxury / Obsidian Minimalism*.
- **Fluidez Digital / Futuro Espacial** → *Glassmorphism Refinado / Spatial UI (visionOS)*.
- **Expresividad Cruda / Editorial Disruptivo** → *Neo-Brutalism Refinado*.

### Pregunta 4: Entorno Físico y Hardware de Despliegue
- **Monitores de Oficina / Laptops (100% control de iluminación)**: Fondos claros neutros (`#FAFAFA`) o modo oscuro coordinado.
- **Pantallas en Planta Industrial / Almacén (Luz directa o reflejos)**: Fondos de máximo contraste, hitboxes de interacción grandes (mínimo 44px), tipografía grotesca bold.
- **Salas de Control / Trading Desks (Poca luz, múltiples pantallas)**: Fondos oscuros profundos (`#0A0A0A`), acentos de color limitados a datos de estado (verde, ámbar, rojo).

---

## 2. Matriz de Correspondencia: Negocio vs. Modelo Proyectado

| Industria / Tipo de Negocio | Modelo Proyectado Primario | Modelo Secundario / Acento | Justificación de Negocio |
| :--- | :--- | :--- | :--- |
| **Fintech B2B / Banca / Pagos** | **Swiss Modern** | **Bento Grid** | Proyecta precisión matemática, orden y seguridad. Elimina cualquier duda visual sobre transacciones y saldos. |
| **B2B SaaS / ERP / Gestión Operativa** | **Bento Grid** | **Swiss Modern** | Agrupa flujos de trabajo complejos en bloques legibles. Reduce la fatiga visual en jornadas de 8 horas. |
| **Ciberseguridad / DevTools / Cloud Ops** | **High-Density Cyber / Telemetry** | **Dark Luxury** | Los ingenieros exigen alta densidad, números tabulares alineados, rejillas técnicas y retroalimentación instantánea. |
| **Salud / Clínicas / SST / Riesgo Psicosocial** | **Swiss Modern (Alto Contraste)** | **Bento Grid Técnico** | Tolerancia cero a interpretaciones erróneas. Requiere fondos limpios, estados semánticos inequívocos y legibilidad instantánea. |
| **E-commerce de Alta Gama / Real Estate** | **Dark Luxury** | **Spatial UI** | El producto es el protagonista. La UI debe retirarse a un segundo plano con negros obsidian, tipografía fina y bordes de 0.5px. |
| **Logística / Cadena de Suministro** | **Brutalismo Funcional** | **High-Density Telemetry** | Interfaz resistente a la fatiga del operario. Botones robustos, etiquetas claras, sin decoraciones etéreas. |
| **AI Consumer / Web3 / Plataformas Creativas** | **Glassmorphism Refinado** | **Aurora Mesh** | Transmite innovación, liquidez algorítmica y dimensionalidad espacial contemporánea. |
| **Media / Editorial / Agencias de Diseño** | **Neo-Brutalism Refinado** | **Bento Grid** | Comunica voz propia, audacia visual y carácter autoral sin caer en plantillas de IA repetitivas. |

---

## 3. Ejemplo de Diálogo de Consulta con el Usuario

Cuando el usuario pida: *"Diseña el módulo de usuarios para mi aplicación"*, el agente debe responder formulando la alineación antes de generar código:

```markdown
Para diseñar una interfaz de usuarios no genérica y con alto valor funcional, definamos la proyección visual según su tipo de negocio:

1. ¿Se trata de un panel corporativo/administrativo (donde aplicaremos **Swiss Modern + Bento Grid** para máxima claridad y velocidad de escaneo)?
2. ¿Es un entorno técnico u operativo (donde utilizaremos **High-Density Telemetry** con rejilla compacta y status pills)?
3. ¿O busca una experiencia inmersiva ejecutiva (donde integraremos **Glassmorphism Refinado** con bordes especulares y efecto aero)?

Indíqueme su preferencia o confirme el contexto para aplicar los tokens visuales exactos.
```
