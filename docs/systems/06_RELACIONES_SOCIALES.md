# 06 - Relaciones Sociales

## 📋 Resumen

El **Sistema de Relaciones Sociales** modela la compleja red de vínculos entre agentes: desde el primer encuentro hasta las relaciones más profundas (amistad, romance, rivalidad, enemistad). Las relaciones son **emergentes**: no se asignan linealmente, sino que surgen de la acumulación de experiencias compartidas moduladas por la personalidad, los sesgos cognitivos y los objetivos individuales.

**Filosofía fundamental**: *Las etiquetas relacionales emergen de memorias acumuladas, no se asignan manualmente.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Calcular compatibilidad multifactorial entre agentes (`CompatibilityEngine`)
- Generar eventos de intimidad que llevan a relaciones emergentes (`MarriageSystem`)
- Detectar nuevos encuentros entre agentes cercanos (`RelationshipManager`)
- Traducir eventos en recuerdos personales asimétricos (`RelationshipExperienceEngine`)
- Generar experiencias basadas en etiquetas relacionales (`ExperienceGenerator`)
- Influir en decisiones conductuales según etiquetas (`BehaviorInfluence`)
- Detectar patrones narrativos complejos (`NarrativeEngine`)
- Generar etiquetas relacionales a partir de memorias (`LabelGenerator`)
- Gestionar adopciones con algoritmo de utilidad (`AdoptionSystem`)

