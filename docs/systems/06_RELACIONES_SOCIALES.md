# 06 - Relaciones Sociales

## 📋 Resumen

El **Sistema de Relaciones Sociales** modela la red compleja de relaciones interpersonales que emergen entre los agentes a lo largo de sus vidas. Desde encuentros casuales entre desconocidos hasta matrimonios consolidados, pasando por rivalidades, amistades y conflictos familiares. Es uno de los sistemas más ricos del simulador, donde las relaciones **no se fuerzan ni se programan**: emergen naturalmente de las experiencias compartidas, los sesgos cognitivos y las narrativas que los agentes construyen sobre sus interacciones.

**Filosofía fundamental**: *Las relaciones son emergentes, no programadas. No hay un "nivel de amor" que suba linealmente. En su lugar, los agentes acumulan memorias de eventos compartidos, que el motor de sesgos cognitivos procesa de forma asimétrica (recordamos más lo malo, idealizamos a los muertos, etc.), dando lugar a etiquetas relacionales como "Amigo", "Enemigo" o "Amante" que emergen del patrón de experiencias.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Definir el vocabulario común de eventos relacionales (`RelationshipEventType`, `RelationshipEvent`)
- Detectar nuevos encuentros entre agentes desconocidos (`RelationshipManager`)
- Calcular compatibilidad entre agentes (`CompatibilityEngine`)
- Gestionar formación y disolución de parejas (`MarriageSystem`)
- Generar experiencias relacionales cotidianas (`ExperienceGenerator`)
- Procesar eventos en memorias con sesgos cognitivos (`RelationshipExperienceEngine`)
- Aplicar sesgos cognitivos (negatividad, recencia, idealización) (`BiasEngine`)
- Filtrar memorias por objetivos relacionales (`GoalFilter`)
- Generar narrativas relacionales (`NarrativeEngine`)
- Influir en el comportamiento a partir de las relaciones (`BehaviorInfluence`)
- Derivar capacidades sociales del genoma (`SocialCapabilities`)
- Registrar logs de eventos relacionales significativos (`RelationshipLogger`)

