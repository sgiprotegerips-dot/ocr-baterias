# Arquitectura de Navegación, Menús Modernos y Rigor Iconográfico

Sistemas de navegación de grado profesional, componentes de menú avanzados y reglas inquebrantables de iconografía técnica (Cero Emojis).

---

## 1. Regla Suprema de Iconografía: CERO EMOJIS

### Manifiesto Anti-Slop:
Queda terminantemente prohibido el uso de caracteres emoji (ej. , , , , ️, , , , , , etc.) en interfaces de usuario profesionales. Los emojis:
- Carecen de consistencia de renderizado entre sistemas operativos (Apple vs. Windows vs. Android).
- Tienen proporciones infantiles y colores discordantes que rompen la paleta cromática.
- No permiten escalado vectorial nítido ni control de grosor de trazo.

### Estándar Vectorial Obligatorio:
- Utilizar exclusivamente librerías vectoriales de grado profesional: **Lucide Icons**, **Phosphor Icons**, **Radix Icons** o **Heroicons**.
- **Grosor de trazo uniforme**: Fijar el trazo en `strokeWidth={1.5}` (alta elegancia) o `strokeWidth={1.75}` (paneles densos) en toda la aplicación. Prohibido mezclar grosores en la misma vista.
- **Escala de tamaños ópticos**:
  - **Micro (`size={16}` / 16px)**: En badges, metadatos, tags y botones secundarios.
  - **Estándar (`size={20}` / 20px)**: En ítems de menú de navegación y botones primarios.
  - **Hero (`size={24}` o `size={28}`)**: En encabezados de módulo y estados vacíos (*empty states*).
- **Alineación con la línea base (Baseline)**: El icono debe acompañarse con `flex items-center gap-2` o `gap-2.5` para garantizar equilibrio visual con el texto contiguo.

---

## 2. Componentes de Navegación Avanzada

### 2.1 Sidebar Colapsable Inteligente (Desktop & Rail)
Maneja dos estados sin perder contexto:
1. **Modo Expandido (`w-64` / 256px)**: Muestra logotipo, títulos de sección, enlaces con iconos y etiquetas, y widgets de estado.
2. **Modo Compacto Rail (`w-16` / 64px)**: Oculta textos y solo muestra iconos centrados. Al hacer hover sobre un icono, se despliega un *flyout tooltip* flotante fijado en `z-50` con el nombre del módulo y atajo rápido.
3. **Persistencia & Atajos**: Guarda el estado en `localStorage` y soporta el atajo global `Cmd + B` o `Ctrl + B`.

