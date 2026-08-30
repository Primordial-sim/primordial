# 17 - Entidad Persona

## 📋 Resumen

La **Entidad Persona** (`Person`) es el corazón del simulador: representa a cada agente individual con toda su complejidad biológica, psicológica y social. Es la estructura de datos central que almacena el estado completo de un individuo: genoma, posición, edad, emociones, motivaciones, relaciones, memoria inmunológica, estado reproductivo y mucho más.

**Filosofía fundamental**: *Una Persona es un microcosmos del simulador. Contiene toda la información necesaria para que cualquier sistema pueda consultar su estado y tomar decisiones informadas sobre ella, desde la genética hasta las relaciones sociales, pasando por la salud y el comportamiento.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Almacenar el estado completo de un agente individual
- Gestionar sus atributos básicos (ID, posición, edad, género, especie)
- Contener su genoma y propiedades derivadas (sociabilidad efectiva, temperamento)
- Gestionar sus relaciones interpersonales (diccionario optimizado O(1))
- Almacenar su estado de salud e infecciones activas
- Mantener su memoria inmunológica (adquirida y por cepa)
- Gestionar su estado reproductivo (embarazo, hijos, fertilidad)
- Almacenar sus emociones y motivaciones continuas
- Mantener su memoria implícita (traumas, preferencias espaciales)
- Gestionar su estado civil y relaciones de pareja
- Almacenar su historial de adopciones y reputación
- Integrarse con el sistema de núcleos residenciales