**NO es responsable de:**
- ❌ Decidir el movimiento físico (eso lo hace `MovementSystem`)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`)
- ❌ Gestionar la reproducción (eso lo hace `ConceptionSystem`)
- ❌ Decidir si un agente muere (eso lo hace `MortalitySystem`)
- ❌ Gestionar motivaciones individuales (eso lo hace `FreeWillSystem`)
- ❌ Lógica centralizada de afinidad lineal (la afinidad es emergente)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Relationship** | Vínculo interpersonal | Relación |
| **RelationshipEventType** | Vocabulario de experiencias | Catálogo |
| **RelationshipEvent** | Experiencia compartida | Recuerdo |
| **PersonalMemory** | Recuerdo subjetivo | Memoria episódica |
| **BiasEngine** | Sesgos cognitivos | Psicología |
| **Negativity bias** | Recordar más lo malo | Sesgo de negatividad |
| **Recency bias** | Lo reciente pesa más | Sesgo de recencia |
| **Post-mortem idealization** | Los muertos mejoran con el tiempo | Duelo |
| **Betrayal context** | Traiciones se recuerdan más | Herida emocional |
| **Relationship labels** | Cómo definimos a alguien | Amigo/Enemigo |
| **Narrative pattern** | Historia que contamos de una relación | Narrativa |
| **Compatibility** | Afinidad potencial | Matchmaking |
| **Marriage** | Compromiso formal | Matrimonio |
| **Social capabilities** | Nivel de complejidad social | Etología |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/relationships/relationship_events.py` | `RelationshipEventType`, `RelationshipEvent` | Vocabulario común de eventos relacionales |
| `systems/relationships/relationship_model.py` | `Relationship`, `RelationshipStatus`, `PersonalMemory`, `BiasEngine`, `GoalFilter` | Modelo de datos relacional y sesgos cognitivos |
| `systems/relationships/relationship_manager.py` | `RelationshipManager` | Detección y creación de nuevas relaciones |
| `systems/relationships/compatibility_engine.py` | `CompatibilityEngine` | Cálculo de compatibilidad entre agentes |
| `systems/relationships/marriage_system.py` | `MarriageSystem` | Formación y disolución de parejas |
| `systems/relationships/experience_generator.py` | `ExperienceGenerator` | Generación de experiencias cotidianas |
| `systems/relationships/relationship_experience_engine.py` | `RelationshipExperienceEngine` | Procesamiento de eventos con sesgos cognitivos |
| `systems/relationships/behavior_influence.py` | `BehaviorInfluence` | Influencia de relaciones en comportamiento |
| `systems/relationships/narrative_engine.py` | `NarrativeEngine` | Generación de narrativas relacionales |
| `systems/relationships/social_capabilities.py` | `SocialCapabilities` | Capacidades sociales derivadas del genoma |
| `systems/relationships/relationship_system.py` | `RelationshipSystem` (stub) | Placeholder intencionalmente vacío |
| `systems/relationships/relationship_logger.py` | `RelationshipLogger` | Logging especializado de eventos relacionales |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              FASE 0: VOCABULARIO Y CAPACIDADES                  │
│                                                                 │
│ SocialCapabilities.from_genome(genome):                         │
│  ├── can_have_friendship, can_have_romantic_bonds               │
│  ├── can_form_pair_bond, can_form_family_bonds                  │
│  ├── can_have_marriage, can_have_social_pressure                │
│  └── social_complexity [0.0, 1.0]                               │
│                                                                 │
│ RelationshipEventType:                                          │
│  └── 14 tipos de eventos (CARE, BIRTH, BETRAYAL, etc.)          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 1: DETECCIÓN DE NUEVAS RELACIONES             │
│                                                                 │
│ RelationshipManager:                                            │
│  ├── Identificar agentes dentro de RADIUS_RELATIONSHIP (1.5)    │
│  ├── Si no tienen relación previa → crear Relationship          │
│  └── Añadir memoria inicial "met" (conocido)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 2: FORMACIÓN DE PAREJAS                       │
│                                                                 │
│ MarriageSystem:                                                 │
│  ├── Para cada agente sin pareja:                               │
│  │   ├── Validar SocialCapabilities (can_have_romantic_bonds)   │
│  │   ├── Verificar orientación sexual compatible                │
│  │   ├── Calcular compatibilidad (CompatibilityEngine)          │
│  │   ├── Verificar edad fértil                                  │
│  │   └── Verificar distancia geográfica                         │
│  ├── Filtrar candidatos y ordenar por compatibilidad            │
│  └── Si mutuo acuerdo:                                          │
│      ├── pending.register_marriage(a, b)                        │
│      ├── Crear Relationship con status=CONSOLIDATED             │
│      └── Asignar núcleo residencial (ResidentialNucleus)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 3: GENERACIÓN DE EXPERIENCIAS COTIDIANAS      │
│                                                                 │
│ ExperienceGenerator:                                            │
│  ├── Identificar pares de agentes relacionados cercanos         │
│  ├── Para cada par, generar experiencias según contexto:        │
│  │   ├── cooperation (aliados)                                  │
│  │   ├── care (enfermedad)                                      │
│  │   ├── conflict (rivales)                                     │
│  │   ├── intimacy (amantes)                                     │
│  │   └── share_resource (amigos)                                │
│  └── Crear RelationshipEvent con intensidad contextual          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 4: PROCESAMIENTO DE EVENTOS RELACIONALES      │
│                                                                 │
│ RelationshipExperienceEngine:                                   │
│  ├── Para cada evento:                                          │
│  │   ├── Crear PersonalMemory para agente A (con sus sesgos)    │
│  │   └── Crear PersonalMemory para agente B (con sus sesgos)    │
│  ├── Aplicar BiasEngine (negatividad, recencia, idealización)   │
│  ├── Aplicar GoalFilter (filtrar por objetivos relacionales)    │
│  ├── Añadir memorias a Relationship.memories                    │
│  ├── Recalcular etiquetas con Relationship.get_labels()         │
│  ├── Detectar narrativas con NarrativeEngine                    │
│  └── Loggear eventos con RelationshipLogger                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 5: INFLUENCIA EN EL COMPORTAMIENTO            │
│                                                                 │
│ BehaviorInfluence:                                              │
│  ├── get_social_attraction(person, target)                      │
│  ├── get_target_priority(person, target)                        │
│  └── Usado por FreeWillSystem y MovementSystem                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 0. Vocabulario de Eventos Relacionales

**📁 Archivo**: `systems/relationships/relationship_events.py`
**🌍 Equivalencia real**: El vocabulario común que todos los sistemas usan para comunicar experiencias significativas al motor de relaciones.

#### Tipos de eventos relacionales (enum `RelationshipEventType`)

**Interacciones positivas:**

| Evento | Valor | Descripción | Ejemplo de contexto |
|--------|-------|-------------|---------------------|
| `CARE` | "care" | Un agente cuida a otro | "Influenza_000001" |
| `COOPERATION` | "cooperation" | Trabajo conjunto, defensa mutua | "caza_compartida" |
| `SHARE_RESOURCE` | "share_resource" | Donación o intercambio voluntario | "comida" |
| `INTIMACY` | "intimacy" | Tiempo de calidad, cercanía | "conversacion_profunda" |
| `RECONCILIATION` | "reconciliation" | Resolución de un conflicto previo | "perdon_tras_conflicto" |

**Interacciones negativas:**

| Evento | Valor | Descripción | Ejemplo de contexto |
|--------|-------|-------------|---------------------|
| `COMPETITION` | "competition" | Competencia por un recurso limitado | "food_node_42" |
| `BETRAYAL` | "betrayal" | Robo, abandono, infidelidad | "infidelidad_detectada" |
| `CONFLICT` | "conflict" | Pelea física o discusión directa | "disputa_territorial" |
| `NEGLECT` | "neglect" | Ignorar necesidades básicas | "abandono_temporal" |

**Hitos vitales (eventos de estado):**

