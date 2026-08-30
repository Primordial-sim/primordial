# 07 - Movimiento

## 📋 Resumen

El **Sistema de Movimiento** modela cómo los agentes se desplazan físicamente por el mundo. Incluye el movimiento táctico inmediato (decisión de siguiente paso), el arbitraje de colisiones espaciales (evitar que dos agentes ocupen la misma casilla) y las migraciones masivas a larga distancia. Todo filtrado por las **capacidades de movimiento** derivadas del genoma.

**Filosofía fundamental**: *El movimiento emerge de una evaluación multicriterio del entorno (Utility AI), modulada por la fisiología locomotora del organismo y resuelta por un árbitro espacial que garantiza la regla 1 agente = 1 casilla.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Derivar capacidades de movimiento del genoma (`MovementCapabilities`)
- Decidir el siguiente paso táctico de cada agente (`MovementSystem`)
- Arbitrar colisiones espaciales antes del commit (`MovementResolver`)
- Gestionar migraciones masivas a larga distancia (`MigrationSystem`)
- Aplicar Utility AI para evaluación de celdas
- Soportar movimiento toroidal (wrapping)
- Integrar presión social, carga viral y recursos en decisiones

**NO es responsable de:**
- ❌ Decidir QUÉ motivación seguir (eso lo hace `FreeWillSystem`, documento 08)
- ❌ Gestionar memoria episódica (eso lo hace `CognitiveMemorySystem`, documento 08)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`, documento 09)
- ❌ Gestionar relaciones sociales (eso lo hacen los sistemas del documento 06)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`, documento 10)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **MovementCapabilities** | Fisiología locomotora | Anatomía |
| **MovementSystem** | Navegación espacial | Decisión motora |
| **MovementResolver** | Coordinación en multitudes | Evitar colisiones |
| **MigrationSystem** | Migración animal/humana | Desplazamiento masivo |
| **Utility AI** | Evaluación multicriterio | Toma de decisiones |
| **Selection temperature** | Entropía conductual | Predictibilidad |
| **Push factor** | Factor de expulsión | Hambre, guerra |
| **Pull factor** | Factor de atracción | Oportunidad, recursos |
| **SpatialGrid** | Sistema de coordenadas | Grid espacial |
| **Toroidal wrapping** | Superficie esférica | Planeta |
| **Preferred sector** | Territorio conocido | Hogar |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/movement/movement_capabilities.py` | `MovementCapabilities` | Capacidades derivadas del genoma |
| `systems/movement/movement_system.py` | `MovementSystem` | Movimiento táctico inmediato |
| `systems/movement/movement_resolver.py` | `MovementResolver` | Arbitraje de colisiones |
| `systems/movement/migration_system.py` | `MigrationSystem` | Migraciones a larga distancia |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│       FASE 1: DECISIÓN MIGRATORIA (largo plazo)                 │
│                                                                 │
│ MigrationSystem:                                                │
│  ├── Para cada agente con can_migrate:                          │
│  │   ├── Verificar cooldown (90 días)                           │
│  │   ├── Si tiene destino activo:                               │
│  │   │   ├── Reevaluar cada 30 días                             │
│  │   │   ├── Invalidar si destino dejó de ser viable            │
│  │   │   └── Si llega: memoria positiva + establecimiento       │
│  │   └── Evaluar push factors:                                  │
│  │       ├── Superpoblación (pressure > 1.8)                    │
│  │       ├── Hambre (energy baja + recursos bajos)              │
│  │       ├── Epidemia (trauma_sickness o viral_load alto)       │
│  │       ├── Clima hostil (danger > 0.5)                        │
│  │       ├── Trauma de abandono                                 │
│  │       ├── Trauma de adopción                                 │
│  │       └── Motivación interna 'migration' > umbral            │
│  └── Si necesita migrar: muestrear mapa y asignar destino       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 2: MOVIMIENTO TÁCTICO (corto plazo)                  │
│                                                                 │
│ MovementSystem:                                                 │
│  ├── Para cada agente con can_move:                             │
│  │   ├── Si tiene destino migratorio → moverse hacia él         │
│  │   └── Si no: evaluar celdas cercanas (radio = vision_range)  │
│  │       ├── Puntuar cada celda (Utility AI):                   │
│  │       │   ├── + recursos (×10)                               │
│  │       │   ├── - carga viral (×15)                            │
│  │       │   ├── - densidad excesiva (×8)                       │
│  │       │   ├── + presión social                               │
│  │       │   ├── - distancia a migración (×peso)                │
│  │       │   ├── + memoria espacial (preferred_sector +5)       │
│  │       │   └── - distancia desde actual (×curiosity_factor)   │
│  │       ├── Incluir casilla actual como opción (inercia +5)    │
│  │       ├── Filtrar casillas ocupadas                          │
│  │       └── Selección probabilística (temperatura)             │
│  └── Registrar movimiento en pending.movements                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 3: RESOLUCIÓN DE COLISIONES                          │
│                                                                 │
│ MovementResolver:                                               │
│  ├── Identificar casillas bloqueadas (agentes estáticos)        │
│  ├── Agrupar peticiones por celda destino                       │
│  ├── Para cada destino:                                         │
│  │   ├── Si bloqueado por estático → cancelar movimientos       │
│  │   ├── Si un solo candidato → movimiento válido               │
│  │   └── Si conflicto → random.choice entre candidatos          │
│  └── Reemplazar pending.movements con movimientos validados     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. MovementCapabilities - Capacidades de Movimiento

**📁 Archivo**: `systems/movement/movement_capabilities.py`
**🌍 Equivalencia real**: La fisiología locomotora del organismo: si puede caminar, volar, nadar, etc.

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `can_move` | `bool` | Motricidad | ¿Puede moverse? (mobility > 0.1) |
| `can_migrate` | `bool` | Resistencia viajera | ¿Puede hacer migraciones largas? |
| `can_walk` | `bool` | Locomoción terrestre | Movilidad en tierra |
| `can_fly` | `bool` | Vuelo | flight > 0.5 |
| `can_swim` | `bool` | Natación | swimming > 0.5 |
| `can_burrow` | `bool` | Excavación | burrowing > 0.5 |
| `movement_speed` | `float` | Velocidad relativa | [0.5, 2.0] |
| `vision_range` | `float` | Agudeza visual | [0.5, 5.0] |
| `smell_range` | `float` | Agudeza olfativa | [0.0, 3.0] |
| `is_social` | `bool` | Tendencia grupal | sociability > 0.7 |
| `is_territorial` | `bool` | Defensa territorial | territoriality > 0.7 (si no social) |
| `exploration_tendency` | `float` | Curiosidad | [0.0, 1.0] |
| `needs_ground_resources` | `bool` | Dependencia del suelo | Si no fotosintetiza |

#### Reglas de derivación del genoma

| Rasgo | Regla | Resultado |
|-------|-------|-----------|
| mobility | `> 0.1` | `can_move = True` |
| swimming, mobility | `swimming > 0.7 AND mobility < 0.5` | Pez: no camina |
| mobility, is_primarily_swimmer | `> 0.3 AND not primarily_swimmer` | `can_walk = True` |
| flight | `> 0.5` | `can_fly = True` |
| swimming | `> 0.5` | `can_swim = True` |
| burrowing | `> 0.5` | `can_burrow = True` |
| Combinado | `can_move AND mobility > 0.5 AND (speed OR flight OR swimming > 0.5) AND curiosity > 0.3` | `can_migrate = True` |

#### Ejemplos

```python
human_caps = MovementCapabilities.from_genome(human_genome)
# modes=['walk'], speed=1.0, vision=1.5, social=social, can_migrate=True

