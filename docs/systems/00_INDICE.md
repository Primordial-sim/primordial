# 00 - Índice General del Simulador de Vida

## 📋 Resumen

Este documento sirve como **índice maestro** y **mapa de navegación** para toda la documentación técnica del Simulador de Vida. Proporciona una visión panorámica de la arquitectura del sistema, las relaciones entre componentes, y enlaces directos a la documentación detallada de cada subsistema.

**Propósito**: Permitir a desarrolladores, diseñadores y analistas comprender rápidamente la estructura del simulador y navegar eficientemente hacia la documentación específica que necesitan.

---

## 🎯 Visión General del Proyecto

El **Simulador de Vida** es un ecosistema artificial complejo donde agentes autónomos con genética, comportamiento, emociones y relaciones sociales interactúan en un mundo dinámico con estaciones, enfermedades, migraciones y evolución. El sistema está diseñado para estudiar fenómenos emergentes, dinámica poblacional, evolución cultural y biológica, y patrones sociales complejos.

### Características principales

- **Agentes autónomos** con genética heredable, emociones, memoria y motivaciones
- **Mundo dinámico** con clima, estaciones, recursos, catástrofes naturales y hábitats ecológicos
- **Relaciones sociales emergentes** desde encuentros casuales hasta matrimonios y familias
- **Evolución biológica** observable en tiempo real con selección natural
- **Epidemiología realista** con patógenos mutantes, inmunidad cruzada y carga viral ambiental
- **Estructura social compleja** con núcleos residenciales, presión social y reputación
- **Genealogía completa** con árboles familiares, linajes y análisis de consanguinidad
- **Métricas multidimensionales** para análisis demográfico, genético y epidemiológico
- **Interfaz visual en Godot** con controles en tiempo real vía WebSocket
- **Sistema de eventos pub/sub** como infraestructura de extensibilidad
- **Taxonomía y perfiles biológicos** para clasificación de especies y descripción ecológica
- **Relaciones ecológicas emergentes** entre especies (depredación, mutualismo, competencia, herbivoría)
- **Sistema de energía** con fotosíntesis, metabolismo, gasto por movimiento/reproducción e inanición

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE CONFIGURACIÓN                        │
│  SimulationConfig (time, reproduction, diseases, evolution...)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE ESTADO                               │
│  WorldState (agentes, mapa, núcleos)                            │
│  PendingChanges (buffer transaccional)                          │
│  EnvironmentContext (presión, recursos, biomas)                 │
│  SpatialGrid (optimización de búsquedas)                        │
│  EpidemiologicalMap (carga viral ambiental)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE SISTEMAS                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 0: MOTOR DE SIMULACIÓN                            │    │
│  │  SimulationEngine, PhaseScheduler, LoopController       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 1: GENÉTICA Y REPRODUCCIÓN                        │    │
│  │  Genome, TraitLibrary, SpeciesRegistry                  │    │
│  │  ConceptionSystem, GestationSystem, EggSystem           │    │
│  │  TaxonomicSystem, SpeciesProfile, ProfileInference      │    │
│  │  SpeciesClassificationSystem                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 2: ENTORNO Y MOVIMIENTO                           │    │
│  │  TileMap, EnvironmentSystem, CatastropheSystem          │    │
│  │  HabitatPreference, HabitatCompatibility                │    │
│  │  MovementSystem, MigrationSystem, SpatialGrid           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 3: ECOLOGÍA Y ENERGÍA                             │    │
│  │  EcologicalRelationshipSystem, EnergySystem             │    │
│  │  RelationshipInference, EcologicalRelationship          │    │
│  │  RelationshipTypes, RelationshipEffects                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 4: COMPORTAMIENTO Y COGNICIÓN                     │    │
│  │  FreeWillSystem, CognitiveMemorySystem, BiasEngine      │    │
│  │  CognitiveCapabilities, MovementCapabilities            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 5: RELACIONES Y ESTRUCTURA SOCIAL                 │    │
│  │  CompatibilityEngine, MarriageSystem, ExperienceGen.    │    │
│  │  NarrativeEngine, SocialPressure, ResidentialNucleus    │    │
│  │  RelationshipEventType, RelationshipLogger              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 6: SALUD Y MORTALIDAD                             │    │
│  │  DiseaseSystem, Pathogen, ImmunologicalCapabilities     │    │
│  │  MortalitySystem, DeathResolver                         │    │
│  │  EpidemiologicalMap (carga viral ambiental)             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 7: TEMPORAL Y ENVEJECIMIENTO                      │    │
│  │  TemporalSystem, AgingSystem                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 8: GENEALOGÍA Y EVOLUCIÓN                         │    │
│  │  GenealogySystem, AncestryQueries                       │    │
│  │  EvolutionEngine, AdoptionSystem                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 9: MÉTRICAS Y OBSERVACIÓN                         │    │
│  │  MetricsSystem                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  FASE 10: INFRAESTRUCTURA                               │    │
│  │  EventBus (pub/sub), Person (entidad central)           │    │
│  │  Interfaz Godot, WebSocket, Herramientas CLI            │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE INTERFAZ                             │
│  CLI (launcher.py), API REST, Exportación JSON/CSV              │
│  Godot (visualización en tiempo real vía WebSocket)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentación por Sistema

