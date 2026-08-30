# 11 - Estructura Social

## 📋 Resumen

El **Sistema de Estructura Social** modela las estructuras sociales emergentes: la presión que las relaciones ejercen sobre los agentes, los núcleos residenciales (convivencia), y las capacidades sociales derivadas del genoma que determinan qué tipo de vínculos puede formar cada organismo. Es el puente entre las relaciones personales y el comportamiento físico.

**Filosofía fundamental**: *La estructura social emerge de las capacidades genéticas del organismo. Las plantas no forman familias, los lobos no se casan, los humanos sí. Cada especie tiene su propio nivel de complejidad social, y el sistema lo respeta.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Derivar capacidades sociales del genoma (`SocialCapabilities`)
- Calcular presión social individual para decisiones de movimiento (`SocialPressureCalculator`)
- Aplicar presión ambiental al mapa basada en eventos sociales
- Gestionar núcleos residenciales (convivencia) (`ResidentialNucleus`)
- Proveer selección probabilística para decisiones de movimiento
- Determinar qué etiquetas relacionales puede tener cada organismo
- Determinar qué eventos relacionales puede experimentar

**NO es responsable de:**
- ❌ Crear relaciones entre agentes (eso lo hacen `MarriageSystem`, `ExperienceGenerator`)
- ❌ Decidir el movimiento físico (eso lo hace `MovementSystem`, documento 07)
- ❌ Generar emociones o traumas (eso lo hace `CognitiveMemorySystem`, documento 08)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`, documento 09)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`, documento 10)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **SocialCapabilities** | Nivel de complejidad social | Etología |
| **ResidentialNucleus** | Hogar / unidad familiar | Convivencia |
| **SocialPressure** | Influencia social sobre decisiones | Presión de grupo |
| **PressureMap** | Zonas sociales cargadas | Ambiente social |
| **NucleusType.SINGLE** | Persona sola | Hogar unipersonal |
| **NucleusType.COUPLE** | Pareja sin hijos | Pareja |
| **NucleusType.FAMILY** | Familia nuclear | Familia |
| **NucleusType.SINGLE_PARENT** | Familia monoparental | Monoparentalidad |
| **ProbabilisticSelection** | Decisión bajo incertidumbre | Elección ponderada |
| **Target distance** | Distancia ideal entre convivientes | Proxémica |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/social/social_capabilities.py` | `SocialCapabilities` | Capacidades sociales derivadas |
| `systems/social/social_pressure.py` | `SocialPressureCalculator` | Presión individual + ambiental |
| `systems/social/residential_nucleus.py` | `ResidentialNucleus` | Estructura de convivencia |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              FASE 0: DERIVACIÓN DE CAPACIDADES                  │
│                                                                 │
│ SocialCapabilities.from_genome(genome):                         │
│  ├── Consultar: sociability, intelligence, nervous_system,     │
│  │             aggressiveness                                   │
│  ├── Determinar:                                               │
│  │   ├── has_social_awareness (nervous_system ≥ 0.2)            │
│  │   ├── can_recognize_individuals (int ≥ 0.3)                  │
│  │   ├── can_form_pair_bond (soc ≥ 0.7 AND int ≥ 0.5)           │
│  │   ├── can_form_family_bonds (soc ≥ 0.8 AND int ≥ 0.6)        │
│  │   ├── can_have_marriage (int ≥ 0.8)                          │
│  │   ├── can_have_romantic_bonds (int ≥ 0.7)                    │
│  │   └── can_have_social_pressure (soc ≥ 0.7)                   │
│  └── social_complexity = soc * 0.6 + int * 0.4                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 1: PRESIÓN INDIVIDUAL (movimiento)            │
│                                                                 │
│ SocialPressureCalculator.calculate_pressure_for_cell:           │
│  ├── Si NOT can_have_social_pressure → return 0.0               │
│  │                                                               │
│  ├── 1. Presión por relaciones (_relationship_pressure):        │
│  │   └── Para cada relación del agente:                         │
│  │       ├── Si partner dentro de RADIUS_PRESENCE (5):          │
│  │       │   ├── Obtener etiquetas de relación                  │
│  │       │   ├── Determinar presión base según etiqueta         │
│  │       │   │   ├── "Amante" → +10                             │
│  │       │   │   ├── "Amigo" / "Aliado" → +2                    │
│  │       │   │   ├── "Rival" → -8                               │
│  │       │   │   └── Niños por edad: 0-5=+20, 5-12=+12, etc.    │
│  │       │   └── × distance_factor (1 - dist/5)                 │
│  │       └── Sumar al total                                     │
│  │                                                               │
│  ├── 2. Presión por núcleo (_nucleus_pressure):                 │
│  │   ├── Si distancia a centro ≤ target_distance → +3           │
│  │   └── Si excede → -min(excess*1.5, 5)                        │
│  │                                                               │
│  └── 3. Presión por enfermedad (_disease_pressure):             │
│      └── Si is_sick → -3.0 (aislamiento)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         FASE 2: PRESIÓN AMBIENTAL (mapa del entorno)            │
│                                                                 │
│ SocialPressureCalculator.apply_environmental_pressure:          │
│  ├── Si no hay eventos sociales en pending → return             │
│  │                                                               │
│  ├── Para cada adopción:                                        │
│  │   └── +0.3 presión en radio 15 alrededor de los padres       │
│  │                                                               │
│  ├── Para cada matrimonio:                                      │
│  │   └── +0.2 presión en radio 15 alrededor de los cónyuges     │
│  │                                                               │
│  ├── Para cada muerte:                                          │
│  │   └── +0.4 presión en radio 15 (trauma comunitario)          │
│  │                                                               │
│  ├── Para cada migración:                                       │
│  │   └── -0.2 presión (alivio por emigración)                   │
│  │                                                               │
│  └── Para cada divorcio:                                        │
│      └── -0.1 presión (alivio por separación)                   │
│                                                                 │
│  Decay con distancia: decay = 1 - (dist / 15)                   │
│  Clamp mínimo: MIN_PRESSURE = 0.5                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         FASE 3: EVENTOS DE NÚCLEO RESIDENCIAL                   │
│                                                                 │
│ ResidentialNucleus:                                              │
│  ├── on_marriage(a, b) → añadir como PARTNER                    │
│  ├── on_birth(child) → añadir como CHILD                        │
│  ├── on_death(agent) → eliminar miembro                         │
│  ├── on_child_independence(child) → crear nuevo SINGLE          │
│  └── _update_type() → SINGLE/COUPLE/FAMILY/SINGLE_PARENT        │
│                                                                 │
│ Cálculos espaciales:                                             │
│  ├── update_center(positions) → promedio de posiciones          │
│  └── get_distance_to_center(x, y) → distancia al centro         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. SocialCapabilities - Capacidades Sociales

**📁 Archivo**: `systems/social/social_capabilities.py`
**🌍 Equivalencia real**: El nivel etológico de la especie: qué complejidad social puede alcanzar.

#### Niveles de complejidad social

| Nivel | Descripción | Ejemplos |
|-------|-------------|----------|
| **Nivel 0** | Sin interacciones sociales | Plantas, bacterias |
| **Nivel 1** | Proximidad básica | Peces, reptiles |
| **Nivel 2** | Vínculos grupales simples | Lobos, aves sociales |
| **Nivel 3** | Vínculos complejos | Primates, delfines |
| **Nivel 4** | Conceptos sociales abstractos | Humanos |

#### Atributos

| Atributo | Tipo | Descripción | Condición |
|----------|------|-------------|-----------|
| `has_social_awareness` | `bool` | Reconoce otros individuos | `nervous_system ≥ 0.2 AND sociability ≥ 0.2` |
| `can_recognize_individuals` | `bool` | Distingue individuos | `nervous_system ≥ 0.4 AND intelligence ≥ 0.3` |
| `can_form_relationships` | `bool` | Forma vínculos | awareness + recognition |
| `can_form_cooperation` | `bool` | Puede cooperar | `sociability ≥ 0.4 AND intelligence ≥ 0.2` |
| `can_form_conflict` | `bool` | Puede tener conflictos | recognition + `aggressiveness ≥ 0.3` |
| `can_form_pair_bond` | `bool` | Forma parejas estables | `sociability ≥ 0.7 AND intelligence ≥ 0.5` |
| `can_form_family_bonds` | `bool` | Vínculos familiares | `sociability ≥ 0.8 AND intelligence ≥ 0.6` |
| `can_form_group_identity` | `bool` | Identidad grupal | `sociability ≥ 0.6 AND cooperación` |
| `can_have_friendship` | `bool` | Amistades | `sociability ≥ 0.7 AND intelligence ≥ 0.7` |
| `can_have_romantic_bonds` | `bool` | Vínculos románticos | `intelligence ≥ 0.7 AND sociability ≥ 0.7` |
| `can_have_marriage` | `bool` | Concepto de matrimonio | `intelligence ≥ 0.8 AND romantic_bonds` |
| `can_have_divorce` | `bool` | Concepto de divorcio | `= can_have_marriage` |
| `can_have_social_reputation` | `bool` | Reputación social | `intelligence ≥ 0.6 AND sociability ≥ 0.5` |
| `can_have_social_pressure` | `bool` | Siente presión social | `intelligence ≥ 0.6 AND group_identity` |
| `social_complexity` | `float` | Nivel continuo [0, 1] | Fórmula combinada |

#### Fórmula de social_complexity

```python
social_complexity = max(0.0, min(1.0,
    (sociability * 0.6 + intelligence * 0.4) * 
    (nervous_system if nervous_system > 0.1 else 0.0)
))
```

**Interpretación**: 
- Sociabilidad pesa más (0.6) que inteligencia (0.4)
- Sin sistema nervioso funcional (≤ 0.1), complejidad = 0

#### Métodos de consulta

| Método | Parámetro | Descripción |
|--------|-----------|-------------|
| `can_have_label(label)` | `"Amante"`, `"Amigo"`, `"Rival"`, etc. | ¿Puede tener esta etiqueta? |
| `can_participate_in_event(event_type)` | `"care"`, `"cooperation"`, etc. | ¿Puede participar en este evento? |
| `can_form_nucleus_type(type)` | `"single"`, `"couple"`, `"family"`, etc. | ¿Puede formar este tipo de núcleo? |

#### Tabla de etiquetas y capacidades

| Etiqueta | Capacidad requerida |
|----------|---------------------|
| "Desconocido" | Siempre `True` |
| "Conocido" | `can_recognize_individuals` |
| "Aliado" | `can_form_cooperation` |
| "Amigo" | `can_have_friendship` |
| "Familia Elegida" | `can_form_family_bonds` |
| "Interés Romántico" | `can_have_romantic_bonds` |
| "Amante" | `can_have_romantic_bonds` |
| "Rival" | `can_form_conflict` |
| "Rival Respetado" | `can_form_conflict AND can_form_cooperation` |
| "Enemigo" | `can_form_conflict` |

#### Tabla de eventos y capacidades

| Evento | Capacidad requerida |
|--------|---------------------|
| `met` | `has_social_awareness` |
| `care` | `can_form_cooperation` |
| `cooperation` | `can_form_cooperation` |
| `share_resource` | `can_form_cooperation` |
| `intimacy` | `can_have_romantic_bonds` |
| `reconciliation` | `can_form_cooperation AND can_form_conflict` |
| `competition` | `can_form_conflict` |
| `betrayal` | `can_have_social_reputation` |
| `conflict` | `can_form_conflict` |
| `neglect` | `has_social_awareness` |
| `birth` | `can_form_family_bonds` |
| `child_death` | `can_form_family_bonds` |
| `partner_death` | `can_form_pair_bond` |
| `cohabitation_start` | `can_have_marriage` |
| `cohabitation_end` | `can_have_divorce` |

#### Tabla de núcleos y capacidades

| Tipo de núcleo | Capacidad requerida |
|----------------|---------------------|
| `single` | Siempre `True` |
| `couple` | `can_form_pair_bond` |
| `family` | `can_form_family_bonds` |
| `single_parent` | `can_form_family_bonds` |
| `dependent_care` | `can_form_family_bonds` |

#### Ejemplos

```python
# Humano: complejidad social máxima
human_caps = SocialCapabilities.from_genome(human_genome)
human_caps.social_complexity         # ~0.9
human_caps.can_have_marriage         # True
human_caps.can_have_romantic_bonds   # True
human_caps.can_have_social_pressure  # True
human_caps.can_have_label("Amante")  # True

