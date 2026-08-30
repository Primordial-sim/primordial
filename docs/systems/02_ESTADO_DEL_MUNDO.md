# 02 - Estado del Mundo

## 📋 Resumen

El **Estado del Mundo** es la memoria viva del Simulador de Vida. Almacena toda la información del universo simulado: los agentes que lo habitan, sus posiciones, sus relaciones, el terreno, y los cambios pendientes de aplicar. Es la fuente única de verdad sobre la que todos los sistemas leen y escriben.

**Filosofía fundamental**: *El estado se lee libremente, pero se escribe solo a través del búfer transaccional.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Almacenar el estado completo del mundo (agentes, posiciones, relaciones)
- Garantizar la regla fundamental: **1 agente = 1 casilla**
- Gestionar el búfer transaccional de cambios (`PendingChanges`)
- Consolidar cambios atómicamente al final de cada tick (`apply_commit`)
- Proveer acceso espacial eficiente (`WorldGrid`)
- Gestionar núcleos residenciales (familias, parejas)
- Rastrear ocupación de casillas
- Generar recuerdos de duelo y nacimiento

**NO es responsable de:**
- ❌ Decidir QUÉ cambios hacer (eso lo hacen los sistemas)
- ❌ Ejecutar lógica de juego (eso lo hacen los sistemas)
- ❌ Orquestar el orden de ejecución (eso lo hace el Motor)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **WorldState** | La realidad consolidada del universo | Materia |
| **PendingChanges** | Cambios cuánticos no observados | Potencial |
| **apply_commit** | El colapso de la función de onda | Observación |
| **WorldGrid** | El espacio físico tridimensional | Territorio |
| **Person** | Un ser vivo individual | Organismo |
| **Tile** | Una parcela de terreno | Ecosistema local |
| **Núcleo residencial** | Un hogar / familia | Unidad familiar |
| **Ocupación de casilla** | Presencia física en un lugar | Posición |
| **entity_id** | Identificación única (ADN, huella) | Identidad |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `core/state/world_state.py` | `WorldState` | Estado global del mundo |
| `core/state/pending_changes.py` | `PendingChanges` | Búfer transaccional |
| `core/state/world_grid.py` | `WorldGrid` | Grid espacial de celdas |

---

## 🔄 Flujo de ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│              CICLO DE VIDA DEL ESTADO                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE DE LECTURA (durante el tick)                               │
│                                                                 │
│ Los sistemas LEEN el estado actual:                             │
│ ├── state.get_all_persons() → lista de agentes                  │
│ ├── state.get_person(id) → agente específico                    │
│ ├── state.get_tile_at(x, y) → tile del terreno                  │
│ ├── state.is_cell_occupied(x, y) → ¿hay alguien aquí?           │
│ └── state.get_nucleus_for_agent(id) → núcleo familiar           │
│                                                                 │
│ Los sistemas ESCRIBEN en el búfer:                              │
│ ├── pending.register_movement(id, x, y)                         │
│ ├── pending.register_infection(id, pathogen)                    │
│ ├── pending.register_birth(mother, father, x, y, genome)        │
│ ├── pending.register_death(id, reason)                          │
│ ├── pending.register_marriage(p1, p2)                           │
│ └── pending.register_emotion_update(id, emotion, amount)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE DE CONSOLIDACIÓN (fin del tick)                            │
│                                                                 │
│ state.apply_commit(pending, event_bus, current_tick)            │
│ │                                                               │
│ ├── 1. MUERTES: eliminar agentes, liberar casillas              │
│ ├── 2. ENVEJECIMIENTO: incrementar edad                         │
│ ├── 3. SALUD: aplicar infecciones y recuperaciones              │
│ ├── 4. NACIMIENTOS: crear nuevos agentes                        │
│ ├── 5. ADOPCIONES: transferir filiación                         │
│ ├── 6. MOVIMIENTOS: actualizar posiciones                       │
│ ├── 7. RELACIONES: matrimonios y divorcios                      │
│ ├── 8. PSICOLOGÍA: emociones, memoria, motivaciones             │
│ └── 9. ACTUALIZACIÓN FINAL: núcleos, ocupación                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ pending.clear()                                                 │
│ El búfer se limpia y está listo para el siguiente tick          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Estado

---

### 1. WorldState - La Realidad Consolidada