**NO es responsable de:**
- ❌ Decidir con quién se casa un agente (eso emerge del sistema completo)
- ❌ Generar emociones directamente (las emociones derivan de memorias)
- ❌ Almacenar el genoma (eso lo hace `Genome`)
- ❌ Gestionar núcleos residenciales (eso lo hace `WorldState`)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **CompatibilityEngine** | Primera impresión / atracción | Química inicial |
| **MarriageSystem** | Cortejo y apareamiento | Búsqueda de pareja |
| **RelationshipManager** | Red social personal | Conocidos |
| **RelationshipExperienceEngine** | Memoria autobiográfica | Recuerdos |
| **ExperienceGenerator** | Interacciones cotidianas | Vida social |
| **BehaviorInfluence** | Sesgo hacia amigos/enemigos | Preferencia social |
| **NarrativeEngine** | Historia que contamos de una relación | Narrativa personal |
| **LabelGenerator** | Cómo definimos una relación | Etiqueta social |
| **AdoptionSystem** | Acogida familiar | Adopción |
| **PersonalMemory** | Recuerdo episódico | Memoria declarativa |
| **WorldEvent** | Evento objetivo | Hecho real |
| **BiasEngine** | Sesgos cognitivos | Psicología |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/relationships/compatibility_engine.py` | `CompatibilityEngine` | Cálculo de compatibilidad |
| `systems/relationships/marriage_system.py` | `MarriageSystem` | Formación de parejas |
| `systems/relationships/relationship_manager.py` | `RelationshipManager` | Detección de encuentros |
| `systems/relationships/relationship_experience_engine.py` | `RelationshipExperienceEngine` | Motor de experiencias |
| `systems/relationships/experience_generator.py` | `ExperienceGenerator` | Generador de experiencias |
| `systems/relationships/behavior_influence.py` | `BehaviorInfluence` | Influencia conductual |
| `systems/relationships/narrative_engine.py` | `NarrativeEngine` | Detección de narrativas |
| `systems/relationships/label_generator.py` | `LabelGenerator` | Generación de etiquetas |
| `systems/adoptions/adoption_system.py` | `AdoptionSystem` | Sistema de adopciones |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              CICLO DE VIDA RELACIONAL                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: ENCUENTROS INICIALES                                    │
│                                                                 │
│ RelationshipManager:                                            │
│  ├── Poblar SpatialGrid con todos los agentes                   │
│  ├── Para cada agente: buscar vecinos cercanos (radio 35)       │
│  ├── Verificar capacidades sociales (SocialCapabilities)        │
│  ├── Verificar compatibilidad de orientaciones                  │
│  └── Si random() < probabilidad ajustada por distancia:         │
│      └── Crear WorldEvent tipo "met" + PersonalMemory para ambos│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: FORMACIÓN DE PAREJAS                                    │
│                                                                 │
│ MarriageSystem:                                                 │
│  ├── Filtrar agentes elegibles:                                 │
│  │   ├── Adultos, no embarazadas, no en luto                    │
│  │   ├── Sin pareja romántica activa (verificar etiquetas)      │
│  │   └── Puede formar vínculos románticos (SocialCapabilities)  │
│  ├── Buscar candidatos en radio 20:                             │
│  │   ├── Compatibilidad de orientación                          │
│  │   ├── No parientes cercanos                                  │
│  │   └── Usar CompatibilityEngine para puntuar                  │
│  ├── Seleccionar mejor candidato                                │
│  └── Generar evento INTIMACY → RelationshipExperienceEngine     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: EXPERIENCIAS COTIDIANAS                                 │
│                                                                 │
│ ExperienceGenerator:                                            │
│  ├── Para cada relación con etiquetas activas:                  │
│  │   ├── Consultar tabla de probabilidades por etiqueta         │
│  │   ├── Si random() < probabilidad:                            │
│  │   │   ├── Seleccionar experiencia (cooperation, care, etc.)  │
│  │   │   ├── Obtener contexto rico según etiqueta               │
│  │   │   └── Generar evento → RelationshipExperienceEngine      │
│                                                                 │
│ RelationshipExperienceEngine:                                   │
│  ├── Crear WorldEvent objetivo                                  │
│  ├── Crear PersonalMemory ASIMÉTRICA para cada agente           │
│  │   ├── Modulada por personalidad (sociability, temperament)   │
│  │   ├── Filtrada por objetivos personales (GoalFilter)         │
│  │   └── Sesgada cognitivamente (BiasEngine)                    │
│  └── Añadir memorias a Relationship.memories                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: NARRATIVAS Y ETIQUETAS                                  │
│                                                                 │
│ NarrativeEngine:                                                │
│  ├── Analizar memorias recientes (ventana 365 días)             │
│  ├── Detectar patrones:                                         │
│  │   ├── Tensión acumulada → "Hay mucha tensión últimamente"    │
│  │   ├── Salvador en crisis → "Es mi roca en momentos difíciles"│
│  │   ├── Relación superficial → "Nuestra relación es superficial"│
│  │   ├── Traición → "Me traicionó y no lo olvido"               │
│  │   ├── Apoyo profundo → "Siempre puedo contar con esta persona"│
│  │   └── Distanciamiento → "Nos estamos distanciando"           │
│  └── Fortalecer/crear narrativas en Relationship                │
│                                                                 │
│ LabelGenerator:                                                 │
│  ├── Evaluar pesos acumulados de memorias                       │
│  ├── Generar etiquetas: Amante, Amigo, Rival, Enemigo, etc.     │
│  └── Las etiquetas emergen de umbrales de memorias              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: INFLUENCIA CONDUCTUAL                                   │
│                                                                 │
│ BehaviorInfluence:                                              │
│  ├── get_target_priority(agent, target):                        │
│  │   └── Multiplicador [0.0-2.0] para selección de targets      │
│  ├── get_social_attraction(agent, target):                      │
│  │   └── Valor [-5.0, 10.0] para evaluación de celdas           │
│  └── get_multiple_social_anchors(agent, all_agents):            │
│      └── Top N anclas sociales del agente                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 6: ADOPCIONES (independiente)                              │
│                                                                 │
│ AdoptionSystem:                                                 │
│  ├── Detectar huérfanos elegibles                               │
│  ├── Agrupar por hermandad (Union-Find)                         │
│  ├── Filtrar familias elegibles (hard limits)                   │
│  ├── Calcular suitability (Utility AI)                          │
│  ├── Asignar hermanos juntos si es posible                      │
│  ├── Aplicar penalizaciones a no adoptados                      │
│  └── Generar memorias episódicas de adopción                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. CompatibilityEngine - Motor de Compatibilidad

**📁 Archivo**: `systems/relationships/compatibility_engine.py`
**🌍 Equivalencia real**: La química inicial entre dos personas: atracción, afinidad, cercanía.

#### Entradas del cálculo

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `p1`, `p2` | `Person` | Los dos individuos | Personas a evaluar |
| `current_day` | `float` | Tiempo presente | Para decaimiento de memorias |
| `free_will_boost` | `float` | Libre albedrío | Boost opcional |

#### Factores de compatibilidad

| Factor | Peso | Rango | Descripción |
|--------|------|-------|-------------|
| `orientation_score` | Multiplicador | 0.0-1.0 | Compatibilidad de orientación sexual |
| `age_score` | `cfg.age_weight` | 0.0-1.0 | Diferencia de edad (peor si >20 años) |
| `distance_score` | `cfg.distance_weight` | 0.0-1.0 | Distancia física (peor si >50 tiles) |
| `affinity` | `cfg.affinity_weight` | 0.0-1.0 | Afinidad base + memorias compartidas |

#### Flujo interno

```
calculate_compatibility(p1, p2, current_day, free_will_boost)
    │
    ├── orientation_score = is_orientation_compatible(
    │       p1.sexual_orientation, p2.sexual_orientation,
    │       tolerance=cfg.orientation_tolerance)
    ├── Si orientation_score <= 0.0 → return 0.0
    │
    ├── age_score = max(0, 1 - (age_diff_years / 20))
    ├── distance_score = max(0, 1 - (distance / 50))
    │
    ├── affinity = _calculate_base_affinity(p1, p2, current_day)
    │   ├── soc_score = 1 - (soc_diff / 2.0)
    │   ├── temp_score = temp_diff / 1.5 (opuestos se atraen)
    │   ├── base = (soc_score + temp_score) / 2
    │   └── Ajustar con memorias compartidas:
    │       ├── shared_positive * 0.002 (máx +0.3)
    │       └── shared_negative * 0.003 (máx -0.3)
    │
    ├── raw_score = affinity*cfg.affinity_weight
    │             + age_score*cfg.age_weight
    │             + distance_score*cfg.distance_weight
    │
    ├── base_compatibility = raw_score * orientation_score
    └── final_score = clamp(0, 1, base + free_will_boost)
```

#### Ejemplos

```python
score = compatibility_engine.calculate_compatibility(p1, p2, current_day=365.0)
# score = 0.73 → Alta compatibilidad