# Lobo: nivel 2-3 (vínculos grupales complejos)
wolf_caps = SocialCapabilities.from_genome(wolf_genome)
wolf_caps.can_form_pair_bond         # True
wolf_caps.can_form_group_identity    # True (manada)
wolf_caps.can_have_marriage          # False (no concepto abstracto)
wolf_caps.can_have_social_pressure   # True

# Planta: nivel 0 (sin vida social)
plant_caps = SocialCapabilities.from_genome(plant_genome)
plant_caps.social_complexity         # 0.0
plant_caps.has_social_awareness      # False
plant_caps.can_form_relationships    # False

# Pez: nivel 1 (proximidad básica)
fish_caps = SocialCapabilities.from_genome(fish_genome)
fish_caps.has_social_awareness       # True (percibe otros)
fish_caps.can_recognize_individuals  # False (no distingue individuos)
fish_caps.can_form_pair_bond         # False
```

---

### 2. SocialPressureCalculator - Presión Social

**📁 Archivo**: `systems/social/social_pressure.py`
**🌍 Equivalencia real**: La influencia social que sientes de tus seres queridos + el ambiente social del barrio.

#### Constantes de presión individual

| Relación | Valor | Descripción |
|----------|-------|-------------|
| `partner` (Amante) | +10.0 | Máxima atracción |
| `child_0_5` | +20.0 | Dependencia extrema |
| `child_5_12` | +12.0 | Dependencia media |
| `child_13_17` | +6.0 | Dependencia baja |
| `sibling` | +3.0 | Vínculo fraternal |
| `friend` / `ally` | +2.0 | Amistad |
| `acquaintance` | 0.0 | Neutro |
| `conflict` (Rival) | -8.0 | Repulsión |
| `disease_isolation` | -10.0 | Aislamiento por enfermedad |

#### Radios de influencia

| Radio | Valor | Descripción |
|-------|-------|-------------|
| `RADIUS_PRESENCE` | 5.0 | Distancia máxima para considerar presencia |
| `RADIUS_INTERACTION` | 2.0 | Distancia de interacción directa |
| `RADIUS_RELATIONSHIP` | 1.0 | Distancia íntima |

#### Constantes de presión ambiental

| Evento | Valor | Descripción |
|--------|-------|-------------|
| `adoption` | +0.3 | Celebración comunitaria |
| `marriage` | +0.2 | Celebración |
| `death` | +0.4 | Trauma comunitario |
| `migration` | -0.2 | Alivio (menos gente) |
| `divorce` | -0.1 | Ligero alivio |

#### Constantes globales

```python
SOCIAL_INFLUENCE_RADIUS = 15.0  # Radio de influencia ambiental
MIN_PRESSURE = 0.5              # Presión mínima del mapa
```

#### Umbral de edades (en días)

| Edad | Días | Equivalencia |
|------|------|--------------|
| `AGE_CHILD_0_5` | 1825 | 5 años |
| `AGE_CHILD_5_12` | 4380 | 12 años |
| `AGE_CHILD_13_17` | 6205 | 17 años |
| `AGE_ADULT` | 6570 | 18 años |

#### Método principal de presión individual

```python
def calculate_pressure_for_cell(person, cell_x, cell_y, state) -> float:
    social_caps = SocialCapabilities.from_genome(person.genome)
    if not social_caps.can_have_social_pressure:
        return 0.0
    
    total = 0.0
    total += self._relationship_pressure(person, cell_x, cell_y, state)
    total += self._nucleus_pressure(person, cell_x, cell_y, state)
    total += self._disease_pressure(person)
    return total