### 01 - Motor de Simulación
**Archivos**: `simulation_engine.py`, `phase_scheduler.py`, `loop_controller.py`, `simulation_runner.py`, `scenario_loader.py`, `world_initializer.py`, `pending_changes.py`, `world_state.py`, `environment_context.py`

**Responsabilidad**: Orquesta el ciclo de vida completo de la simulación, gestiona las fases de ejecución, controla el bucle principal, carga escenarios, inicializa el mundo y proporciona el buffer transaccional.

📄 [Documentación completa → 01_MOTOR_DE_SIMULACION.md](./01_MOTOR_DE_SIMULACION.md)

---

### 02 - Estado del Mundo
**Archivos**: `world_state.py`, `pending_changes.py`, `environment_context.py`

**Responsabilidad**: Mantiene el estado autoritativo del mundo, gestiona el buffer transaccional de cambios pendientes, y proporciona contexto ambiental a los sistemas.

📄 [Documentación completa → 02_ESTADO_DEL_MUNDO.md](./02_ESTADO_DEL_MUNDO.md)

---

### 03 - Genética Universal
**Archivos**: `genome.py`, `trait.py`, `trait_library.py`, `allele.py`, `gene.py`, `species_definition.py`, `species_registry.py`, `biological_validator.py`, `realism_index.py`

**Responsabilidad**: Define el sistema genético completo con herencia mendeliana, múltiples modelos de expresión, catálogo de rasgos, registro de especies y validación biológica.

📄 [Documentación completa → 03_GENETICA.md](./03_GENETICA.md)

---

### 04 - Entorno
**Archivos**: `tile.py`, `tile_map.py`, `tile_map_initializer.py`, `world_config.py`, `biome_classifier.py`, `environment_context.py`, `environment_system.py`, `environment_dynamics.py`, `catastrophe_model.py`, `catastrophe_system.py`, `feedback_system.py`, `organism_impact.py`, `density_system.py`, `habitat_preference.py`, `habitat_compatibility.py`

**Responsabilidad**: Modela el mundo físico con terreno, clima, estaciones, biomas emergentes, catástrofes naturales (8 tipos con severidades), retroalimentación organismo-entorno, preferencias ecológicas por especie y cálculo de compatibilidad hábitat-especie mediante función gaussiana.

📄 [Documentación completa → 04_ENTORNO.md](./04_ENTORNO.md)

---

### 05 - Reproducción
**Archivos**: `conception_system.py`, `gestation_system.py`, `egg_system.py`, `egg_model.py`, `reproductive_capabilities.py`

**Responsabilidad**: Gestiona el ciclo reproductivo completo: concepción, gestación (vivíparos), incubación de huevos (ovíparos), reproducción asexual, con restricciones biológicas realistas.

📄 [Documentación completa → 05_REPRODUCCION.md](./05_REPRODUCCION.md)

---

### 06 - Relaciones Sociales
**Archivos**: `compatibility_engine.py`, `marriage_system.py`, `relationship_manager.py`, `relationship_experience_engine.py`, `experience_generator.py`, `behavior_influence.py`, `narrative_engine.py`, `relationship_model.py` (incluye `BiasEngine`, `GoalFilter`), `relationship_events.py`, `relationship_system.py` (stub), `relationship_logger.py`, `social_capabilities.py`

**Responsabilidad**: Modela la red compleja de relaciones sociales emergentes mediante un vocabulario común de 14 eventos relacionales. Incluye compatibilidad, formación de parejas, experiencias cotidianas, narrativas, etiquetas emergentes, sesgos cognitivos y logging especializado. La lógica es emergente (no centralizada).

📄 [Documentación completa → 06_RELACIONES_SOCIALES.md](./06_RELACIONES_SOCIALES.md)

---

### 07 - Movimiento
**Archivos**: `movement_system.py`, `movement_resolver.py`, `migration_system.py`, `movement_capabilities.py`, `spatial_grid.py`

**Responsabilidad**: Gestiona el movimiento físico de agentes con Utility AI, arbitraje de colisiones (regla 1 agente = 1 casilla), migraciones masivas a larga distancia con push/pull factors, y optimización espacial O(k) mediante SpatialGrid. Todo filtrado por capacidades derivadas del genoma.

📄 [Documentación completa → 07_MOVIMIENTO.md](./07_MOVIMIENTO.md)

---

### 08 - Comportamiento
**Archivos**: `free_will_system.py`, `cognitive_memory_system.py`, `cognitive_capabilities.py`, `bias_engine.py` (en `relationship_model.py`)

**Responsabilidad**: Modela la vida interior de los agentes: motivaciones continuas con inhibición competitiva, memoria episódica e implícita (traumas), sesgos cognitivos, con capacidades derivadas del genoma.

