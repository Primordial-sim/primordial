# 18 - Interfaz y Herramientas

## 📋 Resumen

La **Interfaz y Herramientas** proporciona múltiples formas de ejecutar y visualizar la simulación: un CLI principal (`launcher.py`), herramientas específicas para escenarios, un servidor WebSocket que conecta la simulación con Godot, y una interfaz gráfica en Godot con renderizado del mundo, controles de simulación e inspector de agentes.

**Estado actual**: ✅ **Funcional pero en desarrollo activo**. La arquitectura base está implementada: el CLI funciona, el servidor WebSocket integra el motor real, y la interfaz Godot renderiza el mundo y permite controlar la simulación. Quedan por implementar funcionalidades avanzadas como visualización de relaciones, métricas en tiempo real y gráficos evolutivos.

---

## 🎯 Responsabilidad

**Es responsable de:**
- Proporcionar punto de entrada CLI con argumentos configurables (`launcher.py`)
- Cargar y ejecutar escenarios desde archivos JSON (`run_scenario.py`)
- Servir el estado de la simulación vía WebSocket a clientes externos
- Renderizar el mundo en Godot (rejilla, agentes, selección)
- Mostrar controles de simulación (pause, speed, step)
- Mostrar estadísticas en tiempo real (población, enfermedades, nacimientos, muertes)
- Inspeccionar agentes individuales mediante clic
- Controlar la cámara (zoom, paneo, centrado)
- Filtrar logs relevantes por patrones de eventos