```

#### Presión por relaciones

```python
def _relationship_pressure(person, cell_x, cell_y, state) -> float:
    pressure = 0.0
    
    for partner_id, rel in person._relationships.items():
        partner = state.get_person_by_id(partner_id)
        dist_to_partner = sqrt((cell_x - partner.x)² + (cell_y - partner.y)²)
        
        if dist_to_partner > RADIUS_PRESENCE:  # 5 tiles
            continue
        
        base_pressure = self._get_pressure_from_labels(rel, partner, state)
        distance_factor = max(0.0, 1.0 - (dist_to_partner / RADIUS_PRESENCE))
        
        pressure += base_pressure * distance_factor
    
    return pressure
```

#### Determinación de presión por etiquetas

```python
def _get_pressure_from_labels(rel, partner, state) -> float:
    labels = rel.get_labels(state.world_days_elapsed)
    
    if "Amante" in labels:
        return PRESSURE_VALUES["partner"]  # +10
    
    if "Amigo" in labels or "Aliado" in labels:
        return PRESSURE_VALUES["friend"]   # +2
    
    if "Rival" in labels or "Rival Respetado" in labels:
        return PRESSURE_VALUES["conflict"] # -8
    
    if partner.age < AGE_ADULT:
        return self._child_pressure_by_age(partner.age)
    
    return PRESSURE_VALUES["acquaintance"] # 0
