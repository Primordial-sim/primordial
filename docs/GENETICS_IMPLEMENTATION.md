# IMPLEMENTACIÓN DEL NÚCLEO GENÉTICO

**Versión:** 2.0
**Última actualización:** Agosto 2026
**Estado:** Núcleo genético CONGELADO (estable)
**Tests:** 181/181 pasando
**Nota:** Este documento describe el ESTADO ACTUAL de la implementación.
Para la especificación conceptual, ver GENETICS_CORE_SPEC.md

---

**ESTADO: CONGELADO**

El núcleo genético está cerrado. No se modificará salvo necesidad
real de otro sistema. Este documento describe el estado actual
de la implementación.

Fecha de congelación: Agosto 2026

## 1. ESTRUCTURA DE ARCHIVOS

core/genetics/
├── trait.py                      # Definición de Trait (neutro)
├── trait_library.py              # Biblioteca de 36 rasgos
├── species_definition.py         # Especies + plantillas + herencia
├── biological_validator.py       # Validador con reglas
└── realism_index.py              # Índice de realismo

entities/person/
├── allele.py                     # Allele + Gene (con modelos de expresión)
└── genome.py                     # Genome (por individuo)

core/config/
└── simulation_config.py          # MutationConfig

tests/unit/
├── test_genetics_universal.py    # 40 tests de genética universal
├── test_mutation.py              # 22 tests de mutación
└── test_genome_combine.py        # 21 tests de recombinación

scenarios/
├── humans.json                   # Escenario de humanos
├── birds.json                    # Escenario de aves
├── insects.json                  # Escenario de insectos
├── bacteria.json                 # Escenario de bacterias
├── mixed.json                    # Escenario multiespecie
└── custom_template.json          # Plantilla para personalizar

tools/
├── run_scenario.py               # CLI para ejecutar escenarios
└── ws_server_real.py             # Servidor WebSocket para Godot

docs/
├── GENETICS_CORE_SPEC.md         # Especificación conceptual
├── GENETICS_IMPLEMENTATION.md    # Este documento
└── SYSTEMS_DEPENDENCIES.md       # Mapa de dependencias de sistemas

---

## 2. CLASES IMPLEMENTADAS

### 2.1 Trait (core/genetics/trait.py)

- dataclass frozen
- Atributos: trait_id, name, category, min_value, max_value, default_value,
  expression_model, evolutionary_weight, heritability, initial_distribution,
  initial_mean, initial_std, description
- Método: clamp_value(value) -> float

### 2.2 TraitLibrary (core/genetics/trait_library.py)

- Singleton con get_default()
- Métodos: register_trait(), get_trait(), get_all_traits()
- Actualmente: 36 rasgos registrados

### 2.3 SpeciesDefinition (core/genetics/species_definition.py)

- Soporta herencia de plantillas
- Métodos: from_template(), empty(), add_trait(), get_trait_config(),
  get_all_trait_ids(), get_inheritance_chain(), has_trait()
- Actualmente: 9 plantillas base + 6 especies predefinidas

### 2.4 SpeciesRegistry (core/genetics/species_definition.py)

- Registro global de especies
- Métodos: initialize_defaults(), register(), get(), get_all(),
  get_by_archetype(), get_templates()

### 2.5 Allele (entities/person/allele.py)

- dataclass frozen
- Atributos: value, dominance
- Método: create_random(base_value, mutation_range, min_value, max_value)

### 2.6 Gene (entities/person/allele.py)

- Contiene allele_a y allele_b
- Métodos: express(expression_model), meiosis()

### 2.7 Genome (entities/person/genome.py)

- Almacén pasivo de información genética
- Métodos: create_founder(species), get_trait_value(trait_id), has_trait(),
  get_all_trait_ids(), combine(other_genome, mutation_config),
  replicate(mutation_config)
- Properties retrocompatibles: longevity, sociability, temperament, fertility,
  immunity, impulsivity, curiosity, obedience, aggressiveness

### 2.8 MutationConfig (core/config/simulation_config.py)

- dataclass
- Atributos: probability, magnitude_std, mutate_dominance, dominance_std
- Valores por defecto: 0.05, 0.1, False, 0.05

### 2.9 BiologicalValidator (core/genetics/biological_validator.py)

- Reglas declarativas de coherencia
- Métodos: validate_species(species) -> ValidationResult
- Niveles: INFO, WARNING, ERROR

### 2.10 RealismIndex (core/genetics/realism_index.py)

- Calcula índice de realismo (0-100%)
- Métodos: calculate(species) -> float, get_description(score) -> str

---

## 3. PLANTILLAS EXISTENTES