| Evento | Valor | Descripción | Ejemplo de contexto |
|--------|-------|-------------|---------------------|
| `BIRTH` | "birth" | Nacimiento de un hijo en común | "child_123" |
| `CHILD_DEATH` | "child_death" | Muerte de un hijo en común | "child_123_enfermedad" |
| `PARTNER_DEATH` | "partner_death" | Muerte de la pareja | "duelo_profundo" |
| `COHABITATION_START` | "cohabitation_start" | Decisión de vivir juntos | "nucleo_familiar_7" |
| `COHABITATION_END` | "cohabitation_end" | Decisión de separar hogares | "separacion_voluntaria" |

#### Estructura de `RelationshipEvent` (dataclass)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `event_type` | `RelationshipEventType` | Tipo de experiencia |
| `agent_a_id` | `int` | Agente que inicia/es sujeto principal |
| `agent_b_id` | `int` | Agente que recibe la acción |
| `intensity` | `float` [0.0, 1.0] | Magnitud emocional |
| `context` | `str` | Información adicional |
| `day` | `float` | Día de simulación |
| `metadata` | `Dict[str, Any]` | Datos adicionales |

#### Ejemplos de emisión

```python
# DiseaseSystem emitiendo cuidado durante enfermedad
event = RelationshipEvent(
    event_type=RelationshipEventType.CARE,
    agent_a_id=agente_sano.entity_id,
    agent_b_id=agente_enfermo.entity_id,
    intensity=0.8,
    context="Influenza_000001",
    day=current_day,
    metadata={"duration_days": 5}
)

# ConceptionSystem emitiendo nacimiento
event = RelationshipEvent(
    event_type=RelationshipEventType.BIRTH,
    agent_a_id=madre.entity_id,
    agent_b_id=padre.entity_id,
    intensity=0.9,
    context=f"child_{nuevo_bebe.entity_id}",
    day=current_day
)
```

#### Filosofía de diseño

Los eventos son **estructuras puras de datos** (dataclasses sin lógica):
- Cualquier sistema puede emitirlos sin conocer el procesamiento
- Fáciles de serializar para logs y exportación
- Extensibles: nuevos eventos no rompen sistemas existentes

---

### 1. SocialCapabilities - Capacidades Sociales

**📁 Archivo**: `systems/social/social_capabilities.py` (también referenciado como `systems/relationships/social_capabilities.py`)
**🌍 Equivalencia real**: El nivel etológico de la especie: qué complejidad social puede alcanzar.

#### Atributos principales

| Atributo | Tipo | Condición genética |
|----------|------|-------------------|
| `has_social_awareness` | `bool` | `nervous_system ≥ 0.2` AND `sociability ≥ 0.2` |
| `can_recognize_individuals` | `bool` | `intelligence ≥ 0.3` AND `sociability ≥ 0.3` |
| `can_form_cooperation` | `bool` | `sociability ≥ 0.4` AND `intelligence ≥ 0.2` |
| `can_form_conflict` | `bool` | `aggressiveness ≥ 0.3` |
| `can_form_pair_bond` | `bool` | `sociability ≥ 0.7` AND `intelligence ≥ 0.5` |
| `can_form_family_bonds` | `bool` | `sociability ≥ 0.8` AND `intelligence ≥ 0.6` |
| `can_have_friendship` | `bool` | `sociability ≥ 0.7` AND `intelligence ≥ 0.7` |
| `can_have_romantic_bonds` | `bool` | `intelligence ≥ 0.7` AND `sociability ≥ 0.7` |
| `can_have_marriage` | `bool` | `intelligence ≥ 0.8` |
| `can_have_social_pressure` | `bool` | `intelligence ≥ 0.6` AND `sociability ≥ 0.7` |
| `social_complexity` | `float` | Combinación de sociabilidad e inteligencia |

#### Métodos de consulta

| Método | Descripción |
|--------|-------------|
| `can_have_label(label)` | ¿Puede tener esta etiqueta? |
| `can_participate_in_event(event_type)` | ¿Puede participar en este evento? |
| `can_form_nucleus_type(type)` | ¿Puede formar este tipo de núcleo? |

#### Ejemplos

```python
human_caps = SocialCapabilities.from_genome(human_genome)
human_caps.can_have_marriage       # True
human_caps.can_have_romantic_bonds # True

wolf_caps = SocialCapabilities.from_genome(wolf_genome)
wolf_caps.can_form_pair_bond       # True (forma parejas)
wolf_caps.can_have_marriage        # False (no concepto abstracto)

plant_caps = SocialCapabilities.from_genome(plant_genome)
plant_caps.social_complexity       # 0.0
plant_caps.has_social_awareness    # False
```

---

### 2. Relationship - Modelo de Relación

**📁 Archivo**: `systems/relationships/relationship_model.py`
**🌍 Equivalencia real**: Un vínculo interpersonal con historia acumulada.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `owner_id` | `int` | ID del dueño (asimétrico) |
| `partner_id` | `int` | ID del otro agente |
| `start_day` | `float` | Día de inicio |
| `last_interaction_day` | `float` | Última interacción |
| `status` | `RelationshipStatus` | Estado (UNKNOWN, ACQUAINTANCE, DATING, etc.) |
| `affinity` | `float` | Afinidad cruda [0.0, 1.0] (legacy) |
| `relationship_type` | `RelationshipType` | EXCLUSIVE, OPEN, etc. |
| `shared_children` | `int` | Número de hijos en común |
| `memories` | `List[PersonalMemory]` | Historia de experiencias |