bird_caps = MovementCapabilities.from_genome(bird_genome)
# modes=['walk', 'fly'], can_migrate=True

fish_caps = MovementCapabilities.from_genome(fish_genome)
# modes=['swim'], can_walk=False, can_migrate=True

plant_caps = MovementCapabilities.from_genome(plant_genome)
# modes=['static'], can_move=False, needs_ground_resources=False
```

#### Consideraciones

- **Inmutable**: una vez creada, no se modifica
- **Determinista**: mismo genoma → mismas capacidades
- **No conoce especies**: solo consulta rasgos
- Si un rasgo no existe, usa valores por defecto apropiados
- Los peces NO pueden caminar (nadadores exclusivos)
- Las aves SÍ pueden caminar y volar

---

### 2. MovementSystem - Movimiento Táctico

**📁 Archivo**: `systems/movement/movement_system.py`
**🌍 Equivalencia real**: La decisión momento a momento: "¿dónde doy el siguiente paso?"

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Configuración

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `eval_radius` | 1 | Radio de evaluación base |
| `social_distance` | 10.0 | Umbral de distancia social |
| `sector_size` | 10 | Tamaño de sector para memoria |
| `selection_temperature` | 2.0 | Temperatura de selección probabilística |

#### Factores de Utility AI

| Factor | Peso | Tipo | Descripción |
|--------|------|------|-------------|
| Recursos | ×10 | + | Comida, agua disponible |
| Carga viral | ×15 | - | Evitar epidemias |
| Densidad excesiva | ×8 | - | Evitar hacinamiento |
| Presión social | variable | ± | Acercarse a familia/pareja |
| Distancia a migración | ×peso (3.0) | - | Si tiene destino |
| Memoria espacial | +5 | + | Si celda en preferred_sector |
| Distancia al actual | ×curiosity_factor | - | Coste de moverse |

#### Radio de evaluación

```python
radius = max(1, int(capabilities.vision_range))
```

- **Visión alta** (águila, humano): evalúa hasta 5 tiles
- **Visión baja** (topo, bacteria): evalúa 1 tile

#### Velocidad de movimiento

```python
max_step = capabilities.movement_speed
if capabilities.can_fly:
    max_step *= 1.5  # Las aves cubren más terreno