📄 [Documentación completa → 08_COMPORTAMIENTO.md](./08_COMPORTAMIENTO.md)

---

### 09 - Salud
**Archivos**: `disease_system.py`, `pathogen.py`, `immunological_capabilities.py`, `epidemiological_map.py`

**Responsabilidad**: Gestiona la epidemiología completa: patógenos con identidad y mutación, 5 fases biológicas de infección (expuesto→incubando→contagioso→sintomático→recuperándose), inmunidad multinivel (innata/adaptativa/cruzada/familia/cepa), carga viral ambiental mediante sparse grid, contagios por proximidad y brotes espontáneos.

📄 [Documentación completa → 09_SALUD.md](./09_SALUD.md)

---

### 10 - Mortalidad
**Archivos**: `mortality_system.py`, `death_resolver.py`

**Responsabilidad**: Calcula mortalidad multifactorial (modelo Gompertz-Makeham expandido con 11 factores), diagnostica causas de muerte, notifica a relaciones, y purga todas las intenciones pendientes del fallecido para coherencia transaccional.

📄 [Documentación completa → 10_MORTALIDAD.md](./10_MORTALIDAD.md)

---

### 11 - Estructura Social
**Archivos**: `social_capabilities.py`, `social_pressure.py`, `residential_nucleus.py`

**Responsabilidad**: Gestiona estructuras sociales emergentes: capacidades sociales derivadas del genoma (5 niveles de complejidad), presión social individual y ambiental, núcleos residenciales (convivencia).

📄 [Documentación completa → 11_ESTRUCTURA_SOCIAL.md](./11_ESTRUCTURA_SOCIAL.md)

---

### 12 - Genealogía
**Archivos**: `genealogy_system.py`, `ancestry_queries.py`

**Responsabilidad**: Mantiene el árbol genealógico completo (vivos y muertos), registra matrimonios/divorcios/adopciones, detecta extinciones de linajes, calcula grados de parentesco (BFS), analiza endogamia, provee estadísticas de linajes.

📄 [Documentación completa → 12_GENEALOGIA.md](./12_GENEALOGIA.md)

---

### 13 - Evolución
**Archivos**: `evolution_engine.py`

**Responsabilidad**: Observador puro que monitorea macroevolución: snapshots genéticos, diversidad, presión de selección, correlaciones entre genes, causas de muerte, éxito de linajes, eventos drásticos (cuellos de botella).

📄 [Documentación completa → 13_EVOLUCION.md](./13_EVOLUCION.md)

---

### 14 - Temporal y Envejecimiento
**Archivos**: `temporal_system.py`, `aging_system.py`

**Responsabilidad**: Gestiona el reloj global, metabolismo basal con trade-offs evolutivos, hitos biológicos con efectos emocionales, y envejecimiento biológico multifactorial (reproductivo, embarazo, estrés, enfermedad, energía, genético).

📄 [Documentación completa → 14_TEMPORAL.md](./14_TEMPORAL.md)

---

### 15 - Métricas
**Archivos**: `metrics_system.py`

**Responsabilidad**: Observador puro que recolecta snapshots multidimensionales (10 dimensiones): demografía, genética, epidemiología, espacial, reproducción, cognición, genealogía, social. Gestiona historial con límites de memoria y exporta a JSON.

📄 [Documentación completa → 15_METRICAS.md](./15_METRICAS.md)

---

### 16 - Eventos
**Archivos**: `event_bus.py`, eventos en `population/` (5 implementados), `simulation/` (5 vacíos), `world/` (3 vacíos)

**Responsabilidad**: Implementa el patrón Publicación/Suscripción (Pub/Sub) para desacoplar sistemas. Estado actual: infraestructura implementada pero sin suscriptores activos. Publica 5 eventos de población (nacimientos, muertes, matrimonios, divorcios, adopciones) desde WorldState.

📄 [Documentación completa → 16_EVENTOS.md](./16_EVENTOS.md)

---

### 17 - Entidad Persona
**Archivos**: `person.py`, `genome.py`, `allele.py`

**Responsabilidad**: La entidad central del simulador. Almacena el estado completo de un agente individual: genoma, posición, edad, emociones, motivaciones, relaciones (optimizado O(1)), memoria inmunológica, estado reproductivo, estado civil, reputación, orientación sexual y núcleo residencial.

📄 [Documentación completa → 17_PERSONA.md](./17_PERSONA.md)

---

### 18 - Interfaz y Herramientas
**Archivos**: `launcher.py`, `tools/run_scenario.py`, `tools/ws_server.py`, `tools/ws_server_real.py`, scripts de Godot (`websocket_client.gd`, `world_renderer.gd`, `ui_renderer.gd`, `camera_controller.gd`)

**Responsabilidad**: Múltiples formas de ejecutar y visualizar la simulación: CLI principal, herramienta de escenarios, servidor WebSocket (integración con motor real) y interfaz Godot con renderizado del mundo, controles de simulación e inspector de agentes.

