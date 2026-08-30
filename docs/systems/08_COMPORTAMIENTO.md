# 08 - Comportamiento

## 📋 Resumen

El **Sistema de Comportamiento** modela la vida interior de los agentes: sus motivaciones continuas, sus recuerdos episódicos, sus traumas implícitos, y cómo todo esto se modula por las capacidades cognitivas derivadas del genoma. Es el "cerebro" del simulador: traduce estímulos externos e internos en decisiones autónomas.

**Filosofía fundamental**: *El comportamiento emerge de motivaciones continuas moduladas por el genoma, las emociones, la memoria y el entorno. Los agentes no siguen guiones: deciden en cada tick qué impulso seguir, con inhibición competitiva que garantiza foco conductual.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Derivar capacidades cognitivas del genoma (`CognitiveCapabilities`)
- Gestionar motivaciones continuas del agente (`FreeWillSystem`)
- Gestionar memoria implícita (traumas) y explícita (episódica) (`CognitiveMemorySystem`)
- Aplicar sesgos cognitivos a las memorias (`BiasEngine`)
- Decidir qué motivación domina en cada tick (inhibición competitiva)
- Emitir eventos relacionales cuando las decisiones afectan a otros agentes
- Desarrollar preferencias espaciales y memoria de arraigo
- Calcular estrés cognitivo a partir de traumas y nostalgia

