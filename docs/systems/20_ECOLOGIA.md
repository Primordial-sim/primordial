# 20 - Sistema de Relaciones Ecológicas

## 📋 Resumen

El **Sistema de Relaciones Ecológicas** gestiona las interacciones entre especies del simulador. Las relaciones **emergen** de la combinación de perfil biológico, rasgos genéticos y condiciones ambientales, sin reglas fijas de "quién come a quién".

**Filosofía fundamental**: *Las relaciones ecológicas son OBJETOS, no reglas fijas. Emergen de la combinación de perfil + genoma + entorno.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Inferir relaciones ecológicas entre dos especies (`RelationshipInference`)
- Representar relaciones como objetos con tipo, mecanismo, intensidad y efectos (`EcologicalRelationship`)
- Cuantificar la fuerza de las relaciones (intensidad 0.0-1.0)
- Calcular efectos sobre ambas especies (`RelationshipEffect`)
- Verificar compatibilidad de hábitats para interacciones
- Ejecutar las relaciones durante la simulación (`EcologicalRelationshipSystem`)
- Despachar mecanismos de interacción modulares (`MechanismFactory`)

**NO es responsable de:**
- ❌ Clasificar especies (lo hace `TaxonomicSystem`)
- ❌ Describir perfiles biológicos (lo hace `SpeciesProfile`)
- ❌ Decidir capacidades individuales (lo hace `Genome`)
- ❌ Almacenar el estado del mundo (lo hace `WorldState`)

---

## 🌍 Tipos de relaciones ecológicas

| Relación | Especie A | Especie B | Ejemplo real |
|----------|-----------|-----------|--------------|
| **Predation** | + (se alimenta) | - (muere) | Lobo → Ciervo |
| **Herbivory** | + (come plantas) | - (dañada) | Conejo → Hierba |
| **Parasitism** | + (vive a expensas) | - (dañada) | Pulga → Perro |
| **Mutualism** | + | + | Abeja + Flor |
| **Commensalism** | + | 0 | Cangrejo ermitaño + Anémona |
| **Amensalism** | 0 | - | Elefante pisando hormigas |
| **Competition** | - | - | León vs Hiena |
| **Neutralism** | 0 | 0 | Sin interacción |