```

#### Selección probabilística (Fase B)

```python
selected = SocialPressureCalculator.probabilistic_selection(
    available_cells, temperature=self.selection_temperature
)
```

- **Temperatura baja (0.5)**: comportamiento determinista, elige casi siempre la mejor
- **Temperatura alta (5.0)**: comportamiento muy aleatorio

#### Curiosity factor

```python
curiosity_factor = 0.5 * (1.0 - curiosity) if curiosity > 0.6 else 1.0 * (1.0 - curiosity)
```

- **Curiosidad alta**: menor penalización por distancia → explora más
- **Curiosidad baja**: mayor penalización → se queda cerca

#### Casilla actual (inercia)

La casilla actual del agente se incluye con bonus +5.0 para evitar movimientos innecesarios. Si se selecciona, el agente se queda quieto.

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada person con can_move:
        ├── Si ya tiene movimiento registrado → skip
        │
        ├── Si tiene migration_target:
        │   └── _move_towards_target(person, target, ...)
        │       ├── Calcular dirección vectorial
        │       ├── Normalizar a max_step
        │       ├── Envolver como toroide
        │       ├── Si casilla destino ocupada → buscar adyacentes libres
        │       └── pending.register_movement(...)
        │
        └── Si no tiene destino:
            └── _evaluate_nearby_cells(person, ...)
                ├── Incluir casilla actual con bonus +5
                ├── Evaluar celdas en radio vision_range
                │   └── Para cada celda: _score_cell(...)
                ├── Ordenar por puntuación
                ├── Filtrar casillas ocupadas (excepto actual)
                ├── Selección probabilística
                └── pending.register_movement si cambia
```

#### Movimiento hacia destino migratorio

Si el agente tiene `migration_target`:
- Calcula dirección vectorial hacia el destino
- Normaliza a un paso de tamaño `max_step`
- Envuelve como toroide (sale por un lado, aparece por otro)
- Si la casilla está ocupada, busca adyacentes libres
- Si todas ocupadas, no se mueve