**📁 Archivo**: `core/state/world_state.py`
**🌍 Equivalencia real**: La realidad consolidada del universo. Todo lo que existe, existe aquí.

#### Entradas (constructor)

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `config` | `SimulationConfig` | Leyes físicas | Configuración central |
| `width` | `int` | Longitud del planeta | Ancho del mundo |
| `height` | `int` | Anchura del planeta | Alto del mundo |

#### Salidas (métodos de consulta)

| Método | Tipo de retorno | Equivalencia real | Descripción |
|--------|-----------------|-------------------|-------------|
| `get_all_persons()` | `List[Person]` | Censo poblacional | Todos los agentes vivos |
| `get_person(id)` | `Person` | Identificar individuo | Un agente específico |
| `get_tile_at(x, y)` | `Tile` | Parcela de terreno | Tile en posición |
| `is_cell_occupied(x, y)` | `bool` | ¿Hay alguien aquí? | Ocupación de casilla |
| `get_cell_occupant(x, y)` | `int` | ¿Quién está aquí? | ID del ocupante |
| `get_nucleus_for_agent(id)` | `ResidentialNucleus` | ¿Dónde vive? | Núcleo familiar |
| `has_tile_map()` | `bool` | ¿Existe el terreno? | Tile map inicializado |

#### Métodos de mutación (solo a través de apply_commit)

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `apply_commit(pending)` | Colapso cuántico | Consolida todos los cambios |
| `add_person(person)` | Nacimiento | Registra nuevo agente |
| `occupy_cell(x, y, id)` | Presencia física | Marca casilla ocupada |
| `free_cell(x, y)` | Ausencia | Libera casilla |
| `register_nucleus(nucleus)` | Crear hogar | Registra núcleo familiar |

#### Flujo interno de apply_commit

```
apply_commit(pending, event_bus, current_tick)
    │
    ├── 1. MUERTES
    │   ├── Eliminar agente de persons
    │   ├── Liberar casilla
    │   ├── Eliminar de núcleo
    │   ├── Generar recuerdos de duelo
    │   └── Publicar PersonDiedEvent
    │
    ├── 2. ENVEJECIMIENTO
    │   └── person.add_age(days)
    │
    ├── 3. SALUD
    │   ├── person.infect(pathogen)
    │   └── person.recover(pathogen_id)
    │
    ├── 4. NACIMIENTOS
    │   ├── Crear Person con genoma recombinado
    │   ├── Asignar padres
    │   ├── Ocupar casilla
    │   ├── Añadir a núcleo
    │   ├── Registrar recuerdos
    │   └── Publicar PersonBornEvent
    │
    ├── 5. ADOPCIONES
    │   ├── Transferir filiación
    │   ├── Añadir a núcleo
    │   └── Publicar AdoptionCompletedEvent
    │
    ├── 6. MOVIMIENTOS
    │   ├── Liberar casilla antigua
    │   ├── Aplicar wrapping toroidal
    │   ├── person.set_position(x, y)
    │   └── Ocupar casilla nueva
    │
    ├── 7. RELACIONES
    │   ├── Divorcios: separar núcleos
    │   └── Matrimonios: fusionar núcleos
    │
    ├── 8. PSICOLOGÍA
    │   ├── Actualizar memoria
    │   ├── Actualizar emociones
    │   ├── Actualizar flags de libre albedrío
    │   └── Actualizar motivaciones
    │
    └── 9. ACTUALIZACIÓN FINAL
        ├── Actualizar centros de núcleos
        └── Verificar consistencia de ocupación
```

#### Ejemplos

```python
# Crear estado del mundo
state = WorldState(config=config, width=100, height=100)

# Inicializar terreno
state.initialize_tile_map(seed=42)

# Consultar agentes
for person in state.get_all_persons():
    print(f"Agente {person.entity_id} en ({person.x}, {person.y})")

# Consultar tile
tile = state.get_tile_at(50, 50)
print(f"Bioma: {BiomeClassifier.classify(tile)}")

# Verificar ocupación
if state.is_cell_occupied(50, 50):
    occupant_id = state.get_cell_occupant(50, 50)
    print(f"Casilla ocupada por agente {occupant_id}")
```

#### Consideraciones

- **Regla fundamental**: 1 agente = 1 casilla. No se permiten dos agentes en la misma posición
- **Wrapping toroidal**: si un agente sale por un lado, aparece por el otro
- **apply_commit es atómico**: todos los cambios se aplican juntos o ninguno
- Los recuerdos de duelo se generan automáticamente al morir un agente
- Los núcleos residenciales se gestionan automáticamente (crear, fusionar, separar)