📄 [Documentación completa → 18_INTERFAZ_Y_HERRAMIENTAS.md](./18_INTERFAZ_Y_HERRAMIENTAS.md)

---

### 19 - Taxonomía
**Archivos**: `taxonomic_node.py`, `taxonomic_system.py`, `profile_enums.py`, `species_profile.py`, `profile_inference.py`, `species_classification.py`

**Responsabilidad**: Clasificación jerárquica de especies (9 niveles: Domain → Subspecies), perfiles biológicos inferidos desde rasgos genéticos (dieta, hábitat, locomoción, estructura social, termorregulación, tamaño corporal), y sistema unificado de clasificación. La taxonomía es **informativa**: clasifica especies pero **no decide capacidades** (las capacidades salen del genoma).

📄 [Documentación completa → 19_TAXONOMIA.md](./19_TAXONOMIA.md)

---

### 20 - Ecología
**Archivos**: `relationship_types.py`, `relationship_effect.py`, `ecological_relationship.py`, `relationship_inference.py`

**Responsabilidad**: Inferencia de relaciones ecológicas entre especies (Predation, Herbivory, Competition, Mutualism, Parasitism, Commensalism, Amensalism, Neutralism). Las relaciones **emergen** de la combinación de perfil biológico, rasgos genéticos y condiciones ambientales. Incluye 8 tipos de relación, 12 mecanismos de interacción, y cálculo de efectos sobre ambas especies.

📄 [Documentación completa → 20_ECOLOGIA.md](./20_ECOLOGIA.md)

---

### 21 - Energía
**Archivos**: `energy_system.py`, `person.py` (atributos de energía), `movement_resolver.py` (gasto por movimiento), `conception_system.py` (gasto por reproducción)

**Responsabilidad**: Gestiona el metabolismo energético de todos los organismos: fotosíntesis para plantas, metabolismo basal, gasto por movimiento y reproducción, inanición y muerte por falta de energía, y sincronización con el sistema emocional.

📄 [Documentación completa → 21_ENERGIA.md](./21_ENERGIA.md)

---

## 🔄 Flujo de Ejecución por Tick

```text
TICK DE SIMULACIÓN
   │
   ├── FASE 0: INDEXACIÓN ESPACIAL (Pre-procesamiento)
   │   └── SpatialGrid: indexación de agentes para búsquedas O(k)
   │
   ├── FASE 1: TEMPORAL ('temporal')
   │   ├── TemporalSystem: reloj global y actualización de tiempos
   │   └── AgingSystem: envejecimiento biológico y hitos de edad
   │
   ├── FASE 2: AMBIENTAL ('environment')
   │   ├── EnvironmentSystem: propagación de variables físicas y clima
   │   ├── DensitySystem: cálculo del mapa de densidad poblacional
   │   ├── EpidemiologicalSystem: propagación de carga viral ambiental
   │   ├── SocialPressureCalculator: campo de presión social del tick anterior
   │   └── CognitiveMemorySystem: actualización de memoria según estrés del entorno
   │
   ├── FASE 3: ECOLOGÍA Y ENERGÍA ('ecology')
   │   ├── EcologicalRelationshipSystem: encuentros, depredación, herbivoría, mutualismo
   │   └── EnergySystem: fotosíntesis, metabolismo basal, sincronización emocional e inanición
   │
   ├── FASE 4: RELACIONES SOCIALES ('relationships')
   │   ├── CompatibilityEngine: precálculo de compatibilidades
   │   ├── MarriageSystem: formación de relaciones y parejas
   │   ├── RelationshipManager: mantenimiento, rupturas y transiciones relacionales
   │   ├── AdoptionSystem: reasignaciones familiares legales de huérfanos
   │   └── ExperienceGenerator: generación de experiencias basadas en etiquetas
   │
   ├── FASE 5: MOVIMIENTO Y CONDUCTA ('behavior_and_movement')
   │   ├── FreeWillSystem: decisiones autónomas, rebeldía y motivaciones
   │   ├── MigrationSystem: cálculo de vectores de migración masiva
   │   ├── MovementSystem: decisiones tácticas de desplazamiento (Utility AI)
   │   └── MovementResolver: arbitraje de colisiones y gasto de energía por movimiento
   │
   ├── FASE 6: SALUD ('health')
   │   └── DiseaseSystem: interacciones inmunológicas, contagios, brotes y recuperaciones
   │
   ├── FASE 7: REPRODUCCIÓN ('reproduction')
   │   ├── ConceptionSystem: ventanas de fertilidad, concepciones y gasto de energía reproductiva
   │   ├── EggSystem: incubación, mortalidad ambiental y eclosión de huevos (ovíparos)
   │   └── GestationSystem: progresión de embarazos y encolado de nacimientos (vivíparos)
   │
   ├── FASE 8: MORTALIDAD ('mortality')
   │   ├── MortalitySystem: curvas de supervivencia (Gompertz) y fallecimientos
   │   └── DeathResolver: purga de acciones de recién fallecidos del búfer
   │
   ├── FASE 9: OBSERVADORES ('observers')
   │   ├── GenealogySystem: sincronización del árbol genealógico
   │   ├── MetricsSystem: métricas poblacionales macroscópicas
   │   └── EvolutionEngine: snapshots evolutivos y motor evolutivo
   │
   └── [COMMIT]
       └── WorldState.apply_commit(): consolidación del búfer transaccional en memoria

---

## 🔗 Relaciones entre Sistemas

### Dependencias principales

```
Genome (03) ──► Todas las capacidades derivadas:
                ├── MovementCapabilities (07)
                ├── CognitiveCapabilities (08)
                ├── ReproductiveCapabilities (05)
                ├── ImmunologicalCapabilities (09)
                └── SocialCapabilities (11)