# Con boost de libre albedrío
score = compatibility_engine.calculate_compatibility(p1, p2, current_day, free_will_boost=0.2)
```

#### Consideraciones

- Si las orientaciones son incompatibles, la compatibilidad es 0.0
- Los temperamentos opuestos se atraen (temp_score alto con diferencia alta)
- Las memorias positivas tienen peso menor (×0.002) que las negativas (×0.003) — asimetría natural
- Las memorias compartidas tienen límite superior (±0.3) para no dominar

---

### 2. MarriageSystem - Formación de Parejas

**📁 Archivo**: `systems/relationships/marriage_system.py`
**🌍 Equivalencia real**: El proceso de cortejo: búsqueda de pareja, compatibilidad, intimidad.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Todos los agentes |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Flujo interno

```
Para cada person en all_persons:
    │
    ├── FILTROS DE ELEGIBILIDAD:
    │   ├── Si entity_id en pending.deaths → skip
    │   ├── Si NOT SocialCapabilities.can_have_romantic_bonds → skip
    │   ├── Si NOT is_adult → skip
    │   ├── Si is_pregnant → skip
    │   ├── Si está en luto (< widowhood_duration) → skip
    │   └── Si ya tiene pareja romántica (verificar etiquetas) → skip
    │
    ├── BÚSQUEDA DE CANDIDATOS (radio 20):
    │   ├── Filtrar muertos, no adultos, embarazadas
    │   ├── Excluir agentes con pareja romántica
    │   ├── Verificar compatibilidad de orientación
    │   └── Excluir parientes cercanos
    │
    ├── SELECCIÓN DEL MEJOR:
    │   ├── Calcular compatibility con cada candidato
    │   ├── Ajustar: score -= (distancia/radio) * 0.2
    │   └── Elegir el de mayor score
    │
    └── GENERAR EVENTO DE INTIMIDAD:
        └── _IntimacyEvent(intensity=random(0.4, 0.8))
            → RelationshipExperienceEngine.process_event(...)
```

#### Tabla de compatibilidad de orientación

| Orientación del buscador | Compatible con |
|--------------------------|----------------|
| HETEROSEXUAL | Solo género opuesto |
| HOMOSEXUAL | Solo mismo género |
| BISEXUAL | Ambos géneros |
| MOSTLY_HETERO | Opuesto (100%) o mismo (10%) |
| MOSTLY_HOMO | Mismo (100%) o opuesto (10%) |
| BISEXUAL_HETERO | Opuesto (100%) o mismo (30%) |
| BISEXUAL_HOMO | Mismo (100%) o opuesto (30%) |

#### Verificación de monogamia

Se verifica monogamia usando **etiquetas emergentes**, no estados lineales:
- Etiquetas románticas: `"Amante"`, `"Interés Romántico"`
- Si el agente tiene alguna de estas etiquetas activa → ya tiene pareja
- **Optimización**: caché `_romantic_partner_cache` por tick

#### Consideraciones

- **Periodo de luto**: 365 días tras perder pareja (configurable)
- **Cooldown de intimidad**: 30 días entre eventos (configurable)
- **Radio de búsqueda**: 20 tiles (configurable)
- **Parientes cercanos**: padres, hermanos — siempre excluidos

---

### 3. RelationshipManager - Detección de Encuentros

**📁 Archivo**: `systems/relationships/relationship_manager.py`
**🌍 Equivalencia real**: La red social personal: conocer gente nueva en tu vecindad.

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── Limpiar _relationships_created_this_tick
    ├── spatial_grid.populate_from_state(state)  ← O(N)
    │
    └── Para cada person:
        ├── nearby_agents = spatial_grid.get_nearby_agents(person, 35)
        │
        └── Para cada other en nearby_agents:
            ├── Si other.entity_id <= person.entity_id → skip (evitar duplicados)
            ├── Verificar SocialCapabilities.can_recognize_individuals en AMBOS
            ├── Verificar compatibilidad de orientaciones
            ├── Si relación ya tiene memorias → skip
            ├── Si random() >= 0.15 → skip (filtro rápido)
            ├── Si random() >= (1 - distancia/35) → skip
            │
            └── Crear relación inicial:
                ├── Generar event_id determinista (MD5 de IDs + día)
                ├── Crear WorldEvent(event_type="met")
                ├── Crear PersonalMemory de primera impresión
                │   ├── base_valence = 0.2 (positiva por defecto)
                │   ├── personality_modifier basado en sociability/temperament
                │   └── uncertainty = gauss(1.0, 0.2)
                └── Añadir a Relationship.memories de ambos
```

#### Optimizaciones críticas

1. **SpatialGrid**: reduce búsquedas de O(N²) a O(N)
2. **Comparaciones cuadradas**: evita `math.sqrt` cuando es posible
3. **Filtro aleatorio rápido**: descarta 85% de pares sin calcular distancia
4. **Set de relaciones creadas**: evita procesar el mismo par dos veces

#### Primera impresión

| Factor | Modificador |
|--------|-------------|
| Base valence | +0.2 |
| Base weight | 15.0 |
| Sociability alta | +30% peso |
| Temperament alto (>0.7) | -20% peso (más crítico) |
| Incertidumbre | ×gauss(1.0, 0.2) |

---

### 4. RelationshipExperienceEngine - Motor de Experiencias

