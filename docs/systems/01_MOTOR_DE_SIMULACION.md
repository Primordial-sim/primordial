# 01 - Motor de Simulación

## 📋 Resumen

El **Motor de Simulación** es el corazón del Simulador de Vida. Orquesta el ciclo de vida completo de cada tick, garantizando que todos los sistemas biológicos, sociales y ambientales se ejecuten en el orden correcto, con la configuración correcta, y manteniendo la coherencia temporal del mundo.

**Filosofía fundamental**: *El usuario controla la vida, el motor controla el mundo.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Orquestar el ciclo de vida completo de la simulación
- Gestionar el tiempo biológico interno y su representación visible
- Construir y ejecutar el pipeline de fases en cada tick
- Cargar escenarios personalizados definidos por el usuario
- Persistir el estado del mundo (guardar/cargar partidas)
- Garantizar causalidad temporal estricta entre eventos
- Adaptarse dinámicamente a cambios de escala temporal en caliente

**NO es responsable de:**
- ❌ Decidir comportamientos de agentes (lo hacen los sistemas individuales)
- ❌ Almacenar el estado del mundo (lo hace `WorldState`)
- ❌ Calcular lógica biológica (lo hacen los sistemas especializados)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Tick** | Latido del corazón del universo | Pulso temporal |
| **Día simulado** | Rotación planetaria | 24 horas reales |
| **Año visible** | Órbita completa alrededor de su estrella | 365 días |
| **Pipeline de fases** | Cadena de montaje biológica | Secuencia natural |
| **Fase** | Etapa del ciclo vital (nacer → crecer → morir) | Período evolutivo |
| **Snapshot** | Fotografía instantánea del universo | Momento congelado |
| **Escenario** | Plan experimental / receta de laboratorio | Protocolo |
| **SimulationEngine** | Sistema nervioso central del universo | Conciencia |
| **PendingChanges** | Cambios cuánticos no consolidados | Potencial |
| **WorldState** | Realidad consolidada del universo | Materia |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `core/engine/simulation_engine.py` | `SimulationEngine` | Orquestador maestro |
| `core/engine/phase_scheduler.py` | `PhaseScheduler` | Constructor de fases |
| `core/engine/tick_manager.py` | `TickManager` | Gestor del tiempo |
| `core/engine/snapshot_manager.py` | `SnapshotManager` | Persistencia de estado |
| `core/engine/scenario_loader.py` | `ScenarioLoader` | Cargador de escenarios |
| `core/execution/execution_pipeline.py` | `ExecutionPipeline` | Ejecutor de ticks |
| `core/execution/phase_executor.py` | `PhaseExecutor` | Ejecutor de fases |
| `core/execution/system_runner.py` | `SystemRunner` | Ejecutor de sistemas |
| `core/execution/execution_context.py` | `ExecutionContext` | Contexto compartido |
| `core/config/simulation_config.py` | `SimulationConfig` | Configuración central |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│                   INICIO DE SIMULACIÓN                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ SimulationEngine.create_default() o create_from_scenario()      │
│ ├── Crear WorldState con dimensiones                            │
│ ├── Inicializar tile_map (generación procedural)                │
│ ├── Generar población fundadora (según escenario)               │
│ ├── Crear TickManager (configurar escala temporal)              │
│ └── Construir ExecutionPipeline con PhaseScheduler              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ CICLO DE SIMULACIÓN                                             │
│ while world_days_elapsed < total_days:                          │
│                                                                 │
│ 1. tick_manager.advance_tick()                                  │
│    └── Incrementa current_tick y total_simulated_days           │
│                                                                 │
│ 2. execution_pipeline.execute_tick(state, delta_days, ...)      │
│    │                                                            │
│    ├── Crear PendingChanges (búfer transaccional)               │
│    ├── Crear EnvironmentContext (snapshot ambiental)            │
│    │                                                            │
│    └── Para cada fase (8 fases):                                │
│        ├── FASE 1: Temporal (AgingSystem)                       │
│        ├── FASE 2: Ambiente (Environment, Density, Feedback)    │
│        ├── FASE 3: Social (Marriage, Relationships, Adoption)   │
│        ├── FASE 4: Movimiento (FreeWill, Migration, Movement)   │
│        ├── FASE 5: Salud (DiseaseSystem)                        │
│        ├── FASE 6: Reproducción (Conception, Gestation, Egg)    │
│        ├── FASE 7: Mortalidad (Mortality, DeathResolver)        │
│        └── FASE 8: Observadores (Genealogy, Metrics)            │
│                                                                 │
│ 3. state.apply_commit(pending)                                  │
│    └── Consolida cambios transaccionales en WorldState          │
│                                                                 │
│ 4. Actualizar métricas y snapshots                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FIN DE SIMULACIÓN                                               │
│ Exportar resultados a CSV/JSON                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Motor

