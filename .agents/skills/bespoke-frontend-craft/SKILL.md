---
name: bespoke-frontend-craft
description: >-
  Diseño y arquitectura de interfaces web frontend modernas, profesionales y no genéricas (anti-AI-slop),
  con módulos lógicos adaptados al tipo de negocio y consulta interactiva del modelo proyectado
  (Glassmorphism, Bento Grid, Neumorphism, Claymorphism, Modern Skeuomorphism/Spatial UI, Dark Luxury,
  Cyber/Telemetry HUD, Neo-Brutalism, Swiss Modern, Aurora Mesh).
  Cubre menús avanzados (sidebars colapsables, Cmd+K, floating docks, mega-menús), animaciones cinemáticas
  serias (GSAP, Framer Motion, CSS Grid 0fr->1fr), micro-interacciones de alta fidelidad,
  estricta regla CERO EMOJIS (solo iconografía SVG profesional Lucide/Radix/Phosphor) y balance visual 60-30-10.
---

# Bespoke Frontend Craft — Arquitectura Visual Profesional y No Genérica

Esta habilidad guía la creación de interfaces de usuario modernas, de alto nivel y con identidad propia, erradicando los clichés genéricos de plantillas de IA (AI slop, fondos violeta genéricos, tarjetas flotantes sin sentido, interfaces infantiles o emojis en paneles corporativos).

---

## 1. Principios Fundamentales e Invariantes

### Invariante 1: Regla Absoluta Anti-Emojis
- **PROHIBIDO**: Insertar emojis (``, ``, ``, ``, `️`, ``, ``, ``, ``, ``, etc.) en menús, botones, encabezados, estados o badges.
- **OBLIGATORIO**: Utilizar iconografía técnica vectorial limpia (**Lucide React**, **Phosphor Icons**, **Radix Icons** o **Heroicons**).
- El trazo (`strokeWidth`) debe ser consistente en todo el sistema (ej. `1.5px` para interfaces ejecutivas o `1.75px` para dashboards operativos).
- Los estados semánticos se representan mediante **píldoras con puntos de estado (status dots de 6px)** con anillo de dispersión, jamás con caritas ni símbolos emoji.

### Invariante 2: Separación de Responsabilidades y Arquitectura Modular
Debe integrarse de forma estricta con la habilidad `component-architecture`:
1. **Fórmulas y Cálculos → `src/lib/`**: Cero lógica matemática o transformaciones inline en el JSX.
2. **Componentes Delgados**: Límite de ~150-200 líneas por archivo. Dividir en `modulo/`, `ui/` primitivos y `layout/`.
3. **Páginas Orquestadoras**: Las rutas de páginas solo orquestan datos y componen vistas modulares.
4. **Tipos Centralizados**: Cero tipos `any`. Todos los modelos en `src/types/`.

### Invariante 3: Balance Visual Armónico (Regla 60-30-10)
- **60% Fondo y Superficie Neutra**: Canvas limpios (`#0A0A0A` en dark mode, `#FAFAFA` o `#FFFFFF` en light mode).
- **30% Estructura y Superficie Secundaria**: Tarjetas, paneles divisores, tipografía de cuerpo, bordes hairline (`neutral-800` / `slate-200`).
- **10% Acento Focal Intencional**: Reservado exclusivamente para estados activos, CTAs primarios y datos críticos. Prohibido pintar toda la interfaz con colores de acento.

---

## 2. Protocolo de Diagnóstico y Consulta por Tipo de Negocio

**NUNCA asumas el diseño a ciegas.** Antes de iniciar un desarrollo frontend, consulta o analiza el contexto del negocio según la matriz:

```
                  ┌─────────────────────────────────────┐
                  │    Diagnóstico de Tipo de Negocio   │
                  └──────────────────┬──────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   Densidad & Velocidad      Criticidad de Error       Postura de Marca
   - Telemetry (Crítica)     - Vital/Financiero (AAA)  - Institucional (Swiss)
   - Swiss/Bento (Media)     - Operativo (Modal/Step)  - Tech/Cyber (Dark/HUD)
   - Luxury (Contemplativa)  - Exploratorio (Fluido)   - Exclusivo (Obsidian)
                                                       - Innovador (Spatial/Glass)
```