#### PersonalMemory (memoria individual)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `event_type` | `str` | Tipo de evento |
| `day` | `float` | Día en que ocurrió |
| `valence` | `int` | +1 (positivo) / -1 (negativo) |
| `personal_weight` | `float` | Peso subjetivo (con sesgos) |
| `context` | `str` | Contexto |

#### Etiquetas relacionales (emergentes)

Las etiquetas emergen del patrón de memorias, no se asignan manualmente:

| Etiqueta | Condición |
|----------|-----------|
| `"Desconocido"` | Sin memorias |
| `"Conocido"` | Memorías leves |
| `"Aliado"` | Memorías positivas de cooperación |
| `"Amigo"` | Alta acumulación positiva |
| `"Familia Elegida"` | Vínculos profundos no biológicos |
| `"Interés Romántico"` | Memorías de intimidad |
| `"Amante"` | Romance consolidado |
| `"Rival"` | Competencia sostenida |
| `"Enemigo"` | Hostilidad acumulada |

---

### 3. BiasEngine - Sesgos Cognitivos

**📁 Archivo**: `systems/relationships/relationship_model.py` (incluido)
**🌍 Equivalencia real**: Los sesgos cognitivos que distorsionan nuestra percepción de las relaciones.

#### Sesgos implementados

| Sesgo | Descripción |
|-------|-------------|
| **Negativity bias** | Memorías negativas se amplifican |
| **Recency bias** | Lo reciente pesa más |
| **Post-mortem idealization** | Los muertos se idealizan (reduce negatividad) |
| **Betrayal context** | Traiciones se recuerdan más intensamente |
| **Narrative amplification** | Memorías coherentes con narrativa activa se amplifican |

#### Flujo de aplicación

```python
BiasEngine.apply_biases(temp_memory, owner, rel, current_day) -> float
    ├── weight = temp_memory.personal_weight
    ├── Si valence < 0: weight *= negativity_multiplier
    ├── recency_factor = exp(-days_since * decay)
    ├── weight *= (1 + recency_factor * recency_bonus)
    ├── Si partner muerto Y valence < 0: weight *= idealization
    ├── Si "traicion" en context: weight *= betrayal_amplification
    └── Si valence > 0 y narrativa positiva: weight *= narrative_amp
```

---

### 4. GoalFilter - Filtros por Objetivos

**📁 Archivo**: `systems/relationships/relationship_model.py` (incluido)
**🌍 Equivalencia real**: Cómo filtramos memorias según nuestras metas actuales.

#### Funcionalidad

Filtra memorias según los objetivos relacionales activos del agente:
- Si el agente busca pareja → prioriza memorias de intimidad
- Si busca cooperación → prioriza memorias de cooperación
- Filtra eventos irrelevantes para el objetivo actual

---

### 5. CompatibilityEngine - Compatibilidad

**📁 Archivo**: `systems/relationships/compatibility_engine.py`
**🌍 Equivalencia real**: El "matchmaking" que determina qué tan compatibles son dos agentes para formar pareja.

#### Factores de compatibilidad

| Factor | Descripción |
|--------|-------------|
| **Genética** | Similitud de rasgos (sociabilidad, inteligencia) |
| **Edad** | Diferencia de edad aceptable |
| **Género y orientación** | Compatibilidad sexual |
| **Ubicación** | Distancia geográfica |
| **Historia** | Relaciones previas con parientes |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `calculate(person_a, person_b)` | Calcula score de compatibilidad |
| `can_form_pair(person_a, person_b)` | ¿Pueden formar pareja? |

---

### 6. RelationshipManager - Detección de Relaciones

**📁 Archivo**: `systems/relationships/relationship_manager.py`
**🌍 Equivalencia real**: El proceso natural de conocer gente nueva.

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada persona con capacidades sociales:
        ├── Encontrar agentes en radio de relación (1.5 tiles)
        ├── Para cada agente cercano:
        │   ├── Si no existe Relationship previa:
        │   │   ├── Crear nueva Relationship
        │   │   ├── status = UNKNOWN → ACQUAINTANCE
        │   │   ├── Añadir memoria "met" (primer encuentro)
        │   │   └── Loggear con RelationshipLogger
        │   └── Si ya existe: actualizar last_interaction_day
        └── Limpiar relaciones muy antiguas sin interacción
```

---

### 7. MarriageSystem - Formación de Parejas

**📁 Archivo**: `systems/relationships/marriage_system.py`
**🌍 Equivalencia real**: El proceso de formación de pareja estable.

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada agente sin pareja:
        ├── Validar SocialCapabilities.can_have_romantic_bonds
        ├── Validar edad fértil
        ├── Buscar candidatos cercanos
        ├── Para cada candidato:
        │   ├── Verificar orientación sexual compatible
        │   ├── Verificar edad fértil del candidato
        │   ├── Validar NO consanguinidad (AncestryQueries)
        │   └── Calcular compatibilidad
        ├── Filtrar y ordenar por compatibilidad
        ├── Si mutuo acuerdo (bidireccional):
        │   ├── pending.register_marriage(a, b)
        │   ├── Crear núcleo residencial
        │   └── Generar evento COHABITATION_START
        └── Evaluar divorcios (si afinidad muy baja)
```