**Leyenda**: `+` beneficia | `-` perjudica | `0` no afecta

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/ecology/relationship_types.py` | `RelationshipType`, `MechanismType`, `InteractionOutcome` | Enums de tipos y mecanismos |
| `systems/ecology/relationship_effect.py` | `RelationshipEffect` | Efectos sobre especies |
| `systems/ecology/ecological_relationship.py` | `EcologicalRelationship` | Objeto central de relación |
| `systems/ecology/relationship_inference.py` | `RelationshipInference` | Inferencia desde perfil + genoma |
| `systems/ecology/ecological_relationship_system.py` | `EcologicalRelationshipSystem` | Orquestador que ejecuta relaciones |
| `systems/ecology/mechanisms.py` | `BaseMechanism`, `HuntMechanism`, etc. | Mecanismos modulares de ejecución |
| `systems/ecology/biome_condition_checker.py` | `BiomeConditionChecker` | Verificación de biomas y estaciones |
| `systems/ecology/__init__.py` | Exports | API pública del sistema |

---

## 🔄 Flujo de ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│              FLUJO DE INFERENCIA ECOLÓGICA                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. ENTRADA: DOS ESPECIES                                        │
│    ├── SpeciesDefinition A (ej: "bird")                          │
│    └── SpeciesDefinition B (ej: "insect")                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONSULTA DE PERFILES (SpeciesClassificationSystem)            │
│    ├── Dieta: ¿Es carnívoro? ¿Es herbívoro?                     │
│    ├── Hábitat: ¿Terrestre? ¿Acuático? ¿Aéreo?                  │
│    ├── Tamaño corporal: ¿Pequeño? ¿Mediano? ¿Grande?            │
│    └── Estructura social: ¿Solitario? ¿Manada?                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. INFERENCIA DE RELACIONES (RelationshipInference)             │
│    ├── _infer_predation(): ¿A puede depredar a B?               │
│    ├── _infer_herbivory(): ¿A puede consumir a B (planta)?      │
│    ├── _infer_mutualism(): ¿A y B tienen symbiosis alto?        │
│    └── _infer_competition(): ¿A y B compiten por recursos?      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CÁLCULO DE INTENSIDAD                                        │
│    ├── Predation: ataque vs defensa (incluye inteligencia)      │
│    ├── Herbivory: metabolismo del herbívoro vs defensa planta   │
│    ├── Mutualism: promedio de symbiosis en ambos                │
│    └── Competition: similitud de nicho ecológico                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SALIDA: EcologicalRelationship                               │
│    ├── species_a_id, species_b_id                                │
│    ├── relationship_type (PREDATION, MUTUALISM, etc.)            │
│    ├── mechanism (HUNT, GRAZING, POLLINATION, etc.)              │
│    ├── intensity [0.0, 1.0]                                      │
│    ├── effect_on_a: RelationshipEffect                           │
│    └── effect_on_b: RelationshipEffect                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. RelationshipType - Tipos de Relaciones

**📁 Archivo**: `systems/ecology/relationship_types.py`
**🌍 Equivalencia real**: Las categorías clásicas de interacción ecológica.

#### Tipos disponibles (8)

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `PREDATION` | A se come a B | Lobo → Ciervo |
| `HERBIVORY` | A consume B (planta/alga) | Conejo → Hierba |
| `COMPETITION` | A y B compiten por recursos | León vs Hiena |
| `MUTUALISM` | A y B se benefician mutuamente | Abeja + Flor |
| `PARASITISM` | A vive a expensas de B | Pulga → Perro |
| `COMMENSALISM` | A se beneficia, B no se afecta | Cangrejo + Anémona |
| `AMENSALISM` | A perjudica a B sin afectarse | Elefante + Hormigas |
| `NEUTRALISM` | Sin interacción significativa | Especies distantes |

---

### 2. MechanismType - Mecanismos de Interacción

**📁 Archivo**: `systems/ecology/relationship_types.py`
**🌍 Equivalencia real**: CÓMO se ejecuta una relación ecológica.

#### Mecanismos disponibles (12)

| Mecanismo | Descripción | Relación típica |
|-----------|-------------|-----------------|
| `HUNT` | Caza activa (persecución, emboscada) | Predation |
| `PACK_HUNTING` | Caza en manada coordinada | Predation |
| `AMBUSH` | Emboscada sigilosa | Predation |
| `GRAZING` | Pastoreo de vegetación | Herbivory |
| `FILTER_FEEDING` | Filtrado de agua | Herbivory/Feeding |
| `POLLINATION` | Polinización de flores | Mutualism |
| `SEED_DISPERSAL` | Dispersión de semillas | Mutualism |
| `INFECTION` | Infección parasitaria | Parasitism |
| `RESOURCE_CONSUMPTION` | Competencia por recursos | Competition |
| `TERRITORIAL_DISPLAY` | Exhibición territorial | Competition |
| `CHEMICAL_SUPPRESSION` | Supresión química (alelopatía) | Amensalism |
| `SCAVENGING` | Carroñeo | Predation/Decomposition |

---

### 3. RelationshipEffect - Efectos sobre Especies

**📁 Archivo**: `systems/ecology/relationship_effect.py`
**🌍 Equivalencia real**: El impacto ecológico de una interacción.

#### Atributos

| Atributo | Tipo | Rango | Descripción |
|----------|------|-------|-------------|
| `energy_change` | `float` | [-1.0, 1.0] | Ganancia/pérdida de energía |
| `survival_impact` | `float` | [-1.0, 1.0] | Impacto en supervivencia |
| `reproduction_impact` | `float` | [-1.0, 1.0] | Impacto en reproducción |
| `growth_impact` | `float` | [-1.0, 1.0] | Impacto en crecimiento |
| `stress_change` | `float` | [0.0, 1.0] | Aumento de estrés |
| `death_probability` | `float` | [0.0, 1.0] | Probabilidad de muerte |
| `description` | `str` | — | Descripción del efecto |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `is_beneficial()` | ¿El efecto es netamente beneficioso? |
| `is_harmful()` | ¿El efecto es netamente perjudicial? |

#### Funciones de creación rápida

| Función | Uso |
|---------|-----|
| `predator_success_effect()` | Efecto sobre depredador tras caza exitosa |
| `prey_death_effect()` | Efecto sobre presa cazada |
| `herbivore_grazing_effect()` | Efecto sobre herbívoro pastando |
| `plant_consumed_effect()` | Efecto sobre planta consumida |
| `mutualism_benefit()` | Beneficio mutuo |

#### Ejemplos

```python
# Efecto sobre depredador exitoso
predator_effect = predator_success_effect(energy_gain=0.6)
print(predator_effect.energy_change)  # 0.6
print(predator_effect.is_beneficial())  # True