#### Cálculo de score por celda

```python
def _score_cell(self, cell_x, cell_y, context, state, person, ...):
    score = 0.0
    
    # 1. RECURSOS (atracción)
    resources = context.get_resources_at(cell_x, cell_y)
    score += resources * 10.0
    
    # 2. CARGA VIRAL (repulsión)
    viral_load = self._get_viral_load(state, cell_x, cell_y)
    score -= viral_load * 15.0
    
    # 3. DENSIDAD LOCAL (repulsión)
    pressure = context.get_local_pressure(cell_x, cell_y)
    excess_pressure = max(0.0, pressure - 1.0)
    score -= excess_pressure * 8.0
    
    # 4. PRESIÓN SOCIAL (atracción a familia/pareja)
    social_press = self.social_pressure.calculate_pressure_for_cell(
        person, cell_x, cell_y, state
    )
    score += social_press
    
    # 5. DISTANCIA AL DESTINO MIGRATORIO
    if migration_target is not None:
        dist_to_migration = math.sqrt((cell_x - mt_x)**2 + (cell_y - mt_y)**2)
        score -= dist_to_migration * migration_weight
    
    # 6. MEMORIA ESPACIAL (preferred_sector)
    if preferred_sector is not None:
        cell_sector = (cell_x // self.sector_size, cell_y // self.sector_size)
        if cell_sector == preferred_sector:
            score += 5.0
    
    # 7. COSTE POR DISTANCIA (curiosity)
    distance_from_current = math.sqrt(dx*dx + dy*dy)
    score -= distance_from_current * curiosity_factor
    
    return score
```

---

### 3. MovementResolver - Arbitraje de Colisiones

**📁 Archivo**: `systems/movement/movement_resolver.py`
**🌍 Equivalencia real**: El protocolo de tráfico que evita que dos personas ocupen el mismo espacio.

#### Regla fundamental

**1 agente = 1 casilla**. Dos agentes no pueden terminar el tick en la misma celda.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── Aborto temprano si pending.movements está vacío
    │
    ├── 1. Identificar casillas bloqueadas:
    │   └── Para cada person:
    │       ├── Si en pending.deaths → skip
    │       └── Si NO se mueve este tick:
    │           └── casillas_bloqueadas.add((person.x, person.y))
    │
    ├── 2. Agrupar peticiones por destino:
    │   └── Para cada (entity_id, (target_x, target_y)):
    │       ├── Si en pending.deaths → skip (doble validación)
    │       ├── Clamping estricto a límites del mapa
    │       └── peticiones_por_celda[destino].append(entity_id)
    │
    ├── 3. Arbitrar conflictos:
    │   └── Para cada destino y candidatos:
    │       ├── REGLA A: Si destino en casillas_bloqueadas:
    │       │   └── Cancelar todos (continuar sin agregar)
    │       ├── REGLA B: Si un solo candidato:
    │       │   └── movimientos_validados[candidato] = destino
    │       └── REGLA C: Si conflicto (varios candidatos):
    │           └── ganador = random.choice(candidatos)
    │               └── movimientos_validados[ganador] = destino
    │
    └── 4. Reemplazo atómico:
        └── pending.movements = movimientos_validados
```

#### Reglas de arbitraje

| Regla | Condición | Resultado |
|-------|-----------|-----------|
| **A: Bloqueo estático** | Destino ocupado por agente no-moviéndose | Cancelar todos los movimientos hacia allí |
| **B: Sin conflicto** | Un solo candidato al destino | Movimiento válido |
| **C: Conflicto dinámico** | Múltiples candidatos al mismo destino | `random.choice` entre ellos |

#### Consideraciones

- **Fail-safe de muertos**: descarta agentes en `pending.deaths` dos veces
- **Clamping estricto**: nunca sale de los límites del mapa
- **Aleatoriedad justa**: conflictos se resuelven con `random.choice`, no por orden de ID
- **Cancelación en cascada**: si destino está bloqueado, todos los peticionarios se quedan donde están
- **Reemplazo atómico**: al final, `pending.movements` contiene solo movimientos validados

#### Ejemplos

```python
# Caso 1: Destino libre
pending.movements = {101: (50, 50)}
# Resultado: {101: (50, 50)} - movimiento válido