#### Consideraciones

- El matrimonio es **mutuo**: ambos deben aceptar
- La consanguinidad se valida con `AncestryQueries.is_forbidden_marriage()`
- Los divorcios son raros y requieren afinidad muy baja sostenida

---

### 8. ExperienceGenerator - Generación de Experiencias

**📁 Archivo**: `systems/relationships/experience_generator.py`
**🌍 Equivalencia real**: Las interacciones cotidianas que construyen las relaciones.

#### Tipos de experiencias generadas

| Experiencia | Contexto | Etiquetas previas |
|-------------|----------|-------------------|
| `cooperation` | Aliados cercanos | Amigo, Aliado, Familia |
| `care` | Uno enfermo | Familia, Amigo, Amante |
| `conflict` | Rivales cercanos | Rival, Enemigo |
| `intimacy` | Amantes cercanos | Amante, Interés Romántico |
| `share_resource` | Recursos disponibles | Amigo, Aliado |

#### Intensidad contextual

La intensidad depende del contexto:
- `care` durante enfermedad grave: intensidad alta (0.7-0.95)
- `cooperation` exitosa: intensidad media (0.3-0.6)
- `conflict` territorial: intensidad variable

---

### 9. RelationshipExperienceEngine - Procesador Central

**📁 Archivo**: `systems/relationships/relationship_experience_engine.py`
**🌍 Equivalencia real**: El cerebro que procesa las experiencias y actualiza las relaciones.

#### Flujo interno

```python
def process_event(self, event, agent_a, agent_b, current_day):
    # 1. Crear WorldEvent
    world_event = WorldEvent(event, current_day)
    
    # 2. Crear memorias ASIMÉTRICAS
    memory_a = PersonalMemory(...)  # Para agente A
    memory_b = PersonalMemory(...)  # Para agente B (diferente perspectiva)
    
    # 3. Aplicar sesgos cognitivos
    weight_a = BiasEngine.apply_biases(memory_a, agent_a, rel_ab, current_day)
    weight_b = BiasEngine.apply_biases(memory_b, agent_b, rel_ba, current_day)
    
    # 4. Aplicar filtro de objetivos
    memory_a = GoalFilter.apply(memory_a, agent_a)
    memory_b = GoalFilter.apply(memory_b, agent_b)
    
    # 5. Añadir a las relaciones
    rel_ab.memories.append(memory_a)
    rel_ba.memories.append(memory_b)
    
    # 6. Recalcular etiquetas
    new_labels_a = rel_ab.get_labels(current_day)
    new_labels_b = rel_ba.get_labels(current_day)
    
    # 7. Detectar narrativas
    narrative = NarrativeEngine.detect_pattern(rel_ab, current_day)
    
    # 8. Loggear evento
    relationship_logger.log_significant_event(...)
```

#### Asimetría fundamental

**Principio clave**: El mismo evento genera **diferentes memorias** para cada agente:
- Un CARE durante enfermedad: quien cuida puede sentir carga (valencia mixta), quien es cuidado siente gratitud (valencia positiva fuerte)
- Un CONFLICT: quien inició puede sentir justificación, quien lo recibió siente resentimiento
- Un BIRTH: la madre tiene memorias físicas y emocionales más intensas que el padre

---

### 10. BehaviorInfluence - Influencia en Comportamiento

**📁 Archivo**: `systems/relationships/behavior_influence.py`
**🌍 Equivalencia real**: Cómo nuestras relaciones influyen en nuestras decisiones.

#### Métodos principales

| Método | Descripción |
|--------|-------------|
| `get_social_attraction(person, target)` | Atracción social hacia target |
| `get_target_priority(person, target)` | Prioridad relacional |
| `filter_targets_by_labels(...)` | Filtrar targets por etiquetas |
| `get_multiple_social_anchors(person)` | Anclas sociales múltiples |

#### Uso en otros sistemas

- **FreeWillSystem**: usa `get_target_priority` para elegir hacia quién dirigir motivaciones
- **MovementSystem**: usa `get_social_attraction` para decidir hacia dónde moverse

---

### 11. NarrativeEngine - Narrativas Relacionales

**📁 Archivo**: `systems/relationships/narrative_engine.py`
**🌍 Equivalencia real**: La historia que construimos sobre nuestras relaciones.

#### Patrones narrativos

| Narrativa | Descripción |
|-----------|-------------|
| `"amor_prohibido"` | Romance en contexto difícil |
| `"amistad_inquebrantable"` | Vínculo profundo sostenido |
| `"rivalidad_histórica"` | Conflicto prolongado |
| `"traición_imperdonable"` | Betrayal que marcó la relación |
| `"segunda_oportunidad"` | Reconciliación tras conflicto |
| `"enemistad_creciente"` | Hostilidad en aumento |

#### Detección

El motor analiza el patrón de memorias y detecta si emerge una narrativa coherente. Una vez detectada, **amplifica memorias coherentes** y **reduce memorias disonantes**.

---

### 12. RelationshipSystem - Placeholder Emergente