---

### 1. SimulationEngine - El Orquestador Maestro

**📁 Archivo**: `core/engine/simulation_engine.py`
**🌍 Equivalencia real**: El sistema nervioso central del universo.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `width` | `int` | Longitud del planeta | Ancho del mundo en tiles |
| `height` | `int` | Anchura del planeta | Alto del mundo en tiles |
| `founding_population_size` | `int` | Población fundadora | Número de agentes iniciales |
| `config` | `SimulationConfig` | Leyes físicas | Configuración central |
| `scenario` | `Scenario` | Plan experimental | Escenario personalizado |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `SimulationEngine` | Objeto | Universo en marcha | Instancia lista para ejecutar |

#### Flujo interno

```
create_default(width, height, founding_population_size)
    ├── Crear SimulationConfig
    ├── Crear WorldState(config, width, height)
    ├── state.initialize_tile_map()
    ├── Generar población fundadora humana
    ├── Crear TickManager
    ├── PhaseScheduler.build_phases()
    ├── Crear ExecutionPipeline(config, phases)
    └── Retornar SimulationEngine

run(max_ticks)
    └── while world_days_elapsed < total_days:
        ├── delta = tick_manager.advance_tick()
        ├── pending = pipeline.execute_tick(state, delta, ...)
        ├── state.apply_commit(pending, event_bus, tick)
        ├── state.world_days_elapsed += delta
        ├── Registrar métricas cada N ticks
        └── Guardar snapshot cada N días
```

#### Ejemplos

```python
# Simulación por defecto
engine = SimulationEngine.create_default(width=100, height=100, founding_population_size=50)
engine.run()

# Desde escenario personalizado
scenario = ScenarioLoader.load("scenarios/ecosistema_bosque.json")
engine = SimulationEngine.create_from_scenario(scenario)
engine.run()

# Guardar/cargar
engine.save_game("partida.bin")
engine.load_game("partida.bin")
```

#### Consideraciones

- `create_default()` usa humano como especie por defecto
- `create_from_scenario()` permite múltiples especies
- El tile_map se inicializa automáticamente
- Si el escenario tiene especies no registradas, lanza `ValueError`

---

### 2. TickManager - El Reloj del Universo

**📁 Archivo**: `core/engine/tick_manager.py`
**🌍 Equivalencia real**: El reloj biológico cósmico.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `initial_days_per_tick` | `float` | Velocidad del tiempo | Días por tick (default: 30.0) |
| `start_year` | `int` | Año cero | Año de inicio (default: 1) |
| `custom_delta_days` | `float` | Aceleración temporal | Override dinámico |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `current_tick` | `int` | Latido actual | Número de tick |
| `total_simulated_days` | `float` | Edad del universo | Días acumulados |
| `current_visible_cycle` | `int` | Año actual | Año visible |
| `is_new_visible_cycle` | `bool` | Año nuevo | ¿Completó un año? |

#### Flujo interno

```
advance_tick(custom_delta_days=None)
    ├── current_tick += 1
    ├── delta = custom_delta_days si existe, sino days_per_tick
    ├── total_simulated_days += delta
    └── Retornar delta

get_formatted_date()
    ├── passed_years = total_simulated_days // 365
    ├── remainder = total_simulated_days % 365
    ├── month = remainder // 30.4166 + 1
    └── day = remainder % 30.4166 + 1
```

#### Escalas temporales típicas

