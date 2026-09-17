# Catálogo y Fórmulas de los 10 Modelos Proyectados Modernos

Guía técnica con fórmulas matemáticas, CSS puro y clases Tailwind CSS para implementar los 10 arquetipos de diseño contemporáneo.

---

## 1. Glassmorphism / Frosted Aero Refinado
No es el vidrio borroso genérico de 2020. Es un sistema óptico con refracción, borde especular superior y preservación estricta de contraste WCAG.

### Fórmulas Matemáticas:
- **Translucidez base**: Fondo de 8% a 14% de opacidad (`rgba(255, 255, 255, 0.08)` en dark mode, `rgba(255, 255, 255, 0.70)` en light mode).
- **Desenfoque gaussiano**: `backdrop-filter: blur(16px) saturate(180%)`. El factor de saturación al 180% devuelve la vivacidad que el blur suele lavar.
- **Borde especular**: Borde continuo de 1px `rgba(255, 255, 255, 0.15)` con luz incidente interna `inset 0 1px 0 rgba(255, 255, 255, 0.25)`.

### Código CSS:
```css
.glass-surface {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.12) 0%,
    rgba(255, 255, 255, 0.04) 100%
  );
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    inset 0 1px 1px 0 rgba(255, 255, 255, 0.2),
    0 8px 32px 0 rgba(0, 0, 0, 0.12);
}
```

### Tailwind CSS:
```html
<div class="bg-white/10 dark:bg-black/30 backdrop-blur-xl backdrop-saturate-180 border border-white/20 dark:border-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_8px_32px_rgba(0,0,0,0.15)] rounded-2xl p-6">
  <!-- Contenido con texto solido de alto contraste -->
</div>
```

---

## 2. Bento Grid Architecture
Inspirado en los sistemas de información de Linear, Apple y Vercel. Distribuye información heterogénea en compartimentos modulares asimétricos.

### Fórmulas Matemáticas:
- **Regla del Radio Concéntrico**: Para evitar tensión visual en las esquinas anidadas:
  $$\text{Radio Interno} = \text{Radio Externo} - \text{Padding}$$
  *Ejemplo*: Si la tarjeta tiene `rounded-3xl` (24px) y un `padding` de 16px, el elemento interior debe tener `rounded-lg` (8px).
- **Proporción de Grilla**: 12 columnas con alturas variables (`auto-rows-[minmax(180px, auto)]`).

### Tailwind CSS:
```html
<div class="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 auto-rows-[minmax(190px,auto)]">
  <!-- Tarjeta Hero (destacada): ocupa 8 columnas y 2 filas -->
  <div class="col-span-1 md:col-span-8 md:row-span-2 bg-neutral-900 border border-neutral-800 rounded-3xl p-8 flex flex-col justify-between">
    <!-- Contenido principal -->
  </div>
  
  <!-- Tarjetas Satélite: ocupan 4 columnas cada una -->
  <div class="col-span-1 md:col-span-4 bg-neutral-900 border border-neutral-800 rounded-3xl p-6">
    <!-- Métrica o gráfico secundario -->
  </div>
  <div class="col-span-1 md:col-span-4 bg-neutral-900 border border-neutral-800 rounded-3xl p-6">
    <!-- Lista compacta -->
  </div>
</div>
```

---

## 3. Neumorphism / Soft UI Refinado
Supera las limitaciones de la versión primitiva de 2020 mediante contrastes elevados en tipografía e indicadores, usando la extrusión solo para interactividad física.

### Fórmulas Matemáticas:
- Fondo: Color gris neutro suave (`#e8ecf2` o `#1e222b` en dark).
- Luz superior izquierda: `box-shadow: -6px -6px 14px rgba(255, 255, 255, 0.8)`.
- Sombra inferior derecha: `6px 6px 14px rgba(166, 175, 195, 0.6)`.
- Estado Presionado (Active/Inset): Inversión simétrica a sombras interiores `inset 4px 4px 8px ...`.

### Código CSS:
```css
.neu-raised {
  background: #e8ecf2;
  border-radius: 14px;
  box-shadow: 
    -6px -6px 14px rgba(255, 255, 255, 0.8),
    6px 6px 14px rgba(166, 175, 195, 0.5);
  transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
}

.neu-raised:active, .neu-raised[data-state="active"] {
  box-shadow: 
    inset 4px 4px 8px rgba(166, 175, 195, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.9);
}
```

---

## 4. Claymorphism Refinado
Superficies tridimensionales con curvatura suave, volumen hinchado y acabado mate. Se estiliza para entornos B2B limitando la paleta a tonos titanio, crema o gris carbón.

### Código CSS:
```css
.clay-card {
  background: #f8fafc;
  border-radius: 20px;
  box-shadow: 
    10px 10px 24px rgba(148, 163, 184, 0.18),
    -8px -8px 20px rgba(255, 255, 255, 0.9),
    inset 3px 3px 6px rgba(255, 255, 255, 0.8),
    inset -3px -3px 6px rgba(148, 163, 184, 0.12);
}
```

---

## 5. Modern Skeuomorphism & Spatial UI (visionOS Style)
Recrea la física de materiales hápticos y refracción espacial mediante múltiples capas de iluminación Z-axis y micro-biseles.

### Código CSS:
```css
.spatial-panel {
  background: rgba(22, 27, 34, 0.75);
  backdrop-filter: blur(48px) saturate(210%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 
    0 24px 64px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.25),   /* Bisel superior de luz */
    inset 0 -1px 1.5px 0 rgba(0, 0, 0, 0.3);         /* Oclusión ambiental inferior */
}
```