**📁 Archivo**: `systems/relationships/relationship_system.py`
**🌍 Equivalencia real**: Ninguna. Este módulo está **intencionalmente vacío** por filosofía de diseño.

#### Propósito

Este archivo existe únicamente para:
1. Mantener consistencia en el pipeline de ejecución (todos los sistemas tienen `process()`)
2. Documentar explícitamente que la lógica relacional es **emergente**, no centralizada
3. Servir como punto de extensión futuro

#### Filosofía de diseño emergente

El archivo declara explícitamente cómo evolucionan las relaciones:

- **`RelationshipManager`**: crea relaciones y memorias iniciales
- **`ExperienceGenerator`**: genera experiencias cotidianas
- **`RelationshipExperienceEngine`**: procesa eventos en memorias con sesgos
- **`Relationship.get_labels()`**: etiquetas emergentes
- **Decaimiento temporal**: las memorias pierden peso con el tiempo

#### Lo que NO hace este sistema

> ❌ **NO se usan estados lineales ni affinity**
> ❌ **NO se fuerzan rupturas**
> ❌ **NO hay lógica centralizada de relaciones**

#### Implementación

```python
class RelationshipSystem:
    """Stub inactivo. Toda la lógica relacional es emergente."""

    def __init__(self, config, relationship_engine=None):
        self.config = config
        self.relationship_engine = relationship_engine

    def process(self, state, pending, delta_days, context):
        """Intencionalmente vacío. Las relaciones evolucionan por experiencias."""
        pass
```

---

### 13. RelationshipLogger - Logging Especializado

**📁 Archivo**: `systems/relationships/relationship_logger.py`
**🌍 Equivalencia real**: Un cronista que registra eventos significativos en las relaciones.

#### Instancia global

```python
# Instancia global del logger (disponible como import directo)
relationship_logger = RelationshipLogger()
```

#### Métodos principales

| Método | Descripción | Emoji |
|--------|-------------|-------|
| `log_label_change(agent_id, partner_id, old_labels, new_labels, day)` | Cambios en etiquetas | 🏷️ |
| `log_significant_event(agent_a, agent_b, event_type, labels_a, labels_b, day)` | Eventos con contexto | 💞 |
| `log_narrative_detection(agent_id, partner_id, pattern, strength, day)` | Narrativas detectadas | 📖 |
| `log_relationship_milestone(agent_id, partner_id, milestone, day)` | Hitos relacionales | 🎯 |

#### Ejemplos de uso

```python
from systems.relationships.relationship_logger import relationship_logger

# Cambio de etiquetas
relationship_logger.log_label_change(
    agent_id=101, partner_id=202,
    old_labels={"Conocido"},
    new_labels={"Conocido", "Amigo"},
    current_day=365.0
)
# Output: 🏷️  Día 365: Agente 101 → 202 | Etiquetas añadidas: Amigo

# Evento significativo
relationship_logger.log_significant_event(
    agent_a_id=101, agent_b_id=202,
    event_type="care",
    labels_a=["Amigo", "Aliado"],
    labels_b=["Amigo"],
    current_day=400.0
)
# Output: 💞 Día 400: Evento care entre 101 y 202
```

#### Integración con filtrado de logs

En `launcher.py`, el `RelevantEventsFilter` usa emojis relacionales:

| Emoji | Evento |
|-------|--------|
| `👋` | Encuentros |
| `🤝` | UNKNOWN → ACQUAINTANCE |
| `👥` | Amistades |
| `💕` | Interés romántico |
| `🏠` | Convivencia |
| `💍` | Relaciones consolidadas |
| `💑` | Progresión de relaciones |

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                    │
│   sociability, intelligence, nervous_system, aggressiveness     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           SocialCapabilities (inmutable, derivada)              │
│   - Nivel 0-4 de complejidad social                             │
│   - can_have_marriage, can_have_romantic_bonds, etc.            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ Relationship │  │ Compatibility│  │ ExperienceGenerator  │
│ Manager      │  │ Engine       │  │ (experiencias        │
│              │  │              │  │  cotidianas)         │
│ Crea nuevas  │  │ Valida       │  │                      │
│ relaciones y │  │ parejas      │  │ Genera: cooperation, │
│ memorias     │  │ compatibles  │  │ care, conflict,      │
│ iniciales    │  │              │  │ intimacy             │
└──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘
       │                 │                     │
       │                 │                     ▼
       │                 │          ┌─────────────────────────┐
       │                 │          │ RelationshipEventType   │
       │                 │          │ (vocabulario común)     │
       │                 │          │ CARE, BIRTH, BETRAYAL,  │
       │                 │          │ COOPERATION, etc.       │
       │                 │          └───────────┬─────────────┘
       │                 │                      │
       │                 │                      ▼
       │                 │          ┌─────────────────────────┐
       │                 │          │ RelationshipEvent       │
       │                 │          │ (dataclass puro)        │
       │                 │          │ event_type, intensity,  │
       │                 │          │ context, day, metadata  │
       │                 │          └───────────┬─────────────┘
       │                 │                      │
       │                 │                      ▼
       │                 │          ┌─────────────────────────┐
       │                 │          │ RelationshipExperience  │
       │                 │          │ Engine                  │
       │                 │          │                         │
       │                 │          │ Procesa eventos en      │
       │                 │          │ memorias con sesgos     │
       │                 │          │ (BiasEngine, GoalFilter)│
       │                 │          └───────────┬─────────────┘
       │                 │                      │
       │                 │                      ▼
       │                 │          ┌─────────────────────────┐
       │                 │          │ RelationshipLogger      │
       │                 │          │ (🏷️ 💞 📖 🎯)          │
       └─────────────────┴──────────┴─────────────────────────┘
                                       │
                                       ▼
                          Relationship.memories
                          (etiquetas, narrativas)
                                       │
                                       ▼
                          BehaviorInfluence
                          - get_target_priority
                          - get_social_attraction