**📁 Archivo**: `systems/relationships/relationship_experience_engine.py`
**🌍 Equivalencia real**: La memoria autobiográfica: cómo procesamos subjetivamente los eventos.

#### Perfiles de eventos predefinidos

| Tipo de evento | Categoría | Peso base |
|----------------|-----------|-----------|
| CARE | COOPERATION | 40.0 |
| COOPERATION | COOPERATION | 30.0 |
| INTIMACY | ROMANTIC | 50.0 |
| CONFLICT | CONFLICT | 45.0 |
| BETRAYAL | CONFLICT | 80.0 |
| BIRTH | FAMILY | 90.0 |
| PARTNER_DEATH | TRAUMA | 95.0 |
| MET | SOCIAL | 15.0 |

#### Flujo interno

```
process_event(event, agent_a, agent_b, current_day)
    │
    ├── Crear WorldEvent objetivo con intensidad objetiva
    │
    ├── mem_a = _create_personal_memory(world_event, A, B, base_weight)
    ├── mem_b = _create_personal_memory(world_event, B, A, base_weight)
    │
    ├── rel_a.add_memory(mem_a)
    └── rel_b.add_memory(mem_b)
```

#### Creación de memoria personal (asimétrica)

```
_create_personal_memory(world_event, owner, partner, base_weight)
    │
    ├── 1. PERSONALIDAD (Fase 0):
    │   ├── sociability, independence, temperament
    │   ├── valence según categoría (+1 coop/romantic/family, -1 conflict)
    │   └── Ajustes específicos por tipo de evento
    │
    ├── 2. Crear PersonalMemory temporal
    │
    ├── 3. FILTRO DE OBJETIVOS (GoalFilter):
    │   └── goal_multiplier = max relevance entre owner_goals
    │
    ├── 4. MOTOR DE SESGOS (BiasEngine):
    │   └── Aplicar negativity_bias, recency, betrayal_context, etc.
    │
    └── 5. Determinar rol especial:
        ├── TRAUMA: betrayal, partner_death, child_death
        └── ANCHOR: birth, marriage, cohabitation_start
```

#### Vida media por tipo de evento

| Evento | Vida media (días) | Equivalencia |
|--------|------------------|--------------|
| MET | 30 | Conocidos se olvidan rápido |
| CARE | 180 | Cuidados se recuerdan meses |
| COOPERATION | 180 | Cooperación duradera |
| INTIMACY | 365 | Intimidad se recuerda un año |
| CONFLICT | 240 | Conflictos duran 8 meses |
| BETRAYAL | 1000 | Traición tarda ~3 años en sanar |
| BIRTH | ∞ | Nacimientos no se olvidan |
| PARTNER_DEATH | ∞ | Muerte de pareja no se olvida |

#### Consideraciones

- **Asimetría fundamental**: mismo evento → recuerdos diferentes para A y B
- **Sesgos cognitivos**: negativity bias, idealización post-mortem, recencia
- **Filtros de objetivos**: si el evento es relevante para tus metas, pesa más
- **Roles especiales**: traumas y anclas no decaen con el tiempo

---

### 5. ExperienceGenerator - Generador de Experiencias

**📁 Archivo**: `systems/relationships/experience_generator.py`
**🌍 Equivalencia real**: Las interacciones cotidianas que mantienen vivas las relaciones.

#### Tabla de probabilidades por etiqueta

| Etiqueta | Cooperation | Care | Intimacy | Competition | Conflict | Betrayal |
|----------|-------------|------|----------|-------------|----------|----------|
| Conocido | 0.005 | - | - | - | - | - |
| Aliado | 0.015 | 0.005 | - | - | - | - |
| Amigo | 0.025 | 0.01 | - | - | - | - |
| Interés Romántico | 0.01 | - | 0.015 | - | - | - |
| Amante | 0.02 | - | 0.035 | - | - | - |
| Familia Elegida | 0.015 | 0.025 | - | - | - | - |
| Rival Respetado | 0.005 | - | - | 0.01 | - | - |
| Rival | - | - | - | 0.015 | 0.005 | - |
| Enemigo | - | - | - | - | 0.02 | 0.002 |

#### Contextos ricos por etiqueta

| Etiqueta | Experiencia | Contextos posibles |
|----------|-------------|---------------------|
| Amigo | cooperation | paseo, ayuda_mutua, proyecto_compartido |
| Amigo | care | cuidado_enfermedad, consejo_sabio, apoyo_emocional |
| Amante | intimacy | noche_romantica, confesion_amor, intimidad_profunda |
| Amante | cooperation | construir_hogar, plan_futuro, apoyo_incondicional |
| Rival | competition | competencia_desleal, provocacion |
| Enemigo | conflict | ataque_directo, hostilidad_abierta |
| Enemigo | betrayal | traicion_calculada, sabotaje |
| Familia Elegida | care | cena_familiar, apoyo_incondicional, tradicion_familiar |

#### Flujo interno

```
Para cada agente con relaciones:
    │
    ├── Verificar SocialCapabilities.has_social_awareness
    │
    └── Para cada Relationship con etiquetas activas:
        ├── Para cada etiqueta en labels:
        │   └── Para cada experiencia posible con su probabilidad:
        │       ├── Verificar can_participate_in_event
        │       └── Si random() < probabilidad:
        │           ├── Verificar distancia ≤ 20 tiles
        │           ├── Obtener contexto rico
        │           └── Generar evento → RelationshipExperienceEngine
```