# Caso 2: Conflicto entre dos agentes
pending.movements = {101: (50, 50), 102: (50, 50)}
# Resultado: random.choice → {101: (50, 50)} o {102: (50, 50)}

# Caso 3: Destino bloqueado por agente estático
# Agente 200 está en (50, 50) y NO se mueve
pending.movements = {101: (50, 50), 102: (50, 50)}
# Resultado: {} - todos cancelados

# Caso 4: Coordenadas fuera de límites
pending.movements = {101: (150, -5)}  # Fuera del mapa 100x100
# Resultado: {101: (99, 0)} - clampeado a límites
```

---

### 4. MigrationSystem - Migraciones Masivas

**📁 Archivo**: `systems/movement/migration_system.py`
**🌍 Equivalencia real**: Las grandes migraciones animales/humanas provocadas por hambre, guerra, clima, o impulsos internos.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Configuración

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `arrival_threshold` | 5.0 | Distancia para considerar llegada |
| `migration_cooldown_days` | 90.0 | Cooldown entre migraciones |
| `migration_reevaluation_days` | 30.0 | Reevaluar destino cada 30 días |
| `migration_samples` | 20 | Número de muestras al buscar destino |
| `migration_action_threshold` | 0.85 | Umbral de motivación para migrar |

#### Push factors (factores de expulsión)

| Factor | Umbral | Intensidad |
|--------|--------|------------|
| Superpoblación | `local_pressure > 1.8` | `pressure` |
| Hambre | `energy < 0.3 AND resources < 0.2` | `(1-energy) + (1-resources)` |
| Epidemia | `trauma_sickness > 0.7 OR viral_load > 2.0` | `max(trauma, load/5)` |
| Clima hostil | `danger > 0.5` | `danger` |
| **Trauma de abandono** | `trauma_abandonment > 0.6` | `trauma * 1.5` |
| **Trauma de adopción** | `trauma_adoption > 0.7` | `trauma * 1.2` |
| Objetivo psicológico | `current_goal == "EMIGRATE"` | 1.0 |
| Motivación interna | `migration_motivation > threshold (0.85)` | `motivation` |

#### Pull factors (búsqueda de oportunidad)

```python
score = (resources * 15.0) - (pressure * 8.0) - (danger * 25.0)
```

Muestra N puntos aleatorios del mapa (default: 20) y elige el de mayor score, excluyendo destinos muy cercanos (<25 tiles).

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada person con can_migrate:
        │
        ├── 1. INTEGRIDAD: si entity_id en pending.deaths → limpiar estado
        │
        ├── 2. VERIFICAR COOLDOWN:
        │   └── Si (current_day - last_migration) < cooldown → skip
        │
        ├── 3. SEGUIMIENTO DE MIGRACIÓN ACTIVA:
        │   └── Si tiene migration_target:
        │       ├── Si pasó reevaluation_interval (30 días):
        │       │   ├── Verificar _is_target_still_valid(...)
        │       │   ├── Si NO válido: invalidar y buscar nuevo destino
        │       │   └── Si válido: continuar
        │       └── Verificar llegada:
        │           ├── distance = hypot(person.x - tx, person.y - ty)
        │           ├── arrival_threshold = 5.0 * capabilities.movement_speed
        │           └── Si distance <= threshold:
        │               ├── _handle_arrival(person, tx, ty, ...)
        │               ├── clear_migration_target
        │               └── limpiar target_set_day
        │
        ├── 4. EVALUACIÓN DE PUSH FACTORS:
        │   ├── Superpoblación, hambre, epidemia, clima
        │   ├── Trauma de abandono / adopción
        │   ├── Objetivo psicológico "EMIGRATE"
        │   └── Motivación interna 'migration'
        │
        └── 5. BÚSQUEDA DE OPORTUNIDADES (si needs_to_migrate):
            └── best_target = _find_opportunity(...)
                ├── Muestrear 20 puntos aleatorios
                ├── Excluir cercanos (<25 tiles)
                ├── Calcular score de cada uno
                └── Elegir el de mayor score
            └── Si hay best_target:
                ├── pending.set_migration_target(eid, target)
                ├── Registrar cooldown
                └── Registrar target_set_day
```