**NO es responsable de:**
- ❌ Decidir el movimiento físico (eso lo hace `MovementSystem`, documento 07)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`, documento 09)
- ❌ Generar experiencias relacionales cotidianas (eso lo hace `ExperienceGenerator`, documento 06)
- ❌ Gestionar parejas y matrimonios (eso lo hace `MarriageSystem`, documento 06)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`, documento 10)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **CognitiveCapabilities** | Arquitectura cerebral | Neuroanatomía |
| **FreeWillSystem** | Volición / motivación intrínseca | Impulsos |
| **CognitiveMemorySystem** | Memoria autobiográfica + improntas | Recuerdo |
| **BiasEngine** | Sesgos cognitivos | Psicología |
| **Motivation** | Impulso psicológico | Deseo/Necesidad |
| **Inhibición competitiva** | Foco atencional | Bottleneck cognitivo |
| **Trauma** | Herida psicológica | Estrés postraumático |
| **EpisodicMemory** | Recuerdo de evento | Memoria declarativa |
| **Emotional adjustment** | Estado de ánimo influyendo decisiones | Psicología emocional |
| **Sickness adjustment** | Malestar reduciendo actividad | Convalecencia |
| **Age adjustment** | Etapa vital influyendo impulsos | Psicología evolutiva |
| **Reputation** | Estigma social | Reputación |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/behavior/cognitive_capabilities.py` | `CognitiveCapabilities` | Capacidades cognitivas derivadas |
| `systems/behavior/free_will_system.py` | `FreeWillSystem` | Motivaciones continuas |
| `systems/behavior/cognitive_memory_system.py` | `CognitiveMemorySystem` | Memoria implícita y explícita |
| `systems/relationships/relationship_model.py` | `BiasEngine`, `GoalFilter` | Sesgos cognitivos y filtros de objetivos |

**Nota**: `BiasEngine` y `GoalFilter` están definidos en `relationship_model.py` porque se aplican a memorias relacionales, pero su funcionalidad es parte del sistema cognitivo.

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│         FASE 1: ACTUALIZACIÓN DE ESTADO MENTAL                  │
│                                                                 │
│ CognitiveMemorySystem:                                          │
│  ├── Para cada agente vivo:                                     │
│  │   ├── Consultar CognitiveCapabilities                        │
│  │   ├── Si tiene emociones:                                    │
│  │   │   ├── Decaer trauma_overcrowding                         │
│  │   │   ├── Acumular si local_pressure > threshold             │
│  │   │   ├── Decaer trauma_sickness                             │
│  │   │   ├── Acumular si is_sick                                │
│  │   │   ├── Decaer trauma_adoption                             │
│  │   │   ├── Decaer trauma_abandonment                          │
│  │   │   └── Calcular preferred_sector (adultos/seniors)        │
│  │   ├── Si tiene memoria episódica:                            │
│  │   │   ├── Decaer cada recuerdo con consolidación             │
│  │   │   ├── Podar memorias débiles (intensity < min)           │
│  │   │   ├── Podar exceso de capacidad                          │
│  │   │   ├── Sumar trauma episódico (valence < 0)               │
│  │   │   └── Sumar nostalgia (valence > 0)                      │
│  │   └── Si tiene cerebro complejo:                             │
│  │       └── cognitive_stress = trauma - nostalgia              │
│  └── Registrar todo en pending.memory_updates                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 2: EVOLUCIÓN DE MOTIVACIONES                         │
│                                                                 │
│ FreeWillSystem:                                                 │
│  ├── Para cada agente vivo con _motivations:                    │
│  │   ├── Consultar CognitiveCapabilities                        │
│  │   ├── 1. Decaimiento natural:                                │
│  │   │   └── person.decay_motivations(delta_days)               │
│  │   │                                                           │
│  │   ├── 2. Calcular 7 capas de ajuste:                         │
│  │   │   ├── genetic_motivations (rasgos base)                  │
│  │   │   ├── emotional_adjustments (stress, happiness, energy)  │
│  │   │   ├── environmental_adjustments (presión local)          │
│  │   │   ├── memory_adjustments (aprendizaje episódico)         │
│  │   │   ├── sickness_adjustments (enfermedad)                  │
│  │   │   ├── age_adjustments (etapa vital)                      │
│  │   │   └── systemic_adjustments (trauma + reputación)         │
│  │   │                                                           │
│  │   ├── 3. Aplicar ajustes a motivaciones continuas:           │
│  │   │   └── target = base + Σ adjustments                      │
│  │   │       └── pending.register_motivation_update(...)        │
│  │   │                                                           │
│  │   └── 4. Inhibición competitiva:                             │
│  │       ├── dominant = max(motivations)                        │
│  │       ├── inhibir las demás: value -= max × inhibition       │
│  │       ├── Si dominant_value >= action_threshold:             │
│  │       │   ├── Verificar cooldown                             │
│  │       │   ├── Si puede actuar:                               │
│  │       │   │   ├── Registrar acción dominante                 │
│  │       │   │   ├── Emitir evento relacional (si aplica)       │
│  │       │   │   ├── Consumir motivación (satisfacción)         │
│  │       │   │   └── Registrar cooldown                         │
│  │       │   └── Si no puede actuar (cooldown):                 │
│  │       │       └── Consumo doble (frustración)                │
│  │       └── Si no supera umbral: no actúa                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 3: INTEGRACIÓN CON RELACIONES                        │
│                                                                 │
│ Cuando FreeWillSystem ejecuta una acción:                       │
│  ├── Buscar agentes cercanos (radio 15)                         │
│  ├── Filtrar por etiquetas relacionales                         │
│  ├── Ponderar por BehaviorInfluence.get_target_priority         │
│  ├── Seleccionar target ponderado                               │
│  └── Emitir evento relacional:                                  │
│      ├── cooperation → COOPERATION                              │
│      ├── protection → CARE                                      │
│      ├── rebellion → CONFLICT                                   │
│      └── partnership → INTIMACY                                 │
│  └── RelationshipExperienceEngine.process_event(...)            │
│      └── Genera recuerdos con BiasEngine                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. CognitiveCapabilities - Capacidades Cognitivas

**📁 Archivo**: `systems/behavior/cognitive_capabilities.py`
**🌍 Equivalencia real**: La arquitectura cerebral: qué capacidades mentales tiene el organismo.

#### Atributos principales (derivados del genoma)

| Atributo | Tipo | Equivalencia real | Condición genética |
|----------|------|-------------------|-------------------|
| `has_emotions` | `bool` | Vida emocional | `nervous_system` > umbral |
| `has_episodic_memory` | `bool` | Memoria de eventos | `intelligence + nervous_system` altos |
| `has_complex_brain` | `bool` | Cerebro complejo | `intelligence` > 1.0 |
| `has_complex_motivations` | `bool` | Motivaciones elaboradas | `intelligence + sociability` altos |
| `has_social_awareness` | `bool` | Conciencia social | `sociability + nervous_system` |
| `can_recognize_individuals` | `bool` | Reconocer individuos | `nervous_system + intelligence` |
| `can_have_romantic_bonds` | `bool` | Vínculos románticos | `intelligence + sociability` altos |
| `can_form_immunological_memory` | `bool` | (ver doc 08 Salud) | `adaptive_immunity + nervous_system` |

#### Métodos de consulta

| Método | Parámetro | Descripción |
|--------|-----------|-------------|
| `can_form_trauma(type)` | `"overcrowding"`, `"sickness"`, `"abandonment"`, `"adoption"` | ¿Puede formar este trauma? |
| `can_have_memory_type(type)` | `"companion"`, `"conflict"`, `"marriage"`, etc. | ¿Puede tener este recuerdo? |
| `can_have_motivation(name)` | `"independence"`, `"exploration"`, etc. | ¿Puede tener esta motivación? |
| `can_participate_in_event(type)` | `"cooperation"`, `"conflict"`, etc. | ¿Puede participar en este evento? |

#### Jerarquía cognitiva por organismo

| Organismo | Emotions | Episodic | Complex Brain | Complex Motivations | Romantic Bonds |
|-----------|----------|----------|---------------|---------------------|----------------|
| Planta | ❌ | ❌ | ❌ | ❌ | ❌ |
| Bacteria | ❌ | ❌ | ❌ | ❌ | ❌ |
| Insecto | ⚠️ básico | ❌ | ❌ | ❌ | ❌ |
| Pez | ✅ básico | ❌ | ❌ | ❌ | ❌ |
| Reptil | ✅ básico | ⚠️ limitado | ❌ | ❌ | ❌ |
| Ave | ✅ | ⚠️ limitado | ⚠️ | ❌ | ⚠️ |
| Lobo | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Delfín | ✅ | ✅ | ✅ | ✅ | ✅ |
| Humano | ✅ | ✅ | ✅ | ✅ | ✅ |

#### Tipos de memoria soportados

```python
TYPE_COMPANION    = "companion"
TYPE_CONFLICT     = "conflict"
TYPE_EXPERIENCE   = "experience"
TYPE_EVENT        = "event"
TYPE_MARRIAGE     = "marriage"
TYPE_CHILD        = "child"
TYPE_DEATH        = "death"
TYPE_ADOPTION     = "adoption"
TYPE_DIVORCE      = "divorce"
TYPE_DISEASE      = "disease"
TYPE_MIGRATION    = "migration"
```

#### Tipos de trauma soportados

```python
TYPE_OVERCROWDING = "overcrowding"
TYPE_SICKNESS     = "sickness"
TYPE_ABANDONMENT  = "abandonment"
TYPE_ADOPTION     = "adoption"
```

#### Motivaciones soportadas

```python
TYPE_INDEPENDENCE = "independence"
TYPE_EXPLORATION  = "exploration"
TYPE_REBELLION    = "rebellion"
TYPE_PARTNERSHIP  = "partnership"
TYPE_PROTECTION   = "protection"
TYPE_MIGRATION    = "migration"
TYPE_COOPERATION  = "cooperation"
```

#### Ejemplos

```python
# Humano: cognición completa
human_caps = CognitiveCapabilities.from_genome(human_genome)
human_caps.has_emotions                    # True
human_caps.has_episodic_memory             # True
human_caps.has_complex_brain               # True
human_caps.can_form_trauma("abandonment")  # True
human_caps.can_have_motivation("migration") # True