| Escala | Días/tick | Uso |
|--------|-----------|-----|
| Detallado | 1.0 | Día a día |
| Normal | 30.0 | Estándar |
| Estación | 90.0 | Cambio estacional |
| Año | 365.0 | Rápido |
| Década | 3650.0 | Largo plazo |
| Milenio | 365000.0 | Geológico |

#### Ejemplos

```python
tm = TickManager(initial_days_per_tick=1.0, start_year=1)
delta = tm.advance_tick()           # 1 día
tm.set_tick_duration(30.0)         # Ahora 1 tick = 1 mes
delta = tm.advance_tick()           # 30 días
fecha = tm.get_formatted_date()     # {'tick': 2, 'year': 1, 'month': 2, ...}
```

#### Consideraciones

- Soporta cualquier escala: 0.01 hasta millones de días/tick
- `set_tick_duration(0)` o negativo lanza `ValueError`
- Días siempre en `float` para máxima precisión
- `load_from_snapshot()` restaura sin perder decimales

---

### 3. PhaseScheduler - El Arquitecto de Fases

**📁 Archivo**: `core/engine/phase_scheduler.py`
**🌍 Equivalencia real**: El arquitecto del ciclo vital.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `config` | `SimulationConfig` | Leyes del universo | Configuración central |
| `event_bus` | `Any` | Red neuronal | Sistema de eventos |
| `relationship_engine` | `RelationshipExperienceEngine` | Memoria social | Motor de experiencias |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `List[PhaseDefinition]` | Lista | Ciclo vital | 8 fases ordenadas |

#### Flujo interno

```
build_phases(config, event_bus, relationship_engine)
    ├── Crear dependencias compartidas:
    │   ├── GenealogySystem, AncestryQueries, EvolutionEngine
    │   ├── DensitySystem, CompatibilityEngine
    │   ├── MarriageSystem, RelationshipManager
    │   └── ExperienceGenerator
    └── Retornar 8 PhaseDefinitions en orden
```

#### Las 8 fases

| # | Nombre | Sistemas | Equivalencia real |
|---|--------|----------|-------------------|
| 1 | Temporal | AgingSystem, TemporalSystem | Envejecimiento |
| 2 | Ambiente | EnvironmentSystem, DensitySystem, FeedbackSystem | Clima y entorno |
| 3 | Social | MarriageSystem, RelationshipManager, AdoptionSystem | Interacciones |
| 4 | Movimiento | FreeWillSystem, MigrationSystem, MovementSystem | Desplazamiento |
| 5 | Salud | DiseaseSystem | Enfermedades |
| 6 | Reproducción | ConceptionSystem, EggSystem, GestationSystem | Ciclo reproductivo |
| 7 | Mortalidad | MortalitySystem, DeathResolver | Supervivencia |
| 8 | Observadores | GenealogySystem, MetricsSystem, EvolutionEngine | Registro |

#### Consideraciones

- Las dependencias compartidas se crean UNA vez y se inyectan a múltiples sistemas
- El orden es crítico: cambiarlo rompe la causalidad
- Si un sistema no implementa `process()`, falla al construirse

---

### 4. ExecutionPipeline - La Cadena de Montaje

**📁 Archivo**: `core/execution/execution_pipeline.py`
**🌍 Equivalencia real**: La cadena de montaje biológica.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `state` | `WorldState` | Universo actual | Estado del mundo |
| `delta_days` | `float` | Tiempo transcurrido | Días del tick |
| `current_tick` | `int` | Latido actual | Número de tick |
| `current_day` | `float` | Día actual | Día acumulado |
| `event_bus` | `Any` | Red neuronal | Bus de eventos |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `PendingChanges` | Objeto | Cambios cuánticos | Búfer transaccional |

#### Flujo interno

```
execute_tick(state, delta_days, current_tick, current_day, event_bus)
    ├── Crear PendingChanges() vacío
    ├── Crear/actualizar EnvironmentContext (OPTIMIZACIÓN)
    ├── Crear ExecutionContext
    └── Para cada fase: phase_executor.execute(phase, context)
    └── Retornar pending
```

#### Optimización clave

Reutiliza `EnvironmentContext` entre ticks:

```python
# Primera vez: crear
self._environment = EnvironmentContext(state=state, config=self.config)

# Siguientes: actualizar in-place
self._environment.sector_map = self._environment._build_sector_map(state)
self._environment.pressure_map.clear()
```

#### Validaciones en constructor

- Lanza `ValueError` si no hay fases
- Lanza `ValueError` si hay fases duplicadas
- Lanza `TypeError` si un sistema no implementa `process()`

---

### 5. PhaseExecutor - El Director de Orquesta

**📁 Archivo**: `core/execution/phase_executor.py`
**🌍 Equivalencia real**: El director de orquesta.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `phase` | `PhaseDefinition` | Movimiento musical | Fase a ejecutar |
| `context` | `ExecutionContext` | Partitura | Contexto compartido |

#### Flujo interno

```
execute(phase, context)
    └── Para cada system en phase.systems:
        └── runner.run(system, context, phase_name)
```

#### PhaseDefinition

```python
@dataclass
class PhaseDefinition:
    name: str                              # Nombre de la fase
    systems: list[ProcessableSystem]       # Sistemas de la fase
```

---

### 6. SnapshotManager - La Máquina del Tiempo

**📁 Archivo**: `core/engine/snapshot_manager.py`
**🌍 Equivalencia real**: Una máquina del tiempo que congela el universo.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `state` | `WorldState` | Universo a congelar | Estado actual |
| `tick_manager` | `TickManager` | Reloj a congelar | Gestor temporal |
| `filepath` | `str` | Coordenadas temporales | Ruta del archivo |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| Archivo `.bin` | pickle | Cristal de tiempo | Snapshot completo |
| Tupla | `tuple` | Universo restaurado | (state, tick, days, scale) |

#### Flujo interno

```
create_snapshot(state, tick_manager, filepath)
    ├── snapshot_data = {
    │       "world_state": state,
    │       "tick": tick_manager.current_tick,
    │       "total_days": tick_manager.total_simulated_days,
    │       "scale": tick_manager.days_per_tick,
    │   }
    ├── pickle.dump(snapshot_data, file)
    └── Retornar True/False

load_snapshot(filepath)
    ├── pickle.load(file)
    └── Retornar (state, tick, total_days, scale)
```

#### Ejemplos

```python
sm = SnapshotManager()
sm.create_snapshot(state, tick_manager, "partida.bin")
state, tick, days, scale = sm.load_snapshot("partida.bin")
tick_manager.load_from_snapshot(tick, days)
tick_manager.set_tick_duration(scale)
```

#### Consideraciones

- Usa `pickle` binario (rápido pero no portable entre versiones)
- Lanza `FileNotFoundError` si el archivo no existe
- Lanza `Exception` si el archivo está corrupto

---

### 7. ScenarioLoader - El Cargador de Experimentos

**📁 Archivo**: `core/engine/scenario_loader.py`
**🌍 Equivalencia real**: Un protocolo de laboratorio.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `filepath` | `str` | Carpeta de experimento | Ruta al JSON |

#### Salidas

| Salida | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `Scenario` | Objeto | Plan experimental | Escenario validado |

#### Estructura del JSON

```json
{
    "name": "Ecosistema de Bosque",
    "description": "Simulación con humanos, lobos y pinos",
    "species": [
        {"id": "human", "count": 20},
        {"id": "wolf", "count": 8},
        {"id": "pine", "count": 50}
    ],
    "world": {"width": 200, "height": 200},
    "simulation": {"max_ticks": 10000, "delta_days": 1.0, "total_days": 36500},
    "environment": {"sector_size": 10}
}
```

#### Dataclasses del escenario

```python
@dataclass
class SpeciesConfig:
    species_id: str    # ID de la especie
    count: int         # Número de individuos

@dataclass
class Scenario:
    name: str
    description: str
    species: List[SpeciesConfig]
    world: WorldConfig
    simulation: SimulationConfig
    environment: EnvironmentConfig
```

#### Validaciones

- ❌ Archivo no existe → `FileNotFoundError`
- ❌ Falta campo `name` → `ValueError`
- ❌ Falta campo `species` → `ValueError`
- ❌ Especie no registrada → `ValueError` con lista de disponibles
- ❌ `count <= 0` → `ValueError`