#### Consideraciones

- **Distancia límite**: 20 tiles (las experiencias requieren proximidad)
- **Log interval**: cada 365 ticks para no saturar logs
- **Genética universal**: sin capacidades sociales, no hay experiencias
- **Eventos ligeros**: usa `_ExperienceEvent` dataclass

---

### 6. BehaviorInfluence - Influencia Conductual

**📁 Archivo**: `systems/relationships/behavior_influence.py`
**🌍 Equivalencia real**: Los sesgos sociales: preferimos estar cerca de amigos, lejos de enemigos.

#### Métodos estáticos

##### `get_target_priority(agent, target)` → multiplicador [0.0, 2.0]

| Etiqueta | Prioridad | Interpretación |
|----------|-----------|----------------|
| Amante | 2.0 | Máxima prioridad |
| Amigo | 1.8 | Muy alta |
| Familia Elegida | 1.7 | Muy alta |
| Interés Romántico | 1.6 | Alta |
| Aliado | 1.5 | Alta |
| Conocido | 1.0 | Neutra |
| Rival Respetado | 0.8 | Ligera evitación |
| Rival | 0.6 | Evitación |
| Enemigo | 0.3 | Fuerte evitación |

##### `get_social_attraction(agent, target)` → valor [-5.0, 10.0]

| Etiqueta | Atracción | Interpretación |
|----------|-----------|----------------|
| Amante | 10.0 | Atracción máxima |
| Familia Elegida | 8.0 | Atracción muy alta |
| Amigo | 7.0 | Alta atracción |
| Interés Romántico | 6.0 | Atracción |
| Aliado | 5.0 | Moderada atracción |
| Conocido | 2.0 | Leve atracción |
| Rival Respetado | -1.0 | Leve repulsión |
| Rival | -3.0 | Repulsión |
| Enemigo | -5.0 | Fuerte repulsión |

##### `filter_targets_by_labels(agent, candidates, required, excluded)`

Filtra candidatos basándose en etiquetas requeridas y excluidas.

##### `get_multiple_social_anchors(agent, all_agents, max_anchors)`

Retorna los N agentes más importantes como "anclas sociales" para el movimiento.

#### Ejemplos

```python
# Prioridad para elegir con quién interactuar
priority = BehaviorInfluence.get_target_priority(agent, target, current_day)

# Atracción social para evaluar celdas
attraction = BehaviorInfluence.get_social_attraction(agent, target, current_day)

# Top 3 anclas sociales del agente
anchors = BehaviorInfluence.get_multiple_social_anchors(agent, all_agents, max_anchors=3)
# [(amante, 10.0), (amigo, 7.0), (aliado, 5.0)]

# Filtrar candidatos
amigos = BehaviorInfluence.filter_targets_by_labels(
    agent, candidates,
    required_labels=["Amigo", "Aliado"],
    excluded_labels=["Enemigo"],
)
```

#### Consideraciones

- **Sin capacidades sociales**: todos los métodos retornan valores neutros
- **Estático**: no tiene estado, es una clase utility
- **Usado por**: `FreeWillSystem` (targets) y `MovementSystem` (celdas)

---

### 7. NarrativeEngine - Motor de Narrativas

**📁 Archivo**: `systems/relationships/narrative_engine.py`
**🌍 Equivalencia real**: La historia que nos contamos sobre una relación.

#### Ventana temporal

```python
RECENT_WINDOW_DAYS = 365.0  # Solo recuerdos del último año
```

#### Patrones de narrativa

| Patrón | Condición | Narrativa | Intensidad |
|--------|-----------|-----------|------------|
| A | conflict_weight_recent > 80 | "Últimamente hay mucha tensión" | 0.25 |
| B | support_weight > 150 | "Es mi roca en momentos difíciles" | 0.20 |
| C | social_weight > 100 y deep < 50 | "Nuestra relación es superficial" | 0.15 |
| D | Trauma + "traicion"/"sabotaje" | "Me traicionó y no lo olvido" | 0.60 |
| D' | Trauma sin contexto específico | "Me falló en un momento clave" | 0.40 |
| E | Conflict + "discusion_acalorada" | "Siempre terminamos discutiendo" | 0.25 |
| E' | Conflict sin contexto | "Siempre me falla" | 0.20 |
| F | Cooperation + "ayuda_mutua"/"apoyo_incondicional" | "Siempre puedo contar con esta persona" | 0.25 |
| F' | Cooperation sin contexto | "Siempre me ayuda" | 0.15 |
| G | >180 días sin interacción + <3 memorias | "Nos estamos distanciando" | 0.10 |
| H | Romantic + "noche_romantica"/"confesion_amor" | "Nuestra conexión es profunda" | 0.30 |

#### Flujo interno

```
update_narratives(rel, new_memory, current_day)
    │
    ├── Obtener recuerdos recientes (ventana 365 días)
    ├── Context_lower = new_memory.context.lower()
    │
    ├── Para cada patrón (A-H):
    │   ├── Evaluar condición sobre memorias
    │   └── Si se cumple:
    │       └── rel._strengthen_or_create_narrative(texto, current_day, intensidad)
```