Genome (03) ──► ProfileInference (19): perfiles biológicos desde rasgos
            ──► RelationshipInference (20): inferencia de relaciones

TaxonomicSystem (19) ──► SpeciesProfile (19): perfiles biológicos
                     ──► SpeciesClassificationSystem (19): sistema unificado
                     ──► RelationshipInference (20): consulta de perfiles

EcologicalRelationship (20) ──► EcologicalRelationshipSystem (pendiente):
                                 ejecución de relaciones en runtime

WorldState (02) ──► Todos los sistemas (lectura)
PendingChanges (02) ──► Todos los sistemas (escritura transaccional)
EnvironmentContext (02) ──► Todos los sistemas (contexto ambiental)

SpatialGrid (07) ──► MovementSystem (búsquedas O(k))
                  ──► DiseaseSystem (vecinos para contagios)
                  ──► RelationshipManager (encuentros)

EpidemiologicalMap (09) ──► MovementSystem (evitar zonas peligrosas)
                        ──► MigrationSystem (validar destinos)
                        ──► DiseaseSystem (propagación)

GenealogySystem (12) ──► AncestryQueries (12)
                      ──► EvolutionEngine (13) [fitness]
                      ──► AdoptionSystem (11) [prioridad parientes]
                      ──► MortalitySystem (10) [endogamia]
                      ──► MetricsSystem (15) [métricas genealógicas]

EvolutionEngine (13) ──► GenealogySystem (12) [descendencia]
                     ──► Genome (03) [introspección]

MetricsSystem (15) ──► GenealogySystem (12) [opcional]
                   ──► EnvironmentContext (02) [presión espacial]

EventBus (16) ──► WorldState (publica eventos)
             ──► Sin suscriptores activos (preparado para UI/logs)

Person (17) ──► Todos los sistemas (entidad central consultada)

Interfaz (18) ──► SimulationEngine (WebSocket server)
             ──► Godot (cliente visual)
```

### Flujos de datos clave

```
Genome (03) ──► ProfileInference (19) ──► SpeciesProfile
                                     ──► SpeciesClassificationSystem

SpeciesProfile ──► RelationshipInference (20) ──► EcologicalRelationship
Genome (03) ──► RelationshipInference (20) ──► EcologicalRelationship

ConceptionSystem ──► pending.register_pregnancy_update()
                 ──► pending.new_eggs (para ovíparos)
                 ──► pending.register_birth() (para asexuales)

GestationSystem ──► pending.register_birth()
               ──► pending.register_death() (mortalidad materna)

DiseaseSystem ──► pending.register_infection()
             ──► pending.register_recovery()
             ──► pending.register_death()
             ──► epidemiological_map.add_viral_load()

MortalitySystem ──► pending.register_death()
               ──► RelationshipExperienceEngine (PARTNER_DEATH)

DeathResolver ──► pending (purga todas las colecciones)

MovementSystem ──► pending.register_movement()
MovementResolver ──► pending.movements (arbitraje)

FreeWillSystem ──► pending.register_motivation_update()
              ──► RelationshipExperienceEngine (eventos relacionales)

CognitiveMemorySystem ──► pending.register_memory_update()
                     ──► pending.register_emotion_update()

TemporalSystem ──► pending.register_time_pass()
              ──► pending.register_emotion_update()
              ──► pending.register_age_increment() (indirectamente)

AgingSystem ──► pending.register_age_increment()