**NO es responsable de:**
- ❌ Ejecutar la lógica de la simulación (eso lo hace `SimulationEngine`)
- ❌ Gestionar el estado del mundo (eso lo hace `WorldState`)
- ❌ Procesar sistemas biológicos (eso lo hacen los sistemas individuales)
- ❌ Persistir datos a largo plazo (eso lo hace `MetricsSystem`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **launcher.py** | Script de arranque | CLI principal |
| **run_scenario.py** | Ejecutor de escenarios | Herramienta CLI |
| **ws_server_real.py** | Servidor de streaming | API WebSocket |
| **websocket_client.gd** | Cliente de visualización | Frontend |
| **world_renderer.gd** | Visualización del mundo | Canvas 2D |
| **ui_renderer.gd** | Panel de control | HUD |
| **camera_controller.gd** | Control de cámara | Cámara virtual |
| **JSON tick message** | Frame de animación | Estado del mundo |

---

## 📁 Archivos que lo componen

| Archivo | Lenguaje | Responsabilidad |
|---------|----------|-----------------|
| `launcher.py` | Python | Punto de entrada CLI principal |
| `tools/run_scenario.py` | Python | Ejecuta escenarios desde JSON |
| `tools/ws_server.py` | Python | Servidor WebSocket de prueba (agentes ficticios) |
| `tools/ws_server_real.py` | Python | Servidor WebSocket con `SimulationEngine` real |
| `godot/simulador-vida/main.tscn` | Godot | Escena principal |
| `godot/simulador-vida/scripts/websocket_client.gd` | GDScript | Coordinador principal |
| `godot/simulador-vida/scripts/world_renderer.gd` | GDScript | Renderizado del mundo |
| `godot/simulador-vida/scripts/ui_renderer.gd` | GDScript | Interfaz de usuario |
| `godot/simulador-vida/scripts/camera_controller.gd` | GDScript | Control de cámara |

---

## 🏗️ Arquitectura general

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────┐  ┌────────────────┐  ┌────────────────────────┐
│  launcher.py │  │ run_scenario   │  │   Godot Engine         │
│  (CLI base)  │  │ (escenarios)   │  │                        │
│              │  │                │  │ ┌──────────────────┐   │
│ --population │  │ --scenario     │  │ │ websocket_       │   │
│ --ticks      │  │ --list         │  │ │ client.gd        │   │
│ --seed       │  │ --export       │  │ │ (coordinador)    │   │
│ --verbose    │  │                │  │ └────────┬─────────┘   │
└──────┬───────┘  └────────┬───────┘  │          │             │
       │                   │          │          │ WebSocket    │
       │                   │          │          │ (ws://:8765) │
       ▼                   ▼          │          ▼             │
┌─────────────────────────────────────┐  │ ┌────────────────┐   │
│      SimulationEngine               │  │ │ world_renderer │   │
│  (creado por defecto o escenario)   │  │ │ ui_renderer    │   │
│                                      │  │ │ camera_control │   │
│  run() - ejecución directa          │  │ └────────────────┘   │
│  step() - ejecución por tick        │  └────────────────────────┘
│  get_visualization_state() ─────────┤
└─────────────────────────────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────────┐
                      │  tools/ws_server_real.py          │
                      │                                    │
                      │  - WebSocket en puerto 8765       │
                      │  - Envía estado cada tick         │
                      │  - Recibe comandos (pause, etc.)  │
                      └───────────────────────────────────┘
```

---

## 🚀 Punto de Entrada Principal: `launcher.py`

### Argumentos disponibles

| Argumento | Corto | Default | Descripción |
|-----------|-------|---------|-------------|
| `--config` | `-c` | `None` | Archivo JSON de configuración |
| `--population` | `-p` | `50` | Población inicial |
| `--width` | `-w` | `100` | Ancho del mundo |
| `--height` | `-H` | `100` | Alto del mundo |
| `--ticks` | `-t` | `None` | Número de ticks a ejecutar |
| `--seed` | `-s` | `None` | Semilla aleatoria (reproducibilidad) |
| `--export` | `-e` | `simulation_metrics.json` | Archivo de exportación |
| `--no-export` | - | - | Desactivar exportación |
| `--snapshot-interval` | - | `config` | Intervalo de snapshots |
| `--verbose` | `-v` | - | Logging detallado (DEBUG) |
| `--quiet` | `-q` | - | Solo errores críticos |

### Ejemplos de uso

```bash
# Ejecución básica
python launcher.py

# Prueba de integración (rápida, reproducible)
python launcher.py --population 50 --ticks 50 --seed 42 --verbose

# Simulación larga con exportación
python launcher.py --population 500 --ticks 5000 --seed 7 --export results.json

# Con configuración externa
python launcher.py --config scenario_extreme.json --population 200 --ticks 1000
```

### Sistema de logging inteligente

El launcher incluye un `RelevantEventsFilter` que filtra logs en modo normal para mostrar solo eventos relevantes:

| Emoji | Evento |
|-------|--------|
| 👶 | Nacimientos |
| ⚰️ | Muertes |
| ❤️ 💍 💑 💕 | Relaciones (matrimonio, consolidación, romance) |
| 💔 | Divorcios |
| 🚶 🏁 | Migraciones |
| 🎯 | Motivaciones activas |
| 🤒 🚨 | Contagios y brotes |
| 🌍 | Cambios de estación |
| 📜 | Eventos históricos (linajes extintos) |
| 🛑 | Cuellos de botella |
| 👑 | Linajes dominantes |
| 📊 | Informes evolutivos |
| 🎂 👴 | Hitos biológicos |

En modo `--verbose` se muestran todos los logs sin filtrar.

---

## 🔧 Herramientas CLI

### `tools/run_scenario.py`

CLI específico para ejecutar escenarios predefinidos desde archivos JSON.

```bash
# Listar escenarios disponibles
python tools/run_scenario.py --list

# Ejecutar escenario específico
python tools/run_scenario.py scenarios/birds.json

# Con sobrescritura de ticks y exportación
python tools/run_scenario.py scenarios/mixed.json --ticks 1000 --export report.csv
```

### `tools/ws_server.py`

**Servidor de prueba** con agentes ficticios que se mueven aleatoriamente. Útil para:
- Probar la conexión WebSocket sin cargar el motor completo
- Desarrollar la interfaz Godot en paralelo
- Debugging de renderizado

```bash
python tools/ws_server.py
# Sirve en ws://localhost:8765 con 20 agentes ficticios a 10 FPS
```

### `tools/ws_server_real.py`

**Servidor real** que integra el `SimulationEngine` con Godot.

```bash
# Con humanos por defecto
python tools/ws_server_real.py

# Con escenario específico
python tools/ws_server_real.py --scenario scenarios/birds.json

# Puerto personalizado
python tools/ws_server_real.py --port 8766
```

---

## 🎮 Interfaz Godot

### Estructura de nodos

```
main.tscn
├── World (Node2D)
│   ├── Camera2D (camera_controller.gd)
│   └── WorldRenderer (world_renderer.gd)
└── UI (CanvasLayer)
    └── UIRenderer (Control - ui_renderer.gd)
```

### Scripts principales

#### `websocket_client.gd` - Coordinador Principal

**Responsabilidades**:
- Conectar al servidor WebSocket (`ws://localhost:8765`)
- Recibir mensajes `tick` del servidor
- Distribuir datos a `world_renderer` y `ui_renderer`
- Manejar TODOS los inputs (botones + selección + teclado)
- Enviar comandos al servidor (pause, resume, set_speed, step)
- Reconexión automática tras desconexión

**Comandos de teclado**:

| Tecla | Acción |
|-------|--------|
| `Espacio` | Play/Pause |
| `1` | Velocidad 1x |
| `2` | Velocidad 2x |
| `3` | Velocidad 5x |
| `4` | Velocidad 10x |
| `N` | Avanzar 1 tick (modo paso a paso) |
| `C` | Centrar cámara |
| `ESC` | Deseleccionar agente |
| Clic derecho + arrastrar | Paneo |
| Rueda del ratón | Zoom |

#### `world_renderer.gd` - Renderizado del Mundo

**Responsabilidades**:
- Dibujar rejilla del mundo
- Dibujar agentes como cuadrados con colores por especie/estado
- Detectar superposiciones (varios agentes en la misma casilla)
- Gestionar selección de agentes mediante clic
- Emitir señales `agent_selected` y `agent_deselected`

**Paleta de colores por especie**:

| Especie | Color |
|---------|-------|
| `human` | Verde 🟢 |
| `mammal` | Verde lima |
| `bird` | Azul 🟦 |
| `fish` | Cian |
| `insect` | Naranja 🟧 |
| `reptile` | Marrón |
| `amphibian` | Turquesa |
| `bacteria` | Magenta |
| `plant` | Verde oscuro |
| `fungus` | Beige |
| `fantasy_creature` | Rosa |

**Sobrescritura por estado** (prioridad sobre especie):

| Estado | Color |
|--------|-------|
| Enfermo | Rojo |
| Embarazada | Amarillo |
| Joven | Azul claro |
| Anciano | Gris |

#### `ui_renderer.gd` - Interfaz de Usuario

**Responsabilidades**:
- Barra superior con estado de conexión, tick, día, agentes
- Botones de control (Play/Pause, velocidades)
- Leyenda de especies presentes y estados
- Panel de estadísticas (población, enfermos, nacimientos, muertes)
- Información de ocupación (superposiciones)
- Inspector de agente seleccionado (clic en agente)

**Información mostrada en el inspector**:
- ID, edad, posición, sexo, especie
- Estado de salud (sano/enfermo)
- Estado de embarazo
- Etapa vital (joven/adulto/anciano)

#### `camera_controller.gd` - Control de Cámara

**Responsabilidades**:
- Zoom con rueda del ratón (0.2x a 10x)
- Paneo con clic derecho + arrastrar
- Centrado con tecla `C`
- Recentrado automático al cambiar dimensiones del mundo

---

## 📡 Protocolo de Comunicación WebSocket

### Mensaje `tick` (servidor → cliente)

```json
{
  "type": "tick",
  "tick": 1234,
  "day": 456.7,
  "world_width": 100,
  "world_height": 100,
  "agents": [
    {
      "id": 42,
      "x": 50.0,
      "y": 75.0,
      "species": "human",
      "gender": "F",
      "age": 10950.0,
      "is_adult": true,
      "is_senior": false,
      "is_sick": false,
      "is_pregnant": true
    }
  ],
  "stats": {
    "total_population": 150,
    "sick_count": 8,
    "total_births": 25,
    "total_deaths": 12,
    "species_counts": {"human": 120, "wolf": 30}
  }
}
```

### Comando `pause` / `resume` (cliente → servidor)

```json
{"type": "pause"}
{"type": "resume"}
```

### Comando `set_speed` (cliente → servidor)

```json
{"type": "set_speed", "speed": 5.0}
```

### Comando `step` (cliente → servidor)

```json
{"type": "step"}
```

### Mensaje `status` (servidor → cliente, respuesta a comandos)

```json
{"type": "status", "status": "paused"}
{"type": "status", "status": "running"}
{"type": "status", "status": "speed:5.0"}
```

---

## 🔗 Interacción con el Motor de Simulación

### Flujo de un tick en modo visualización

```
1. ws_server_real.py arranca SimulationEngine.create_from_scenario(...)
2. engine.initialize() prepara el mundo (sin ejecutar ticks)
3. Servidor WebSocket escucha en puerto 8765
4. Godot se conecta al servidor
5. Bucle del servidor (cada 0.1s por defecto):
   ├── Si NO está pausado:
   │   └── state = engine.step()  ← ejecuta UN tick del motor
   └── Envía state como JSON a todos los clientes conectados
6. Godot recibe el mensaje y:
   ├── Actualiza world_renderer con agentes
   ├── Actualiza ui_renderer con estadísticas
   └── Si hay agente seleccionado, actualiza inspector
```

### Métodos del SimulationEngine usados

| Método | Uso |
|--------|-----|
| `create_default(...)` | Crear motor con parámetros por defecto |
| `create_from_scenario(scenario)` | Crear motor desde archivo JSON |
| `initialize()` | Preparar mundo sin ejecutar ticks |
| `step()` | Ejecutar UN tick y devolver estado |
| `run()` | Ejecutar bucle completo (modo CLI) |
| `get_visualization_state()` | Obtener estado completo para visualización |
| `export_metrics(path)` | Exportar métricas a JSON |

---

## 📝 Ejemplos de uso completos

### Ejemplo 1: Ejecución CLI rápida para validar

```bash
# Simulación corta reproducible
python launcher.py --population 100 --ticks 100 --seed 42 -v

# Salida esperada:
# 2026-08-30 14:23:45 [INFO] 🚀 INICIANDO SIMULADOR DE VIDA EVOLUTIVA
# 2026-08-30 14:23:45 [INFO] 📋 Configuración:
# 2026-08-30 14:23:45 [INFO]    • Población inicial: 100 agentes
# 2026-08-30 14:23:45 [INFO]    • Ticks a ejecutar: 100
# 2026-08-30 14:23:45 [INFO]    • Semilla aleatoria: 42 (reproducible)
# ... (eventos relevantes filtrados)
# 2026-08-30 14:24:12 [INFO] ✅ SIMULACIÓN FINALIZADA CORRECTAMENTE
```

### Ejemplo 2: Visualización en Godot

```bash
# Terminal 1: arrancar servidor
python tools/ws_server_real.py --scenario scenarios/humans.json

# Terminal 2: abrir Godot y ejecutar main.tscn
godot godot/simulador-vida/project.godot
```

El cliente Godot se conecta automáticamente, renderiza el mundo y permite:
- Pausar/reanudar con Espacio
- Cambiar velocidad con teclas 1-4
- Inspeccionar agentes con clic
- Zoom y paneo con ratón

### Ejemplo 3: Modo paso a paso para debugging

```bash
# Arrancar servidor
python tools/ws_server_real.py

# En Godot:
# 1. Pausar con Espacio
# 2. Avanzar tick por tick con tecla N
# 3. Observar cambios en el inspector de agentes
```

### Ejemplo 4: Exportar métricas tras simulación larga

```bash
python launcher.py --population 200 --ticks 5000 --seed 123 \
    --export results.json --snapshot-interval 30

# Genera results.json con todos los snapshots
# Analizable con pandas, matplotlib, etc.
```

---

## 🚨 Estado actual y limitaciones

### Lo que está implementado ✅

- ✅ CLI principal con todos los argumentos necesarios
- ✅ Sistema de logging filtrado por eventos relevantes
- ✅ Herramienta para ejecutar escenarios
- ✅ Servidor WebSocket integrado con el motor real
- ✅ Cliente Godot completo con renderizado y UI
- ✅ Control de simulación (pause, speed, step)
- ✅ Inspector de agentes con información básica
- ✅ Leyenda de especies y estados
- ✅ Estadísticas poblacionales en tiempo real
- ✅ Control de cámara (zoom, paneo, centrado)
- ✅ Reconexión automática del cliente
- ✅ Detección de superposiciones visuales

### Lo que falta o podría mejorar ⚠️

- ⚠️ **Inspector limitado**: no muestra relaciones, genoma completo, ni emociones
- ⚠️ **Sin visualización de relaciones**: las conexiones entre agentes no se dibujan
- ⚠️ **Sin gráficos evolutivos**: no hay visualización de tendencias a lo largo del tiempo
- ⚠️ **Sin visualización de biomas/terreno**: el fondo es uniforme
- ⚠️ **Sin visualización de carga viral/epidemiológica**: no se ven zonas de infección
- ⚠️ **Sin gráficos de estadísticas históricas**: solo valores actuales
- ⚠️ **Sin persistencia de estado visual**: al cerrar Godot se pierde
- ⚠️ **Sin exportación desde la UI**: solo desde CLI
- ⚠️ **Sin control de filtros de visualización**: no se pueden ocultar especies
- ⚠️ **EventBus no está conectado a la UI**: podría usarse para actualizaciones más eficientes

### Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| Godot no conecta | Servidor no arrancado | Arrancar `ws_server_real.py` primero |
| Puerto en uso | Otro proceso en 8765 | Usar `--port 8766` |
| Agente no aparece en inspector | Clic muy lejos del centro | Zoom más y clic preciso |
| Simulación muy lenta | Velocidad alta + muchos agentes | Bajar velocidad o reducir población |
| Logs no aparecen | Modo normal filtra eventos | Usar `-v` para ver todo |

---

## 📊 Métricas de la interfaz

| Métrica | Valor |
|---------|-------|
| Archivos Python de herramientas | 4 |
| Scripts GDScript | 4 |
| Argumentos CLI | 11 |
| Atajos de teclado | 8 |
| Comandos WebSocket | 4 |
| Estados de agente visualizados | 4 (sick, pregnant, young, senior) |
| Especies con colores definidos | 11 |

---

## 🔮 Próximos pasos sugeridos

### Corto plazo (funcionalidades de UI)
- [ ] Mostrar relaciones del agente seleccionado (líneas a pareja/hijos/padres)
- [ ] Visualizar biomas/terreno como fondo
- [ ] Añadir heatmap de carga viral/zonas epidemiológicas
- [ ] Mostrar emociones/motivaciones en el inspector
- [ ] Mostrar árbol genealógico simple del agente seleccionado

### Medio plazo (visualización avanzada)
- [ ] Gráficas temporales (población, enfermedades, evolución de genes)
- [ ] Filtros de visualización por especie, edad, estado
- [ ] Highlight de linajes dominantes con colores distintivos
- [ ] Visualización de núcleos residenciales (grupos familiares)
- [ ] Modo "cámara rápida" con salto de N ticks

### Largo plazo (análisis y UX)
- [ ] Exportar snapshots directamente desde Godot
- [ ] Rebobinar la simulación (usando `storage/snapshots/` si se implementa)
- [ ] Comparar escenarios lado a lado
- [ ] Modo colaborativo (múltiples clientes viendo la misma simulación)
- [ ] Integración con el EventBus para eventos en tiempo real

---

*Documento: 18_INTERFAZ_Y_HERRAMIENTAS.md*
*Versión: 1.0 (transición)*
*Estado: Interfaz funcional, documentación pendiente de expansión cuando se completen las funcionalidades avanzadas*
*Última actualización: Agosto 2026*