```

#### Presión por edad del hijo

```python
def _child_pressure_by_age(child_age_days) -> float:
    if child_age_days < 1825:      # 0-5 años
        return 20.0                 # Máxima dependencia
    if child_age_days < 4380:      # 5-12 años
        return 12.0
    if child_age_days < 6205:      # 13-17 años
        return 6.0
    return 0.0                      # Adulto: sin dependencia
```

#### Presión por núcleo residencial

```python
def _nucleus_pressure(person, cell_x, cell_y, state) -> float:
    nucleus_id = getattr(person, "nucleus_id", None)
    if nucleus_id is None:
        return 0.0
    
    nucleus = state.get_nucleus(nucleus_id)
    dist_to_center = nucleus.get_distance_to_center(cell_x, cell_y)
    target_dist = nucleus.target_distance
    
    if dist_to_center <= target_dist:
        return 3.0  # Dentro del núcleo: atracción
    
    excess = dist_to_center - target_dist
    penalty = min(excess * 1.5, 5.0)
    return -penalty  # Fuera del núcleo: repulsión
```

#### Presión por enfermedad (aislamiento)

```python
def _disease_pressure(person) -> float:
    if getattr(person, "is_sick", False):
        return PRESSURE_VALUES["disease_isolation"] * 0.3  # -3.0
    return 0.0
```

#### Presión ambiental (modifica el mapa)

```python
def apply_environmental_pressure(state, pending, context, delta_days):
    if not self._has_social_events(pending):
        return
    
    # Adopciones: +0.3 en radio 15
    for adoption in pending.adoptions:
        parent = state.get_person_by_id(adoption['parent_a'])
        if parent:
            self._apply_pressure_to_area(context, parent.x, parent.y,
                                         0.3, delta_days)
    
    # Matrimonios: +0.2 en radio 15
    for person_a_id in pending.marriages:
        person_a = state.get_person_by_id(person_a_id)
        if person_a:
            self._apply_pressure_to_area(context, person_a.x, person_a.y,
                                         0.2, delta_days)
    
    # Muertes: +0.4 en radio 15 (trauma comunitario)
    for death_id in pending.deaths:
        deceased = state.get_person_by_id(death_id)
        if deceased:
            self._apply_pressure_to_area(context, deceased.x, deceased.y,
                                         0.4, delta_days)
    
    # Migraciones: -0.2 en radio 15 (alivio)
    for entity_id in pending.migration_targets:
        person = state.get_person_by_id(entity_id)
        if person:
            self._apply_pressure_to_area(context, person.x, person.y,
                                         -0.2, delta_days)
    
    # Divorcios: -0.1 en radio 15 (alivio menor)
    for person_a_id, person_b_id in pending.divorces:
        person_a = state.get_person_by_id(person_a_id)
        if person_a:
            self._apply_pressure_to_area(context, person_a.x, person_a.y,
                                         -0.1, delta_days)
