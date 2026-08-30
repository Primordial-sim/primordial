# 00 - Índice General del Simulador de Vida

## 📋 Resumen

Este documento sirve como **índice maestro** y **mapa de navegación** para toda la documentación técnica del Simulador de Vida. Proporciona una visión panorámica de la arquitectura del sistema, las relaciones entre componentes, y enlaces directos a la documentación detallada de cada subsistema.

**Propósito**: Permitir a desarrolladores, diseñadores y analistas comprender rápidamente la estructura del simulador y navegar eficientemente hacia la documentación específica que necesitan.

---

## 🎯 Visión General del Proyecto

El **Simulador de Vida** es un ecosistema artificial complejo donde agentes autónomos con genética, comportamiento, emociones y relaciones sociales interactúan en un mundo dinámico con estaciones, enfermedades, migraciones y evolución. El sistema está diseñado para estudiar fenómenos emergentes, dinámica poblacional, evolución cultural y biológica, y patrones sociales complejos.

### Características principales

- **Agentes autónomos** con genética heredable, emociones, memoria y motivaciones
- **Mundo dinámico** con clima, estaciones, recursos y catástrofes naturales
- **Relaciones sociales emergentes** desde encuentros casuales hasta matrimonios y familias
- **Evolución biológica** observable en tiempo real con selección natural
- **Epidemiología realista** con patógenos mutantes e inmunidad cruzada
- **Estructura social compleja** con núcleos residenciales, presión social y reputación
- **Genealogía completa** con árboles familiares, linajes y análisis de consanguinidad
- **Métricas multidimensionales** para análisis demográfico, genético y epidemiológico

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE CONFIGURACIÓN                         │
│  SimulationConfig (time, reproduction, diseases, evolution...)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE ESTADO                                │
│  WorldState (agentes, mapa, núcleos)                            │
│  PendingChanges (buffer transaccional)                          │
│  EnvironmentContext (presión, recursos, biomas)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE SISTEMAS                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 0: MOTOR DE SIMULACIÓN                            │   │
│  │  SimulationEngine, PhaseScheduler, LoopController       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 1: GENÉTICA Y REPRODUCCIÓN                        │   │
│  │  Genome, TraitLibrary, SpeciesRegistry                  │   │
│  │  ConceptionSystem, GestationSystem, EggSystem           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 2: ENTORNO Y MOVIMIENTO                           │   │
│  │  TileMap, EnvironmentSystem, CatastropheSystem          │   │
│  │  MovementSystem, MigrationSystem, MovementResolver      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 3: COMPORTAMIENTO Y COGNICIÓN                     │   │
│  │  FreeWillSystem, CognitiveMemorySystem, BiasEngine      │   │
│  │  CognitiveCapabilities, MovementCapabilities            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 4: RELACIONES Y ESTRUCTURA SOCIAL                 │   │
│  │  CompatibilityEngine, MarriageSystem, ExperienceGen.    │   │
│  │  NarrativeEngine, SocialPressure, ResidentialNucleus    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 5: SALUD Y MORTALIDAD                             │   │
│  │  DiseaseSystem, Pathogen, ImmunologicalCapabilities     │   │
│  │  MortalitySystem, DeathResolver                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 6: TEMPORAL Y ENVEJECIMIENTO                      │   │
│  │  TemporalSystem, AgingSystem                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 7: GENEALOGÍA Y EVOLUCIÓN                         │   │
│  │  GenealogySystem, AncestryQueries                       │   │
│  │  EvolutionEngine, AdoptionSystem                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FASE 8: MÉTRICAS Y OBSERVACIÓN                         │   │
│  │  MetricsSystem                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE INTERFAZ                              │
│  CLI, API REST, Exportación JSON/CSV                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentación por Sistema

### 01 - Motor de Simulación
**Archivos**: `simulation_engine.py`, `phase_scheduler.py`, `loop_controller.py`, `simulation_runner.py`, `scenario_loader.py`, `world_initializer.py`, `pending_changes.py`, `world_state.py`, `environment_context.py`