---

### 2. PendingChanges - El Búfer Transaccional

**📁 Archivo**: `core/state/pending_changes.py`
**🌍 Equivalencia real**: Cambios cuánticos no observados. Existen como potencial hasta que se consolidan.

#### Entradas (métodos de registro)

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `register_movement(id, x, y)` | Intención de moverse | Encola desplazamiento |
| `register_infection(id, pathogen)` | Contagio | Encola infección |
| `register_recovery(id, pathogen_id)` | Curación | Encola recuperación |
| `register_death(id, reason)` | Muerte | Marca para eliminación |
| `register_birth(mother, father, x, y, genome)` | Nacimiento | Encola nuevo agente |
| `register_pregnancy_update(id, ...)` | Gestación | Actualiza embarazo |
| `register_marriage(p1, p2)` | Unión | Encola matrimonio |
| `register_divorce(p1, p2)` | Separación | Encola divorcio |
| `register_adoption(child, parent_a, parent_b)` | Adopción | Encola filiación |
| `register_emotion_update(id, emotion, amount)` | Cambio emocional | Encola emoción |
| `register_memory_update(id, key, value)` | Recuerdo | Encola memoria |
| `register_motivation_update(id, name, delta)` | Impulso | Encola motivación |
| `set_migration_target(id, target)` | Destino migratorio | Establece destino |
| `register_age_increment(id, days)` | Envejecimiento | Acumula edad |

#### Salidas (colecciones leídas por apply_commit)

| Colección | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `movements` | `Dict[int, Tuple]` | Desplazamientos | ID → (x, y) |
| `infections` | `List[Tuple]` | Contagios | (ID, Pathogen) |
| `recoveries` | `List[Tuple]` | Curaciones | (ID, pathogen_id) |
| `deaths` | `Dict[int, str]` | Muertes | ID → razón |
| `births` | `List[Dict]` | Nacimientos | Datos del bebé |
| `pregnancy_updates` | `Dict[int, Dict]` | Gestaciones | ID → estado |
| `marriages` | `Dict[int, int]` | Uniones | p1 → p2 |
| `divorces` | `List[Tuple]` | Separaciones | (p1, p2) |
| `adoptions` | `List[Dict]` | Adopciones | Datos completos |
| `emotion_updates` | `Dict[int, List]` | Emociones | ID → cambios |
| `memory_updates` | `Dict[int, Dict]` | Recuerdos | ID → cambios |
| `motivation_updates` | `Dict[int, Dict]` | Motivaciones | ID → deltas |

#### Flujo interno

```
Durante el tick:
    Sistema A → pending.register_movement(1, 50, 50)
    Sistema B → pending.register_infection(2, pathogen)
    Sistema C → pending.register_death(3, "vejez")
    Sistema D → pending.register_emotion_update(1, "stress", 0.3)

Fin del tick:
    state.apply_commit(pending)
    → Todos los cambios se aplican atómicamente

Después del commit:
    pending.clear()
    → El búfer queda vacío para el siguiente tick
```

#### Ejemplos

```python
pending = PendingChanges()

# Registrar un movimiento
pending.register_movement(entity_id=1, x=50, y=50)

# Registrar una infección
pending.register_infection(entity_id=2, pathogen=pathogen)

# Registrar un nacimiento
pending.register_birth(
    mother_id=10,
    father_id=11,
    x=50,
    y=50,
    genome=baby_genome,
)

# Registrar una emoción
pending.register_emotion_update(entity_id=1, emotion="stress", amount=0.3)

# Registrar una motivación (acumulativo)
pending.register_motivation_update(entity_id=1, motivation_name="migration", delta=0.1)

# Establecer motivación (absoluto)
pending.set_motivation(entity_id=1, motivation_name="migration", value=0.8)

# Limpiar búfer
pending.clear()
```

#### Consideraciones

- **Nunca modificar WorldState directamente durante el tick**: siempre usar PendingChanges
- Los movimientos usan `Dict` (último registro gana)
- Las infecciones usan `List` (puede haber múltiples)
- `register_death` solo registra la primera muerte (no se puede morir dos veces)
- Las motivaciones soportan modo acumulativo (`register_motivation_update`) y absoluto (`set_motivation` con prefijo `__set__`)
- `migration_targets` se crea bajo demanda (no existe hasta que se usa)