```

#### Aplicación de presión a área

```python
def _apply_pressure_to_area(context, x, y, intensity, delta_days):
    radius = int(SOCIAL_INFLUENCE_RADIUS)  # 15
    
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            dist = sqrt(dx² + dy²)
            
            if dist <= SOCIAL_INFLUENCE_RADIUS:
                decay_factor = 1.0 - (dist / SOCIAL_INFLUENCE_RADIUS)
                pressure_delta = intensity * decay_factor * delta_days
                
                coord = (int(x) + dx, int(y) + dy)
                current_pressure = context.pressure_map.get(coord, 1.0)
                new_pressure = max(MIN_PRESSURE, current_pressure + pressure_delta)
                context.pressure_map[coord] = new_pressure
```

**Interpretación**:
- El efecto decae linealmente con la distancia
- Nunca baja de `MIN_PRESSURE` (0.5)
- Se multiplica por `delta_days` para normalizar en el tiempo

#### Selección probabilística (usada por MovementSystem)

```python
@staticmethod
def probabilistic_selection(scored_cells, temperature=2.0):
    if not scored_cells:
        return None
    
    scores = [score for _, score in scored_cells]
    min_score = min(scores)
    shifted_scores = [s - min_score + 1.0 for s in scores]  # Shift para evitar negativos
    
    weights = []
    for s in shifted_scores:
        weight = math.exp(s / temperature)  # Softmax con temperatura
        weights.append(weight)
    
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]
    
    cells = [cell for cell, _ in scored_cells]
    selected = random.choices(cells, weights=probabilities, k=1)[0]
    
    return selected
```

**Interpretación**:
- Temperatura baja (0.5): comportamiento determinista
- Temperatura alta (5.0): comportamiento aleatorio
- Shift +1.0 para evitar problemas con scores negativos
- Softmax clásico para convertir scores en probabilidades

---

### 3. ResidentialNucleus - Núcleo Residencial

**📁 Archivo**: `systems/social/residential_nucleus.py`
**🌍 Equivalencia real**: El hogar: unidad de convivencia que genera preferencias de proximidad.

#### Tipos de núcleo (enum `NucleusType`)

| Tipo | Valor | Descripción |
|------|-------|-------------|
| `SINGLE` | "single" | Persona sola |
| `COUPLE` | "couple" | Pareja sin hijos |
| `FAMILY` | "family" | Pareja con hijos |
| `SINGLE_PARENT` | "single_parent" | Monoparental |
| `DEPENDENT_CARE` | "dependent_care" | Con dependientes |

#### Roles dentro del núcleo (enum `NucleusMemberRole`)

| Rol | Valor | Descripción |
|-----|-------|-------------|
| `HEAD` | "head" | Cabeza del núcleo |
| `PARTNER` | "partner" | Pareja del cabeza |
| `CHILD` | "child" | Hijo/a |
| `DEPENDENT` | "dependent" | Dependiente (anciano, enfermo) |
| `OTHER` | "other" | Otro |

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `nucleus_id` | `int` | ID único auto-generado |
| `nucleus_type` | `NucleusType` | Tipo actual |
| `members` | `Dict[int, NucleusMemberRole]` | Miembros y sus roles |
| `center` | `Tuple[float, float]` | Centro geométrico |
| `target_distance` | `float` | Distancia ideal entre miembros |

#### Target distance por tipo

| Tipo | Distancia | Equivalencia |
|------|-----------|--------------|
| `SINGLE` | 0.0 | Solo |
| `COUPLE` | 1.5 | Pareja cercana |
| `FAMILY` | 2.0 | Familia extendida |
| `SINGLE_PARENT` | 2.0 | Familia monoparental |

#### Factories (creación)

```python
# Persona sola
nucleus = ResidentialNucleus.create_single(agent_id)

# Pareja
nucleus = ResidentialNucleus.create_couple(agent_a_id, agent_b_id)

# Familia completa
nucleus = ResidentialNucleus.create_family(
    parent_a_id=101,
    parent_b_id=102,
    children_ids=[201, 202, 203]
)
```

#### Gestión de miembros

| Método | Descripción |
|--------|-------------|
| `add_member(agent_id, role)` | Añade miembro con rol |
| `remove_member(agent_id)` | Elimina miembro |
| `get_members()` | Lista de IDs de miembros |
| `get_member_role(agent_id)` | Rol de un miembro |
| `has_member(agent_id)` | ¿Pertenece al núcleo? |
| `size` (propiedad) | Número de miembros |
| `is_empty` (propiedad) | ¿Sin miembros? |

#### Eventos de ciclo de vida

##### `on_marriage(agent_a_id, agent_b_id)`

```python
def on_marriage(self, agent_a_id, agent_b_id):
    # Si uno ya está en el núcleo, añadir al otro como PARTNER
    if self.has_member(agent_a_id):
        self.add_member(agent_b_id, NucleusMemberRole.PARTNER)
    elif self.has_member(agent_b_id):
        self.add_member(agent_a_id, NucleusMemberRole.PARTNER)
    else:
        # Ninguno estaba: crear desde cero
        self.add_member(agent_a_id, NucleusMemberRole.HEAD)
        self.add_member(agent_b_id, NucleusMemberRole.PARTNER)
```

##### `on_birth(child_id)`

```python
def on_birth(self, child_id):
    self.add_member(child_id, NucleusMemberRole.CHILD)
    # _update_type() se llama automáticamente