---

## 6. Dark Luxury / Obsidian Minimalism
El estándar de prestigio técnico. Utiliza negros profundos, micro-bordes de medio píxel y acentos de metales fríos.

### Reglas Clave:
- **Fondos**: No uses `#000000` puro para tarjetas. Usa `#080808` para el canvas y `#111111` para superficies elevadas.
- **Bordes Hairline**: En pantallas Retina, los bordes normales de 1px pueden verse pesados. Combina `border border-white/[0.07]` con `ring-1 ring-white/[0.03]`.
- **Tipografía**: Jerarquía estricta con contrastes sutiles: títulos en `#EDEDED`, textos secundarios en `#888888`, micro-etiquetas en `#555555`.

### Tailwind CSS:
```html
<div class="bg-[#0c0c0c] border border-white/[0.08] ring-1 ring-white/[0.03] rounded-xl p-6 shadow-[0_4px_24px_rgba(0,0,0,0.6)]">
  <span class="text-[11px] font-medium tracking-widest uppercase text-neutral-500">Métrica Consolidada</span>
  <div class="mt-2 text-3xl font-semibold tracking-tight text-neutral-100">$1,420,890.00</div>
  <div class="mt-1 text-xs text-neutral-400 font-mono tracking-tight">+3.42% vs periodo anterior</div>
</div>
```

---

## 7. High-Density Cyber / Telemetry / Mission Control
Diseñado para ingenieros de confiabilidad, centros de operaciones de red (NOC) y analistas financieros.

### Reglas Clave:
- **Fuentes monoespaciadas**: Todas las cifras deben usar `font-mono tabular-nums` para que los números no salten al cambiar.
- **Divisores Técnicos**: En lugar de tarjetas separadas por márgenes amplios, usa paneles unidos por líneas de rejilla de 1px (`divide-x divide-y divide-neutral-800`).
- **Píldoras de Estado (Status Pills)**: Indicadores de pulso o fijos de 6px con anillos de dispersión sutiles.

### Tailwind CSS:
```html
<div class="bg-neutral-950 border border-neutral-800 rounded-lg overflow-hidden">
  <div class="grid grid-cols-4 divide-x divide-neutral-800">
    <div class="p-3">
      <div class="flex items-center justify-between mb-1">
        <span class="text-[10px] uppercase font-mono tracking-wider text-neutral-500">CPU Clust #01</span>
        <span class="flex h-2 w-2 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
      </div>
      <div class="text-xl font-mono tabular-nums font-semibold text-emerald-400">14.2%</div>
    </div>
    <!-- Repetir celdas de rejilla compactas -->
  </div>
</div>
```

---

## 8. Neo-Brutalism Refinado
Una evolución del brutalismo que conserva la audacia gráfica y la legibilidad editorial, pero elimina la torpeza visual.

### Reglas Clave:
- Bordes negros sólidos de 2px (`border-2 border-black dark:border-white`).
- Sombras rígidas sin desenfoque (hard offset shadows): `box-shadow: 4px 4px 0px 0px #000000`.
- Micro-interacción: Al hacer hover o active, el elemento se desplaza 2px hacia la sombra y ésta se reduce proporcionalmente, creando un clic físico.

### Tailwind CSS:
```html
<button class="px-5 py-2.5 bg-white dark:bg-neutral-900 text-black dark:text-white font-semibold text-sm border-2 border-black dark:border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] dark:shadow-[4px_4px_0px_0px_rgba(255,255,255,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all duration-150 rounded-md">
  Ejecutar Verificación
</button>
```

---

## 9. Swiss Modern / Stripe & Linear Minimalist
La cúspide de la tipografía y el diseño modular funcional. Todo elemento está calculado en base a una retícula de múltiplos de 4px u 8px.

### Reglas Clave:
- Sombras invisibles compuestas: No una sombra fuerte, sino dos sombras superpuestas de opacidad ultra-baja (ej. 2% y 4%).
- Contraste de texto sin colores puros: Títulos en `#0F172A`, cuerpo en `#334155`, sutiles en `#64748B`.
- Fondos de página en off-white (`#F8FAFC` o `#FAFAFA`).

### Tailwind CSS:
```html
<div class="bg-white border border-slate-200/80 rounded-xl p-6 shadow-[0_1px_3px_0_rgba(0,0,0,0.02),0_4px_12px_0_rgba(0,0,0,0.03)] hover:border-slate-300 transition-colors duration-200">
  <div class="flex items-center justify-between">
    <h4 class="text-sm font-semibold text-slate-900">Total Baterías Procesadas</h4>
    <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
      Completado
    </span>
  </div>
  <p class="mt-4 text-3xl font-bold tracking-tight text-slate-900">1,248</p>
</div>
```

---

## 10. Aurora / Mesh Atmosphere
Capas de iluminación difusa dinámica ubicadas detrás del plano de contenido. Aportan calidez visual, profundidad escénica y un toque de sofisticación cinemática.

### Código CSS:
```css
.aurora-container {
  position: relative;
  overflow: hidden;
  background-color: #050505;
}

.aurora-container::before {
  content: '';
  position: absolute;
  top: -20%;
  left: 15%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(79, 70, 229, 0.15) 0%, transparent 70%);
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
}

.aurora-container::after {
  content: '';
  position: absolute;
  bottom: -10%;
  right: 10%;
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.12) 0%, transparent 70%);
  filter: blur(90px);
  pointer-events: none;
  z-index: 0;
}
```