#### Gestión de destino activo

| Estado | Acción |
|--------|--------|
| **Sin destino** | Evaluar push factors → si hay, buscar pull |
| **Con destino vigente** | Continuar hacia él |
| **Destino caducado (30 días)** | Reevaluar viabilidad |
| **Destino ya no viable** | Invalidar y buscar nuevo |
| **Llegada al destino** | Memoria positiva + establecerse |

#### Llegada al destino

```python
_handle_arrival(person, target_x, target_y, current_day, pending)
    ├── Calcular intensidad según distancia recorrida:
    │   ├── < 50 tiles: 0.3
    │   ├── < 150 tiles: 0.6
    │   └── >= 150 tiles: 0.9
    │
    ├── CognitiveMemorySystem.add_memory(TYPE_MIGRATION, ..., valence=1)
    ├── Reducir motivación "migration" (satisfacción)
    └── Actualizar preferred_sector (arraigo territorial)
```

#### Validación de destino

```python
_is_target_still_valid(target_x, target_y, context, state)
    ├── resources >= 0.15
    ├── pressure <= 2.5
    └── viral_load <= 3.0
```

Si alguna falla → destino inválido.

#### Ejemplos

```python
# Migración por hambruna
# Agente con energy=0.2 y local_resources=0.1
# Push factor "hambre" con intensidad 1.7
# MigrationSystem busca sector con recursos altos
# Asigna destino (80, 120)
# MovementSystem mueve hacia allí cada tick
# Al llegar: memoria positiva + preferred_sector = (8, 12)

# Reevaluación de destino
# Tras 30 días, el destino tiene pressure=2.7
# _is_target_still_valid retorna False
# Invalida destino y busca uno nuevo

# Migración por trauma de abandono
# Agente con trauma_abandonment=0.8
# Push factor: 0.8 * 1.5 = 1.2 (huida emocional)
# Genera migración aunque condiciones locales sean buenas
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                     │
│   mobility, speed, flight, swimming, vision, sociability,      │
│   curiosity, burrowing, territoriality, photosynthesis         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              MovementCapabilities (inmutable)                   │
│   - can_move, can_migrate, can_fly, can_swim                   │
│   - movement_speed, vision_range, smell_range                  │
│   - is_social, is_territorial, exploration_tendency            │
│   - needs_ground_resources                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Migration    │  │ Movement     │  │ MovementResolver │
│ System       │  │ System       │  │                  │
│              │  │              │  │ (arbitraje final)│
│ Push/Pull    │  │ Utility AI   │  │                  │
│ Destinos     │  │ Selección    │  │                  │
│              │  │ probabilíst. │  │                  │
└──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
       │                 │                   │
       │ set_migration_  │ register_         │
       │ target          │ movement          │ reemplaza
       │                 │                   │ pending.
       ▼                 ▼                   │ movements
┌────────────────────────────────────┐       │
│      pending (PendingChanges)      │◄──────┘
│                                    │
│  .movements: Dict[int, Tuple]      │
│  .migration_targets: Dict[int,     │
│                    Tuple]          │
└──────────────┬─────────────────────┘
               │ consolidado por
               ▼
   WorldState.apply_commit()
```

---

## ⚙️ Configuración relevante