```

##### `on_death(agent_id)`

```python
def on_death(self, agent_id):
    role = self.get_member_role(agent_id)
    self.remove_member(agent_id)
    # _update_type() se llama automáticamente
```

##### `on_child_independence(child_id)`

```python
def on_child_independence(self, child_id) -> Optional[ResidentialNucleus]:
    role = self.get_member_role(child_id)
    if role != NucleusMemberRole.CHILD:
        return None
    
    self.remove_member(child_id)
    new_nucleus = ResidentialNucleus.create_single(child_id)
    return new_nucleus
```

#### Actualización automática del tipo

```python
def _update_type(self):
    if self.is_empty:
        return
    
    roles = list(self.members.values())
    has_partner = NucleusMemberRole.PARTNER in roles
    has_children = NucleusMemberRole.CHILD in roles
    
    if self.size == 1:
        self.nucleus_type = NucleusType.SINGLE
        self.target_distance = 0.0
    elif has_partner and not has_children:
        self.nucleus_type = NucleusType.COUPLE
        self.target_distance = 1.5
    elif has_partner and has_children:
        self.nucleus_type = NucleusType.FAMILY
        self.target_distance = 2.0
    elif not has_partner and has_children:
        self.nucleus_type = NucleusType.SINGLE_PARENT
        self.target_distance = 2.0
    else:
        self.nucleus_type = NucleusType.SINGLE
        self.target_distance = 1.0
```

#### Cálculos espaciales

```python
def update_center(self, positions):
    """Actualiza centro basado en posiciones actuales."""
    member_positions = []
    for agent_id in self.members:
        if agent_id in positions:
            member_positions.append(positions[agent_id])
    
    if member_positions:
        avg_x = sum(p[0] for p in member_positions) / len(member_positions)
        avg_y = sum(p[1] for p in member_positions) / len(member_positions)
        self.center = (avg_x, avg_y)

def get_distance_to_center(self, x, y):
    """Distancia desde un punto al centro del núcleo."""
    dx = x - self.center[0]
    dy = y - self.center[1]
    return math.sqrt(dx*dx + dy*dy)
```

#### Serialización (para Godot / guardado)

```python
def to_dict(self):
    return {
        "nucleus_id": self.nucleus_id,
        "type": self.nucleus_type.value,
        "members": {str(k): v.value for k, v in self.members.items()},
        "center": list(self.center),
        "size": self.size,
        "target_distance": self.target_distance,
    }
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                     │
│   sociability, intelligence, nervous_system, aggressiveness    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           SocialCapabilities (inmutable, derivada)              │
│   - Nivel 0-4 de complejidad social                            │
│   - can_have_marriage, can_have_romantic_bonds, etc.           │
│   - can_have_social_pressure                                   │
│   - can_form_nucleus_type(type)                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ Social       │  │ Experience   │  │ MarriageSystem       │
│ PressureCalc │  │ Generator    │  │ (doc 06)             │
│              │  │ (doc 06)     │  │                      │
│ Filtra por:  │  │ Filtra por:  │  │ Filtra por:          │
│ can_have_    │  │ can_partici- │  │ can_have_romantic_   │
│ social_      │  │ pate_in_     │  │ bonds, can_have_     │
│ pressure     │  │ event        │  │ marriage             │
└──────┬───────┘  └──────────────┘  └────────────┬─────────┘
       │                                         │
       │                                         │ crea
       │                                         ▼
       │                              ┌──────────────────────┐
       │                              │ ResidentialNucleus   │
       │                              │                      │
       │                              │ - create_couple()    │
       │                              │ - create_family()    │
       │                              │ - on_marriage()      │
       │                              │ - on_birth()         │
       │                              │ - on_death()         │
       └──────────────────────────────┤ - on_independence()  │
                                      └──────────┬───────────┘
                                                 │
                                                 │ genera
                                                 ▼
                                      Presión individual
                                      (usada por MovementSystem)
```

---

## ⚙️ Configuración relevante

```python
# El sistema no tiene configuración propia significativa.
# Usa valores hardcodeados y constantes derivadas del genoma.

# Valores importantes (constantes en social_pressure.py):
PRESSURE_VALUES = {
    "partner": 10.0,
    "child_0_5": 20.0,
    "child_5_12": 12.0,
    "child_13_17": 6.0,
    "sibling": 3.0,
    "friend": 2.0,
    "acquaintance": 0.0,
    "conflict": -8.0,
    "disease_isolation": -10.0,
}

ENVIRONMENTAL_PRESSURE = {
    "adoption": 0.3,
    "marriage": 0.2,
    "death": 0.4,
    "migration": -0.2,
    "divorce": -0.1,
}

RADIUS_PRESENCE = 5.0
SOCIAL_INFLUENCE_RADIUS = 15.0
MIN_PRESSURE = 0.5
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_social_capabilities.py` | Derivación desde genoma |
| `tests/unit/test_social_pressure.py` | Cálculo de presión individual |
| `tests/unit/test_residential_nucleus.py` | Gestión de miembros, tipos |
| `tests/integration/test_tile_integration.py` | Presión en movimiento |

---

## 📝 Ejemplos completos

### Ejemplo 1: Presión individual de un padre con hijos

```python
# Padre con 3 hijos de diferentes edades
parent._relationships = {
    101: rel_5_years,    # 5 años (1825 días)
    102: rel_8_years,    # 8 años (2920 días)
    103: rel_15_years,   # 15 años (5475 días)
}