# Planta: sin cognición
plant_caps = CognitiveCapabilities.from_genome(plant_genome)
plant_caps.has_emotions                    # False
plant_caps.has_episodic_memory             # False
plant_caps.can_form_trauma(...)            # False
plant_caps.can_have_motivation(...)        # False

# Pez: emoción básica pero sin memoria episódica
fish_caps = CognitiveCapabilities.from_genome(fish_genome)
fish_caps.has_emotions                     # True
fish_caps.has_episodic_memory              # False
fish_caps.can_have_motivation("migration") # True (instinto)

# Insecto: sistema nervioso simple
insect_caps = CognitiveCapabilities.from_genome(insect_genome)
insect_caps.has_emotions                   # False (o muy básico)
insect_caps.can_recognize_individuals      # False
```

#### Consideraciones

- **Inmutable**: una vez creada, no se modifica
- **Determinista**: mismo genoma → mismas capacidades
- **No conoce especies**: solo consulta rasgos
- Si un rasgo no existe, usa valores por defecto apropiados
- Todos los métodos de consulta son seguros ante rasgos faltantes

---

### 2. FreeWillSystem - Motivaciones Continuas

**📁 Archivo**: `systems/behavior/free_will_system.py`
**🌍 Equivalencia real**: El sistema de impulsos psicológicos que guían el comportamiento: hambre, curiosidad, deseo de compañía, etc.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Las 7 motivaciones

| Motivación | Base genética | Equivalencia real |
|------------|---------------|-------------------|
| `independence` | impulsivity + aggressiveness | Deseo de autonomía |
| `exploration` | curiosity + impulsivity | Curiosidad |
| `rebellion` | aggressiveness + impulsivity | Impulso contestatario |
| `partnership` | sociability + temperament | Deseo de compañía |
| `protection` | temperament | Instinto protector |
| `migration` | curiosity + impulsivity | Impulso migratorio |
| `cooperation` | sociability + obedience + temperament | Impulso cooperativo |

#### Fórmulas de base genética

```python
independence = impulsivity * impulsivity_weight 
             + aggressiveness * aggressiveness_weight * 0.5 
             + (1.0 - obedience) * obedience_weight * 0.5

exploration = curiosity * curiosity_weight 
            + impulsivity * impulsivity_weight * 0.3

rebellion = aggressiveness * aggressiveness_weight 
          + impulsivity * impulsivity_weight * 0.5 
          + (1.0 - obedience) * obedience_weight

partnership = sociability * sociability_weight 
            + temperament * temperament_weight * 0.5

protection = temperament * temperament_weight 
           + (1.0 - impulsivity) * impulsivity_weight * 0.3

migration = curiosity * curiosity_weight 
          + impulsivity * impulsivity_weight * 0.4

cooperation = sociability * sociability_weight 
            + obedience * obedience_weight 
            + temperament * temperament_weight * 0.3
```

#### Factores de ajuste (7 capas)

| Capa | Descripción | Ejemplo |
|------|-------------|---------|
| **Genética** | Base desde rasgos | Agresividad alta → más rebelión |
| **Emocional** | Estado actual | Estrés alto → más migración |
| **Ambiental** | Presión local | Superpoblación → más independencia |
| **Memoria** | Aprendizaje episódico | Recuerdos de migración positiva → más migración |
| **Enfermedad** | Estado de salud | Enfermo → menos exploración |
| **Edad** | Etapa vital | Adolescente → más rebelión |
| **Sistémico** | Trauma + reputación | Trauma de abandono → más migración |

#### Ajustes emocionales

```python
# Solo si has_emotions == True
independence += stress * stress_weight * 0.5
exploration += (happiness - 0.5) * happiness_weight * 0.3
rebellion += stress * stress_weight
partnership += (happiness - 0.5) * happiness_weight
protection += (1.0 - happiness) * happiness_weight * 0.5
migration += stress * stress_weight * 0.7
cooperation += (happiness - 0.5) * happiness_weight * 0.5

# Factor de energía (multiplicador global)
energy_factor = energy * energy_weight
for motivation in adjustments:
    adjustments[motivation] *= energy_factor
```

#### Ajustes ambientales

```python
excess_pressure = max(0.0, pressure - 1.0)
independence += excess_pressure * crowding_weight
rebellion += excess_pressure * pressure_weight * 0.5
partnership -= excess_pressure * pressure_weight * 0.3
protection += excess_pressure * pressure_weight * 0.3
migration += excess_pressure * pressure_weight
cooperation -= excess_pressure * pressure_weight * 0.2
```

#### Ajustes por memoria episódica (aprendizaje)

| Tipo de memoria | Efecto en motivaciones |
|----------------|----------------------|
| `migration_*` (valence +) | +migration, +exploration |
| `conflict_*` (valence -) | +rebellion, -cooperation |
| `conflict_*` (valence +) | +cooperation |
| `marriage_*`, `companion_*` (valence +) | +partnership, +protection |
| `divorce_*` (valence -) | -partnership, +independence |
| `adoption_*` (valence +) | +protection, +cooperation |
| `death_*` (valence -) | +independence, -cooperation, +migration |
| `child_*` (valence +) | +protection, +partnership |
| `disease_*` (valence -) | +independence |

#### Ajustes por enfermedad

```python
# Solo si is_sick == True
sickness_factor = min(1.0, len(active_infections) * 0.3)
independence -= sickness_factor * sickness_factor
exploration -= sickness_factor * sickness_factor
rebellion -= sickness_factor * sickness_factor * 0.5
partnership += sickness_factor * sickness_factor * 0.3
protection += sickness_factor * sickness_factor
migration -= sickness_factor * sickness_factor
cooperation += sickness_factor * sickness_factor * 0.5
```

#### Ajustes por etapa vital

| Etapa | Efecto |
|-------|--------|
| **Adolescencia** | +independence (0.3), +rebellion (0.3), +exploration (0.2) |
| **Adultez temprana** | +partnership (0.2) |
| **Con hijos** | +protection (0.3) |
| **Senior** | -exploration (0.2), -migration (0.3), +protection (0.2) |

#### Ajustes sistémicos (trauma + reputación)

```python
# Solo si can_form_trauma("abandonment")
if trauma_abandonment > 0.3:
    migration += trauma_abandonment * 0.6
    cooperation -= trauma_abandonment * 0.4
    partnership -= trauma_abandonment * 0.3