---

### 3. WorldGrid - El Espacio Físico

**📁 Archivo**: `core/state/world_grid.py`
**🌍 Equivalencia real**: El espacio físico tridimensional donde ocurre todo.

#### Entradas (constructor)

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `width` | `int` | Longitud del terreno | Ancho del grid |
| `height` | `int` | Anchura del terreno | Alto del grid |
| `max_occupants_per_cell` | `int` | Capacidad del espacio | Máximo por celda (default: 1) |

#### Salidas (métodos de consulta)

| Método | Tipo | Equivalencia real | Descripción |
|--------|------|-------------------|-------------|
| `get_occupants_at(x, y)` | `List` | ¿Quién está aquí? | Agentes en celda |
| `can_move_to(x, y)` | `bool` | ¿Cabe alguien más? | Valida movimiento |
| `get_density_at(x, y)` | `int` | Densidad puntual | Cuántos hay aquí |
| `get_area_density(x, y, radius)` | `int` | Densidad zonal | Cuántos hay alrededor |

#### Flujo interno

```
place_person(person, x, y)
    ├── Clamp a límites del mapa
    ├── Crear celda si no existe
    ├── Añadir person a la celda
    └── Actualizar person.x, person.y

remove_person(person)
    ├── Obtener coordenada actual
    ├── Eliminar de la celda
    └── Borrar celda si queda vacía

can_move_to(x, y)
    ├── Verificar límites del mapa
    └── Verificar capacidad de la celda

get_area_density(x, y, radius)
    ├── Acotar bucle a límites del mapa (OPTIMIZACIÓN)
    └── Sumar ocupantes en el radio
```

#### Ejemplos

```python
grid = WorldGrid(width=100, height=100, max_occupants_per_cell=1)

# Colocar agente
grid.place_person(person, x=50, y=50)

# Verificar si se puede mover
if grid.can_move_to(51, 50):
    grid.remove_person(person)
    grid.place_person(person, x=51, y=50)

# Consultar densidad
density = grid.get_density_at(50, 50)        # Densidad puntual
area_density = grid.get_area_density(50, 50, radius=5)  # Densidad zonal
```

#### Consideraciones

- `place_person` hace clamp automático a los límites del mapa
- `remove_person` limpia la celda si queda vacía (evita memory leaks)
- `get_area_density` acota el bucle a los límites del mapa (optimización)
- Por defecto `max_occupants_per_cell=1` (regla: 1 agente = 1 casilla)

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                      WorldState                                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ persons      │  │ world_grid   │  │ tile_map             │ │
│  │ Dict[int,    │  │ WorldGrid    │  │ TileMap              │ │
│  │ Person]      │  │              │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ _nuclei      │  │ _cell_       │  │ epidemiological_map  │ │
│  │ Dict[int,    │  │ occupancy    │  │ EpidemiologicalMap   │ │
│  │ Nucleus]     │  │ Dict[Tuple,  │  │                      │ │
│  │              │  │ int]         │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ apply_commit(pending)                                    │   │
│  │ ← Recibe PendingChanges y consolida todo atómicamente    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ recibe
                            │
┌─────────────────────────────────────────────────────────────────┐
│                   PendingChanges                                │
│                                                                 │
│  movements, infections, recoveries, deaths, births,             │
│  marriages, divorces, adoptions, emotion_updates,               │
│  memory_updates, motivation_updates, migration_targets          │
│                                                                 │
│  ← Los sistemas escriben aquí durante el tick                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# Desde SimulationConfig
config.environment.sector_size = 10          # Tamaño de sector
config.environment.carrying_capacity = 200   # Capacidad de carga
config.environment.max_agents_per_sector = 8 # Máximo por sector
config.environment.max_viral_load = 10.0     # Carga viral máxima
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/integration/test_tile_integration.py` | Integración de tile_map con WorldState |
| `tests/unit/test_feedback_system.py` | FeedbackSystem con WorldState |
| `tests/integration/test_regression_bugs.py` | Bugs de register_birth y otros |

---

## 📝 Ejemplos completos

### Crear y poblar un mundo

```python
from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig

config = SimulationConfig()
state = WorldState(config=config, width=100, height=100)
state.initialize_tile_map(seed=42)