```

### Sistemas emisores de eventos (usando RelationshipEventType)

| Sistema | Eventos que emite |
|---------|-------------------|
| `DiseaseSystem` | `CARE` (durante recuperación) |
| `ConceptionSystem` | `BIRTH` (al nacer hijo) |
| `MortalitySystem` | `PARTNER_DEATH`, `CHILD_DEATH` |
| `MarriageSystem` | `COHABITATION_START`, `COHABITATION_END` |
| `FreeWillSystem` | `COOPERATION`, `CARE`, `CONFLICT`, `INTIMACY` |
| `ExperienceGenerator` | `COMPETITION`, `SHARE_RESOURCE`, `RECONCILIATION`, `BETRAYAL` |

**Nota**: `RelationshipSystem` es un **stub vacío** por diseño. Toda la lógica es emergente vía experiencias, no centralizada.

---

## ⚙️ Configuración relevante

```python
# RelationshipsConfig
config.relationships.relationship_radius = 1.5
config.relationships.experience_interval_days = 5.0
config.relationships.label_decay_rate = 0.001
config.relationships.marriage_compatibility_threshold = 0.6
```

### Parámetros hardcodeados importantes

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| RADIUS_RELATIONSHIP | 1.5 tiles | Distancia de interacción |
| Negativity multiplier | 1.5 | Amplificación de memorias negativas |
| Recency decay | 0.01 | Decaimiento temporal |
| Idealization factor | 0.5 | Reducción de negatividad post-mortem |
| Betrayal amplification | 1.8 | Amplificación de traiciones |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_compatibility_engine.py` | Cálculo de compatibilidad |
| `tests/unit/test_bias_engine.py` | Sesgos cognitivos |
| `tests/unit/test_label_generator.py` | Generación de etiquetas |
| `tests/unit/test_behavior_influence.py` | Influencia en comportamiento |
| `tests/unit/test_narrative_decay.py` | Decaimiento de narrativas |
| `tests/benchmarks/test_relationship_benchmarks.py` | Rendimiento |
| `tests/benchmarks/test_experience_generator.py` | Rendimiento de experiencias |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo completo de una amistad emergente

```python
# Día 1: Agentes 101 y 202 se encuentran por primera vez
# RelationshipManager detecta proximidad
rel = Relationship(owner_id=101, partner_id=202, start_day=1.0)
rel.memories.append(PersonalMemory(
    event_type="met", day=1.0, valence=0, personal_weight=0.5
))
# Etiqueta: "Desconocido" → "Conocido"

# Día 15: Experiencia de cooperación exitosa
event = RelationshipEvent(
    event_type=RelationshipEventType.COOPERATION,
    agent_a_id=101, agent_b_id=202,
    intensity=0.5, context="defensa_comun", day=15.0
)
relationship_engine.process_event(event)
# Memoría añadida con peso ponderado por sesgos
# Etiqueta: "Conocido" → "Aliado"

# Día 60: Múltiples cooperaciones acumuladas
# Las memorias positivas superan umbral
# Etiqueta: "Aliado" → "Amigo"

# Día 180: 202 enferma, 101 la cuida
event = RelationshipEvent(
    event_type=RelationshipEventType.CARE,
    agent_a_id=101, agent_b_id=202,
    intensity=0.8, context="Influenza_000123", day=180.0
)
# Memoria con peso alto por intensidad + sesgo de recencia
# NarrativeEngine detecta patrón: "amistad_inquebrantable"
# Amplifica memorias positivas futuras
```

### Ejemplo 2: Ruptura por traición

```python
# Relación de amantes consolidada (2 años)
# Evento de infidelidad detectado
event = RelationshipEvent(
    event_type=RelationshipEventType.BETRAYAL,
    agent_a_id=101, agent_b_id=202,
    intensity=0.95, context="infidelidad_detectada", day=730.0
)

# BiasEngine aplica:
# - Negativity bias: ×1.5
# - Betrayal context: ×1.8
# - Recency: ×1.2 (reciente)
# Peso final muy alto (~1.95 * base)

# Etiqueta cambia: "Amante" → "Enemigo" (si acumula suficiente)
# NarrativeEngine detecta: "traición_imperdonable"
# Amplifica futuras memorias negativas
# MarriageSystem evalúa divorcio tras sostenida baja afinidad
```

### Ejemplo 3: Duelo por muerte de pareja