# Solo si can_form_trauma("adoption")
if trauma_adoption > 0.3:
    independence += trauma_adoption * 0.5
    rebellion += trauma_adoption * 0.4
    protection -= trauma_adoption * 0.3

# Reputación baja: dificulta cooperación y emparejamiento
if reputation < 0.5:
    deficit = 0.5 - reputation
    cooperation -= deficit * 0.5
    partnership -= deficit * 0.4
```

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada person:
        ├── Si entity_id en pending.deaths → limpiar cooldowns
        ├── Si no tiene _motivations → skip
        ├── Consultar CognitiveCapabilities
        │
        ├── 1. Decaimiento natural:
        │   └── person.decay_motivations(delta_days, decay_rate)
        │
        ├── 2. Calcular 7 capas de ajuste
        │
        ├── 3. Aplicar ajustes:
        │   └── Para cada motivation en fw_cfg.motivations:
        │       ├── Si NOT can_have_motivation → forzar a 0
        │       ├── target = base + Σ adjustments
        │       ├── target = clamp(0, 1, target)
        │       ├── delta = target - current
        │       └── Si |delta| > 0.01: register_motivation_update
        │
        └── 4. Inhibición competitiva:
            ├── dominant, value = _get_dominant_motivation(...)
            ├── threshold = _get_action_threshold(dominant, fw_cfg)
            ├── Si value >= threshold:
            │   ├── Si _can_trigger_action(eid, dominant, current_day):
            │   │   ├── Registrar acción dominante
            │   │   ├── _emit_relationship_events(...)
            │   │   ├── Consumo de motivación (satisfacción)
            │   │   └── _register_action(eid, dominant, current_day)
            │   └── Si NO puede actuar (cooldown):
            │       └── Consumo doble (frustración)
```

#### Inhibición competitiva

```python
def _get_dominant_motivation(self, person, fw_cfg):
    max_name, max_value = max(person._motivations.items(), key=lambda x: x[1])
    
    inhibited_motivations = {}
    for name, value in person._motivations.items():
        if name == max_name:
            inhibited_motivations[name] = value
        else:
            inhibition = max_value * fw_cfg.inhibition_factor
            inhibited_motivations[name] = max(0.0, value - inhibition)
    
    if inhibited_motivations:
        return max(inhibited_motivations.items(), key=lambda x: x[1])
    
    return (max_name, max_value)
```

**Problema que resuelve**: Sin inhibición, múltiples motivaciones podrían activarse simultáneamente.

**Solución**: 
- La motivación máxima inhibe proporcionalmente a las demás
- Solo la motivación más fuerte tras inhibición puede ejecutar acción
- `inhibition_factor` (config) controla la intensidad

#### Cooldowns por motivación

| Motivación | Cooldown (días) | Consumo |
|------------|-----------------|---------|
| independence | 30 | 0.20 |
| exploration | 15 | 0.15 |
| rebellion | 60 | 0.25 |
| partnership | 30 | 0.20 |
| protection | 7 | 0.15 |
| migration | 90 | 0.30 |
| cooperation | 15 | 0.15 |

#### Integración con Relaciones

Cuando una motivación dominante supera el umbral, `FreeWillSystem` puede emitir un evento relacional hacia un agente cercano, filtrado por etiquetas:

| Motivación | Evento emitido | Etiquetas requeridas | Etiquetas excluidas |
|------------|----------------|---------------------|---------------------|
| cooperation | COOPERATION | Amigo, Aliado, Familia, Conocido | Rival, Enemigo |
| protection | CARE | Familia, Amigo, Amante | - |
| rebellion | CONFLICT | - | Familia, Amante |
| partnership | INTIMACY | - | Enemigo, Rival |

El target se selecciona ponderado por `BehaviorInfluence.get_target_priority`.

```python
def _emit_relationship_events(self, person, motivation, motivation_value, state, current_day):
    nearby_agents = self._find_nearby_agents(person, state, radius=15.0)
    if not nearby_agents:
        return
    
    # Filtrar por etiquetas según motivación
    filtered_targets = BehaviorInfluence.filter_targets_by_labels(
        person, nearby_agents, current_day,
        required_labels=required_labels,
        excluded_labels=excluded_labels
    )
    
    # Ponderar por prioridad relacional
    weighted_targets = [(t, BehaviorInfluence.get_target_priority(person, t, current_day)) 
                        for t in filtered_targets]
    
    # Selección ponderada aleatoria
    total_weight = sum(w for _, w in weighted_targets)
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    for t, w in weighted_targets:
        cumulative += w
        if cumulative >= r:
            target = t
            break
    
    # Determinar tipo de evento
    if motivation == "cooperation":
        event_type = RelationshipEventType.COOPERATION
        intensity = min(1.0, motivation_value * 0.7)
        context_str = "cooperacion_motivada"
    elif motivation == "protection":
        event_type = RelationshipEventType.CARE
        intensity = min(1.0, motivation_value * 0.8)
        context_str = "proteccion_motivada"
    # ... etc
```

---

### 3. CognitiveMemorySystem - Memoria Cognitiva

**📁 Archivo**: `systems/behavior/cognitive_memory_system.py`
**🌍 Equivalencia real**: El cerebro con su capacidad de recordar eventos, guardar traumas, y desarrollar preferencias.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Dos tipos de memoria