# Añadir un agente
person = Person(config=config, entity_id=1, x=50, y=50, age=6570.0)
state.add_person(person)

# Consultar
print(state.get_all_persons())       # Todos los agentes
print(state.get_tile_at(50, 50))     # Tile en posición
print(state.is_cell_occupied(50, 50)) # True
```

### Simular un tick completo

```python
# 1. Crear búfer
pending = PendingChanges()

# 2. Los sistemas registran cambios
pending.register_movement(entity_id=1, x=51, y=50)
pending.register_emotion_update(entity_id=1, emotion="happiness", amount=0.1)
pending.register_age_increment(entity_id=1, increment_days=1.0)

# 3. Consolidar
state.apply_commit(pending, event_bus=event_bus, current_tick=42)

# 4. Limpiar búfer
pending.clear()
```

### Gestionar núcleos residenciales

```python
# Crear núcleo individual
state._create_single_nucleus(agent_id=1)

# Consultar núcleo
nucleus = state.get_nucleus_for_agent(agent_id=1)
print(f"Núcleo {nucleus.nucleus_id}, tipo: {nucleus.nucleus_type}")

# Fusionar núcleos (matrimonio)
state._handle_marriage_in_nucleus(agent_a_id=1, agent_b_id=2)

# Separar núcleos (divorcio)
state._handle_divorce_in_nucleus(agent_a_id=1, agent_b_id=2)
```

---

## 🚨 Consideraciones y limitaciones

### Reglas fundamentales
- **1 agente = 1 casilla**: nunca dos agentes en la misma posición
- **Transaccionalidad**: los cambios se aplican todos juntos al final del tick
- **Wrapping toroidal**: el mundo es una esfera (sale por un lado, entra por otro)
- **apply_commit es atómico**: si falla a mitad, el estado puede ser inconsistente

### Rendimiento
- `get_all_persons()` retorna una vista O(1), no una copia
- `get_person(id)` es O(1) gracias al Dict
- `_verify_occupancy_consistency()` reconstruye el mapa si detecta conflictos
- `WorldGrid.get_area_density()` acota el bucle a los límites del mapa

### Limitaciones
- El número máximo de agentes está limitado por la memoria
- Los snapshots con muchos agentes pueden ser grandes
- `apply_commit` no es reversible (no hay rollback)

### Errores comunes
- ❌ Modificar `WorldState` directamente durante el tick (usar `PendingChanges`)
- ❌ No verificar `is_cell_occupied` antes de mover
- ❌ Olvidar llamar `pending.clear()` después del commit
- ❌ Asumir que `get_tile_at` siempre retorna un tile (puede ser None)

---

## 🎓 Conceptos clave

### ¿Por qué PendingChanges?

**Principio de transaccionalidad**:
- Los sistemas NO modifican el estado directamente
- Registran sus intenciones en el búfer
- Al final del tick, TODO se aplica de una vez
- Esto garantiza que el orden de ejecución no cause efectos secundarios

Ejemplo: si el sistema de mortalidad mata a un agente en la fase 7, ese agente NO desaparece hasta el commit. Así, los sistemas de las fases 1-6 pueden seguir leyéndolo.

### ¿Por qué 1 agente = 1 casilla?

Simplifica enormemente la lógica espacial:
- No hay que gestionar listas de agentes por celda
- La ocupación es O(1) con un Dict
- Los movimientos son atómicos (liberar + ocupar)
- Evita problemas de superposición visual

### ¿Por qué wrapping toroidal?

El mundo es finito pero sin bordes:
- Si un agente sale por la derecha, aparece por la izquierda
- Si sale por arriba, aparece por abajo
- Evita problemas de agentes atrapados en los bordes
- Simula un planeta esférico

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Líneas de código | ~1500 |
| Colecciones en PendingChanges | 15 |
| Métodos de registro | 18 |
| Pasos en apply_commit | 9 |
| Tests cubriendo el estado | ~30 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Rollback de apply_commit (deshacer el último commit)
- [ ] Snapshots diferenciales (solo guardar cambios)
- [ ] Compresión de WorldState para mapas grandes

### Posibles
- [ ] WorldState distribuido (para mapas enormes)
- [ ] Versionado de estado (historial de commits)
- [ ] Serialización a formato portable (JSON, protobuf)

---

*Documento: 02_ESTADO_DEL_MUNDO.md*
*Versión: 1.0*