# Efecto sobre presa cazada
prey_effect = prey_death_effect(death_probability=0.7)
print(prey_effect.death_probability)  # 0.7
print(prey_effect.is_harmful())  # True
```

---

### 4. EcologicalRelationship - Objeto Central

**📁 Archivo**: `systems/ecology/ecological_relationship.py`
**🌍 Equivalencia real**: Una relación ecológica específica entre dos especies.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `species_a_id` | `str` | ID de la especie que inicia la relación |
| `species_b_id` | `str` | ID de la especie objetivo |
| `relationship_type` | `RelationshipType` | Tipo de relación |
| `mechanism` | `MechanismType` | Mecanismo de interacción |
| `intensity` | `float` | Fuerza de la relación [0.0, 1.0] |
| `biome_requirements` | `List[str]` | Biomas donde es válida |
| `seasonal_constraints` | `List[str]` | Estaciones donde ocurre |
| `effect_on_a` | `RelationshipEffect` | Efecto sobre especie A |
| `effect_on_b` | `RelationshipEffect` | Efecto sobre especie B |
| `notes` | `str` | Notas opcionales |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `intensity_level` | Nivel de intensidad (WEAK, MODERATE, STRONG, EXTREME) |
| `is_valid_in_biome(biome)` | ¿Es válida en un bioma específico? |
| `is_valid_in_season(season)` | ¿Es válida en una estación específica? |
| `get_effect_on(species_id)` | Obtiene el efecto sobre una especie |
| `is_mutualistic()` | ¿Es una relación mutualista? |
| `is_antagonistic()` | ¿Es una relación antagónica? |

#### Ejemplos

```python
from systems.ecology import (
    EcologicalRelationship,
    RelationshipType,
    MechanismType,
)
from systems.ecology.relationship_effect import (
    predator_success_effect,
    prey_death_effect,
)

# Crear una relación de depredación
predation = EcologicalRelationship(
    species_a_id="bird",
    species_b_id="insect",
    relationship_type=RelationshipType.PREDATION,
    mechanism=MechanismType.HUNT,
    intensity=0.75,
    biome_requirements=["forest", "grassland"],
    effect_on_a=predator_success_effect(energy_gain=0.5),
    effect_on_b=prey_death_effect(death_probability=0.6),
    notes="Ave insectívora cazando insectos",
)

print(predation.relationship_type)  # RelationshipType.PREDATION
print(predation.intensity_level)    # RelationshipIntensity.STRONG
print(predation.is_antagonistic())  # True
```

---

### 5. RelationshipInference - Inferencia desde Perfil + Genoma

**📁 Archivo**: `systems/ecology/relationship_inference.py`
**🌍 Equivalencia real**: Un ecólogo que deduce interacciones observando las especies.

#### Método principal

```python
def infer_relationships(
    self,
    species_a: SpeciesDefinition,
    species_b: SpeciesDefinition,
) -> List[EcologicalRelationship]:
    """Infiere todas las relaciones posibles entre dos especies."""
```

#### Lógica de inferencia por tipo

##### Predation

| Verificación | Condición |
|--------------|-----------|
| Depredador es carnívoro | `profile.is_predator()` o `predatory_instinct > 0.5` |
| Presa es herbívora u omnívora | `prey.diet in (HERBIVORE, OMNIVORE)` |
| Hábitats compatibles | `_can_predation_habitat_interact()` |
| Tamaño adecuado | Presa no mucho más grande que depredador |
| Intensidad suficiente | `intensity >= 0.5` |

**Cálculo de intensidad**:
```
attack_factor = (predatory_instinct + speed) / 2
defense_factor = (defense + speed) / 2 + intelligence * 0.25 + sociability * 0.15
intensity = 0.5 + attack_factor * 0.3 - defense_factor * 0.25
```

**Nota clave**: La **inteligencia** y **sociabilidad** de la presa actúan como defensas poderosas. Esto evita que aves depreden humanos, por ejemplo.

##### Herbivory

| Verificación | Condición |
|--------------|-----------|
| Herbívoro es herbívoro | `herbivore.diet == HERBIVORE` |
| Planta es fotosintética | `plant.diet == PHOTOSYNTHETIC` |
| Hábitats compatibles | `classification.can_interact()` |

**Cálculo de intensidad**:
```
intensity = 0.5 + herbivore_metabolism * 0.2 - plant_defense * 0.1
```

##### Mutualism

| Verificación | Condición |
|--------------|-----------|
| Ambos tienen symbiosis alto | `symbiosis_a >= 0.5 AND symbiosis_b >= 0.5` |
| Hábitats compatibles | `classification.can_interact()` |

**Cálculo de intensidad**:
```
intensity = (symbiosis_a + symbiosis_b) / 4.0
```

##### Competition

| Verificación | Condición |
|--------------|-----------|
| Misma dieta | `profile_a.diet == profile_b.diet` |
| Hábitats con solapamiento | Igualdad o compatibilidad de hábitats |

**Cálculo de intensidad**:
```
intensity = 0.3 (base)
          + 0.2 (si mismo tamaño corporal)
          + 0.1 (si misma locomoción)
          + 0.1 (si mismo hábitat exacto)