```python
# MovementConfig
config.movement.eval_radius = 1
config.movement.social_distance = 10.0
config.movement.selection_temperature = 2.0

# FreeWillConfig (usado por MigrationSystem)
config.free_will.migration_cooldown_days = 90.0
config.free_will.migration_reevaluation_days = 30.0
config.free_will.migration_samples = 20
config.free_will.migration_action_threshold = 0.85
config.free_will.success_reinforcement_rate = -0.5  # Reduce motivación tras éxito

# EnvironmentConfig
config.environment.sector_size = 10
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_movement_capabilities.py` | Derivación de capacidades, todos los tipos de organismos |
| `tests/integration/test_tile_integration.py` | Movimiento y colisiones |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo de decisión completo de un humano

```python
# Tick 100: Agente con motivación "migration" alta
agent._motivations["migration"] = 0.86  # > threshold 0.85

# 1. MigrationSystem detecta motivación alta
#    - No tiene destino activo
#    - Evalúa push factors: ninguno crítico
#    - Pero motivación > threshold → buscar pull factor
#    - Muestrea 20 puntos, encuentra (80, 120) con score alto
#    - pending.set_migration_target(eid, (80, 120))

# 2. MovementSystem ve migration_target
#    - Dirección: (80-50, 120-50) = (30, 70)
#    - Distancia = sqrt(30² + 70²) ≈ 76 tiles
#    - max_step = 1.0 (speed humano)
#    - Nuevo paso: (50 + 30/76, 50 + 70/76) ≈ (50.4, 50.9)
#    - Round: (50, 51)
#    - Si libre: pending.register_movement(eid, 50, 51)

# 3. MovementResolver valida
#    - Si nadie más va a (50, 51): movimiento aprobado
#    - Si hay conflicto: random.choice

# 4. Siguiente tick: agente en (50, 51)
#    - MigrationSystem: aún lejos del destino, continúa
#    - MovementSystem: recalcula dirección
```

### Ejemplo 2: Ave migratoria

```python
bird_caps = MovementCapabilities.from_genome(bird_genome)
print(bird_caps.can_migrate)    # True
print(bird_caps.can_fly)        # True
print(bird_caps.movement_speed) # 1.2

# Push factor: invierno (recursos bajos)
# MigrationSystem asigna destino cálido
# MovementSystem: max_step = 1.2 * 1.5 (por vuelo) = 1.8 tiles/tick
# Viaja 1.8 tiles cada tick hasta llegar
# Al llegar: memoria positiva + establece preferred_sector
```

### Ejemplo 3: Planta (sin movimiento)

```python
plant_caps = MovementCapabilities.from_genome(plant_genome)
print(plant_caps.can_move)      # False

# MovementSystem: if not capabilities.can_move: continue
# MigrationSystem: if not capabilities.can_migrate: continue
# La planta nunca se mueve, solo crece y se reproduce in situ
```

### Ejemplo 4: Conflicto de movimiento resuelto

```python
# Tres agentes quieren la misma casilla (50, 50)
pending.movements = {
    101: (50, 50),
    102: (50, 50),
    103: (50, 50),
}

# MovementResolver:
# peticiones_por_celda[(50, 50)] = [101, 102, 103]
# Conflicto → random.choice([101, 102, 103]) → gana 102
# pending.movements = {102: (50, 50)}
# Los otros dos (101 y 103) se quedan donde están
```

### Ejemplo 5: Wrapping toroidal

```python
# Mapa 100x100
# Agente en (99, 50) quiere moverse a la derecha
# Nuevo x = (99 + 1) % 100 = 0
# Agente aparece en (0, 50) - lado opuesto del mapa

# Simula superficie esférica del planeta
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Utility AI**: decisión multicriterio con puntuación
- **Selección probabilística**: temperatura controla predictibilidad
- **Arbitraje justo**: `random.choice` sin sesgos de ID
- **Regla 1 agente = 1 casilla**: garantizada por MovementResolver
- **Wrapping toroidal**: el mundo es una esfera sin bordes
- **Inercia**: la casilla actual tiene bonus +5

### Arquitectura de decisión

```
GENOMA
   ↓
MovementCapabilities (qué puede hacer)
   ↓
MigrationSystem (decisión a largo plazo)
   ↓
MovementSystem (decisión a corto plazo, Utility AI)
   ↓