# Evaluando casilla a 2 tiles del hijo de 5 años, 4 del de 8, 10 del de 15:
# child_5_years: dist=2 < 5, age=1825 < 4380 → base=12.0
#   factor = 1 - 2/5 = 0.6 → presión = 12.0 * 0.6 = 7.2
#
# child_8_years: dist=4 < 5, age=2920 < 4380 → base=12.0
#   factor = 1 - 4/5 = 0.2 → presión = 12.0 * 0.2 = 2.4
#
# child_15_years: dist=10 > 5 → fuera de radio, ignorado
#
# Presión total por hijos = 7.2 + 2.4 = 9.6 (fuerte atracción)
```

### Ejemplo 2: Presión ambiental tras una muerte

```python
# Muere un agente en (50, 50)
pending.deaths = {101: "reason"}

# apply_environmental_pressure:
# death event → intensity = +0.4, radius = 15

# Para cada celda (50+dx, 50+dy) con dist ≤ 15:
#   decay = 1 - (dist/15)
#   delta = 0.4 * decay * delta_days
#   pressure_map[(x,y)] += delta

# Ejemplo para celda (52, 50) - dist = 2:
# decay = 1 - 2/15 = 0.867
# delta = 0.4 * 0.867 * 1.0 = 0.347
# pressure_map[(52, 50)] += 0.347

# Ejemplo para celda (60, 50) - dist = 10:
# decay = 1 - 10/15 = 0.333
# delta = 0.4 * 0.333 * 1.0 = 0.133
# pressure_map[(60, 50)] += 0.133

# Ejemplo para celda (70, 50) - dist = 20 > 15:
# No se aplica (fuera de radio)
```

### Ejemplo 3: Selección probabilística de celda

```python
# Celdas con diferentes puntuaciones
scored_cells = [
    ((50, 50), 10.0),  # Casilla actual (inercia)
    ((51, 50), 8.0),   # Buena opción
    ((52, 50), 3.0),   # Regular
    ((53, 50), -5.0),  # Mala opción
]

# Con temperatura = 2.0 (moderada)
selected = SocialPressureCalculator.probabilistic_selection(scored_cells, temperature=2.0)

# Cálculo interno:
# min_score = -5.0
# shifted: [15.0, 13.0, 8.0, 0.0]
# weights: [exp(7.5), exp(6.5), exp(4.0), exp(0)]
#        ≈ [1808, 665, 55, 1]
# total ≈ 2529
# probabilidades ≈ [71.5%, 26.3%, 2.2%, 0.04%]
# → Muy probable elegir (50,50) o (51,50)

# Con temperatura = 0.5 (baja, determinista)
# → Casi siempre elige la de mayor score: (50,50)

# Con temperatura = 10.0 (alta, aleatoria)
# → Distribución casi uniforme
```

### Ejemplo 4: Evolución de un núcleo residencial

```python
# 1. Crear persona sola
nucleus = ResidentialNucleus.create_single(agent_a_id=101)
# type=SINGLE, members={101: HEAD}

# 2. Se casa
nucleus.on_marriage(101, 102)
# type=COUPLE, members={101: HEAD, 102: PARTNER}

# 3. Nace primer hijo
nucleus.on_birth(201)
# type=FAMILY, members={101: HEAD, 102: PARTNER, 201: CHILD}

# 4. Nace segundo hijo
nucleus.on_birth(202)
# type=FAMILY, members={..., 202: CHILD}

# 5. El hijo mayor (201) se independiza
new_nucleus = nucleus.on_child_independence(201)
# nucleus original: {101: HEAD, 102: PARTNER, 202: CHILD} → FAMILY
# new_nucleus: {201: HEAD} → SINGLE

# 6. Muere el padre (101)
nucleus.on_death(101)
# type=SINGLE_PARENT, members={102: HEAD, 202: CHILD}
# (update_type detecta: sin PARTNER pero con CHILD)
```

### Ejemplo 5: Capacidades por organismo

```python
# Humano: nivel 4 (máximo)
human_caps = SocialCapabilities.from_genome(human_genome)
# can_have_marriage: True
# can_have_romantic_bonds: True
# can_have_social_pressure: True
# can_form_nucleus_type("family"): True

# MarriageSystem valida antes de crear pareja:
if human_caps.can_have_romantic_bonds:
    # Puede formar pareja
    nucleus = ResidentialNucleus.create_couple(human_a, human_b)

# Lobo: nivel 2-3 (sin matrimonio abstracto)
wolf_caps = SocialCapabilities.from_genome(wolf_genome)
# can_form_pair_bond: True (forma parejas)
# can_have_marriage: False (no concepto abstracto)
# can_form_nucleus_type("couple"): True
# can_form_nucleus_type("family"): False