**NO es responsable de:**
- ❌ Decidir qué acciones tomar (eso lo hacen `FreeWillSystem`, `MovementSystem`)
- ❌ Calcular su propio envejecimiento (eso lo hace `AgingSystem`)
- ❌ Procesar sus enfermedades (eso lo hace `DiseaseSystem`)
- ❌ Decidir si muere (eso lo hace `MortalitySystem`)
- ❌ Gestionar sus relaciones a alto nivel (eso lo hacen `MarriageSystem`, `RelationshipManager`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Person** | Un individuo completo | Ser vivo |
| **entity_id** | Identificación única | DNI / ADN |
| **x, y** | Posición geográfica | Coordenadas |
| **age** | Edad cronológica | Días |
| **gender** | Sexo biológico | M/F |
| **genome** | ADN completo | Genoma |
| **emotions** | Estado emocional | Psicología |
| **motivations** | Impulsos psicológicos | Deseos |
| **memory** | Recuerdos implícitos | Memoria no declarativa |
| **relationships** | Red social personal | Contactos |
| **active_infections** | Enfermedades activas | Patologías |
| **immune_memory** | Inmunidad adquirida | Anticuerpos |
| **is_pregnant** | Estado de gestación | Embarazo |
| **children_count** | Descendencia | Hijos |
| **partner_id** | Pareja actual | Cónyuge |
| **marital_status** | Estado civil | Registro civil |
| **reputation_score** | Reputación social | Imagen pública |
| **sexual_orientation** | Orientación sexual | Identidad |
| **nucleus_id** | Hogar actual | Residencia |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `entities/person/person.py` | `Person` | Entidad principal completa |
| `entities/person/genome.py` | `Genome` | Genoma del agente (ver doc 03) |
| `entities/person/allele.py` | `Allele`, `Gene` | Unidades genéticas (ver doc 03) |

---

## 🏗️ Estructura de la Entidad

### Constructor y atributos principales

```python
def __init__(
    self,
    config: SimulationConfig,
    entity_id: int,
    x: int,
    y: int,
    age: float = 0.0,
    genome: Optional[Genome] = None,
    gender: Optional[str] = None,
    species: str = "human",
) -> None:
```

#### Atributos de identidad y posición

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `entity_id` | `int` | Identificador único (atributo directo, optimizado) |
| `x`, `y` | `int` | Posición en el mapa (atributos directos, optimizados) |
| `_species` | `str` | Especie del agente ("human", "wolf", etc.) |
| `_age` | `float` | Edad en días |
| `_gender` | `str` | Género ("M" o "F", aleatorio si no se especifica) |
| `_genome` | `Genome` | Genoma completo del agente |

#### Atributos de salud y reproducción

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `_health_state` | `str` | Estado de salud ("sano", "enfermo") |
| `_is_adult` | `bool` | Si es adulto |
| `_is_senior` | `bool` | Si es anciano |
| `_active_infections` | `Dict[str, InfectionState]` | Infecciones activas |
| `_immune_memory` | `Dict[str, float]` | Inmunidad adquirida por familia |
| `_strain_immunity` | `Dict[str, float]` | Inmunidad por cepa específica |
| `_strain_metadata` | `Dict[str, dict]` | Metadatos de cepas conocidas |
| `_is_pregnant` | `bool` | Si está embarazada |
| `_pregnancy_days` | `float` | Días de embarazo |
| `_failed_pregnancies` | `int` | Embarazos fallidos |
| `_children_count` | `int` | Número total de hijos |
| `_biological_children_count` | `int` | Número de hijos biológicos |
| `_litter_size_gestating` | `int` | Tamaño de camada gestante |

#### Atributos familiares y sociales

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `_mother_id` | `Optional[int]` | ID de la madre biológica |
| `_father_id` | `Optional[int]` | ID del padre biológico |
| `_parents` | `List[int]` | Lista de padres biológicos |
| `_adoptive_parents` | `List[int]` | Lista de padres adoptivos |
| `_adoption_history` | `List[Dict]` | Historial de adopciones |
| `_reputation_score` | `float` | Reputación social [0.0, 1.0] |
| `_relationships` | `Dict[int, Relationship]` | Relaciones (optimizado O(1)) |
| `_partner_id` | `Optional[int]` | ID de pareja actual |
| `_marital_status` | `str` | Estado civil |
| `nucleus_id` | `Optional[int]` | Núcleo residencial actual |

#### Atributos psicológicos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `_memory` | `Dict[str, Any]` | Memoria implícita (traumas, preferencias) |
| `_emotions` | `Dict[str, float]` | Emociones actuales |
| `_motivations` | `Dict[str, float]` | Motivaciones continuas |
| `_sexual_orientation` | `SexualOrientation` | Orientación sexual |

---

## 📊 Estado Inicial por Defecto

### Memoria implícita

```python
self._memory = {
    "trauma_overcrowding": 0.0,
    "trauma_sickness": 0.0,
    "preferred_sector": None,
    "rebellion_cooldown": 0.0,
}
```

### Emociones

```python
self._emotions = {
    "stress": 0.0,
    "happiness": 0.8,
    "energy": 1.0,
}
```

### Motivaciones

```python
self._motivations = {
    "independence": 0.3,
    "exploration": 0.3,
    "rebellion": 0.2,
    "partnership": 0.5,
    "protection": 0.4,
    "migration": 0.2,
    "cooperation": 0.5,
    "fertility_desire": 0.5,
}
```

**Nota**: `fertility_desire` es una motivación adicional que no está en `FreeWillSystem`. Puede ser una extensión específica para reproducción.

---

## 🔍 Propiedades Principales

### Propiedades básicas (solo lectura)

| Propiedad | Retorno | Descripción |
|-----------|---------|-------------|
| `species` | `str` | Especie del agente |
| `age` | `float` | Edad en días |
| `gender` | `str` | Género |
| `health_state` | `str` | Estado de salud |
| `genome` | `Genome` | Genoma completo |
| `is_adult` | `bool` | Si es adulto |
| `is_senior` | `bool` | Si es anciano |
| `is_pregnant` | `bool` | Si está embarazada |
| `children_count` | `int` | Total de hijos |
| `biological_children_count` | `int` | Hijos biológicos |
| `parents` | `List[int]` | Padres biológicos |
| `adoptive_parents` | `List[int]` | Padres adoptivos |
| `mother_id` | `Optional[int]` | Madre biológica |
| `father_id` | `Optional[int]` | Padre biológico |
| `pregnancy_days` | `float` | Días de embarazo |
| `litter_size_gestating` | `int` | Tamaño de camada |
| `memory` | `Dict` | Memoria implícita |
| `emotions` | `Dict` | Emociones actuales |
| `motivations` | `Dict` | Motivaciones continuas |
| `sexual_orientation` | `SexualOrientation` | Orientación sexual |

### Propiedades de salud

| Propiedad | Retorno | Descripción |
|-----------|---------|-------------|
| `active_pathogens` | `Dict[str, Pathogen]` | Patógenos activos |
| `active_infections` | `Dict[str, InfectionState]` | Estados de infección |
| `is_sick` | `bool` | Si tiene alguna infección |
| `is_symptomatic` | `bool` | Si tiene síntomas visibles |
| `effective_sociability` | `float` | Sociabilidad ajustada por emociones |
| `effective_temperament` | `float` | Temperamento ajustado por traumas |

### Propiedades sociales

| Propiedad | Retorno | Descripción |
|-----------|---------|-------------|
| `relationships` | `List[Relationship]` | Lista de relaciones (compatibilidad) |
| `adoption_history` | `List[Dict]` | Historial de adopciones |
| `parental_status` | `str` | Estado parental |
| `reputation_score` | `float` | Reputación social |
| `adopted_children_count` | `int` | Hijos adoptivos |
| `partner_id` | `Optional[int]` | Pareja actual (calculada) |
| `marital_status` | `str` | Estado civil (calculado) |
| `relationship_days` | `float` | Duración de relación actual |
| `has_nucleus` | `bool` | Si pertenece a un núcleo |

### Propiedades calculadas

#### `effective_sociability`

```python
@property
def effective_sociability(self) -> float:
    base = self._genome.sociability
    stress_penalty = self._emotions["stress"] * 0.4
    happiness_bonus = (self._emotions["happiness"] - 0.5) * 0.2
    return max(0.1, min(2.0, base - stress_penalty + happiness_bonus))
```

**Interpretación**: La sociabilidad real se ve afectada por el estado emocional. El estrés reduce la sociabilidad, la felicidad la aumenta.

#### `effective_temperament`

```python
@property
def effective_temperament(self) -> float:
    base = self._genome.temperament
    trauma = min(1.0, self._memory.get("trauma_sickness", 0.0) 
                + self._memory.get("trauma_overcrowding", 0.0))
    return max(0.1, min(2.0, base - (trauma * 0.5)))
```

**Interpretación**: Los traumas reducen el temperamento efectivo (más inestable).

#### `partner_id` (calculado con prioridad)

```python
@property
def partner_id(self) -> Optional[int]:
    active = self._get_active_relationships()
    if not active: return self._partner_id
    priority = [CONSOLIDATED, COHABITATION, DATING, CASUAL, ROMANTIC_INTEREST]
    for status in priority:
        for rel in active:
            if rel.status == status: return rel.partner_id
    return active[0].partner_id if active else self._partner_id
```

**Interpretación**: Se elige la pareja según el estado de relación más consolidado.

#### `marital_status` (calculado dinámicamente)

```python
@property
def marital_status(self) -> str:
    active = self._get_active_relationships()
    if not active: return self._marital_status
    # Si hay relación consolidada/cohabitando/noviazgo → "casado"
    # Si hay ex-pareja → "divorciado"
    # Si no → "soltero"
```

#### `parental_status` (calculado)

```python
@property
def parental_status(self) -> str:
    adopted_count = self._children_count - self._biological_children_count
    if self._children_count == 0: return "sin_hijos"
    elif self._biological_children_count > 0 and adopted_count == 0: return "padre_biologico"
    elif self._biological_children_count == 0 and adopted_count > 0: return "padre_adoptivo"
    else: return "padre_mixto"
```

---

## 🔧 Métodos Principales

### Gestión de Relaciones (optimizada O(1))

| Método | Descripción |
|--------|-------------|
| `get_relationship_with(partner_id, current_day)` | Obtiene o crea relación (O(1) con dict) |
| `add_relationship(partner_id, status, ...)` | Añade relación con estado |
| `update_relationship_status(partner_id, new_status, ...)` | Actualiza estado de relación |
| `_get_active_relationships()` | Obtiene relaciones activas (cacheado) |
| `_invalidate_relationships_cache()` | Invalida caché de relaciones |

**Optimización clave**: `_relationships` es un `Dict[int, Relationship]` en lugar de una lista, permitiendo búsqueda O(1) por `partner_id`.

### Gestión de Salud e Inmunidad

| Método | Descripción |
|--------|-------------|
| `infect(pathogen)` | Infecta con un patógeno (reemplaza familia) |
| `recover(pathogen_id)` | Recupera de infección y genera inmunidad |
| `advance_infections(delta_days)` | Avanza fases de todas las infecciones |
| `decay_immunity(delta_days, decay_rate)` | Decae la inmunidad con el tiempo |
| `set_health_state(new_state)` | Establece estado de salud |
| `get_specific_immunity(pathogen)` | Calcula inmunidad total contra patógeno |
| `_calculate_related_strain_immunity(pathogen)` | Calcula inmunidad cruzada por cepa |

### Gestión de Motivaciones

| Método | Descripción |
|--------|-------------|
| `get_motivation(motivation_name)` | Obtiene valor de motivación |
| `update_motivation(motivation_name, amount)` | Actualiza motivación (delta) |
| `get_dominant_motivation()` | Obtiene motivación dominante |
| `decay_motivations(delta_days, decay_rate)` | Decae motivaciones con el tiempo |

### Gestión de Posición y Edad

| Método | Descripción |
|--------|-------------|
| `set_position(x, y)` | Establece posición |
| `add_age(increment_days)` | Incrementa edad y verifica hitos |
| `_check_milestones()` | Verifica hitos (adulto, senior) |

### Gestión Familiar

| Método | Descripción |
|--------|-------------|
| `set_parents(mother_id, father_id)` | Establece padres biológicos |
| `add_adoptive_parent(parent_id, current_day)` | Añade padre adoptivo |
| `add_child()` | Registra un hijo |
| `add_biological_child()` | Registra un hijo biológico |
| `register_marriage(partner_id, current_day)` | Registra matrimonio |
| `register_divorce(current_day)` | Registra divorcio |
| `update_pregnancy(status, days, litter_size)` | Actualiza embarazo |
| `add_failed_pregnancy()` | Registra embarazo fallido |

### Gestión de Emociones

| Método | Descripción |
|--------|-------------|
| `update_emotion(emotion, amount)` | Actualiza emoción (delta) |

### Gestión de Reputación y Adopciones

| Método | Descripción |
|--------|-------------|
| `register_adoption_event(event_type, entity_id, day, context)` | Registra evento de adopción |
| `get_adoption_history()` | Obtiene historial completo |
| `get_adoptions_as_parent()` | Obtiene adopciones como padre |
| `get_adoptions_as_child()` | Obtiene adopciones como hijo |
| `update_reputation_score(delta)` | Actualiza reputación |

### Métodos de Consulta Reproductiva

| Método | Descripción |
|--------|-------------|
| `is_fertile()` | Verifica si está en edad fértil |
| `can_reproduce()` | Verifica si puede reproducirse |

### Métodos de Consulta Genética

| Método | Descripción |
|--------|-------------|
| `get_longevity()` | Obtiene longevidad genética |
| `get_immunity()` | Obtiene inmunidad efectiva (ajustada por energía) |

---

## 🎲 Generación de Orientación Sexual

```python
def _generate_orientation(self) -> SexualOrientation:
    roll = random.random()
    if roll < 0.65: return SexualOrientation.HETEROSEXUAL      # 65%
    elif roll < 0.80: return SexualOrientation.MOSTLY_HETERO   # 15%
    elif roll < 0.85: return SexualOrientation.BISEXUAL_HETERO # 5%
    elif roll < 0.88: return SexualOrientation.BISEXUAL        # 3%
    elif roll < 0.90: return SexualOrientation.BISEXUAL_HOMO   # 2%
    elif roll < 0.95: return SexualOrientation.MOSTLY_HOMO     # 5%
    else: return SexualOrientation.HOMOSEXUAL                  # 5%
```

**Distribución realista**: Basada en estudios de Kinsey y distribuciones poblacionales reales.

---

## 🔗 Interacción con Otros Sistemas

```
┌─────────────────────────────────────────────────────────────────┐
│                       Person                                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Identidad: entity_id, x, y, age, gender, species        │  │
│  │  Genoma: genome → propiedades derivadas                  │  │
│  │  Estado: health_state, is_adult, is_senior               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Salud: active_infections, immune_memory                 │  │
│  │  Inmunidad: strain_immunity, strain_metadata             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Reproducción: is_pregnant, pregnancy_days, children     │  │
│  │  Padres: mother_id, father_id, parents, adoptive_parents │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Relaciones: _relationships (Dict O(1)), partner_id      │  │
│  │  Social: marital_status, reputation_score, nucleus_id    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Psicología: memory, emotions, motivations               │  │
│  │  Orientación: sexual_orientation                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ Genoma (03)  │  │ Relaciones   │  │ Todos los sistemas   │
│              │  │ (06)         │  │ consultan/actualizan │
│ - herencia   │  │ - Marriage   │  │                      │
│ - mutación   │  │ - Experience │  │ - Movement           │
│ - capacidades│  │ - Narrative  │  │ - Mortality          │
│              │  │              │  │ - Disease            │
│              │  │              │  │ - Reproduction       │
│              │  │              │  │ - Behavior           │
│              │  │              │  │ - Aging              │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

## ⚙️ Configuración Relevante

La clase `Person` usa la configuración para varios cálculos:

```python
# TimeConfig (para hitos)
self._config.time.adult_age_days      # Edad de madurez
self._config.time.senior_age_days     # Edad de senectud

# ReproductionConfig (para fertilidad)
self._config.reproduction.min_fertility_age_days
self._config.reproduction.max_fertility_age_days
```

---

## 📝 Ejemplos Completos

### Ejemplo 1: Creación de un agente

```python
from core.config.simulation_config import SimulationConfig
from entities.person.person import Person
from entities.person.genome import Genome

config = SimulationConfig()

# Agente humano adulto
person = Person(
    config=config,
    entity_id=1,
    x=50,
    y=50,
    age=10950.0,  # ~30 años
    genome=Genome(species_baseline="human"),
    gender="F",
    species="human"
)

# Verificar estado inicial
print(person.species)          # "human"
print(person.age)              # 10950.0
print(person.gender)           # "F"
print(person.is_adult)         # True (verificado en _check_milestones)
print(person.is_sick)          # False
print(person.emotions)         # {"stress": 0.0, "happiness": 0.8, "energy": 1.0}
print(person.sexual_orientation)  # Aleatorio según distribución
```

### Ejemplo 2: Infección y recuperación

```python
from systems.diseases.pathogen import Pathogen

# Crear patógeno
virus = Pathogen.create_random_variant("Influenza")

# Infectar
person.infect(virus)
print(person.is_sick)          # True
print(person.is_symptomatic)   # False (aún incubando)
print(person.health_state)     # "sano" (aún no sintomático)

# Avanzar la infección
person.advance_infections(delta_days=5.0)
print(person.is_symptomatic)   # True (ahora sintomático)
print(person.health_state)     # "enfermo"

# Calcular inmunidad específica
immunity = person.get_specific_immunity(virus)
print(f"Inmunidad contra {virus.pathogen_id}: {immunity:.2f}")

# Recuperar
person.recover(virus.pathogen_id)
print(person.is_sick)          # False
print(person._immune_memory)   # {"Influenza": 0.4}
print(person._strain_immunity) # {"Influenza_000001": 0.8}
```

### Ejemplo 3: Gestión de relaciones

```python
# Obtener o crear relación con otro agente
rel = person.get_relationship_with(partner_id=2, current_day=100.0)
print(rel.status)  # RelationshipStatus.UNKNOWN

# Añadir relación con estado
person.add_relationship(
    partner_id=2,
    status=RelationshipStatus.DATING,
    current_day=100.0,
    affinity=0.6
)

# Consultar estado civil
print(person.marital_status)   # "casado" (DATING cuenta como relación activa)
print(person.partner_id)       # 2

# Registrar matrimonio
person.register_marriage(partner_id=2, current_day=200.0)
print(person.marital_status)   # "casado"
print(person.emotions["happiness"])  # +0.4

# Registrar divorcio
person.register_divorce(current_day=500.0)
print(person.marital_status)   # "divorciado"
print(person.emotions["stress"])     # +0.5
```

### Ejemplo 4: Motivaciones y emociones

```python
# Consultar motivación dominante
motivation, value = person.get_dominant_motivation()
print(f"Dominante: {motivation} ({value:.2f})")

# Actualizar motivación
person.update_motivation("migration", 0.2)
print(person.get_motivation("migration"))  # 0.4

# Decaer motivaciones
person.decay_motivations(delta_days=1.0)

# Actualizar emoción
person.update_emotion("happiness", 0.1)
print(person.emotions["happiness"])  # 0.9

# Consultar sociabilidad efectiva
print(person.effective_sociability)  # Ajustada por emociones
```

### Ejemplo 5: Reproducción

```python
# Verificar fertilidad
print(person.is_fertile())     # True (si está en edad fértil)
print(person.can_reproduce())  # True (si no está embarazada ni enferma)

# Actualizar embarazo
person.update_pregnancy(status=True, days=0.0, litter_size=1)
print(person.is_pregnant)      # True
print(person.litter_size_gestating)  # 1

# Avanzar embarazo (lo hace GestationSystem)
# ...

# Registrar hijo biológico
person.add_biological_child()
print(person.children_count)   # 1
print(person.biological_children_count)  # 1
print(person.parental_status)  # "padre_biologico"
```

### Ejemplo 6: Inmunidad cruzada

```python
# Recuperarse de Influenza
person.infect(influenza_virus)
person.advance_infections(10.0)
person.recover(influenza_virus.pathogen_id)

# Ahora consultar inmunidad contra Coronavirus (similitud 0.15)
coronavirus = Pathogen.create_random_variant("Coronavirus")
immunity = person.get_specific_immunity(coronavirus)

# La inmunidad incluye:
# - base_innate: genoma.immunity ajustada por energía
# - genetic_specific: inmunidad genética específica a Coronavirus
# - acquired_bonus: inmunidad adquirida a Coronavirus (0 si nunca infectado)
# - cross_immunity: inmunidad cruzada desde Influenza (similitud 0.15)
# - strain_immunity: inmunidad por cepa específica
print(f"Inmunidad contra Coronavirus: {immunity:.2f}")
```

### Ejemplo 7: Adopción y reputación

```python
# Registrar evento de adopción como hijo
person.register_adoption_event(
    event_type="adopted_by",
    entity_id=100,
    day=50.0,
    context="adopcion"
)

# Consultar historial
history = person.get_adoption_history()
print(history)  # [{"type": "adopted_by", "entity_id": 100, "day": 50.0, "context": "adopcion"}]

# Consultar adopciones como hijo
adoptions_as_child = person.get_adoptions_as_child()
print(len(adoptions_as_child))  # 1

# Actualizar reputación
person.update_reputation_score(0.1)
print(person.reputation_score)  # 0.6
```

---

## 🚨 Consideraciones y Limitaciones

### Optimizaciones aplicadas

| Optimización | Descripción | Beneficio |
|--------------|-------------|-----------|
| `entity_id`, `x`, `y` como atributos directos | Sin properties | Acceso rápido |
| `_relationships` como `Dict[int, Relationship]` | En lugar de `List[Relationship]` | Búsqueda O(1) |
| `_get_active_relationships()` con caché | Evita recomputar cada llamada | Rendimiento |
| Property `relationships` retorna lista | Para compatibilidad hacia atrás | Flexibilidad |

### Limitaciones

- **Estado de salud simplificado**: Solo "sano" o "enfermo", no hay estados intermedios
- **Emociones limitadas**: Solo 3 emociones básicas (stress, happiness, energy)
- **Motivaciones fijas**: No se añaden nuevas motivaciones dinámicamente
- **Orientación sexual estática**: Generada al nacer, no cambia
- **Sin memoria episódica directa**: La memoria episódica se maneja en `CognitiveMemorySystem`
- **Sin habilidades aprendidas**: No hay sistema de aprendizaje de habilidades
- **Sin estado nutricional detallado**: Solo se modela como `energy`

### Errores comunes

| Error | Consecuencia | Solución |
|-------|-------------|----------|
| ❌ Modificar `_relationships` directamente | Inconsistencia con caché | Usar `add_relationship()` o `update_relationship_status()` |
| ❌ Olvidar invalidar caché de relaciones | Datos obsoletos | Llamar a `_invalidate_relationships_cache()` |
| ❌ Acceder a `_age` directamente | Saltar verificación de hitos | Usar `add_age()` que verifica hitos |
| ❌ Modificar emociones sin clamp | Valores fuera de [0, 1] | Usar `update_emotion()` que clampea |
| ❌ Asumir que `partner_id` siempre está definido | Puede ser `None` | Verificar con `if partner_id is not None` |
| ❌ Confundir `children_count` con `biological_children_count` | Incluye adoptivos | Usar el correcto según contexto |
| ❌ Olvidar verificar `is_fertile()` antes de reproducción | Reproducción inválida | Verificar siempre |

---

## 🎓 Conceptos Clave

### ¿Por qué entity_id, x, y son atributos directos?

**Principio de rendimiento**:
- Se acceden miles de veces por tick
- Las properties tienen overhead (llamada a función)
- Los atributos directos son más rápidos en Python
- Solo se usa property cuando hay lógica adicional necesaria

### ¿Por qué _relationships es un Dict?

**Principio de complejidad algorítmica**:
- Búsqueda en lista: O(N) - recorrer hasta encontrar
- Búsqueda en dict: O(1) - acceso directo por clave
- Con 1000 agentes y 100 relaciones cada uno, la diferencia es enorme
- La clave es `partner_id`, que es único por relación

### ¿Por qué _get_active_relationships() tiene caché?

**Principio de memoización**:
- Se llama frecuentemente (en cada propiedad calculada)
- Filtrar relaciones activas es O(N)
- El caché evita recomputar si no cambió
- Se invalida cuando se modifican relaciones

### ¿Por qué hay inmunidad por cepa Y por familia?

**Principio de inmunología real**:
- **Por cepa**: Inmunidad específica a una variante concreta (ej: Influenza_000001)
- **Por familia**: Inmunidad general a la familia (ej: Influenza)
- **Cruzada**: Inmunidad parcial a familias relacionadas (ej: Influenza → Coronavirus)
- Esto modela la realidad biológica donde la inmunidad tiene múltiples niveles

### ¿Por qué la sociabilidad efectiva se ajusta por emociones?

**Principio de estado dependiente**:
- Un agente estresado se comporta diferente a uno feliz
- Las emociones afectan las interacciones sociales
- La sociabilidad genética es el potencial, la efectiva es la real
- Esto crea dinámicas emergentes más realistas

### ¿Por qué parental_status distingue entre biológico y adoptivo?

**Principio de inclusión**:
- Los hijos adoptivos son igual de válidos
- Pero el sistema necesita distinguir para cálculos genéticos
- Permite métricas demográficas más precisas
- Refleja la realidad social moderna

---

## 📊 Métricas de la Entidad

| Métrica | Valor |
|---------|-------|
| Archivos de la entidad | 3 (person.py, genome.py, allele.py) |
| Atributos principales | ~40 |
| Properties | ~30 |
| Métodos públicos | ~40 |
| Métodos privados | ~10 |
| Emociones modeladas | 3 |
| Motivaciones modeladas | 8 |
| Estados de salud | 2 |
| Estados civiles | 3 |

---

## 🔮 Futuras Extensiones

### Planificadas
- [ ] Estados de salud más granulares (leve, moderado, grave, crítico)
- [ ] Más emociones (miedo, ira, sorpresa, asco)
- [ ] Motivaciones dinámicas (añadir/eliminar según contexto)
- [ ] Memoria episódica integrada directamente en Person

### Posibles
- [ ] Sistema de habilidades aprendidas
- [ ] Estado nutricional detallado (hambre, sed, nutrientes específicos)
- [ ] Personalidad más compleja (Big Five: apertura, responsabilidad, extraversión, amabilidad, neuroticismo)
- [ ] Orientación sexual fluida (puede cambiar con el tiempo)
- [ ] Identidad de género separada del sexo biológico
- [ ] Sistema de creencias y valores
- [ ] Estado de sueño y fatiga
- [ ] Lesiones físicas y cicatrices permanentes
- [ ] Adicciones y dependencias
- [ ] Estado de salud mental (depresión, ansiedad, TEPT)

---

*Documento: 17_PERSONA.md*
*Versión: 1.0*
*Última actualización: Agosto 2026*