#### Ejemplos

```python
scenario = ScenarioLoader.load("scenarios/ecosistema_bosque.json")
print(scenario.total_population)  # 78

# Listar escenarios disponibles
archivos = ScenarioLoader.list_scenarios("scenarios")
```

---

### 8. SimulationConfig - Las Leyes del Universo

**📁 Archivo**: `core/config/simulation_config.py`
**🌍 Equivalencia real**: Las leyes de la física del universo simulado.

#### Sub-configuraciones

| Subsistema | Responsabilidad | Parámetros clave |
|------------|-----------------|------------------|
| `EngineConfig` | Bucle principal | `total_days: 3650.0`, `delta_days: 1.0` |
| `TimeConfig` | Tiempo y ciclos | `days_per_year: 365.0`, `adult_age_days: 6570.0` |
| `ReproductionConfig` | Reproducción | `pregnancy_duration_days: 270.0`, `base_conception_chance: 0.15` |
| `DiseasesConfig` | Enfermedades | `base_transmission_chance: 0.18`, `base_recovery_chance: 0.15` |
| `MortalityConfig` | Mortalidad | `base_life_expectancy_days: 25550.0`, `hard_cap_age_days: 41975.0` |
| `EnvironmentConfig` | Entorno | `sector_size: 10`, `carrying_capacity: 200` |
| `CognitionConfig` | Cognición | `max_episodic_memories: 50`, `base_forgetting_rate: 0.2` |
| `FreeWillConfig` | Libre albedrío | `action_threshold: 0.7`, `motivation_decay_rate: 0.02` |
| `MutationConfig` | Mutación | `probability: 0.05`, `magnitude_std: 0.1` |
| `RelationshipsConfig` | Relaciones | `min_affinity_for_dating: 0.5`, `orientation_tolerance: 1.5` |
| `AdoptionsConfig` | Adopciones | `max_orphan_age_days: 6205.0`, `max_children_for_adoption: 3` |
| `AgingConfig` | Envejecimiento | `reproductive_wear_per_child: 0.015`, `stress_aging_factor: 0.5` |
| `GenealogyConfig` | Genealogía | `consanguinity_limit: 3` |

#### Modificación en caliente

```python
config = SimulationConfig()
config.set_parameter("reproduction", "pregnancy_duration_days", 300.0)
value = config.get_parameter("mortality", "base_life_expectancy_days", 25550.0)
```

---

## 🔗 Interacción entre componentes

```
┌──────────────────────────────────────────────────────────────────────┐
│                        SimulationEngine                              │
│                    (Orquestador Maestro)                             │
└──────┬────────────────┬────────────────┬────────────────┬────────────┘
       │                │                │                │
       │ usa            │ usa            │ usa            │ usa
       ▼                ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│ TickManager │  │ Snapshot    │  │ Scenario    │  │ Execution    │
│ (Reloj)     │  │ Manager     │  │ Loader      │  │ Pipeline     │
└─────────────┘  └─────────────┘  └─────────────┘  └──────┬───────┘
                                                           │
                                                           │ construido por
                                                           ▼
                                                    ┌──────────────┐
                                                    │ Phase        │
                                                    │ Scheduler    │
                                                    └──────┬───────┘
                                                           │
                                                           │ usa
                                                           ▼
                                                    ┌──────────────┐
                                                    │ Phase        │
                                                    │ Executor     │
                                                    └──────┬───────┘
                                                           │
                                                           │ usa
                                                           ▼
                                                    ┌──────────────┐
                                                    │ System       │
                                                    │ Runner       │
                                                    └──────────────┘
```

---

## ⚙️ Configuración Global

```python
config = SimulationConfig()

# Motor principal
config.engine.total_days = 3650.0       # 10 años
config.engine.delta_days = 1.0          # 1 día por tick

# Tiempo
config.time.days_per_month = 30.0
config.time.days_per_year = 365.0
config.time.adult_age_days = 6570.0     # ~18 años
config.time.senior_age_days = 21900.0   # ~60 años

# Snapshot
config.evolution.snapshot_interval_days = 30.0
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/integration/test_statistical.py` | Comportamiento global del motor |
| `tests/integration/test_regression_bugs.py` | Bugs conocidos y regresiones |
| `tests/integration/test_tile_integration.py` | Integración con tile_map |