empty (vacía)            0 rasgos
│
├── animal               9 rasgos
│   ├── vertebrate      13 rasgos
│   │   ├── mammal      20 rasgos → human
│   │   ├── bird        17 rasgos
│   │   ├── reptile     17 rasgos
│   │   ├── amphibian   15 rasgos
│   │   └── fish        16 rasgos
│   └── invertebrate    12 rasgos
│       └── insect      15 rasgos
│
├── plant                7 rasgos
├── fungus               7 rasgos
├── bacteria             6 rasgos
└── fantasy_creature     8 rasgos

---

## 4. RASGOS REGISTRADOS (36)

BIOLOGY (8):
    fertility, immunity, longevity, metabolism, growth_rate,
    healing, nervous_system, heterotrophy

BEHAVIOR (10):
    sociability, aggressiveness, territoriality, empathy, cooperation,
    curiosity, impulsivity, obedience, temperament, intelligence

PERCEPTION (5):
    vision, smell, hearing, night_vision, echolocation

MOVEMENT (5):
    speed, flight, swimming, climbing, burrowing

SPECIAL (8):
    venom, photosynthesis, camouflage, regeneration, bioluminescence,
    division_speed, antibiotic_resistance, mobility

---

## 5. ESPECIES PREDEFINIDAS

Especie     Plantilla padre   Rasgos totales   Descripción
-------     ---------------   --------------   -----------
human       mammal            22               Mamífero inteligente
bird        vertebrate        17               Ave voladora
fish        vertebrate        16               Pez acuático
insect      invertebrate      15               Insecto fértil
reptile     vertebrate        17               Reptil longevo
amphibian   vertebrate        15               Anfibio regenerador

---

## 6. SISTEMAS MIGRADOS A API GENÉRICA

Todos los sistemas de simulación han sido migrados para usar get_trait_value()
en lugar de propiedades legacy.

Sistema                                     Propiedades migradas
-------                                     --------------------
systems/diseases/disease_system.py          immunity
systems/temporal/temporal_system.py         temperament, immunity
systems/mortality/mortality_system.py       longevity
systems/behavior/cognitive_memory_system.py temperament
systems/genealogy/genealogy_system.py       longevity, sociability, temperament
systems/free_will/free_will_system.py       impulsivity, curiosity, obedience,
                                            aggressiveness, temperament, sociability
systems/aging/aging_system.py               longevity
systems/movement/movement_system.py         curiosity
systems/reproduction/conception_system.py   fertility, longevity
systems/reproduction/gestation_system.py    Soporte para asexual con replicate()

---

## 7. TESTS

TOTAL: 181 tests pasando

DISTRIBUCIÓN:

tests/unit/test_genetics_universal.py       40 tests
tests/unit/test_mutation.py                 22 tests
tests/unit/test_genome_combine.py           21 tests
tests/integration/test_regression_bugs.py   10 tests
tests/integration/test_statistical.py        3 tests
Otros tests de sistemas                     85 tests

---

## 8. CONFIGURACIÓN ACTUAL DE MUTACIÓN

La configuración de mutación está definida en:
core/config/simulation_config.py → MutationConfig

Valores por defecto:
- probability: 0.05 (5% de alelos mutan)
- magnitude_std: 0.1 (desviación estándar del cambio)
- mutate_dominance: False (la dominancia no muta por defecto)
- dominance_std: 0.05 (desviación de mutación de dominancia)

Se puede cambiar por escenario:
config.mutation.probability = 0.1
config.mutation.magnitude_std = 0.2

---

## 9. ESTADO DE CONGELACIÓN

El núcleo genético está CONGELADO. No se modificará salvo que una necesidad
real de otro sistema lo requiera.

LO QUE ESTÁ CERRADO:
✓ Trait (definición de rasgos)
✓ TraitLibrary (biblioteca de rasgos)
✓ SpeciesDefinition (plantillas y especies)
✓ SpeciesRegistry (registro de especies)
✓ Genome (genotipo de un individuo)
✓ Gene / Allele
✓ ExpressionModel (7 modelos)
✓ MutationConfig
✓ BiologicalValidator
✓ RealismIndex
✓ Herencia mendeliana (combine, meiosis)
✓ Reproducción asexual (replicate)
✓ Mutación con clampeo
✓ Rangos definidos

LO QUE ESTÁ PENDIENTE:
⏸ Taxonomía y compatibilidad reproductiva
⏸ Biomas y terrenos
⏸ Movimiento por rasgos (flight, swimming)
⏸ Interacciones entre especies
⏸ Conceptos humanos opcionales

---

## 10. PRÓXIMOS PASOS SUGERIDOS

1. Taxonomía y compatibilidad reproductiva (evitar cruces imposibles)
2. Diseño de sistema de biomas/terrenos
3. Movimiento por rasgos (flight, swimming, burrowing)
4. Interacciones entre especies (depredación, parasitismo)
5. Conceptos humanos opcionales (marriage, pregnancy según especie)

---

**FIN DEL DOCUMENTO DE IMPLEMENTACIÓN**