```

#### Método auxiliar: `_can_predation_habitat_interact()`

Matriz de hábitats compatibles para depredación:

| Depredador | Presa | ¿Compatible? |
|-----------|-------|--------------|
| AERIAL | TERRESTRIAL | ✅ Aves cazan insectos terrestres |
| AERIAL | AMPHIBIOUS | ✅ Aves cazan anfibios |
| AQUATIC | AMPHIBIOUS | ✅ Peces cazan renacuajos |
| AMPHIBIOUS | TERRESTRIAL | ✅ Anfibios cazan en tierra |
| AMPHIBIOUS | AQUATIC | ✅ Anfibios cazan en agua |
| TERRESTRIAL | AMPHIBIOUS | ✅ Depredadores terrestres cazan anfibios |

---

## ⚙️ Mecanismos de Ejecución

**📁 Archivo**: `systems/ecology/mechanisms.py`

Los mecanismos encapsulan la lógica específica de cada tipo de interacción. El `EcologicalRelationshipSystem` despacha al mecanismo correcto según `relationship.mechanism`.

### Arquitectura

```
BaseMechanism (abstracta)
├── HuntMechanism              → Depredación activa (caza)
├── GrazingMechanism           → Pastoreo / herbivoría
├── PollinationMechanism       → Polinización (mutualismo)
├── ResourceConsumptionMechanism → Competencia por recursos
├── ScavengingMechanism        → Carroñeo
└── InfectionMechanism         → Parasitismo
```

### Mecanismos implementados

| Mecanismo | Tipo de relación | Probabilidad de éxito | Efecto |
|-----------|-----------------|----------------------|--------|
| `HuntMechanism` | Predation | 5% - 85% (según tamaño) | Presa muere, depredador gana energía |
| `GrazingMechanism` | Herbivory | Hasta 90% | Herbívoro gana energía, planta pierde energía |
| `PollinationMechanism` | Mutualism | 95% | Ambos ganan energía |
| `ResourceConsumptionMechanism` | Competition | 100% | Ambos pierden energía |
| `ScavengingMechanism` | Scavenging | Hasta 80% | Carroñero gana energía |
| `InfectionMechanism` | Parasitism | 5% - 70% (según inmunidad) | Parásito gana energía, huésped pierde |

### Uso

```python
from systems.ecology.mechanisms import MechanismFactory
from systems.ecology.relationship_types import MechanismType

# Obtener el mecanismo correcto
mechanism = MechanismFactory.get_mechanism(MechanismType.HUNT)

# Ejecutar la interacción
outcome = mechanism.execute(predator, prey, relationship, pending)

# Consultar estadísticas
stats = MechanismFactory.get_all_stats()
print(stats["hunt"])  # {"executions": 150, "successes": 87, "success_rate": 0.58}
```

### Extensibilidad

Para añadir un nuevo mecanismo:

1. Crear clase que herede de `BaseMechanism`
2. Implementar `_calculate_success_probability()`
3. Implementar `_apply_effects()`
4. Registrarlo en `MechanismFactory._initialize()`

```python
class AmbushMechanism(BaseMechanism):
    """Mecanismo de emboscada sigilosa."""
    
    def _calculate_success_probability(self, person_a, person_b, relationship):
        # Lógica específica de emboscada
        return relationship.intensity * 0.85  # Mayor éxito por sorpresa
    
    def _apply_effects(self, person_a, person_b, relationship, pending, success):
        # Efectos de la emboscada
        if success:
            pending.register_death(entity_id=person_b.entity_id, reason="ambush")
            person_a.add_energy(relationship.effect_on_a.energy_change)