**Responsabilidad**: Orquesta el ciclo de vida completo de la simulación, gestiona las fases de ejecución, controla el bucle principal, carga escenarios, inicializa el mundo y proporciona el buffer transaccional.

📄 [Documentación completa → 01_MOTOR_SIMULACION.md](./01_MOTOR_SIMULACION.md)

---

### 02 - Estado del Mundo
**Archivos**: `world_state.py`, `pending_changes.py`, `environment_context.py`

**Responsabilidad**: Mantiene el estado autoritativo del mundo, gestiona el buffer transaccional de cambios pendientes, y proporciona contexto ambiental a los sistemas.

📄 [Documentación completa → 02_ESTADO_MUNDO.md](./02_ESTADO_MUNDO.md)

---

### 03 - Genética Universal
**Archivos**: `genome.py`, `trait.py`, `trait_library.py`, `allele.py`, `gene.py`, `species_definition.py`, `species_registry.py`, `biological_validator.py`, `realism_index.py`

**Responsabilidad**: Define el sistema genético completo con herencia mendeliana, múltiples modelos de expresión, catálogo de rasgos, registro de especies y validación biológica.

📄 [Documentación completa → 03_GENETICA.md](./03_GENETICA.md)

---

### 04 - Entorno
**Archivos**: `tile.py`, `tile_map.py`, `tile_map_initializer.py`, `world_config.py`, `biome_classifier.py`, `environment_context.py`, `environment_system.py`, `environment_dynamics.py`, `catastrophe_system.py`, `feedback_system.py`, `organism_impact.py`, `density_system.py`, `epidemiological_system.py`

**Responsabilidad**: Modela el mundo físico con terreno, clima, estaciones, biomas, catástrofes naturales, retroalimentación organismo-entorno y propagación epidemiológica.

📄 [Documentación completa → 04_ENTORNO.md](./04_ENTORNO.md)

---

### 05 - Reproducción
**Archivos**: `conception_system.py`, `gestation_system.py`, `egg_system.py`, `egg_model.py`, `reproductive_capabilities.py`

**Responsabilidad**: Gestiona el ciclo reproductivo completo: concepción, gestación (vivíparos), incubación de huevos (ovíparos), reproducción asexual, con restricciones biológicas realistas.

📄 [Documentación completa → 05_REPRODUCCION.md](./05_REPRODUCCION.md)

---

### 06 - Relaciones Sociales
**Archivos**: `compatibility_engine.py`, `marriage_system.py`, `relationship_manager.py`, `relationship_experience_engine.py`, `experience_generator.py`, `behavior_influence.py`, `narrative_engine.py`, `relationship_model.py` (incluye `BiasEngine`, `GoalFilter`)

**Responsabilidad**: Modela la red compleja de relaciones sociales emergentes: compatibilidad, formación de parejas, experiencias relacionales, narrativas, etiquetas y sesgos cognitivos.

📄 [Documentación completa → 06_RELACIONES_SOCIALES.md](./06_RELACIONES_SOCIALES.md)

---

### 07 - Movimiento
**Archivos**: `movement_system.py`, `movement_resolver.py`, `migration_system.py`, `movement_capabilities.py`

**Responsabilidad**: Gestiona el movimiento físico de agentes: decisiones tácticas (Utility AI), arbitraje de colisiones, migraciones masivas a larga distancia, con capacidades derivadas del genoma.

📄 [Documentación completa → 07_MOVIMIENTO.md](./07_MOVIMIENTO.md)

---

### 08 - Comportamiento
**Archivos**: `free_will_system.py`, `cognitive_memory_system.py`, `cognitive_capabilities.py`, `bias_engine.py` (en `relationship_model.py`)