| Tipo | Descripción | Decaimiento |
|------|-------------|-------------|
| **Implícita (traumas)** | Heridas psicológicas automáticas | Exponencial con λ = f(temperament) |
| **Explícita (episódica)** | Recuerdos de eventos específicos | Con consolidación por refuerzo |

#### Traumas implícitos

| Trauma | Desencadenante | Efecto |
|--------|----------------|--------|
| `trauma_overcrowding` | `local_pressure > overcrowding_threshold` | Estrés, ansiedad |
| `trauma_sickness` | `is_sick == True` | Miedo a enfermedad |
| `trauma_abandonment` | Orfandad prolongada | Huida, desconfianza |
| `trauma_adoption` | Adopción (evento disruptivo) | Independencia, rebelión |

#### Fórmula de decaimiento de trauma

```python
adjusted_lambda = base_forgetting_rate * (temperament + temperament_modifier)
decay_factor = exp(-adjusted_lambda * delta_days)
new_trauma = current_trauma * decay_factor
if trigger_active:
    new_trauma += impact * delta_days
new_trauma = min(max_trauma_cap, new_trauma)
```

**Temperamento alto** = olvida más rápido (resiliencia)

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada person:
        ├── Si entity_id en pending.deaths → skip
        ├── Consultar CognitiveCapabilities
        │
        ├── PARTE A: MEMORIA IMPLÍCITA (Traumas y Preferencias)
        │   ├── Si has_emotions:
        │   │   ├── Trauma hacinamiento:
        │   │   │   ├── Decaer exponencialmente
        │   │   │   └── Acumular si pressure > threshold
        │   │   ├── Trauma enfermedad:
        │   │   │   ├── Decaer exponencialmente
        │   │   │   └── Acumular si is_sick
        │   │   ├── Trauma adopción (si can_form):
        │   │   │   ├── Decaer exponencialmente
        │   │   │   └── Reducir stress, aumentar happiness
        │   │   ├── Trauma abandono (si can_form):
        │   │   │   └── Decaer exponencialmente
        │   │   ├── Preferencia espacial (si has_episodic_memory):
        │   │   │   └── Si adulto con hijos o senior: preferred_sector = (x//size, y//size)
        │   │   └── Rebellion cooldown (si has_complex_motivations):
        │   │       └── Reducir por delta_days
        │   └── Registrar en pending.memory_updates
        │
        └── PARTE B: MEMORIA EXPLÍCITA (Recuerdos episódicos)
            ├── Si has_episodic_memory:
            │   ├── Para cada mem en episodic:
            │   │   ├── Asegurar metadatos (created_day, last_reinforced_day, etc.)
            │   │   ├── Calcular emotional_importance
            │   │   ├── Calcular reinforcement_bonus
            │   │   ├── effective_rate = base * (1 - importance - bonus)
            │   │   ├── intensity *= exp(-effective_rate * delta_days)
            │   │   ├── Si intensity <= min → marcar para borrar
            │   │   ├── Si valence < 0 → sumar a total_trauma_episodic
            │   │   └── Si valence > 0 → sumar a total_nostalgia
            │   ├── Borrar memorias débiles
            │   ├── Poda por capacidad máxima
            │   ├── Si has_complex_brain:
            │   │   ├── trauma_penalty = total_trauma * trauma_to_stress_factor
            │   │   ├── nostalgia_buff = total_nostalgia * nostalgia_buffer_factor
            │   │   └── cognitive_stress = max(0, trauma_penalty - nostalgia_buff)
            │   └── Registrar en pending.memory_updates
            └── Si NO has_episodic_memory:
                └── Registrar episodic = {}, cognitive_stress = 0
```

#### Memoria episódica

Estructura de cada recuerdo:

```python
{
    'intensity': float,        # Fuerza actual [0.0, 1.0]
    'valence': int,            # +1 (positivo) / -1 (negativo)
    'created_day': float,      # Día de creación
    'last_reinforced_day': float,  # Último refuerzo
    'times_reinforced': int,   # Número de veces reforzado
    'context': str,            # Contexto del evento
}
```

#### Decaimiento con consolidación

```python
emotional_importance = |valence| * emotional_importance_factor
reinforcement_bonus = min(0.5, times_reinforced * 0.05)
effective_rate = episodic_forgetting_rate * (1 - emotional_importance - reinforcement_bonus)
new_intensity = intensity * exp(-effective_rate * delta_days)
```

**Los recuerdos importantes y reforzados decaen más lentamente.**

#### Estrés cognitivo

```python
trauma_penalty = total_trauma_episodic * trauma_to_stress_factor
nostalgia_buff = total_nostalgia * nostalgia_buffer_factor
cognitive_stress = max(0, trauma_penalty - nostalgia_buff)
```

**Interpretación**: Los traumas no resueltos generan estrés; los recuerdos positivos amortiguan.

#### Método estático para añadir memorias

```python
CognitiveMemorySystem.add_memory(
    person=agent,
    mem_type=CognitiveMemorySystem.TYPE_CHILD,
    target_id=str(child_id),
    intensity=0.9,
    valence=1,
    context="nacimiento",
    current_day=current_day,
    pending=pending,
)
```

**Comportamiento**:
- Si el recuerdo ya existe, lo refuerza:
  - Suma intensidad (hasta 1.0)
  - Promedia valencia
  - Incrementa `times_reinforced`
  - Actualiza `last_reinforced_day`
- Si es nuevo, lo crea con metadatos completos

#### Método para calcular sesgo hacia un target

```python
bias = CognitiveMemorySystem.get_bias_towards(person, target_id)
# Retorna float en [-1.0, 1.0]
# Positivo: afinidad acumulada
# Negativo: hostilidad acumulada
```

Suma `intensity * valence` de todas las memorias que mencionan al target.

---

### 4. BiasEngine - Sesgos Cognitivos

**📁 Archivo**: `systems/relationships/relationship_model.py` (definido junto con el modelo de relaciones)
**🌍 Equivalencia real**: Los sesgos cognitivos que distorsionan nuestra percepción: recordamos más lo malo, idealizamos a los muertos, el sesgo de recencia, etc.

#### Método principal

```python
BiasEngine.apply_biases(temp_memory, owner, rel, current_day) -> float
```

Recibe una `PersonalMemory` recién creada y retorna el peso final después de aplicar todos los sesgos.

#### Sesgos implementados

| Sesgo | Descripción | Efecto |
|-------|-------------|--------|
| **Negativity bias** | Recordamos más lo negativo | Memorias negativas × amplificación |
| **Recency bias** | Lo reciente pesa más | Memorias recientes × amplificación |
| **Post-mortem idealization** | Los muertos se vuelven mejores | Memorias de fallecidos × reducción de negatividad |
| **Betrayal context** | Traiciones se recuerdan más intensamente | Memorias con contexto de traición × extra negatividad |
| **Narrative amplification** | Memorias que coinciden con narrativa se amplifican | Positivas × más si narrativa positiva |

#### Flujo de aplicación

```
apply_biases(temp_memory, owner, rel, current_day)
    │
    ├── weight = temp_memory.personal_weight
    │
    ├── 1. Negativity bias:
    │   └── Si valence < 0: weight *= negativity_multiplier
    │
    ├── 2. Recency bias:
    │   └── days_since = current_day - temp_memory.day
    │   └── recency_factor = exp(-days_since * decay)
    │   └── weight *= (1.0 + recency_factor * recency_bonus)
    │
    ├── 3. Post-mortem idealization:
    │   └── Si partner está muerto Y valence < 0:
    │       └── weight *= idealization_factor (reduce negatividad)
    │
    ├── 4. Betrayal context:
    │   └── Si "traicion" en context.lower():
    │       └── weight *= betrayal_amplification
    │
    ├── 5. Narrative amplification:
    │   └── Si valence > 0 Y narrativa positiva activa:
    │       └── weight *= narrative_amplification
    │
    └── Retornar max(0.0, weight)
```

#### Ejemplos

```python
# Memoria positiva reciente con narrativa positiva
mem = PersonalMemory(valence=1, day=100, personal_weight=50)
# current_day = 105 (reciente)
# Narrativa positiva activa
final_weight = BiasEngine.apply_biases(mem, owner, rel, 105)
# final_weight > 50 (amplificado)

# Memoria negativa antigua
mem = PersonalMemory(valence=-1, day=100, personal_weight=50)
# current_day = 500 (antigua)
final_weight = BiasEngine.apply_biases(mem, owner, rel, 500)
# final_weight < 50 (recencia reduce, pero negativity bias amplifica)

# Memoria de pareja fallecida
mem = PersonalMemory(valence=-1, personal_weight=50)
# Partner está muerto
final_weight = BiasEngine.apply_biases(mem, owner, rel, current_day)
# final_weight reducido por idealización post-mortem

# Memoria de traición
mem = PersonalMemory(valence=-1, context="traicion_calculada", personal_weight=50)
final_weight = BiasEngine.apply_biases(mem, owner, rel, current_day)
# final_weight muy amplificado por betrayal context
```

#### Consideraciones

- El peso final nunca es negativo (máximo 0.0)
- Los sesgos se aplican en orden secuencial
- Cada sesgo es multiplicativo sobre el peso anterior
- El resultado se usa para calcular labels relacionales y afinidad

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                     │
│   nervous_system, intelligence, sociability, curiosity,        │
│   temperament, impulsivity, obedience, aggressiveness           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           CognitiveCapabilities (inmutable)                     │
│   - has_emotions, has_episodic_memory, has_complex_brain       │
│   - can_form_trauma(type), can_have_memory_type(type)          │
│   - can_have_motivation(name), can_participate_in_event(type)  │
│   - has_social_awareness, can_recognize_individuals            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│ CognitiveMemory      │   │        FreeWillSystem            │
│ System               │   │                                  │
│                      │   │   - 7 motivaciones continuas     │
│ - Traumas implícitos │   │   - Inhibición competitiva       │
│ - Memoria episódica  │   │   - Emite eventos relacionales   │
│ - Estrés cognitivo   │   │   - Cooldowns por motivación     │
└──────────┬───────────┘   └─────────────┬────────────────────┘
           │                             │
           │ retroalimenta               │ emite eventos
           │ (aprendizaje)               ▼
           │              ┌──────────────────────────────────────┐
           └──────────────► RelationshipExperienceEngine         │
                          │   (documento 06)                     │
                          │                                      │
                          │  - Crea WorldEvent                   │
                          │  - Crea PersonalMemory (asimétrica)  │
                          │  - Aplica BiasEngine                 │
                          │  - Aplica GoalFilter                 │
                          │  - Añade a Relationship.memories     │
                          └──────────────────────────────────────┘
                                      │
                                      ▼
                          Relationship.memories
                          (etiquetas, narrativas)
                                      │
                                      ▼
                          BehaviorInfluence
                          (documento 06)
                          - get_target_priority
                          - get_social_attraction
                          - get_multiple_social_anchors
                                      │
                                      ▼
                          FreeWillSystem._emit_relationship_events
                          (usa BehaviorInfluence para elegir target)
```

---

## ⚙️ Configuración relevante

```python
# FreeWillConfig
config.free_will.motivation_decay_rate = 0.02
config.free_will.action_threshold = 0.7
config.free_will.inhibition_factor = 0.4

# Pesos genéticos
config.free_will.impulsivity_weight = 0.4
config.free_will.curiosity_weight = 0.4
config.free_will.obedience_weight = 0.3
config.free_will.aggressiveness_weight = 0.4
config.free_will.temperament_weight = 0.3
config.free_will.sociability_weight = 0.4

# Pesos emocionales
config.free_will.stress_weight = 0.5
config.free_will.happiness_weight = 0.4
config.free_will.energy_weight = 0.6

# Pesos ambientales
config.free_will.crowding_weight = 0.6
config.free_will.pressure_weight = 0.5

# Aprendizaje
config.free_will.episodic_memory_factor = 0.2

# Enfermedad
config.free_will.sickness_factor = 0.4

# Etapas vitales
config.free_will.adolescence_start_days = 4380.0   # ~12 años
config.free_will.adolescence_end_days = 6570.0     # ~18 años

# CognitionConfig
config.cognition.base_forgetting_rate = 0.01
config.cognition.temperament_modifier = 0.5
config.cognition.overcrowding_threshold = 1.5
config.cognition.overcrowding_impact = 0.05
config.cognition.sickness_impact = 0.08
config.cognition.max_trauma_cap = 2.0
config.cognition.episodic_forgetting_rate = 0.02
config.cognition.emotional_importance_factor = 0.3
config.cognition.episodic_min_intensity = 0.05
config.cognition.max_episodic_memories = 50
config.cognition.trauma_to_stress_factor = 0.4
config.cognition.nostalgia_buffer_factor = 0.2
config.cognition.max_cognitive_stress = 2.0
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_cognitive_capabilities.py` | Capacidades cognitivas por organismo |
| `tests/unit/test_free_will.py` | Motivaciones continuas |
| `tests/unit/test_cognitive_memory.py` | Memoria implícita y explícita |
| `tests/unit/test_bias_engine.py` | Sesgos cognitivos |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo de decisión completo de un humano estresado

```python
# Estado inicial
agent._motivations = {
    "independence": 0.3,
    "exploration": 0.3,
    "rebellion": 0.2,
    "partnership": 0.5,
    "protection": 0.4,
    "migration": 0.2,
    "cooperation": 0.5,
}
agent.emotions["stress"] = 0.8
agent.emotions["happiness"] = 0.3
agent.emotions["energy"] = 0.7

# 1. CognitiveMemorySystem:
#    - trauma_overcrowding decae
#    - No hay hacinamiento, no se acumula
#    - Memoria episódica: recuerdos de cooperación (+), conflicto (-)

# 2. FreeWillSystem calcula ajustes:
#    Genetic:
#      impulsivity=0.6, curiosity=0.8, obedience=0.4, sociability=0.7
#      migration_base = 0.8*0.4 + 0.6*0.4*0.4 = 0.32 + 0.096 = 0.416
#    Emotional:
#      stress=0.8 → migration += 0.8 * 0.5 * 0.7 = 0.28
#      happiness=0.3 → partnership += (0.3-0.5) * 0.4 = -0.08
#    Environmental:
#      pressure=1.2 → migration += 0.2 * 0.5 = 0.1
#    Memory:
#      Recuerdos de migración positiva → migration += 0.1
#    Systemic:
#      trauma_abandonment=0.5 → migration += 0.5 * 0.6 = 0.3
#
#    migration_target = 0.416 + 0.28 + 0.1 + 0.1 + 0.3 = 1.196
#    migration_target = clamp(0, 1, 1.196) = 1.0

# 3. Inhibición competitiva:
#    migration = 1.0 (dominante)
#    Las demás se inhiben: value -= 1.0 * 0.4
#    Ej: cooperation = 0.5 - 0.4 = 0.1

# 4. migration (1.0) >= threshold (0.7) → activar acción
#    Verificar cooldown: última migración fue hace 100 días > 90 → OK
#    Ejecutar: MigrationSystem detecta motivación alta
#    Consumo de motivación: migration -= 0.3 → 0.7
```

### Ejemplo 2: Planta sin cognición

```python
plant_caps = CognitiveCapabilities.from_genome(plant_genome)

# FreeWillSystem:
# - can_have_motivation("independence") → False
# - can_have_motivation("migration") → False
# - Todas las motivaciones se fuerzan a 0
# - No hay inhibición competitiva (no hay motivaciones)
# - No hay eventos relacionales emitidos

# CognitiveMemorySystem:
# - has_emotions → False
# - No se procesan traumas
# - has_episodic_memory → False
# - No se procesa memoria episódica
# - cognitive_stress = 0

# Resultado: la planta no tiene vida interior, solo crece y se reproduce
```

### Ejemplo 3: Aprendizaje desde memoria episódica

```python
# Agente tuvo una migración exitosa en el pasado
CognitiveMemorySystem.add_memory(
    person=agent,
    mem_type=CognitiveMemorySystem.TYPE_MIGRATION,
    target_id="45_60",
    intensity=0.8,
    valence=1,
    context="migracion_exitosa",
    current_day=365.0,
    pending=pending,
)

# 30 días después, FreeWillSystem lee la memoria:
# - migration ajusta +intensity * episodic_memory_factor = 0.8 * 0.2 = 0.16
# - exploration ajusta +intensity * factor * 0.5 = 0.08
# El agente tiende a querer migrar OTRA VEZ (aprendizaje positivo)
```

### Ejemplo 4: Sesgo de negatividad

```python
# Memoria de una traición reciente
mem = PersonalMemory(
    valence=-1,
    day=current_day - 10,  # 10 días atrás (reciente)
    personal_weight=50,
    context="traicion_calculada",
)

# BiasEngine aplica:
# 1. Negativity bias: 50 * 1.5 = 75
# 2. Recency: 75 * 1.3 = 97.5 (reciente)
# 3. No post-mortem (partner vivo)
# 4. Betrayal context: 97.5 * 1.8 = 175.5
# 5. No narrative amplification (valence negativo)
#
# final_weight = 175.5 (vs 50 original)
# Este recuerdo pesará mucho en las labels relacionales
```

### Ejemplo 5: Estrés cognitivo por trauma acumulado

```python
# Agente con múltiples traumas no resueltos
episodic = {
    "conflict_101": {"intensity": 0.6, "valence": -1},
    "death_202": {"intensity": 0.7, "valence": -1},
    "disease_303": {"intensity": 0.4, "valence": -1},
}

# Nostalgia:
episodic.update({
    "companion_404": {"intensity": 0.5, "valence": 1},
    "child_505": {"intensity": 0.3, "valence": 1},
})

# Cálculo:
total_trauma_episodic = 0.6 + 0.7 + 0.4 = 1.7
total_nostalgia = 0.5 + 0.3 = 0.8

trauma_penalty = 1.7 * 0.4 = 0.68
nostalgia_buff = 0.8 * 0.2 = 0.16

cognitive_stress = max(0, 0.68 - 0.16) = 0.52

# Este estrés cognitivo puede afectar decisiones futuras
# (ej: menos cooperación, más aislamiento)
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Motivaciones continuas**: no hay flags binarios, solo intensidades [0.0, 1.0]
- **Decaimiento natural**: los impulsos no satisfechos desaparecen
- **Inhibición competitiva**: solo una motivación puede ejecutar acción por tick
- **Aprendizaje desde experiencia**: la memoria episódica retroalimenta motivaciones
- **Capacidades derivadas**: genoma → capacidades → comportamiento posible
- **Asimetría subjetiva**: mismo evento → recuerdos diferentes por agente

### Arquitectura de decisión

```
GENOMA
   ↓
CognitiveCapabilities (qué puede sentir/pensar)
   ↓
CognitiveMemorySystem (traumas + recuerdos)
   ↓
FreeWillSystem (motivaciones + decisión)
   ↓
Acción (evento relacional / movimiento)
```

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| Caché de capacidades | Todos | Evita recalcular cada tick |
| Bounding box en `_find_nearby_agents` | FreeWillSystem | O(N²) → O(N·k) |
| Poda de memoria episódica | CognitiveMemorySystem | Mantiene capacidad limitada |
| Decaimiento exponencial | Ambos | Cálculo O(1) por memoria |
| Filtros tempranos | FreeWillSystem | Skip si no tiene capacidades |

### Limitaciones
- No hay planificación a largo plazo (solo reacción inmediata)
- Los agentes no se comunican motivaciones entre sí
- No hay aprendizaje social (solo por experiencia propia)
- Los traumas no se tratan (solo decaen)
- No hay emociones secundarias (vergüenza, culpa, orgullo)
- El estrés cognitivo no tiene efectos directos en movimiento

### Errores comunes
- ❌ Modificar motivaciones directamente (usar `PendingChanges.register_motivation_update`)
- ❌ Asumir que todos los organismos tienen las mismas motivaciones (filtrar por `CognitiveCapabilities`)
- ❌ Olvidar el decaimiento (motivaciones crecen indefinidamente)
- ❌ Aplicar sesgos cognitivos sin considerar valencia (positivo vs negativo)
- ❌ Generar memorias episódicas para organismos sin capacidad (verificar `has_episodic_memory`)
- ❌ Olvidar la inhibición competitiva (varias motivaciones activas simultáneas)

---

## 🎓 Conceptos clave

### ¿Por qué motivaciones continuas y no reglas?

**Principio de emergencia**:
- Las reglas son frágiles: `SI energy < 0.3 ENTONCES emigrar`
- Las motivaciones son fluidas: un agente con hambre Y miedo a migrar tendrá conflicto interno
- El comportamiento emerge del balance, no de condicionales
- Más realista psicológicamente

### ¿Por qué inhibición competitiva?

**Principio de bottleneck atencional**:
- El cerebro no puede perseguir múltiples objetivos simultáneamente
- Una motivación domina en cada momento
- Las demás son inhibidas proporcionalmente
- Esto genera foco conductual realista

### ¿Por qué traumas implícitos y explícitos?

**Principio de memoria dual**:
- **Implícita**: automática, no consciente (miedo, ansiedad)
- **Explícita**: consciente, narrativa (recuerdo de evento)
- En la vida real funcionan así
- Los traumas implícitos afectan sin recordar el evento específico

### ¿Por qué sesgos cognitivos?

**Principio de irracionalidad humana**:
- No procesamos información objetivamente
- Recordamos más lo negativo (sesgo de negatividad)
- Lo reciente pesa más (sesgo de recencia)
- Idealizamos a los muertos (sesgo post-mortem)
- Sin sesgos, las relaciones serían aburridas y predecibles

### ¿Por qué aprendizaje desde memoria episódica?

**Principio de continuidad psicológica**:
- Las experiencias pasadas afectan decisiones futuras
- Migración exitosa → más ganas de migrar
- Conflicto traumático → menos cooperación
- Esto crea personalidades consistentes y evolución de comportamiento

### ¿Por qué estrés cognitivo = trauma - nostalgia?

**Principio de salud mental**:
- Los traumas no resueltos pesan en la mente
- Los recuerdos positivos amortiguan el malestar
- El balance determina el bienestar psicológico
- Ciclo de retroalimentación realista

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 4 |
| Motivaciones modeladas | 7 |
| Tipos de trauma | 4 |
| Tipos de memoria episódica | 11 |
| Capas de ajuste | 7 |
| Sesgos cognitivos | 5 |
| Tests cubriendo comportamiento | ~20 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Planificación a medio plazo (sub-objetivos)
- [ ] Emociones secundarias (vergüenza, culpa, orgullo)
- [ ] Aprendizaje social (observar a otros)
- [ ] Tratamiento de traumas (terapia, tiempo)

### Posibles
- [ ] Metas a largo plazo (proyectos vitales)
- [ ] Comunicación de motivaciones entre agentes
- [ ] Sueño y descanso (necesidad de parar)
- [ ] Adicciones (motivaciones que crecen sin control)
- [ ] Trastornos psicológicos (depresión, ansiedad)
- [ ] Creatividad (generar ideas nuevas)
- [ ] Introspección (auto-evaluación de motivaciones)
- [ ] Altruismo y egoísmo como dimensiones

---

*Documento: 08_COMPORTAMIENTO.md*
*Versión: 1.0*