---

## 📝 Ejemplos completos

### Simulación básica

```python
from core.engine.simulation_engine import SimulationEngine

engine = SimulationEngine.create_default(width=100, height=100, founding_population_size=50)
engine.run()
```

### Escenario personalizado

```python
from core.engine.scenario_loader import ScenarioLoader
from core.engine.simulation_engine import SimulationEngine

scenario = ScenarioLoader.load("scenarios/ecosistema_bosque.json")
engine = SimulationEngine.create_from_scenario(scenario)
engine.run()
```

### Guardar y cargar

```python
from core.engine.snapshot_manager import SnapshotManager

sm = SnapshotManager()
sm.create_snapshot(engine.state, engine.tick_manager, "partida.bin")

state, tick, days, scale = sm.load_snapshot("partida.bin")
engine.tick_manager.load_from_snapshot(tick, days)
engine.tick_manager.set_tick_duration(scale)
```

### Cambiar escala temporal

```python
engine.tick_manager.set_tick_duration(1.0)     # 1 día/tick
engine.run(max_ticks=100)

engine.tick_manager.set_tick_duration(365.0)   # 1 año/tick
engine.run(max_ticks=100)
```

---

## 🚨 Consideraciones y limitaciones

### Rendimiento
- `ExecutionPipeline` reutiliza `EnvironmentContext` entre ticks
- `TickManager` usa `float` para evitar pérdida de precisión
- Snapshots usan `pickle` binario (rápido pero no portable)

### Coherencia temporal
- **Causalidad estricta**: eventos de una fase no afectan fases anteriores
- **Transaccionalidad**: cambios se acumulan en `PendingChanges` y se aplican al final
- **Determinismo**: mismo estado + misma semilla = mismos resultados

### Limitaciones
- No soporta pausa (solo acelerar/desacelerar)
- Snapshots no compatibles entre versiones diferentes
- Número máximo de agentes limitado por memoria

### Errores comunes
- ❌ No validar `delta_days > 0` al cambiar escala
- ❌ Cargar snapshot de versión incompatible
- ❌ Modificar `WorldState` directamente sin `PendingChanges`

---

## 🎓 Conceptos clave

### ¿Por qué 8 fases?

El orden refleja la causalidad biológica natural:

1. **Temporal**: Envejeces antes que nada
2. **Ambiente**: El clima cambia independientemente de ti
3. **Social**: Interactúas con otros
4. **Movimiento**: Te mueves en respuesta
5. **Salud**: Tu salud depende de todo lo anterior
6. **Reproducción**: Te reproduces si estás sano
7. **Mortalidad**: Mueres si no puedes sobrevivir
8. **Observadores**: Registramos lo que pasó

### ¿Por qué PendingChanges?

Principio de transaccionalidad:
- Los cambios NO se aplican inmediatamente
- Se acumulan en un búfer
- Se aplican todos juntos al final del tick
- Garantiza consistencia: si mueres en fase 4, no te mueves en fase 5

### ¿Por qué EnvironmentContext se reutiliza?

Optimización crítica: el sector_map es costoso de calcular. Reutilizarlo entre ticks mejora rendimiento significativamente.

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Líneas de código del motor | ~2500 |
| Sistemas orquestados | ~50 |
| Fases del pipeline | 8 |
| Sub-configuraciones | 13 |
| Tests cubriendo el motor | ~50 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Pausa real (sin acelerar/desacelerar)
- [ ] Snapshots incrementales (solo cambios entre ticks)
- [ ] Rebobinado (volver N ticks atrás)
- [ ] Multi-threading (fases independientes en paralelo)

### Posibles
- [ ] Distribución en cluster
- [ ] Streaming en tiempo real
- [ ] Análisis en vivo
- [ ] IA supervisora de anomalías

---

*Documento: 01_MOTOR_DE_SIMULACION.md*
*Versión: 1.0*