**Responsabilidad**: Modela la vida interior de los agentes: motivaciones continuas con inhibición competitiva, memoria episódica e implícita (traumas), sesgos cognitivos, con capacidades derivadas del genoma.

📄 [Documentación completa → 08_COMPORTAMIENTO.md](./08_COMPORTAMIENTO.md)

---

### 09 - Salud
**Archivos**: `disease_system.py`, `pathogen.py`, `immunological_capabilities.py`

**Responsabilidad**: Gestiona la epidemiología completa: patógenos con identidad y mutación, fases de infección (expuesto→incubando→contagioso→sintomático→recuperándose), inmunidad innata/adaptativa, contagios por carga viral, brotes espontáneos.

📄 [Documentación completa → 09_SALUD.md](./09_SALUD.md)

---

### 10 - Mortalidad
**Archivos**: `mortality_system.py`, `death_resolver.py`

**Responsabilidad**: Calcula mortalidad multifactorial (modelo Gompertz-Makeham expandido), diagnostica causas de muerte, notifica a relaciones, y purga todas las intenciones pendientes del fallecido para coherencia transaccional.

📄 [Documentación completa → 10_MORTALIDAD.md](./10_MORTALIDAD.md)

---

### 11 - Estructura Social
**Archivos**: `social_capabilities.py`, `social_pressure.py`, `residential_nucleus.py`

**Responsabilidad**: Gestiona estructuras sociales emergentes: capacidades sociales derivadas del genoma (5 niveles de complejidad), presión social individual y ambiental, núcleos residenciales (convivencia).

📄 [Documentación completa → 11_ESTRUCTURA_SOCIAL.md](./11_ESTRUCTURA_SOCIAL.md)

---

### 12 - Genealogía
**Archivos**: `genealogy_system.py`, `ancestry_queries.py`

**Responsabilidad**: Mantiene el árbol genealógico completo (vivos y muertos), registra matrimonios/divorcios/adopciones, detecta extinciones de linajes, calcula grados de parentesco, analiza endogamia, provee estadísticas de linajes.

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

## 🔄 Flujo de Ejecución por Tick

```
TICK DE SIMULACIÓN
   │
   ├── FASE 0: TEMPORAL
   │   ├── TemporalSystem: reloj global + metabolismo basal + hitos
   │   └── AgingSystem: envejecimiento biológico multifactorial
   │
   ├── FASE 1: ENTORNO
   │   ├── EnvironmentSystem: clima y estaciones
   │   ├── EnvironmentDynamics: cambios lentos (vegetación, erosión)
   │   ├── CatastropheSystem: catástrofes naturales
   │   ├── FeedbackSystem: impacto organismo-entorno
   │   ├── DensitySystem: densidad poblacional
   │   └── EpidemiologicalSystem: propagación de patógenos
   │
   ├── FASE 2: COMPORTAMIENTO
   │   ├── CognitiveMemorySystem: decaimiento de traumas + memoria episódica
   │   └── FreeWillSystem: evolución de motivaciones + inhibición competitiva
   │
   ├── FASE 3: RELACIONES
   │   ├── RelationshipManager: detección de nuevos encuentros
   │   ├── MarriageSystem: formación de parejas
   │   ├── ExperienceGenerator: experiencias cotidianas
   │   └── RelationshipExperienceEngine: procesamiento de eventos (con BiasEngine)
   │
   ├── FASE 4: SALUD
   │   └── DiseaseSystem: progresión de infecciones + contagios + brotes
   │
   ├── FASE 5: REPRODUCCIÓN
   │   ├── ConceptionSystem: intentos de concepción
   │   ├── GestationSystem: progresión de embarazos
   │   └── EggSystem: incubación de huevos
   │
   ├── FASE 6: ESTRUCTURA SOCIAL
   │   ├── SocialPressureCalculator: presión ambiental
   │   └── AdoptionSystem: reasignación de huérfanos
   │
   ├── FASE 7: MOVIMIENTO
   │   ├── MigrationSystem: asignación de destinos migratorios
   │   ├── MovementSystem: decisiones tácticas de movimiento
   │   └── MovementResolver: arbitraje de colisiones
   │
   ├── FASE 8: MORTALIDAD
   │   ├── MortalitySystem: evaluación de riesgo de muerte
   │   └── DeathResolver: purga de intenciones de fallecidos
   │
   ├── FASE 9: GENEALOGÍA
   │   └── GenealogySystem: sincronización de árbol genealógico
   │
   ├── FASE 10: EVOLUCIÓN (observador)
   │   └── EvolutionEngine: snapshots evolutivos (si toca)
   │
   ├── FASE 11: MÉTRICAS (observador)
   │   └── MetricsSystem: snapshots multidimensionales (si toca)
   │
   └── FASE 12: COMMIT
       └── WorldState.apply_commit(): consolidar cambios pendientes
```

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