MovementResolver (arbitraje)
   ↓
PendingChanges → WorldState.apply_commit()
```

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| Aborto temprano | MovementResolver | No procesar si no hay movimientos |
| Comparaciones cuadradas | MovementSystem | Evita `math.sqrt` cuando es posible |
| Reevaluación cada 30 días | MigrationSystem | No calcular cada tick |
| Muestreo aleatorio (20 puntos) | MigrationSystem | No evaluar todo el mapa |
| Bounding box en `_find_nearby_agents` | (usado por otros) | O(N²) → O(N·k) |

### Limitaciones
- No hay planificación a largo plazo (solo reacción inmediata)
- Los agentes no cooperan en rutas de migración
- No hay aprendizaje social (solo por experiencia propia)
- El movimiento es grid-based (no continuo)
- MovementSystem no ve más allá de `vision_range`

### Errores comunes
- ❌ Usar `pending.movements` sin pasar por `MovementResolver` (colisiones no arbitradas)
- ❌ Asumir que todos los organismos pueden moverse (filtrar por `can_move`)
- ❌ Poner umbral de migración muy bajo (todos migran constantemente)
- ❌ Olvidar el wrapping toroidal al calcular distancias
- ❌ Modificar `pending.movements` directamente después del resolver (se pierde el arbitraje)

---

## 🎓 Conceptos clave

### ¿Por qué Utility AI?

**Principio de decisión multicriterio**:
- El agente no "piensa" en cada factor
- Simplemente evalúa celdas con puntuación total
- La mejor celda (probabilísticamente) se elige
- Comportamiento complejo emerge de reglas simples

### ¿Por qué selección probabilística con temperatura?

**Principio de no-determinismo**:
- Temperatura baja (0.5): comportamiento casi determinista
- Temperatura alta (5.0): comportamiento muy aleatorio
- Esto evita patrones rígidos y predecibles
- Más realista: los humanos no siempre eligen lo óptimo

### ¿Por qué 1 agente = 1 casilla?

**Principio de simplicidad espacial**:
- Evita listas de agentes por celda
- Ocupación es O(1) con un Dict
- Los movimientos son atómicos (liberar + ocupar)
- Evita problemas de superposición visual

### ¿Por qué wrapping toroidal?

**Principio de mundo sin bordes**:
- El mundo es finito pero sin límites
- Si sales por la derecha, apareces por la izquierda
- Simula superficie esférica del planeta
- Evita problemas de agentes atrapados en bordes

### ¿Por qué reevaluar destino migratorio?

**Principio de adaptación**:
- El mundo cambia mientras el agente viaja
- Un destino prometedor puede volverse hostil
- Reevaluar cada 30 días evita migraciones absurdas
- Flexibilidad sin indecisión constante

### ¿Por qué inercia (bonus +5 a la casilla actual)?

**Principio de economía de movimiento**:
- Moverse tiene un coste (energía, riesgo)
- Si todas las opciones son iguales, mejor quedarse
- Evita oscilaciones inútiles entre celdas similares
- Comportamiento más estable y realista

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 4 |
| Atributos de MovementCapabilities | 13 |
| Factores de Utility AI | 7 |
| Push factors de migración | 8 |
| Reglas de arbitraje | 3 |
| Tests cubriendo movimiento | ~15 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Rutas migratorias históricas (transmisión cultural)
- [ ] Fatiga física (no poder moverse tras mucho esfuerzo)
- [ ] Líderes de migración (agentes seguidos por otros)
- [ ] Evitación activa de zonas peligrosas

### Posibles
- [ ] Movimiento continuo (no grid-based)
- [ ] Senderos y caminos (agentes siguen rutas)
- [ ] Territorios marcados (orina, feromonas)
- [ ] Nadar contra corriente (modificadores ambientales)
- [ ] Volar con viento (modificadores de velocidad)
- [ ] Dormir en movimiento (algunas aves)
- [ ] Formación en V (migración coordinada)

---

*Documento: 07_MOVIMIENTO.md*
*Versión: 1.0*