# Animaciones Cinemáticas, Física de Interacción y Rendimiento Crítico

Guía de animación matemática y optimizaciones visuales para interfaces serias de alto rendimiento.

---

## 1. Motores Cinemáticos y Curvas Bézier de Oro

En interfaces de nivel profesional, quedan prohibidas las curvas estándar `ease` o `ease-in-out` de CSS, así como las físicas de resorte subamortiguadas (efectos de gelatina o rebotes cómicos).

### La Curva de Oro: Desaceleración Exponencial
Imita la inercia del mundo físico: aceleración instantánea ante la intención del usuario y desaceleración suave y controlada.

```css
/* Curva exponencial de desaceleración (Out Expo) */
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);

/* Curva simétrica para cambios de pantalla completos */
--ease-in-out-expo: cubic-bezier(0.87, 0, 0.13, 1);
```

En Tailwind CSS:
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'in-out-expo': 'cubic-bezier(0.87, 0, 0.13, 1)',
      }
    }
  }
}
```

### Amortiguamiento Crítico en Física de Resortes (Framer Motion)
Para que un resorte se detenga con naturalidad en el menor tiempo posible sin sobrepasar el destino:
$$\text{Damping} = 2 \times \sqrt{\text{Mass} \times \text{Stiffness}}$$

Para `mass = 1` y `stiffness = 400`, el damping crítico exacto es `40`:

```tsx
import { Transition } from "framer-motion";

export const seriousSpring: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 40, // Cero oscilaciones residuales
  mass: 1,
};
```

---

## 2. Micro-interacciones de Alta Fidelidad

### 2.1 Botón / Tarjeta con Highlight Especular Dinámico (Spotlight)
El elemento responde dinámicamente a la posición del cursor mediante variables CSS en tiempo real:

```tsx
import React, { useRef, MouseEvent } from 'react';

export function SpotlightCard({ children }: { children: React.ReactNode }) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className="group relative bg-neutral-900 border border-neutral-800 rounded-2xl p-6 overflow-hidden"
    >
      {/* Halo de luz especular invisible por defecto, revelado en hover */}
      <div
        className="pointer-events-none absolute -inset-px opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(255,255,255,0.06), transparent 80%)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
```

### 2.2 Skeleton Loader Hiperrealista (Shimmer Direccional)
En lugar de un parpadeo plano de opacidad, proyecta un haz de luz angular de 110 grados que barre la superficie:

```css
@keyframes angularShimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-premium {
  background: #171717;
  background-image: linear-gradient(
    110deg,
    rgba(255, 255, 255, 0) 20%,
    rgba(255, 255, 255, 0.05) 40%,
    rgba(255, 255, 255, 0.09) 50%,
    rgba(255, 255, 255, 0.05) 60%,
    rgba(255, 255, 255, 0) 80%
  );
  background-size: 200% 100%;
  animation: angularShimmer 1.8s cubic-bezier(0.16, 1, 0.3, 1) infinite;
  border-radius: 8px;
}
```

### 2.3 Acordeón Fluido con CSS Grid (Cero Cálculos de Altura en JS)
Evita calcular `scrollHeight` con JavaScript para animar elementos colapsables:

```html
<div class="accordion-item">
  <button class="accordion-trigger" aria-expanded="true">
    Ver detalle del ítem
  </button>
  <div class="accordion-content">
    <div class="overflow-hidden">
      <!-- Todo el contenido interno aquí sin saltos de reflow -->
      <p class="py-4 text-sm text-neutral-400">Detalle psicométrico...</p>
    </div>
  </div>
</div>

<style>
.accordion-content {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 350ms cubic-bezier(0.16, 1, 0.3, 1);
}

.accordion-item[data-state="open"] .accordion-content,
.accordion-content[aria-expanded="true"] {
  grid-template-rows: 1fr;
}
</style>
```

---

## 3. Optimizaciones Visuales y Rendimiento Crítico

### Regla de Oro: Solo `transform` y `opacity`
Cualquier animación que altere `height`, `width`, `top`, `left`, `margin` o `padding` desencadena un **Layout / Reflow** masivo en el árbol DOM del navegador.
- Para mover: usa `transform: translate3d(x, y, 0)`.
- Para cambiar tamaño: usa `transform: scale()`.
- Para mostrar u ocultar: usa `opacity`.

### Aceleración por Capas GPU
Para elementos que ejecutan animaciones continuas:
```css
.gpu-layer {
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
}
```

### Líneas Hairline de 0.5px en Pantallas Retina
En monitores HiDPI, un borde de 1px físico equivale a 2 o 3 píxeles reales, viéndose pesado. Para lograr un trazo ultrafino de grado Apple:

```css
.hairline-bottom {
  position: relative;
}

.hairline-bottom::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.1);
  transform: scaleY(0.5);
  transform-origin: bottom;
}
```

### Prevención de FOUC (Flash of Unstyled Content) al Cambiar Tema
Para evitar destellos cromáticos y retrasos de estilo al cargar:
```html
<!-- En el <head> antes de cualquier CSS o script diferido -->
<script>
  (function() {
    const theme = localStorage.getItem('app-theme') || 
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
  })();
</script>
```

### Respeto a `prefers-reduced-motion`
Garantizar accesibilidad universal transformando traslaciones espaciales en simples desvanecimientos:

```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