WorldState (02) ──► Todos los sistemas (lectura)
PendingChanges (02) ──► Todos los sistemas (escritura transaccional)
EnvironmentContext (02) ──► Todos los sistemas (contexto ambiental)

GenealogySystem (12) ──► AncestryQueries (12)
                      ──► EvolutionEngine (13) [fitness]
                      ──► AdoptionSystem (11) [prioridad parientes]
                      ──► MortalitySystem (10) [endogamia]
                      ──► MetricsSystem (15) [métricas genealógicas]

EvolutionEngine (13) ──► GenealogySystem (12) [descendencia]
                     ──► Genome (03) [introspección]

MetricsSystem (15) ──► GenealogySystem (12) [opcional]
                   ──► EnvironmentContext (02) [presión espacial]
```

### Flujos de datos clave

```
ConceptionSystem ──► pending.register_pregnancy_update()
                 ──► pending.new_eggs (para ovíparos)
                 ──► pending.register_birth() (para asexuales)

GestationSystem ──► pending.register_birth()
               ──► pending.register_death() (mortalidad materna)

DiseaseSystem ──► pending.register_infection()
             ──► pending.register_recovery()
             ──► pending.register_death()

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
```

---

## 📊 Estadísticas del Proyecto

| Categoría | Cantidad |
|-----------|----------|
| **Documentos de sistema** | 15 |
| **Archivos de código documentados** | ~75 |
| **Clases principales** | ~100 |
| **Tests unitarios** | ~200+ |
| **Tests de integración** | ~20+ |
| **Líneas de código** | ~15,000+ |
| **Rasgos genéticos** | 36 |
| **Especies predefinidas** | 15 |
| **Tipos de biomas** | 15 |
| **Tipos de catástrofes** | 8 |
| **Fases de infección** | 5 |
| **Motivaciones modeladas** | 7 |
| **Sesgos cognitivos** | 5 |
| **Dimensiones de métricas** | 10 |

---

## 🚀 Guía de Navegación Rápida

### Para desarrolladores nuevos

1. **Empieza por aquí**: [01_MOTOR_SIMULACION.md](./01_MOTOR_SIMULACION.md) - entiende el ciclo de vida
2. **Luego**: [02_ESTADO_MUNDO.md](./02_ESTADO_MUNDO.md) - comprende la arquitectura de datos
3. **Después**: [03_GENETICA.md](./03_GENETICA.md) - el núcleo biológico
4. **Finalmente**: Explora los sistemas específicos según tu interés

### Para entender un agente completo

1. **Genética**: [03_GENETICA.md](./03_GENETICA.md) - qué puede hacer
2. **Capacidades derivadas**: Movimiento (07), Cognición (08), Reproducción (05), Inmunidad (09), Social (11)
3. **Comportamiento**: [08_COMPORTAMIENTO.md](./08_COMPORTAMIENTO.md) - qué decide hacer
4. **Movimiento**: [07_MOVIMIENTO.md](./07_MOVIMIENTO.md) - cómo se desplaza
5. **Relaciones**: [06_RELACIONES_SOCIALES.md](./06_RELACIONES_SOCIALES.md) - con quién interactúa
6. **Salud**: [09_SALUD.md](./09_SALUD.md) - cómo enferma y se recupera
7. **Muerte**: [10_MORTALIDAD.md](./10_MORTALIDAD.md) - cómo y por qué muere

### Para analizar la simulación

1. **Métricas**: [15_METRICAS.md](./15_METRICAS.md) - observación multidimensional
2. **Evolución**: [13_EVOLUCION.md](./13_EVOLUCION.md) - análisis macroevolutivo
3. **Genealogía**: [12_GENEALOGIA.md](./12_GENEALOGIA.md) - árboles familiares y linajes

### Para modificar el mundo

1. **Entorno**: [04_ENTORNO.md](./04_ENTORNO.md) - terreno, clima, catástrofes
2. **Temporal**: [14_TEMPORAL.md](./14_TEMPORAL.md) - tiempo y envejecimiento
3. **Estructura social**: [11_ESTRUCTURA_SOCIAL.md](./11_ESTRUCTURA_SOCIAL.md) - presión social y núcleos

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

### Patrones arquitectónicos

- **Fase de proceso**: Cada sistema implementa `process(state, pending, delta_days, context)`
- **Buffer transaccional**: `PendingChanges` acumula cambios, `WorldState.apply_commit()` los consolida
- **Capacidades inmutables**: Se derivan del genoma una vez y no cambian
- **Eventos relacionales ligeros**: Dataclasses simples para comunicación entre sistemas
- **Introspección dinámica**: Detección automática de propiedades numéricas en `Genome`

---

## 🔮 Extensiones Futuras Planificadas

### Corto plazo (próximos documentos)
- [ ] **Interfaz/API**: Documentación de CLI y API REST
- [ ] **Visualización**: Integración con Godot/frontend
- [ ] **Escenarios predefinidos**: Catálogo de escenarios y casos de uso

### Medio plazo (nuevos sistemas)
- [ ] **Clima regional**: Frentes meteorológicos que se mueven
- [ ] **Economía**: Recursos intercambiables, comercio, dinero
- [ ] **Cultura**: Transmisión de conocimientos, rituales, tradiciones
- [ ] **Tecnología**: Invenciones, herramientas, progreso tecnológico
- [ ] **Política**: Liderazgo, facciones, conflictos grupales
- [ ] **Religión**: Creencias, rituales, instituciones religiosas

### Largo plazo (visiones ambiciosas)
- [ ] **Multi-especie inteligente**: Diferentes especies con culturas propias
- [ ] **Civilizaciones**: Ciudades, estados, imperios
- [ ] **Guerras**: Conflictos a gran escala entre grupos
- [ ] **Comercio internacional**: Rutas comerciales, economía global
- [ ] **Exploración**: Descubrimiento de nuevas tierras
- [ ] **Extinciones masivas**: Eventos catastróficos globales

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

---

## 🙏 Créditos y Agradecimientos

Este simulador es un proyecto de investigación en sistemas complejos, vida artificial y emergencia de comportamiento inteligente. Agradecemos a:

- La comunidad de vida artificial (ALife)
- Investigadores en sistemas multi-agente
- Estudios de etología y comportamiento animal
- Teoría de juegos y evolución cultural
- Epidemiología matemática
- Genética de poblaciones

---

## 📞 Contacto y Contribuciones

Para preguntas, sugerencias o contribuciones:

- **Issues**: Reportar bugs o solicitar features
- **Pull Requests**: Contribuciones de código y documentación
- **Discusiones**: Debates sobre diseño y arquitectura
- **Documentación**: Mejoras y correcciones a esta documentación

---

*Documento: 00_INDICE.md*
*Versión: 1.0*
*Última actualización: Agosto 2026*