```

---

## 🌐 EcologicalRelationshipSystem - Orquestador de Ejecución

**📁 Archivo**: `systems/ecology/ecological_relationship_system.py`

El orquestador ejecuta las relaciones ecológicas durante la simulación. Se integra en la FASE 3: ECOLOGÍA del `PhaseScheduler`.

### Flujo de ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DETECCIÓN DE ENCUENTROS (SpatialGrid)                         │
│    └── Para cada agente, buscar vecinos en radio 2              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. INFERENCIA DE RELACIONES (con caché)                          │
│    └── Relaciones inferidas una vez por par de especies          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. VERIFICACIÓN DE CONDICIONES AMBIENTALES                       │
│    └── BiomeConditionChecker: bioma + estación                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EJECUCIÓN DEL MECANISMO                                       │
│    └── MechanismFactory despacha al mecanismo correcto           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. APLICACIÓN DE EFECTOS                                         │
│    ├── Energía: add_energy() / spend_energy()                    │
│    ├── Muerte: pending.register_death()                          │
│    └── Estadísticas: actualizar contadores                       │
└─────────────────────────────────────────────────────────────────┘
```

### Configuración

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `process_interval` | 3.0 días | Frecuencia de procesamiento |
| `search_radius` | 2 tiles | Radio de detección de encuentros |

### Estadísticas disponibles

```python
summary = ecology_system.get_summary()
# {
#     "total_encounters": 1250,
#     "total_relationships_executed": 342,
#     "total_predations": 87,
#     "total_herbivory": 156,
#     "total_mutualism": 45,
#     "total_competition": 54,
#     "cached_relationship_pairs": 28,
#     "mechanism_stats": {...}
# }
```

---

## 📊 Ejemplo completo de uso

```python
from core.taxonomy import SpeciesClassificationSystem
from systems.ecology import RelationshipInference
from core.genetics.species_definition import SpeciesRegistry

# Inicializar sistemas
SpeciesRegistry.initialize_defaults()
classification = SpeciesClassificationSystem.get_default()
classification.initialize_defaults()

# Crear inferidor
inference = RelationshipInference(classification)

# Obtener dos especies
bird = SpeciesRegistry.get("bird")
insect = SpeciesRegistry.get("insect")

# Inferir relaciones
relationships = inference.infer_relationships(bird, insect)

# Analizar resultados
for rel in relationships:
    print(f"Tipo: {rel.relationship_type.value}")
    print(f"Mecanismo: {rel.mechanism.value}")
    print(f"Intensidad: {rel.intensity:.2f}")
    print(f"Efecto sobre {rel.species_a_id}: {rel.effect_on_a}")
    print(f"Efecto sobre {rel.species_b_id}: {rel.effect_on_b}")
```

**Salida esperada**:
```
Tipo: predation
Mecanismo: hunt
Intensidad: 0.73
Efecto sobre bird: RelationshipEffect(energy=+0.44)
Efecto sobre insect: RelationshipEffect(death_prob=51%)
```

---

## 🔗 Interacción con otros sistemas