### Tabla de Correspondencia Inmediata:
1. **Fintech / Banca / Liquidación**: *Swiss Modern + Bento Grid*. (Precisión numérica, tipografía nítida, sombras casi invisibles).
2. **B2B SaaS / ERP / Productividad**: *Bento Grid + Swiss Minimalist*. (Compartimentación lógica, escaneo rápido en 8 horas continuas).
3. **Ciberseguridad / DevTools / Cloud Monitoring**: *High-Density Cyber / Telemetry*. (Métricas monoespaciadas `tabular-nums`, rejillas técnicas de 1px, status pills con pulso).
4. **Salud / Clínicas / SST / Riesgo Psicosocial**: *Swiss Modern de Alto Contraste*. (Cero ambigüedad visual, tarjetas legibles, badges semánticos firmes).
5. **E-commerce de Lujo / Real Estate**: *Dark Luxury / Obsidian*. (Negros profundos `#0A0A0A`, bordes hairline de 0.5px, tipografía editorial).
6. **Agencias Creativas / Editorial**: *Neo-Brutalism Refinado*. (Sombras duras desplazadas sin desenfoque, bordes de 2px, carácter tipográfico audaz).
7. **AI Apps / Web3 / Plataformas Espaciales**: *Glassmorphism Refinado + Spatial UI*. (Desenfocados de refracción `blur(20px) saturate(180%)`, micro-biseles superiores e inferiores).

*Para la guía completa de preguntas y justificaciones, consulta [business-matrix.md](./references/business-matrix.md).*

---

## 3. Los 10 Modelos Proyectados Modernos (Resumen de Fórmulas)

| Modelo | Fórmula Visual Clave | Uso Óptimo |
| :--- | :--- | :--- |
| **Glassmorphism Refinado** | `backdrop-blur-xl backdrop-saturate-180 border border-white/15 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2)]` | Modales, docks flotantes, cabeceras flotantes. |
| **Bento Grid** | `grid grid-cols-12 gap-4 md:gap-6 auto-rows-[minmax(180px,auto)]` (Radio ext - pad = Radio int) | Dashboards de KPIs, vistas analíticas modulares. |
| **Neumorphism Refinado** | Sombra dual calculada `-6px -6px 14px #FFF, 6px 6px 14px #A6AFC3` con tipografía de alto contraste | Controles táctiles, interruptores físicos, audio/hardware. |
| **Claymorphism Refinado** | Sombra suave exterior + doble sombra interior mate `inset 3px 3px 6px #FFF, inset -3px -3px 6px ...` | Tarjetas interactivas táctiles en paletas sobrias. |
| **Spatial UI (visionOS)** | Micro-bisel dual: `inset 0 1px 1.5px rgba(255,255,255,0.25)` y `inset 0 -1px 1.5px rgba(0,0,0,0.3)` | Capas flotantes con profundidad en eje Z. |
| **Dark Luxury** | Canvas `#080808`, superficies `#111111`, bordes `border-white/[0.08] ring-1 ring-white/[0.03]` | Paneles de alta gama, informes ejecutivos premium. |
| **High-Density Cyber** | `font-mono tabular-nums text-[11px] divide-x divide-y divide-neutral-800` | Centros de operaciones, terminales, análisis en tiempo real. |
| **Neo-Brutalism Refinado** | `border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]` con traslación en hover | Botones de acción firme, landing pages de impacto. |
| **Swiss Modern** | Rejilla base 8px, sombras difusas de 2%-4% `shadow-[0_1px_3px_rgba(0,0,0,0.02),0_4px_12px_rgba(0,0,0,0.03)]` | Aplicaciones empresariales, tablas masivas, sistemas de lectura. |
| **Aurora Mesh** | Gradientes radiales difusos `blur(80px)` en segundo plano sin competir con el texto | Fondos escénicos dinámicos y transiciones de ambiente. |