#### Consideraciones

- **Incremental**: se llama solo cuando llega un nuevo recuerdo
- **Context-aware**: usa el contexto del evento para refinar la narrativa
- **Ventana temporal**: solo considera recuerdos de los últimos 365 días
- **Acumulativo**: las narrativas se fortalecen con cada ocurrencia

---

### 8. LabelGenerator - Generación de Etiquetas

**📁 Archivo**: `systems/relationships/label_generator.py`
**🌍 Equivalencia real**: Cómo definimos una relación: "es mi amigo", "es mi enemigo".

*Nota: Basado en uso inferido en otros componentes*

#### Responsabilidad

Genera etiquetas relacionales a partir de la acumulación de memorias ponderadas:

| Etiqueta | Condiciones típicas |
|----------|---------------------|
| Conocido | Memorias sociales leves |
| Aliado | Cooperación sostenida |
| Amigo | Cooperación + care acumulado |
| Interés Romántico | Intimacy emergente |
| Amante | Intimacy acumulado alto |
| Familia Elegida | Care profundo + tiempo |
| Rival Respetado | Competition + cooperation |
| Rival | Competition sostenida |
| Enemigo | Conflict + betrayal |

#### Características

- Las etiquetas son **dinámicas**: pueden cambiar con el tiempo
- **Decaimiento**: etiquetas débiles desaparecen si no se refuerzan
- **Coexistencia**: múltiples etiquetas pueden coexistir (p.ej. "Rival Respetado" + "Aliado")
- **Thresholds**: cada etiqueta tiene un umbral mínimo de peso acumulado

---

### 9. AdoptionSystem - Sistema de Adopciones

**📁 Archivo**: `systems/adoptions/adoption_system.py`
**🌍 Equivalencia real**: El sistema de protección a menores: acogida familiar, servicios sociales.

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── 1. DETECCIÓN DE HUÉRFANOS
    │   ├── Para cada person:
    │   │   ├── No debe estar en pending.deaths
    │   │   ├── Sin adoptive_parents previos
    │   │   ├── Edad ≤ max_orphan_age_days
    │   │   └── Sin padres vivos (biológicos)
    │   └── Lista de orphans
    │
    ├── 2. AGRUPACIÓN POR HERMANDAD (Union-Find O(n))
    │   ├── Agrupar por mother_id compartida
    │   ├── Agrupar por father_id compartido
    │   └── Agrupar por adoptive_parents compartidos
    │
    ├── 3. FILTRADO DE FAMILIAS ELEGIBLES (Hard Limits)
    │   ├── Parejas casadas ≥ min_adoptive_age_days
    │   ├── Singles ≥ min_single_parent_age_days
    │   │   ├── energy ≥ min_single_parent_energy
    │   │   └── stress ≤ max_single_parent_stress
    │   ├── children_count < max_children_for_adoption
    │   ├── NOT is_sick
    │   ├── stress ≤ 0.7
    │   └── local_pressure ≤ 0.8
    │
    ├── 4. ASIGNACIÓN POR GRUPOS DE HERMANOS
    │   ├── Buscar familia que pueda adoptar a TODOS juntos
    │   ├── Si existe: adopción grupal
    │   └── Si no: adopciones individuales separadas
    │
    └── 5. PENALIZACIONES A NO ADOPTADOS
        └── trauma_abandonment, stress, happiness negativos