```
┌─────────────────────────────────────────────────────────────────┐
│              SpeciesClassificationSystem                         │
│         Taxonomía + Perfiles + Especies                          │
└────────────────────┬───────────────────────────────────────────┘
                     │ proporciona perfiles
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              RelationshipInference                                │
│    Infiere relaciones desde perfil + genoma                     │
└────────────────────┬───────────────────────────────────────────┘
                     │ produce
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              EcologicalRelationship                               │
│    Objeto con tipo, mecanismo, intensidad, efectos              │
└────────────────────┬───────────────────────────────────────────┘
                     │ usado por
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              EcologicalRelationshipSystem (implementado)         │
│    Ejecuta relaciones durante la simulación                     │
│    ├── Detección de encuentros (SpatialGrid) ✅                  │
│    ├── Verificación de biomas (BiomeConditionChecker) ✅         │
│    ├── Ejecución de mecanismos (MechanismFactory) ✅             │
│    └── Aplicación de efectos (energía, muerte) ✅                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Tipos de relación | 8 |
| Mecanismos de interacción | 12 |
| Mecanismos implementados | 6 (Hunt, Grazing, Pollination, ResourceConsumption, Scavenging, Infection) |
| Niveles de intensidad | 4 (WEAK, MODERATE, STRONG, EXTREME) |
| Atributos de efecto | 7 |
| Relaciones inferidas por defecto | 17 (con 8 especies) |
| Predation detectada | 9 |
| Herbivory detectada | 1 |
| Competition detectada | 5 |
| Mutualism detectado | 2 |

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Relaciones como objetos**: Cada relación es un objeto inmutable, no una regla fija
- **Emergencia desde genética**: Las relaciones emergen de perfil + genoma, no de tablas hardcodeadas
- **Inteligencia como defensa**: La inteligencia y sociabilidad protegen a las presas
- **Hábitats flexibles**: Las interacciones no requieren hábitats idénticos
- **Mecanismos modulares**: Cada tipo de interacción tiene su propia lógica encapsulada

### Limitaciones actuales
- **Duplicados bidireccionales**: Competition y Mutualism aparecen dos veces (A→B y B→A)
- **Procesamiento periódico**: Las relaciones se ejecutan cada 3 días, no cada tick
- **Sin memoria de interacciones**: Los organismos no recuerdan encuentros previos

### Errores comunes
- ❌ Asumir que las relaciones son simétricas (Predation no lo es)
- ❌ Usar `can_interact()` para Predation (usar `_can_predation_habitat_interact()`)
- ❌ Ignorar la intensidad (relaciones con intensity < 0.5 se descartan)
- ❌ Crear relaciones manualmente sin usar `RelationshipInference`

---

## 🎓 Conceptos clave

### ¿Por qué las relaciones son objetos y no reglas?

**Flexibilidad y escalabilidad**: Si tuviéramos 300 especies, una tabla de "quién come a quién" tendría miles de entradas. Con objetos que emergen de rasgos, el sistema escala automáticamente.

### ¿Por qué la inteligencia protege de la depredación?

**Realismo biológico**: Los humanos no somos presas de aves rapaces porque:
- Usamos herramientas y fuego
- Vivimos en grupos coordinados
- Tenemos estrategias de defensa

Esto se modela con `intelligence_bonus = intelligence * 0.25` y `sociability_bonus = sociability * 0.15`.

### ¿Por qué los hábitats son flexibles?

**Realismo ecológico**: Las aves aéreas cazan insectos terrestres constantemente. Un modelo estricto de "mismo hábitat" sería incorrecto. La matriz `_can_predation_habitat_interact()` refleja esta realidad.

### ¿Por qué los mecanismos son modulares?

**Extensibilidad**: Cada mecanismo encapsula una lógica diferente de interacción. Añadir un nuevo tipo de interacción (ej: simbiosis compleja) solo requiere crear una nueva clase sin modificar el orquestador.

---

## 🔮 Futuras extensiones

### Completadas ✅
- [x] `EcologicalRelationshipSystem`: Orquestador que ejecuta relaciones durante la simulación
- [x] `BiomeConditionChecker`: Verificación de biomas y estaciones
- [x] Integración con `SpatialGrid` para detección de encuentros
- [x] Mecanismos de ejecución: `HuntMechanism`, `GrazingMechanism`, etc.
- [x] `MechanismFactory`: Despacho dinámico de mecanismos

### Planificadas (corto plazo)
- [ ] Eliminación de duplicados bidireccionales
- [ ] Efectos sobre poblaciones (mortalidad, natalidad)
- [ ] Cadenas tróficas completas
- [ ] Parasitismo integrado con `DiseaseSystem`

### Planificadas (medio plazo)
- [ ] `AmbushMechanism`, `PackHuntingMechanism`, `TerritorialDisplayMechanism`
- [ ] Memoria de interacciones entre organismos
- [ ] Coevolución (depredador-presa)
- [ ] Extinción de especies

### Posibles (largo plazo)
- [ ] Especiación por aislamiento ecológico
- [ ] Extinciones masivas por colapso de cadenas tróficas
- [ ] Efectos cascada en el ecosistema
- [ ] Redes tróficas visualizables

---

## 📋 Changelog

### Versión 2.0 (Agosto 2026)
- ✅ Añadida sección de Mecanismos de Ejecución
- ✅ Añadida sección de EcologicalRelationshipSystem
- ✅ Actualizado diagrama de interacción (sistema implementado)
- ✅ Actualizadas limitaciones y extensiones futuras
- ✅ Añadidos 6 mecanismos implementados

### Versión 1.0 (Agosto 2026)
- Versión inicial con inferencia de relaciones

---

*Documento: 20_ECOLOGIA.md*
*Versión: 2.0*
*Última actualización: Agosto 2026*