```python
# Pareja consolidada, 50 años de convivencia
# MortalitySystem detecta muerte del agente 202
# Emite evento PARTNER_DEATH

event = RelationshipEvent(
    event_type=RelationshipEventType.PARTNER_DEATH,
    agent_a_id=202, agent_b_id=101,  # fallecido → sobreviviente
    intensity=0.9,
    context="duelo_profundo",
    day=18250.0
)

# RelationshipExperienceEngine procesa:
# Para agente 101 (sobreviviente):
#   - Crea memoria con valence=-1, weight alto
#   - BiasEngine aplica Post-mortem idealization:
#     todas las memorias negativas previas se reducen
#     las positivas se amplifican
#   - La narrativa se vuelve: "amor_eterno"
#   - Etiquetas: "Amante" → "Amor Eterno" (idealizado)

# En ticks futuros:
# - Memorías del fallecido decaen muy lentamente
# - FreeWillSystem emite eventos "PARTNER_DEATH" en el sobreviviente
# - Puede desencadenar migración o depresión
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Emergencia sobre programación**: las etiquetas emergen del patrón de memorias
- **Asimetría subjetiva**: mismo evento → diferentes memorias para cada agente
- **Sesgos cognitivos realistas**: recordamos más lo malo, idealizamos muertos
- **Sin affinity lineal**: no hay un "nivel de amor" que sube
- **Vocabulario común**: todos los sistemas emiten eventos compatibles
- **Narrativas coherentes**: una vez detectada una narrativa, se auto-refuerza

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| Caché de etiquetas | Relationship | Evita recalcular cada consulta |
| Poda de memorias | Relationship | Capacidad limitada |
| Early return si sin relaciones | Todos | Skip agentes solitarios |
| Experiencias por intervalos | ExperienceGenerator | No procesar cada tick |
| Spatial grid | MovementSystem | Búsqueda O(1) de vecinos |

### Limitaciones
- No hay comunicación verbal entre agentes (solo experiencias)
- No hay instituciones sociales (no hay leyes de matrimonio)
- Las memorias no son narrables por el agente (solo el sistema las ve)
- No hay olvido completo: las memorias decaen pero no desaparecen
- Las etiquetas son fijas (no hay "ex-amigo" explícito)
- No hay rituales sociales (bodas formales, funerales)

### Errores comunes
- ❌ Asumir que affinity lineal define la relación (usar etiquetas)
- ❌ Modificar memorias directamente (usar RelationshipExperienceEngine)
- ❌ Crear relaciones entre organismos sin capacidades sociales (validar SocialCapabilities)
- ❌ Forzar etiquetas manualmente (son emergentes)
- ❌ Ignorar la asimetría (cada agente tiene su propia memoria)

---

## 🎓 Conceptos clave

### ¿Por qué relaciones emergentes y no programadas?

**Principio de realismo social**:
- En la vida real, no decidimos conscientemente "ahora somos amigos"
- Las relaciones surgen de experiencias compartidas
- La acumulación de interacciones crea patrones
- Las etiquetas son interpretaciones posteriores

### ¿Por qué sesgos cognitivos?

**Principio de psicología humana**:
- No procesamos información objetivamente
- Recordamos más lo negativo (sesgo de negatividad)
- Lo reciente pesa más (sesgo de recencia)
- Idealizamos a los muertos (sesgo post-mortem)
- Sin sesgos, las relaciones serían predecibles y aburridas

### ¿Por qué vocabulario común de eventos?

**Principio de desacoplamiento**:
- Cualquier sistema puede emitir eventos relacionales
- No hay que modificar el motor para añadir nuevos emisores
- Fácil de extender (nuevos tipos de eventos)
- Serializable para análisis externo

### ¿Por qué RelationshipSystem es un stub vacío?

**Principio de documentación explícita**:
- El pipeline requiere que todos los sistemas tengan `process()`
- En lugar de condiciones especiales, tener un stub limpio
- Documenta explícitamente que la lógica es emergente
- Evita confusiones futuras

### ¿Por qué logging especializado?

**Principio de observabilidad**:
- Las relaciones son complejas y difíciles de debuggear
- Los emojis permiten filtrado visual en logs
- Facilita análisis de patrones emergentes
- Útil para identificar comportamientos inesperados

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 12 |
| Tipos de eventos relacionales | 14 |
| Sesgos cognitivos | 5 |
| Etiquetas emergentes | 10+ |
| Patrones narrativos | 6+ |
| Tests cubriendo relaciones | ~10 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Rituales sociales (bodas formales, funerales)
- [ ] Instituciones (leyes de matrimonio, tribunales)
- [ ] Memoria colectiva (historias compartidas por la comunidad)
- [ ] Transmisión cultural de relaciones

### Posibles
- [ ] Comunicación verbal (mentiras, promesas)
- [ ] Celos y envidia entre agentes
- [ ] Grupos sociales (amistades grupales, facciones)
- [ ] Reputación heredada
- [ ] Amistades a distancia (cartas, comunicación remota)
- [ ] Relaciones tóxicas persistentes
- [ ] Terapia psicológica (sanar traumas)

---

*Documento: 06_RELACIONES_SOCIALES.md*
*Versión: 2.0 (actualizado con relationship_events, relationship_system, relationship_logger)*
*Última actualización: Agosto 2026*