WorldState ──► EventBus.publish(PersonBornEvent, PersonDiedEvent, etc.)
```

---

## 📊 Estadísticas del Proyecto

| Categoría | Cantidad |
|-----------|----------|
| **Documentos de sistema** | 22 (21 sistemas + 1 índice) |
| **Archivos de código documentados** | ~90 |
| **Clases principales** | ~120 |
| **Tests unitarios** | 342 |
| **Tests de integración** | ~20+ |
| **Líneas de código** | ~16,000+ |
| **Rasgos genéticos** | 42 |
| **Especies predefinidas** | 16 |
| **Tipos de biomas** | 15 |
| **Tipos de catástrofes** | 8 |
| **Fases de infección** | 5 |
| **Motivaciones modeladas** | 7 |
| **Sesgos cognitivos** | 5 |
| **Eventos relacionales** | 14 |
| **Dimensiones de métricas** | 10 |
| **Familias de patógenos** | 7+ |
| **Niveles de severidad (catástrofes)** | 4 |
| **Presets de hábitat** | 9 |
| **Niveles taxonómicos** | 9 |
| **Tipos de relación ecológica** | 8 |
| **Mecanismos ecológicos** | 12 |

---

## 🚀 Guía de Navegación Rápida

### Para desarrolladores nuevos

1. **Empieza por aquí**: [01_MOTOR_SIMULACION.md](./01_MOTOR_SIMULACION.md) - entiende el ciclo de vida
2. **Luego**: [02_ESTADO_MUNDO.md](./02_ESTADO_DEL_MUNDO.md) - comprende la arquitectura de datos
3. **Después**: [03_GENETICA.md](./03_GENETICA.md) - el núcleo biológico
4. **Entidad central**: [17_PERSONA.md](./17_PERSONA.md) - el corazón del simulador
5. **Taxonomía**: [19_TAXONOMIA.md](./19_TAXONOMIA.md) - clasificación y perfiles
6. **Ecología**: [20_ECOLOGIA.md](./20_ECOLOGIA.md) - relaciones entre especies
7. **Finalmente**: Explora los sistemas específicos según tu interés

### Para entender un agente completo

1. **Genética**: [03_GENETICA.md](./03_GENETICA.md) - qué puede hacer
2. **Taxonomía**: [19_TAXONOMIA.md](./19_TAXONOMIA.md) - qué es y cómo vive
3. **Entidad**: [17_PERSONA.md](./17_PERSONA.md) - estado completo
4. **Capacidades derivadas**: Movimiento (07), Cognición (08), Reproducción (05), Inmunidad (09), Social (11)
5. **Comportamiento**: [08_COMPORTAMIENTO.md](./08_COMPORTAMIENTO.md) - qué decide hacer
6. **Movimiento**: [07_MOVIMIENTO.md](./07_MOVIMIENTO.md) - cómo se desplaza
7. **Relaciones**: [06_RELACIONES_SOCIALES.md](./06_RELACIONES_SOCIALES.md) - con quién interactúa
8. **Ecología**: [20_ECOLOGIA.md](./20_ECOLOGIA.md) - cómo interactúa con otras especies
9. **Salud**: [09_SALUD.md](./09_SALUD.md) - cómo enferma y se recupera
10. **Muerte**: [10_MORTALIDAD.md](./10_MORTALIDAD.md) - cómo y por qué muere

### Para analizar la simulación

1. **Métricas**: [15_METRICAS.md](./15_METRICAS.md) - observación multidimensional
2. **Evolución**: [13_EVOLUCION.md](./13_EVOLUCION.md) - análisis macroevolutivo
3. **Genealogía**: [12_GENEALOGIA.md](./12_GENEALOGIA.md) - árboles familiares y linajes
4. **Ecología**: [20_ECOLOGIA.md](./20_ECOLOGIA.md) - relaciones entre especies

### Para modificar el mundo

1. **Entorno**: [04_ENTORNO.md](./04_ENTORNO.md) - terreno, clima, catástrofes, hábitats
2. **Temporal**: [14_TEMPORAL.md](./14_TEMPORAL.md) - tiempo y envejecimiento
3. **Estructura social**: [11_ESTRUCTURA_SOCIAL.md](./11_ESTRUCTURA_SOCIAL.md) - presión social y núcleos

### Para usar la interfaz

1. **CLI básico**: [18_INTERFAZ_Y_HERRAMIENTAS.md](./18_INTERFAZ_Y_HERRAMIENTAS.md) - launcher.py
2. **Visualización**: Mismo documento - Godot + WebSocket
3. **Eventos**: [16_EVENTOS.md](./16_EVENTOS.md) - infraestructura pub/sub

---

## 🎓 Conceptos Fundamentales

### Principios de diseño

1. **Separación de responsabilidades**: Cada sistema tiene una responsabilidad clara y única
2. **Arquitectura transaccional**: Todos los cambios pasan por `PendingChanges` para coherencia
3. **Capacidades derivadas del genoma**: El comportamiento posible emerge de la genética
4. **Observadores puros**: `EvolutionEngine` y `MetricsSystem` no modifican el estado
5. **Emergencia sobre programación**: Las relaciones, narrativas y etiquetas emergen de interacciones
6. **Trade-offs evolutivos**: Cada rasgo tiene beneficios y costes
7. **Coherencia temporal**: Fuente de verdad única (`state.world_days_elapsed`)
8. **Extensibilidad**: Introspección automática para nuevos genes
9. **Optimización espacial**: `SpatialGrid` reduce O(N²) a O(k)
10. **Carga viral ambiental**: `EpidemiologicalMap` modela contaminación realista
11. **Vocabulario común**: `RelationshipEventType` desacopla sistemas relacionales
12. **Taxonomía informativa**: La taxonomía clasifica, no decide capacidades
13. **Ecología emergente**: Las relaciones ecológicas emergen de perfil + genoma + entorno

### Patrones arquitectónicos

- **Fase de proceso**: Cada sistema implementa `process(state, pending, delta_days, context)`
- **Buffer transaccional**: `PendingChanges` acumula cambios, `WorldState.apply_commit()` los consolida
- **Capacidades inmutables**: Se derivan del genoma una vez y no cambian
- **Eventos relacionales ligeros**: Dataclasses simples para comunicación entre sistemas
- **Introspección dinámica**: Detección automática de propiedades numéricas en `Genome`
- **Spatial Grid**: Indexación espacial para búsquedas eficientes de vecinos
- **Sparse Grid**: Solo almacenar datos donde hay actividad (EpidemiologicalMap)
- **Pub/Sub**: EventBus para desacoplamiento de sistemas emisores y consumidores
- **Inferencia desde genética**: Perfiles y relaciones se infieren desde rasgos, no se hardcodean

---

## 🔮 Extensiones Futuras Planificadas

### Corto plazo (próximos documentos)
- [x] **Interfaz/API**: Documentación de CLI y API REST (✅ Completado en 18_INTERFAZ)
- [x] **Entidad Persona**: Documentación de la entidad central (✅ Completado en 17_PERSONA)
- [x] **Sistema de Eventos**: Documentación de infraestructura pub/sub (✅ Completado en 16_EVENTOS)
- [x] **Taxonomía**: Documentación del sistema taxonómico (✅ Completado en 19_TAXONOMIA)
- [x] **Ecología**: Documentación del sistema de relaciones ecológicas (✅ Completado en 20_ECOLOGIA)
- [ ] **Visualización avanzada**: Gráficos evolutivos, visualización de relaciones
- [ ] **EcologicalRelationshipSystem**: Orquestador que ejecuta relaciones en runtime

### Medio plazo (nuevos sistemas)
- [ ] **Clima regional**: Frentes meteorológicos que se mueven
- [ ] **Economía**: Recursos intercambiables, comercio, dinero
- [ ] **Cultura**: Transmisión de conocimientos, rituales, tradiciones
- [ ] **Tecnología**: Invenciones, herramientas, progreso tecnológico
- [ ] **Política**: Liderazgo, facciones, conflictos grupales
- [ ] **Religión**: Creencias, rituales, instituciones religiosas
- [ ] **Tratamientos médicos**: Antibióticos, antivirales, vacunas
- [ ] **Suscriptores del EventBus**: Conectar UI y logs al sistema de eventos
- [ ] **Mecanismos ecológicos**: HuntMechanism, GrazingMechanism, PollinationMechanism

### Largo plazo (visiones ambiciosas)
- [ ] **Multi-especie inteligente**: Diferentes especies con culturas propias
- [ ] **Civilizaciones**: Ciudades, estados, imperios
- [ ] **Guerras**: Conflictos a gran escala entre grupos
- [ ] **Comercio internacional**: Rutas comerciales, economía global
- [ ] **Exploración**: Descubrimiento de nuevas tierras
- [ ] **Extinciones masivas**: Eventos catastróficos globales
- [ ] **Evolución cultural**: Transmisión de memes e ideas
- [ ] **Sistema de salud pública**: Cuarentenas, vacunación masiva
- [ ] **Especiación**: Aparición de nuevas especies por aislamiento ecológico

---

## 📝 Convenciones de Documentación

### Estructura de cada documento

Cada documento de sistema sigue esta estructura:

1. **Resumen**: Descripción concisa del sistema
2. **Responsabilidad**: Qué hace y qué NO hace
3. **Equivalencia con la vida real**: Tabla de conceptos
4. **Archivos que lo componen**: Lista de archivos y clases
5. **Flujo de ejecución completo**: Diagrama del ciclo de vida
6. **Componentes del sistema**: Descripción detallada de cada clase
7. **Interacción entre componentes**: Diagrama de dependencias
8. **Configuración relevante**: Parámetros configurables
9. **Tests del sistema**: Archivos de prueba
10. **Ejemplos completos**: Casos de uso detallados
11. **Consideraciones y limitaciones**: Principios, optimizaciones, errores comunes
12. **Conceptos clave**: Explicación de decisiones de diseño
13. **Métricas del sistema**: Estadísticas cuantitativas
14. **Futuras extensiones**: Roadmap de mejoras

### Convenciones de código

- **Fase de proceso**: `process(state, pending, delta_days, context)`
- **Registro transaccional**: `pending.register_*(...)`
- **Capacidades derivadas**: `XCapabilities.from_genome(genome)`
- **Eventos relacionales**: `_XRelationalEvent(event_type, intensity, context)`
- **Introspección**: `getattr(obj, 'attr_name', default_value)`
- **Búsquedas espaciales**: `spatial_grid.get_nearby_agents(agent, radius)`
- **Carga viral**: `epidemiological_map.add_viral_load(x, y, amount)`
- **Inferencia de perfiles**: `ProfileInference.infer(species)`
- **Inferencia de relaciones**: `RelationshipInference.infer_relationships(a, b)`

---

---

## 📋 Documentos de Planificación y Especificaciones

Además de la documentación de sistemas, el proyecto mantiene documentos de planificación y especificaciones conceptuales en carpetas dedicadas.

### Planificación

📄 [SYSTEM_DEPENDENCIES.md](../planning/SYSTEM_DEPENDENCIES.md) - **Mapa de dependencias de sistemas**

Análisis exhaustivo de qué sistemas consumen el núcleo genético y cuáles necesitan migración para ser agnósticos a especie. Incluye:
- Clasificación de 17 sistemas (agnósticos, legacy, hardcodeados)
- Plan de migración en 4 fases
- Lista de conceptos humanos hardcodeados (marriage, pregnancy, gestation)
- Rasgos genéticos usados vs no usados

**Estado**: Documento de planificación activo para futuras sesiones de refactorización.

---

### Especificaciones

📄 [GENETICS_CORE_SPEC.md](../specs/GENETICS_CORE_SPEC.md) - **Especificación del Núcleo Genético**

Contrato conceptual del núcleo genético (cerrado y congelado en Agosto 2026). Define los principios fundamentales:
- Conceptos: Trait, Allele, Gene, Genome
- Modelos de expresión genética (7 modelos)
- Reproducción sexual y asexual
- Mutación y rangos
- Límites del núcleo genético

**Estado**: Documento conceptual atemporal. No habla de implementación.

---

## 🙏 Créditos y Agradecimientos

Este simulador es un proyecto de investigación en sistemas complejos, vida artificial y emergencia de comportamiento inteligente. Agradecemos a:

- La comunidad de vida artificial (ALife)
- Investigadores en sistemas multi-agente
- Estudios de etología y comportamiento animal
- Teoría de juegos y evolución cultural
- Epidemiología matemática
- Genética de poblaciones
- Ecología teórica (nichos ecológicos, hábitats, relaciones interespecíficas)
- Taxonomía biológica (sistema de clasificación de Linneo)

---

## 📞 Contacto y Contribuciones

Para preguntas, sugerencias o contribuciones:

- **Issues**: Reportar bugs o solicitar features
- **Pull Requests**: Contribuciones de código y documentación
- **Discusiones**: Debates sobre diseño y arquitectura
- **Documentación**: Mejoras y correcciones a esta documentación

---

## 📋 Changelog del Índice

### Versión 2.1 (Agosto 2026)
- ✅ Añadido documento 19_TAXONOMIA.md (Sistema Taxonómico)
- ✅ Añadido documento 20_ECOLOGIA.md (Sistema de Relaciones Ecológicas)
- ✅ Actualizado diagrama de arquitectura con TaxonomicSystem y EcologicalRelationshipSystem
- ✅ Añadida nueva fase FASE 3: ECOLOGÍA Y RELACIONES ENTRE ESPECIES
- ✅ Actualizadas estadísticas: 42 rasgos genéticos, 16 especies predefinidas, 21 documentos
- ✅ Añadidas nuevas métricas: niveles taxonómicos, tipos de relación ecológica, mecanismos ecológicos
- ✅ Actualizado flujo de dependencias con TaxonomicSystem y RelationshipInference
- ✅ Actualizada guía de navegación con Taxonomía y Ecología
- ✅ Añadidos principios: Taxonomía informativa, Ecología emergente

### Versión 2.0 (Agosto 2026)
- ✅ Añadidos documentos 16_EVENTOS, 17_PERSONA, 18_INTERFAZ_Y_HERRAMIENTAS
- ✅ Corregidos nombres de archivos con typos (03_GENETICA, 06_RELACIONES_SOCIALES, 10_MORTALIDAD, 12_GENEALOGIA)
- ✅ Añadidos componentes: SpatialGrid (07), EpidemiologicalMap (09), catastrophe_model (04), habitat_preference (04), habitat_compatibility (04), relationship_events (06), relationship_logger (06), relationship_system (06)
- ✅ Actualizadas estadísticas del proyecto
- ✅ Actualizado flujo de ejecución con 13 fases
- ✅ Actualizado diagrama de interacción con nuevas dependencias
- ✅ Actualizada fecha a Agosto 2026

### Versión 2.2 (Agosto 2026)
- ✅ Añadido documento 21_ENERGIA.md (Sistema de Energía)
- ✅ Actualizada FASE 3: ahora incluye EnergySystem junto a EcologicalRelationshipSystem
- ✅ Actualizado diagrama de arquitectura con EnergySystem
- ✅ Actualizadas estadísticas: 342 tests, 22 documentos
- ✅ Añadido flujo de energía en dependencias entre sistemas
- ✅ Actualizada guía de navegación con Energía

---

*Documento: 00_INDICE.md*
*Versión: 2.2*
*Última actualización: Agosto 2026*