# Planta: nivel 0 (sin vida social)
plant_caps = SocialCapabilities.from_genome(plant_genome)
# social_complexity: 0.0
# has_social_awareness: False
# can_form_relationships: False
# SocialPressureCalculator.calculate_pressure_for_cell → 0.0
# No tiene núcleo residencial
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Capacidades derivadas**: genoma → capacidades sociales → qué puede formar
- **Dos tipos de presión**: individual (movimiento) vs ambiental (mapa)
- **Núcleos emergentes**: se crean desde eventos (matrimonio, nacimiento)
- **Actualización automática**: el tipo se recalcula al cambiar miembros
- **Inercia por proximidad**: cerca del núcleo = atracción; lejos = repulsión

### Arquitectura

```
GENOMA
   ↓
SocialCapabilities (qué puede hacer)
   ↓
├── SocialPressureCalculator (presión individual + ambiental)
│     ↓
│     └── MovementSystem (usa presión para decidir movimiento)
│
└── ResidentialNucleus (estructura de convivencia)
      ↓
      └── WorldState (almacena núcleos, provee consulta)
```

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| Caché de capacidades | Todos | Evita recalcular cada tick |
| Early return si sin eventos | SocialPressureCalculator | No procesar vacío |
| Radio limitado (15 tiles) | SocialPressureCalculator | Acota bucles |
| Decay lineal simple | SocialPressureCalculator | Cálculo O(1) por celda |
| IDs auto-generados | ResidentialNucleus | Sin gestión manual |

### Limitaciones
- No hay núcleos extendidos (abuelos, tíos)
- No hay cohabitación sin matrimonio
- No hay roommate / compañeros de piso
- La presión ambiental no decae con el tiempo (persiste)
- No hay "barrios" o "comunidades" como unidades sociales
- No hay presión social negativa por crimen

### Errores comunes
- ❌ Asumir que todos los organismos sienten presión social (filtrar por `can_have_social_pressure`)
- ❌ Crear núcleos familiares para organismos sin `can_form_family_bonds`
- ❌ Iterar sobre `pending.marriages` incorrectamente (es Dict, no List)
- ❌ Olvidar que `pending.deaths` es Dict `{id: reason}`, no List
- ❌ Modificar `pressure_map` directamente sin clamp a `MIN_PRESSURE`
- ❌ Usar `random.choices` con pesos que sumen 0 (manejo explícito incluido)

---

## 🎓 Conceptos clave

### ¿Por qué capacidades sociales derivadas?

**Principio de etología**:
- Las plantas no forman familias
- Los lobos forman manadas pero no se casan
- Los humanos tienen matrimonio, divorcio, reputación
- Cada nivel de complejidad permite ciertas estructuras
- El sistema respeta la biología de cada especie

### ¿Por qué dos tipos de presión?

**Principio de influencia multinivel**:
- **Individual**: "quiero estar cerca de mi pareja/hijos"
- **Ambiental**: "esta zona está cargada emocionalmente"
- La primera es personal, la segunda es comunitaria
- Ambas afectan el comportamiento pero de formas distintas

### ¿Por qué presión individual con radios?

**Principio de proxémica**:
- Las relaciones tienen distancia óptima
- Muy cerca = agobiante, muy lejos = abandonado
- El target_distance del núcleo representa esta distancia ideal
- El decay_factor simula la pérdida de influencia con la distancia

### ¿Por qué núcleos residenciales?

**Principio de unidad de convivencia**:
- Más que "familia", es "con quién vivo"
- Genera preferencias espaciales automáticas
- Se adapta dinámicamente (matrimonios, nacimientos, muertes)
- Los hijos se independizan creando nuevos núcleos

### ¿Por qué selección probabilística con temperatura?

**Principio de decisión bajo incertidumbre**:
- Los agentes no son perfectamente racionales
- Softmax con temperatura modela esto
- Baja temperatura = decisión determinista (siempre elige lo mejor)
- Alta temperatura = decisión aleatoria (exploración)
- Equilibrio entre explotación (lo conocido) y exploración (nuevo)

### ¿Por qué presión ambiental por eventos?

**Principio de memoria comunitaria**:
- Una muerte afecta a todo el barrio
- Un matrimonio es celebrado por la comunidad
- Una migración alivia la presión demográfica
- Estos eventos dejan "huella" en el mapa social

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 3 |
| Tipos de núcleo | 5 |
| Roles dentro del núcleo | 5 |
| Niveles de complejidad social | 5 (0-4) |
| Etiquetas relacionales soportadas | 10 |
| Eventos relacionales soportados | 15 |
| Tests cubriendo estructura social | ~15 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Núcleos extendidos (abuelos, tíos, primos)
- [ ] Cohabitación sin matrimonio (roommates)
- [ ] Decaimiento temporal de presión ambiental
- [ ] Barrios y comunidades como unidades

### Posibles
- [ ] Presión social negativa por crimen
- [ ] Gentrificación (cambio de presión por migración)
- [ ] Segregación social (agentes evitando zonas de diferente clase)
- [ ] Liderazgo comunitario (agentes con alta influencia)
- [ ] Reputación heredada (hijos de padres respetados)
- [ ] Redes sociales complejas (grafos de influencia)
- [ ] Tribus y clanes (identidades grupales mayores)
- [ ] Instituciones sociales (escuelas, templos)

---

*Documento: 11_ESTRUCTURA_SOCIAL.md*
*Versión: 1.0*