*Para el código CSS completo y clases Tailwind de cada modelo, consulta [projected-paradigms.md](./references/projected-paradigms.md).*

---

## 4. Navegación Avanzada y Componentes de Menú

### 1. Sidebar Colapsable Inteligente
- Modo expandido (`w-64`) a compacto (`w-16`).
- Tooltips flotantes (`z-50`) automáticos en modo compacto.
- Atajo de teclado global `Cmd + B` / `Ctrl + B` y persistencia en `localStorage`.

### 2. Command Palette (Cmd + K / Spotlight)
- Búsqueda modal rápida con navegación por teclado (`ArrowUp`, `ArrowDown`, `Enter`, `Escape`).
- Agrupación por categorías lógicas (Acciones, Casos, Navegación).
- Breadcrumbs en resultados para evitar ambigüedades.

### 3. Floating Bottom Dock
- Cápsula flotante central inferior con efecto vidrio (`backdrop-blur-md`).
- Acciones clave a distancia de un clic sin saturar la parte superior de la pantalla.

### 4. Badges de Estado Semánticos
```html
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
  <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 ring-2 ring-emerald-400/20"></span>
  Verificado
</span>
```

*Para la implementación completa en React + Tailwind de estos componentes, consulta [navigation-and-menus.md](./references/navigation-and-menus.md).*

---

## 5. Animaciones Cinemáticas y Física de Interacción

### 1. Curvas Cinemáticas Obligatorias
- **Desaceleración Exponencial**: `cubic-bezier(0.16, 1, 0.3, 1)` para todas las transiciones interactivas.
- **Resortes con Amortiguamiento Crítico**: `damping = 2 * sqrt(mass * stiffness)` (para `stiffness: 400`, `damping: 40` → cero rebote cómico).

### 2. Micro-interacciones de Alto Rendimiento
- **Spotlight Especular**: Rastreo de variables CSS `--mouse-x` y `--mouse-y` para revelar luz incidente en hover.
- **Skeleton Loader Hiperrealista**: Gradiente angular a 110 grados en ciclo continuo sobre `background-position`.
- **Acordeón con CSS Grid**: Animación fluida de `grid-template-rows: 0fr` a `1fr` sin cálculos costosos de JavaScript.

### 3. Rendimiento y Hardware
- Animar **exclusivamente** `transform` y `opacity`. Cero cambios de `height`/`width`/`margin` que provoquen reflows.
- Bordes ultrafinos de 0.5px para pantallas Retina usando `scaleY(0.5)` con pseudo-elementos.
- Detección de tema en el `<head>` sin FOUC y soporte completo para `prefers-reduced-motion`.

*Para los ejemplos técnicos y snippets de código, consulta [serious-animations.md](./references/serious-animations.md).*

---

## 6. Lista de Verificación Pre-Entrega (Auditoría de Calidad)

Antes de entregar cualquier pantalla o componente de frontend, verifica:

- [ ] **¿Cero Emojis?**: No hay ningún emoji en el código JSX, HTML, menús o badges (solo iconos SVG técnicos).
- [ ] **¿Trazo de Iconos Consistente?**: Todos los iconos usan el mismo `strokeWidth` (1.5px o 1.75px) y tamaño óptico alineado.
- [ ] **¿Modelo Proyectado Definido?**: La vista sigue conscientemente uno de los 10 arquetipos alineados al tipo de negocio.
- [ ] **¿Balance 60-30-10?**: El color de acento no satura la pantalla y se reserva para puntos focales.
- [ ] **¿Animaciones Cinemáticas?**: Se utiliza `cubic-bezier(0.16, 1, 0.3, 1)` o resortes críticamente amortiguados (sin rebotes cómicos).
- [ ] **¿Cero Layout Thrashing?**: Todas las animaciones operan sobre `transform` y `opacity`.
- [ ] **¿Cumple `component-architecture`?**: Componentes < 150 líneas, fórmulas en helpers `lib/`, tipos estrictos sin `any`.
- [ ] **¿Accesibilidad y Contraste?**: Todos los textos cumplen WCAG AA/AAA y respetan `prefers-reduced-motion`.