```

#### Algoritmo de Suitability (Utility AI)

| Factor | Peso | Descripción |
|--------|------|-------------|
| Parentesco | 100 / kinship_degree | Tíos, abuelos, primos |
| Distancia | -0.2 × distancia | Cercanía física |
| Presión local | -50 × pressure | Evitar hacinamiento |
| Estrés (>0.7) | -50 × (stress - 0.7) | Penalización |
| Felicidad | +15 × (happiness - 0.5) | Bonificación |
| Reputación | +20 × (reputation - 0.5) | Buen samaritano |
| Hijos actuales | -5 × children_count | Anti-clustering |
| Adopciones previas | -15 × prev_adoptions | Evita acaparar |
| Estabilidad | +1.5 × años_relación | Parejas estables |
| Senior | -10 | Penalización por edad |
| Edad huérfano | -age_ratio^exp × mult | Huérfanos mayores más difíciles |
| Single parent | -penalty | Penalización |
| Motivación protección | +25 × motivation | Deseo de proteger |
| Motivación cooperación | +15 × motivation | Deseo de cooperar |

#### Integración con memoria

Al adoptar, se generan **recuerdos episódicos** para:
- **Huérfano**: "encontré una familia" (valence +1, intensidad 0.7-0.8)
- **Padre adoptivo**: "adopté a un hijo" (valence +1, intensidad 0.8-0.9)
- **Pareja del padre** (si existe): mismo que padre adoptivo

#### Impacto emocional

| Agente | Happiness | Stress | Energy |
|--------|-----------|--------|--------|
| Padre adoptivo | +0.5 (individual) / +0.6+0.1×N (grupal) | +0.3+0.15×N | -0.1-0.05×N |
| Huérfano individual | -0.6 | +0.7 | - |
| Huérfano grupal | -0.2 | +0.4 | - |

*Donde N = número de hermanos adoptados*

#### Consideraciones

- **Hermanos juntos**: el sistema prioriza no separar hermanos
- **Anti-clustering**: evita que una familia acapare todos los huérfanos
- **Hard limits**: edad, salud, estrés — condiciones no negociables
- **Fallback progresivo**: huérfanos no adoptados acumulan trauma

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                                 │
│                                                                 │
│   Person._relationships: Dict[int, Relationship]                │
│   Relationship.memories: List[PersonalMemory]                   │
│   Relationship.narratives: Dict[str, Narrative]                 │
│   PersonalMemory: WorldEvent + sesgos + rol + half_life         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌────────────────────┐
│ Compatibility│   │  Marriage    │   │ Relationship       │
│ Engine       │   │  System      │   │ Manager            │
│              │   │              │   │                    │
│ Puntuación   │   │ Eventos      │   │ Detección de       │
│ multifactor  │   │ intimidad    │   │ nuevos encuentros  │
└──────┬───────┘   └──────┬───────┘   └────────┬───────────┘
       │                  │                     │
       │ usa              │ genera              │ crea
       ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│           RelationshipExperienceEngine                      │
│  (Traductor de eventos a recuerdos personales asimétricos)  │
│                                                             │
│  WorldEvent → PersonalMemory (A)                            │
│  WorldEvent → PersonalMemory (B)   [asimétrico]             │
│                                                             │
│  Usa: BiasEngine + GoalFilter                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ alimenta
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Relationship.memories                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ usado por
              ┌────────────┼────────────┬──────────────┐
              │            │            │              │
              ▼            ▼            ▼              ▼
┌──────────────┐   ┌────────────┐   ┌──────────┐  ┌────────────┐
│ Narrative    │   │ Label      │   │ Experience│  │ Behavior   │
│ Engine       │   │ Generator  │   │ Generator │  │ Influence  │
│              │   │            │   │           │  │            │
│ Detecta      │   │ Genera     │   │ Genera    │  │ Influencia │
│ patrones     │   │ etiquetas  │   │ experienc.│  │ decisiones │
└──────────────┘   └────────────┘   └──────────┘  └────────────┘
```

---

## ⚙️ Configuración relevante

```python
# RelationshipsConfig
config.relationships.orientation_tolerance = 1.5
config.relationships.affinity_weight = 0.4
config.relationships.age_weight = 0.3
config.relationships.distance_weight = 0.3

# Reproducción (usado por MarriageSystem)
config.reproduction.partner_search_radius = 20.0
config.reproduction.widowhood_duration_days = 365.0
config.reproduction.intimacy_cooldown_days = 30.0

# Adopciones
config.adoptions.max_orphan_age_days = 6205.0        # ~17 años
config.adoptions.min_adoptive_age_days = 9125.0      # ~25 años
config.adoptions.min_single_parent_age_days = 10950.0  # ~30 años
config.adoptions.max_children_for_adoption = 3
config.adoptions.allow_single_parent_adoption = True
config.adoptions.min_single_parent_energy = 0.5
config.adoptions.max_single_parent_stress = 0.6
config.adoptions.kinship_weight = 100.0
config.adoptions.distance_weight = 0.2
config.adoptions.pressure_weight = 50.0
config.adoptions.stress_weight = 50.0
config.adoptions.happiness_weight = 15.0
config.adoptions.children_count_weight = 5.0
config.adoptions.stability_weight = 1.5
config.adoptions.senior_penalty = 10.0
config.adoptions.single_parent_penalty = 20.0
config.adoptions.age_penalty_exponent = 2.0
config.adoptions.age_penalty_multiplier = 30.0
config.adoptions.motivation_protection_weight = 25.0
config.adoptions.motivation_cooperation_weight = 15.0
config.adoptions.abandonment_stress_rate = 0.01
config.adoptions.abandonment_happiness_rate = 0.005
config.adoptions.abandonment_trauma_rate = 0.002
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_behavior_influence.py` | Priority, attraction, anchors |
| `tests/unit/test_compatibility_engine.py` | Cálculo de compatibilidad |
| `tests/unit/test_label_generator.py` | Generación de etiquetas |
| `tests/unit/test_bias_engine.py` | Sesgos cognitivos |
| `tests/integration/test_regression_bugs.py` | Bug #1 (breakups masivos), #3 (register_birth) |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo completo de relación

```python
# Dos agentes se conocen
# RelationshipManager crea:
# - WorldEvent tipo "met"
# - PersonalMemory en cada Relationship (con sesgos)

# Después de varias cooperaciones → LabelGenerator asigna "Amigo"
# ExperienceGenerator genera más cooperación con probabilidad 0.025
# Cada cooperación → RelationshipExperienceEngine → memorias más profundas

# Tras meses de amistad:
# NarrativeEngine detecta: "Siempre puedo contar con esta persona"
# BehaviorInfluence da prioridad 1.8 al amigo

# Si surge intimidad → MarriageSystem genera evento INTIMACY
# LabelGenerator puede asignar "Interés Romántico" → "Amante"
```

### Ejemplo 2: Ruptura de relación

```python
# Una traición → RelationshipExperienceEngine
# mem_a: PersonalMemory con valence -1, peso alto (negativity_bias)
# mem_b: PersonalMemory con valence -1, peso diferente (asimétrico)

# NarrativeEngine detecta: "Me traicionó y no lo olvido" (intensidad 0.60)
# LabelGenerator puede transicionar: "Amigo" → "Enemigo"
# BehaviorInfluence: atracción pasa de +7.0 a -5.0
```