```tsx
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, FileSpreadsheet, ShieldAlert, Settings, ChevronLeft, ChevronRight } from 'lucide-react';

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  href: string;
  isActive?: boolean;
  isCollapsed: boolean;
  badge?: string | number;
}

export function IntelligentSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Atajo de teclado Cmd+B / Ctrl+B
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setIsCollapsed((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <aside 
      className={`h-screen bg-neutral-950 border-r border-neutral-800/80 flex flex-col transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Cabecera del Sidebar */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-neutral-800/80">
        {!isCollapsed && (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-xs">
              P
            </div>
            <span className="font-semibold text-sm text-neutral-100 tracking-tight truncate">
              Plataforma SST
            </span>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={`p-1.5 rounded-lg text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/60 transition-colors ${
            isCollapsed ? 'mx-auto' : ''
          }`}
          title={isCollapsed ? 'Expandir (Cmd+B)' : 'Colapsar (Cmd+B)'}
        >
          {isCollapsed ? <ChevronRight size={16} strokeWidth={1.75} /> : <ChevronLeft size={16} strokeWidth={1.75} />}
        </button>
      </div>

      {/* Navegación Principal */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        <SidebarItem
          icon={<LayoutDashboard size={20} strokeWidth={1.75} />}
          label="Bandeja de Entrada"
          href="/casos"
          isActive
          isCollapsed={isCollapsed}
          badge={14}
        />
        <SidebarItem
          icon={<Users size={20} strokeWidth={1.75} />}
          label="Población y Cargos"
          href="/poblacion"
          isCollapsed={isCollapsed}
        />
        <SidebarItem
          icon={<FileSpreadsheet size={20} strokeWidth={1.75} />}
          label="Baremos y Reportes"
          href="/baremos"
          isCollapsed={isCollapsed}
        />
        <SidebarItem
          icon={<ShieldAlert size={20} strokeWidth={1.75} />}
          label="Casos Doble Marca"
          href="/discrepancias"
          isCollapsed={isCollapsed}
          badge="!"
        />
      </nav>

      {/* Footer del Sidebar */}
      <div className="p-2 border-t border-neutral-800/80">
        <SidebarItem
          icon={<Settings size={20} strokeWidth={1.75} />}
          label="Ajustes de Motor"
          href="/configuracion"
          isCollapsed={isCollapsed}
        />
      </div>
    </aside>
  );
}

function SidebarItem({ icon, label, href, isActive, isCollapsed, badge }: NavItemProps) {
  return (
    <a
      href={href}
      className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
        isActive
          ? 'bg-neutral-800/80 text-white shadow-sm ring-1 ring-white/10'
          : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/70'
      } ${isCollapsed ? 'justify-center px-0' : ''}`}
    >
      <span className="shrink-0">{icon}</span>
      {!isCollapsed && <span className="truncate">{label}</span>}
      {!isCollapsed && badge !== undefined && (
        <span className="ml-auto px-2 py-0.5 text-[11px] font-mono font-semibold rounded-md bg-neutral-800 text-neutral-300 ring-1 ring-white/10">
          {badge}
        </span>
      )}

      {/* Flyout flotante en modo colapsado */}
      {isCollapsed && (
        <div className="absolute left-16 ml-2 px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-700 text-white text-xs whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50">
          {label}
        </div>
      )}
    </a>
  );
}
```

---

### 2.2 Command Palette (Cmd + K / Spotlight)
El centro neurálgico de búsqueda rápida para aplicaciones de alta productividad.

```tsx
import React, { useState, useEffect } from 'react';
import { Search, ArrowRight, UserCheck, FileText, Download } from 'lucide-react';

export function CommandPalette({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onClose(); // toggle
      }
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-24 px-4 animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden ring-1 ring-white/10">
        <div className="flex items-center px-4 border-b border-neutral-800">
          <Search size={18} className="text-neutral-500 shrink-0" strokeWidth={1.75} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Escriba un comando o busque por cédula..."
            className="w-full h-12 bg-transparent px-3 text-neutral-100 placeholder-neutral-500 text-sm focus:outline-none"
            autoFocus
          />
          <kbd className="px-2 py-0.5 rounded bg-neutral-800 text-[10px] font-mono text-neutral-400 border border-neutral-700">
            ESC
          </kbd>
        </div>

        <div className="p-2 max-h-80 overflow-y-auto space-y-1">
          <div className="px-3 py-1.5 text-[11px] font-mono uppercase tracking-wider text-neutral-500">
            Acciones Rápidas
          </div>
          <PaletteItem icon={<Download size={16} strokeWidth={1.75} />} title="Exportar Matriz Excel Maestro" shortcut="Cmd+E" />
          <PaletteItem icon={<UserCheck size={16} strokeWidth={1.75} />} title="Resolver casos ambiguos pendientes" shortcut="Cmd+R" />
          <PaletteItem icon={<FileText size={16} strokeWidth={1.75} />} title="Auditar baremo Intralaboral Forma A" />
        </div>
      </div>
    </div>
  );
}

function PaletteItem({ icon, title, shortcut }: { icon: React.ReactNode; title: string; shortcut?: string }) {
  return (
    <div className="flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-neutral-800/80 text-neutral-300 hover:text-white cursor-pointer transition-colors group">
      <div className="flex items-center gap-3">
        <span className="text-neutral-400 group-hover:text-indigo-400 transition-colors">{icon}</span>
        <span className="text-sm font-medium">{title}</span>
      </div>
      {shortcut ? (
        <kbd className="text-[10px] font-mono px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-400">
          {shortcut}
        </kbd>
      ) : (
        <ArrowRight size={14} className="text-neutral-600 opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </div>
  );
}
```

---

### 2.3 Floating Action Dock (Bottom Island)
Permite tener acciones globales elevadas sin ocupar espacio superior permanente.

```tsx
import { Search, Plus, Filter, Download } from 'lucide-react';

export function FloatingBottomDock() {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
      <div className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-neutral-900/80 dark:bg-neutral-950/80 backdrop-blur-xl border border-white/10 shadow-[0_12px_32px_rgba(0,0,0,0.5)]">
        <button 
          className="p-2.5 text-neutral-400 hover:text-white hover:bg-neutral-800/60 rounded-xl transition-all"
          title="Buscar"
        >
          <Search size={18} strokeWidth={1.75} />
        </button>
        <button 
          className="p-2.5 text-neutral-400 hover:text-white hover:bg-neutral-800/60 rounded-xl transition-all"
          title="Filtrar"
        >
          <Filter size={18} strokeWidth={1.75} />
        </button>

        <div className="w-px h-5 bg-neutral-800 mx-1" />

        <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all">
          <Plus size={16} strokeWidth={2} />
          <span>Nuevo Cuadernillo</span>
        </button>

        <div className="w-px h-5 bg-neutral-800 mx-1" />

        <button 
          className="p-2.5 text-neutral-400 hover:text-white hover:bg-neutral-800/60 rounded-xl transition-all"
          title="Exportar"
        >
          <Download size={18} strokeWidth={1.75} />
        </button>
      </div>
    </div>
  );
}
```

---

## 3. Píldoras de Estado y Balance Visual 60-30-10

### Badges Semánticos con Status Dots
En lugar de emojis o colores fluorescentes descontrolados:
- **Punto de 6px (`w-1.5 h-1.5 rounded-full`)**: Indica el estado visualmente.
- **Anillo de Dispersión (`ring-2 ring-emerald-500/20`)**: Aporta legibilidad en cualquier fondo.
- **Fondo sutil (5% a 10% opacidad)** y texto saturado en el mismo tono semántico.

```html
<!-- Estado Óptimo / Éxito -->
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
  <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 ring-2 ring-emerald-400/20"></span>
  Procesado
</span>

<!-- Estado Advertencia / Ambigüedad -->
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
  <span class="w-1.5 h-1.5 rounded-full bg-amber-400 ring-2 ring-amber-400/20"></span>
  Doble Marca
</span>

<!-- Estado Crítico / Faltan Datos -->
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
  <span class="w-1.5 h-1.5 rounded-full bg-rose-400 ring-2 ring-rose-400/20"></span>
  Incompleto
</span>
```