### Ejemplo 3: Adopción de hermanos

```python
# Tres hermanos huérfanos (mismo mother_id)
# AdoptionSystem los agrupa con Union-Find
# Busca familia con capacity ≥ 3
# Encuentra una tía (kinship_degree = 3) con suitability alta
# Adopción grupal: todos juntos

# Se generan:
# - 3 eventos CARE en RelationshipExperienceEngine
# - 9 memorias episódicas (3 huérfanos × 3 figuras parentales)
# - Actualización de reputation_score de los padres
```

### Ejemplo 4: Uso de BehaviorInfluence en FreeWillSystem

```python
# FreeWillSystem decide con quién interactuar
candidates = get_nearby_agents(agent)

# Filtrar por etiquetas
candidates = BehaviorInfluence.filter_targets_by_labels(
    agent, candidates,
    excluded_labels=["Enemigo", "Rival"]
)

# Ordenar por prioridad
candidates.sort(
    key=lambda t: BehaviorInfluence.get_target_priority(agent, t, current_day),
    reverse=True
)

best_target = candidates[0]  # El de mayor prioridad
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Emergencia**: las etiquetas emergen de memorias, no se asignan
- **Asimetría**: misma interacción → recuerdos diferentes para A y B
- **Sesgos cognitivos**: negativity bias, idealización post-mortem, recencia
- **Genética universal**: todo filtrado por `SocialCapabilities`

### Arquitectura de memorias

| Concepto | Descripción |
|----------|-------------|
| **WorldEvent** | Evento objetivo (lo que pasó realmente) |
| **PersonalMemory** | Interpretación subjetiva (lo que recuerdo) |
| **Relationship** | Contenedor de memorias entre dos agentes |
| **Narrative** | Patrón detectado en memorias acumuladas |
| **Label** | Etiqueta emergente de los pesos acumulados |

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| SpatialGrid | RelationshipManager | O(N²) → O(N) |
| Caché `_romantic_partner_cache` | MarriageSystem | Evita re-calcular parejas por tick |
| Diccionario `_relationships` | Person | Búsqueda O(1) por ID |
| Set `_relationships_created_this_tick` | RelationshipManager | Evita duplicados |
| Ventana temporal 365 días | NarrativeEngine | Solo recuerdos recientes |

### Limitaciones
- No hay olvido activo (solo decaimiento exponencial de pesos)
- Las relaciones son binarias (A↔B), no grupales
- No hay dinámicas de grupo (familia como unidad)
- Las adopciones no consideran preferencia del huérfano (menor)

### Errores comunes
- ❌ Asignar etiquetas manualmente (deben emerger de memorias)
- ❌ Usar `_relationships` como lista (es Dict[int, Relationship])
- ❌ Olvidar usar `.values()` al iterar sobre relaciones
- ❌ Crear relaciones sin verificar capacidades sociales
- ❌ Ignorar el decaimiento temporal al calcular pesos

---

## 🎓 Conceptos clave

### ¿Por qué memorias asimétricas?

**Principio de subjetividad**:
- Mismo evento → experiencias diferentes
- Una traición puede ser más intensa para el traicionado
- Un nacimiento es más intenso para la madre
- La personalidad modula la percepción
- Esto crea relaciones complejas y realistas

### ¿Por qué etiquetas emergentes?

**Principio de no-linealidad**:
- No hay "nivel de amistad = 7.3"
- Hay acumulación de experiencias que cruzan umbrales
- "Amigo" emerge cuando hay suficientes cooperaciones + cares
- Las etiquetas pueden desaparecer si no se refuerzan
- Más realista que sistemas lineales

### ¿Por qué sesgos cognitivos?

**Principio de realismo psicológico**:
- Los humanos no somos racionales
- Negativity bias: recordamos más lo malo
- Idealización post-mortem: los muertos se vuelven mejores
- Recencia: lo reciente pesa más
- Sin sesgos, las relaciones serían aburridas y predecibles

### ¿Por qué Union-Find en adopciones?

**Principio de eficiencia algorítmica**:
- Agrupar hermanos es un problema de conectividad
- Union-Find lo resuelve en O(n·α(n)) ≈ O(n)
- Permite agrupar hermanos biológicos y adoptivos
- Garantiza no separar hermanos en adopción

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 9 |
| Tipos de eventos relacionales | 8 |
| Etiquetas relacionales | 9+ |
| Patrones narrativos | 10+ |
| Categorías de memoria | 6 |
| Tests cubriendo relaciones | ~25 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Relaciones grupales (familias como unidades)
- [ ] Olvido activo (memorias que se borran completamente)
- [ ] Reconciliación post-conflicto
- [ ] Rituales sociales (bodas, funerales)

### Posibles
- [ ] Celos y rivalidad romántica
- [ ] Triángulos amorosos
- [ ] Amistades tóxicas (codependencia)
- [ ] Duelos colectivos (muertes que afectan a toda la comunidad)
- [ ] Facciones y lealtades grupales
- [ ] Chismes y rumores (memorias de segunda mano)

---

*Documento: 06_RELACIONES_SOCIALES.md*
*Versión: 1.0*