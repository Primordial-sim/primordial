# 04 - Entorno

## 📋 Resumen

El **Sistema de Entorno** modela el mundo físico donde viven los agentes: el terreno, el clima, los biomas, las catástrofes naturales, los hábitats por especie, y el ciclo de retroalimentación entre los organismos y su entorno. Es la capa geológica, meteorológica y ecológica del simulador.

**Filosofía fundamental**: *El entorno es un resultado emergente. Los biomas emergen de variables físicas, no se asignan manualmente. Las catástrofes no son errores del sistema, son el motor de la transformación del mundo.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Generar el mapa físico del mundo proceduralmente (`TileMapInitializer`)
- Almacenar las variables ambientales de cada tile (`Tile`, `TileMap`)
- Clasificar biomas emergentes a partir de variables (`BiomeClassifier`)
- Gestionar el clima y las estaciones (`EnvironmentSystem`)
- Procesar cambios lentos del terreno: erosión, vegetación (`EnvironmentDynamics`)
- Simular catástrofes naturales: terremotos, inundaciones, incendios (`CatastropheSystem`)
- Modelar eventos catastróficos con tipos y severidades (`CatastropheEvent`)
- Definir preferencias ecológicas por especie (`HabitatPreference`)
- Calcular compatibilidad entre especies y tiles (`HabitatCompatibility`)
- Calcular el impacto de los organismos sobre su entorno (`OrganismImpact`, `FeedbackSystem`)
- Proveer contexto ambiental a los agentes (`EnvironmentContext`)
- Calcular densidad poblacional local (`DensitySystem`)
- Definir la configuración física del mundo (`WorldConfig`)

**NO es responsable de:**
- ❌ Decidir el comportamiento de los agentes (eso lo hacen las capacidades)
- ❌ Almacenar la información genética (eso lo hace `Genome`)
- ❌ Gestionar relaciones sociales (eso lo hacen los sistemas sociales)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`)
- ❌ Propagar cargas virales entre agentes (eso lo hace `EpidemiologicalSystem`, doc 09)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Tile** | Una parcela de terreno (1 km²) | Celda ambiental |
| **TileMap** | El mapa completo del planeta | Cartografía |
| **Biome** | Ecosistema natural (bosque, desierto, tundra) | Bioma ecológico |
| **Height** | Altitud sobre el nivel del mar | Metros |
| **Temperature** | Temperatura ambiental | [0.0-1.0] |
| **Water** | Presencia de agua superficial | [0.0-1.0] |
| **Vegetation** | Cobertura vegetal | [0.0-1.0] |
| **Fertility** | Calidad del suelo | [0.0-1.0] |
| **Season** | Estación del año | Primavera/Verano/Otoño/Invierno |
| **Weather** | Estado meteorológico | Despejado/Lluvioso/Tormenta/Sequía/Ventisca |
| **Catastrophe** | Desastre natural | Terremoto/Inundación/Incendio/Meteorito |
| **CatastropheSeverity** | Magnitud del desastre | Escala de Richter / Beaufort |
| **HabitatPreference** | Nicho ecológico de la especie | Condiciones óptimas |
| **HabitatCompatibility** | Adecuación del hábitat | Idoneidad [0.0-1.0] |
| **Urbanization** | Grado de desarrollo humano | [0.0-1.0] |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/environment/tile.py` | `Tile` | Celda ambiental individual |
| `systems/environment/tile_map.py` | `TileMap` | Colección de tiles |
| `systems/environment/tile_map_initializer.py` | `TileMapInitializer` | Generación procedural |
| `systems/environment/world_config.py` | `WorldConfig` | Configuración física del mundo |
| `systems/environment/biome_classifier.py` | `BiomeClassifier`, `Biome` | Clasificación de biomas |
| `systems/environment/environment_context.py` | `EnvironmentContext` | Contexto ambiental para agentes |
| `systems/environment/environment_system.py` | `EnvironmentSystem`, `Season`, `Weather` | Clima y estaciones |
| `systems/environment/environment_dynamics.py` | `EnvironmentDynamics` | Cambios lentos del entorno |
| `systems/environment/catastrophe_model.py` | `CatastropheEvent`, `CatastropheType`, `CatastropheSeverity` | Modelos de datos de catástrofes |
| `systems/environment/catastrophe_system.py` | `CatastropheSystem` | Simulación de catástrofes naturales |
| `systems/environment/feedback_system.py` | `FeedbackSystem` | Retroalimentación organismo-entorno |
| `systems/environment/organism_impact.py` | `OrganismImpactCalculator`, `TileImpact` | Impacto de organismos |
| `systems/environment/density_system.py` | `DensitySystem` | Densidad poblacional |
| `systems/environment/habitat_preference.py` | `HabitatPreference` | Preferencias ecológicas por especie |
| `systems/environment/habitat_compatibility.py` | `HabitatCompatibility` | Cálculo de compatibilidad hábitat-especie |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              FASE DE INICIALIZACIÓN (una vez al inicio)         │
│                                                                 │
│ 1. WorldConfig define parámetros físicos:                       │
│    ├── geological_activity (actividad tectónica)                │
│    ├── water_coverage (cobertura de agua)                       │
│    ├── mean_temperature (temperatura media)                     │
│    ├── global_humidity (humedad global)                         │
│    └── erosion_rate (tasa de erosión)                           │
│                                                                 │
│ 2. TileMapInitializer genera el mapa procedural:                │
│    ├── Generar height_field con ruido de Perlin                 │
│    ├── Calcular temperature basado en latitud/altitud           │
│    ├── Calcular water basado en height_field                    │
│    ├── Calcular vegetation según condiciones                    │
│    └── Calcular fertility según organic_matter                  │
│                                                                 │
│ 3. BiomeClassifier clasifica cada tile según sus variables     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE DE EJECUCIÓN (cada tick)                      │
│                                                                 │
│ 1. EnvironmentSystem:                                           │
│    ├── Avanzar reloj climático                                  │
│    ├── Cambiar de estación cada 90 días                         │
│    └── Actualizar clima (aleatorio según estación)              │
│                                                                 │
│ 2. EnvironmentDynamics:                                         │
│    ├── Escala rápida: catástrofes (delegado a CatastropheSystem)│
│    ├── Escala media: vegetación y fertilidad (cada 15 días)     │
│    └── Escala lenta: erosión y sedimentación (cada 180 días)   │
│                                                                 │
│ 3. CatastropheSystem (escala rápida):                           │
│    ├── Evaluar probabilidades de cada tipo de catástrofe        │
│    ├── Escalar probabilidades por WorldConfig y estación        │
│    ├── Crear CatastropheEvent con severidad calculada           │
│    └── Ejecutar efectos sobre los tiles                         │
│                                                                 │
│ 4. FeedbackSystem (cada 5 días):                                │
│    ├── Calcular impacto de cada organismo en su tile            │
│    ├── Acumular impactos por coordenada                         │
│    └── Aplicar cambios a los tiles                              │
│                                                                 │
│ 5. DensitySystem:                                               │
│    └── Calcular densidad poblacional por sector                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE DE CONSULTA (bajo demanda)                    │
│                                                                 │
│ 1. BiomeClassifier.classify(tile) → Biome                       │
│ 2. HabitatCompatibility.calculate(tile, preference) → score     │
│ 3. EnvironmentContext.get_resources_at(x, y) → resources        │
│ 4. EnvironmentContext.get_local_pressure(x, y) → pressure       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. Tile - Celda Ambiental

**📁 Archivo**: `systems/environment/tile.py`
**🌍 Equivalencia real**: Una parcela de terreno de aproximadamente 1 km² con todas sus características físicas.

#### Atributos

| Atributo | Tipo | Rango | Equivalencia real |
|----------|------|-------|-------------------|
| `height` | `float` | -500 a 3000 m | Altitud sobre el nivel del mar |
| `slope` | `float` | 0.0-1.0 | Pendiente del terreno |
| `temperature` | `float` | 0.0-1.0 | Temperatura ambiental |
| `humidity` | `float` | 0.0-1.0 | Humedad del aire |
| `water` | `float` | 0.0-1.0 | Presencia de agua superficial |
| `salinity` | `float` | 0.0-1.0 | Salinidad del agua |
| `fertility` | `float` | 0.0-1.0 | Calidad del suelo |
| `vegetation` | `float` | 0.0-1.0 | Cobertura vegetal |
| `organic_matter` | `float` | 0.0-1.0 | Materia orgánica |
| `rockiness` | `float` | 0.0-1.0 | Rococidad del terreno |
| `urbanization` | `float` | 0.0-1.0 | Grado de urbanización |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `normalize()` | Clampear todos los valores a [0.0, 1.0] |
| `to_dict()` | Serializar para debugging/export |

#### Ejemplos

```python
tile = Tile(
    height=500.0,
    temperature=0.6,
    water=0.2,
    vegetation=0.7,
    fertility=0.8,
)
tile.normalize()
print(tile.to_dict())
```

---

### 2. TileMap - Colección de Tiles

**📁 Archivo**: `systems/environment/tile_map.py`
**🌍 Equivalencia real**: El mapa completo del planeta, compuesto por todas las parcelas.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `width` | `int` | Ancho del mapa en tiles |
| `height` | `int` | Alto del mapa en tiles |
| `tiles` | `Dict[Tuple[int, int], Tile]` | Diccionario de tiles |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `get_tile_at(x, y)` | Obtener tile por coordenadas |
| `get_tile_count()` | Número total de tiles |
| `get_all_tiles()` | Todos los tiles |
| `set_tile(x, y, tile)` | Establecer un tile |

#### Ejemplos

```python
tile_map = TileMap(width=100, height=100)
tile = tile_map.get_tile_at(50, 50)
total_tiles = tile_map.get_tile_count()  # 10000
```

---

### 3. TileMapInitializer - Generación Procedural

**📁 Archivo**: `systems/environment/tile_map_initializer.py`
**🌍 Equivalencia real**: Los procesos geológicos que forman un planeta: tectónica, erosión, clima.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `width` | `int` | Ancho del mapa |
| `height` | `int` | Alto del mapa |
| `world_config` | `WorldConfig` | Configuración física |
| `seed` | `int` | Semilla para reproducibilidad |

#### Salidas

| Salida | Tipo | Descripción |
|--------|------|-------------|
| `TileMap` | Objeto | Mapa generado |

#### Flujo interno

```
initialize(width, height, world_config, seed)
    │
    ├── 1. Generar height_field con ruido de Perlin
    │   └── Escalar por geological_activity
    │
    ├── 2. Calcular temperature_field
    │   └── Base: latitud + altitud + mean_temperature
    │
    ├── 3. Calcular water_field
    │   └── Basado en height (bajo = océano, alto = seco)
    │   └── Escalar por water_coverage
    │
    ├── 4. Calcular vegetation_field
    │   └── Función de (temperature, water, fertility)
    │
    ├── 5. Calcular fertility_field
    │   └── Basado en organic_matter y proximity al agua
    │
    └── 6. Crear TileMap con todos los tiles
```

#### Ejemplos

```python
initializer = TileMapInitializer()
world_config = WorldConfig(
    geological_activity=0.5,
    water_coverage=0.6,
    mean_temperature=0.5,
)

tile_map = initializer.initialize(
    width=100,
    height=100,
    world_config=world_config,
    seed=42,  # Reproducible
)
```

#### Consideraciones

- Usa **ruido de Perlin** para generar terrenos realistas
- La semilla garantiza reproducibilidad (mismo seed = mismo mapa)
- `geological_activity` alto = más montañas, más terremotos
- `water_coverage` alto = más océanos, menos tierra
- El mapa es determinista con la misma semilla

---

### 4. WorldConfig - Configuración Física

**📁 Archivo**: `systems/environment/world_config.py`
**🌍 Equivalencia real**: Las constantes físicas del planeta (gravedad, composición atmosférica, actividad tectónica).

#### Atributos

| Atributo | Tipo | Rango | Equivalencia real | Default |
|----------|------|-------|-------------------|---------|
| `geological_activity` | `float` | 0.0-1.0 | Actividad tectónica | 0.5 |
| `water_coverage` | `float` | 0.0-1.0 | % de agua superficial | 0.6 |
| `mean_temperature` | `float` | 0.0-1.0 | Temperatura media | 0.5 |
| `global_humidity` | `float` | 0.0-1.0 | Humedad atmosférica | 0.5 |
| `erosion_rate` | `float` | 0.0-1.0 | Velocidad de erosión | 0.3 |
| `wind_intensity` | `float` | 0.0-1.0 | Intensidad del viento | 0.4 |
| `solar_intensity` | `float` | 0.0-1.0 | Radiación solar | 0.7 |
| `atmospheric_density` | `float` | 0.0-1.0 | Densidad atmosférica | 0.8 |
| `gravity` | `float` | 0.0-2.0 | Gravedad relativa | 1.0 |
| `tectonic_plates` | `int` | 1-50 | Número de placas | 8 |

#### Ejemplos

```python
# Planeta como la Tierra
earth = WorldConfig(
    water_coverage=0.71,
    mean_temperature=0.5,
    geological_activity=0.4,
    gravity=1.0,
)

# Planeta desértico tipo Marte
mars = WorldConfig(
    water_coverage=0.05,
    mean_temperature=0.3,
    geological_activity=0.1,
    gravity=0.38,
    atmospheric_density=0.01,
)

# Planeta oceánico
waterworld = WorldConfig(
    water_coverage=0.95,
    geological_activity=0.8,
    mean_temperature=0.6,
)
```

---

### 5. BiomeClassifier - Clasificación de Biomas

**📁 Archivo**: `systems/environment/biome_classifier.py`
**🌍 Equivalencia real**: Un ecólogo que clasifica ecosistemas basándose en variables ambientales observables.

#### Tipos de biomas (enum `Biome`)

| Bioma | Condiciones principales | Equivalencia real |
|-------|------------------------|-------------------|
| `OCEAN` | water > 0.7, height < 0 | Océano abierto |
| `DEEP_OCEAN` | water > 0.9, height < -200 | Abismo oceánico |
| `LAKE` | water > 0.7, height > 0 | Lago interior |
| `BEACH` | water 0.5-0.7, height ~0 | Costa |
| `DESERT` | temperature > 0.8, water < 0.2 | Desierto |
| `SAVANNA` | temperature alto, water medio | Sabana |
| `GRASSLAND` | temperature medio, water medio | Pradera |
| `FOREST` | vegetation > 0.6 | Bosque |
| `RAINFOREST` | vegetation > 0.8, humidity > 0.7 | Selva tropical |
| `TUNDRA` | temperature < 0.3 | Tundra |
| `TAIGA` | temperature bajo, vegetation alto | Bosque boreal |
| `MOUNTAIN` | height > 1500 | Montaña |
| `SNOW_PEAK` | height > 2500, temperature < 0.2 | Pico nevado |
| `WETLAND` | water 0.5-0.7, vegetation alto | Humedal |
| `URBAN` | urbanization > 0.7 | Zona urbana |

#### Reglas de clasificación (orden de prioridad)

```
1. urbanization > 0.7         → URBAN
2. water > 0.9, height < -200 → DEEP_OCEAN
3. water > 0.7, height < 0    → OCEAN
4. water > 0.7, height > 0    → LAKE
5. temperature < 0.2          → TUNDRA/SNOW_PEAK
6. temperature > 0.8, water<0.2 → DESERT
7. vegetation > 0.8, humidity>0.7 → RAINFOREST
8. vegetation > 0.6           → FOREST
9. height > 1500              → MOUNTAIN
10. default                    → GRASSLAND
```

#### Ejemplos

```python
tile = Tile(water=0.85, height=-300, temperature=0.4)
biome = BiomeClassifier.classify(tile)
print(biome)  # Biome.OCEAN

name = BiomeClassifier.get_biome_name(biome)
print(name)  # "Océano"
```

#### Consideraciones

- La clasificación es **emergente**: depende solo de las variables del tile
- Si las variables cambian (p.ej. sequía), el bioma puede cambiar
- `URBAN` es el único bioma "artificial" (creado por humanos)
- El orden de las reglas es crítico: una regla anterior tiene prioridad

---

### 6. EnvironmentContext - Contexto Ambiental

**📁 Archivo**: `systems/environment/environment_context.py`
**🌍 Equivalencia real**: Lo que un organismo puede percibir de su entorno inmediato.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `config` | `SimulationConfig` | Configuración |
| `current_season` | `Season` | Estación actual |
| `current_weather` | `Weather` | Clima actual |
| `sector_map` | `Dict` | Mapa de sectores |
| `pressure_map` | `Dict` | Mapa de presión social |

#### Métodos de consulta

| Método | Retorno | Descripción |
|--------|---------|-------------|
| `get_tile_at(x, y)` | `Tile` | Tile en coordenadas |
| `get_biome_at(x, y)` | `Biome` | Bioma en coordenadas |
| `get_biome_name_at(x, y)` | `str` | Nombre del bioma |
| `get_local_pressure(x, y)` | `float` | Presión poblacional local |
| `get_resources_at(x, y)` | `dict` | Recursos disponibles |
| `has_tile_map()` | `bool` | ¿Hay mapa de tiles? |

#### Ejemplos

```python
context = EnvironmentContext(state=state, config=config)

# Consultar entorno
biome = context.get_biome_at(50, 50)
print(f"Bioma: {context.get_biome_name_at(50, 50)}")

# Consultar presión social
pressure = context.get_local_pressure(50, 50)
if pressure > 0.8:
    print("Zona superpoblada")
```

---

### 7. EnvironmentSystem - Clima y Estaciones

**📁 Archivo**: `systems/environment/environment_system.py`
**🌍 Equivalencia real**: El sistema climático del planeta: estaciones, clima, patrones meteorológicos.

#### Enumeraciones

**Season (estaciones):**
- `SPRING` - Primavera
- `SUMMER` - Verano
- `AUTUMN` - Otoño
- `WINTER` - Invierno

**Weather (clima):**
- `CLEAR` - Despejado
- `RAINY` - Lluvioso
- `STORMY` - Tormentoso
- `DROUGHT` - Sequía
- `BLIZZARD` - Ventisca

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `current_season` | `Season` | Estación actual |
| `current_weather` | `Weather` | Clima actual |
| `days_in_current_season` | `float` | Días en la estación actual |
| `season_duration_days` | `float` | Duración de cada estación (default: 90) |
| `dynamics` | `EnvironmentDynamics` | Subsistema de dinámica |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── 1. Avanzar reloj de estaciones
    │   └── days_in_current_season += delta_days
    │   └── Si ≥ 90 días → _advance_season()
    │
    ├── 2. Actualizar clima
    │   └── _update_weather_placeholder(delta_days)
    │
    ├── 3. Inyectar en contexto
    │   └── context.current_season = self.current_season
    │   └── context.current_weather = self.current_weather
    │
    └── 4. Delegar a EnvironmentDynamics
        └── self.dynamics.process(state, delta_days, ...)
```

#### Transiciones de clima por estación

| Estación | Climas posibles |
|----------|-----------------|
| SPRING | CLEAR, RAINY, STORMY |
| SUMMER | CLEAR, DROUGHT |
| AUTUMN | CLEAR, RAINY, STORMY |
| WINTER | CLEAR, RAINY, BLIZZARD |

#### Ejemplos

```python
env_system = EnvironmentSystem(config)
env_system.process(state, pending, delta_days=1.0, context=context)

print(env_system.current_season)   # Season.SPRING
print(env_system.current_weather)  # Weather.CLEAR
```

---

### 8. EnvironmentDynamics - Cambios Lentos

**📁 Archivo**: `systems/environment/environment_dynamics.py`
**🌍 Equivalencia real**: Los procesos geológicos y ecológicos lentos: erosión, crecimiento vegetal, sucesión ecológica.

#### Tres escalas temporales

| Escala | Intervalo | Procesos |
|--------|-----------|----------|
| **Rápida** | Cada tick | Catástrofes (delegado a CatastropheSystem) |
| **Media** | Cada 15 días | Crecimiento vegetal, materia orgánica, fertilidad |
| **Lenta** | Cada 180 días | Erosión, sedimentación |

#### Flujo interno

```
process(state, delta_days, current_season, current_weather)
    │
    ├── Escala RÁPIDA (cada tick)
    │   └── catastrophe_system.process(...)
    │       └── Evalúa y ejecuta catástrofes
    │
    ├── Escala MEDIA (cada 15 días)
    │   └── _process_medium_scale(state, current_season)
    │       ├── Crecimiento vegetal (si hay agua, temp, fertilidad)
    │       ├── Decaimiento vegetal (si condiciones desfavorables)
    │       ├── Acumulación de materia orgánica
    │       └── Cambios en fertilidad
    │
    └── Escala LENTA (cada 180 días)
        └── _process_slow_scale(state)
            ├── Erosión en pendientes altas
            └── Sedimentación en zonas bajas cercanas al agua
```

#### Reglas de escala media

```python
# Crecimiento vegetal
if water > 0.2 and temperature > 0.2 and fertility > 0.3:
    growth_potential = (water + temperature + fertility) / 3
    growth_rate = growth_potential * 0.05 * seasonal_factor
    tile.vegetation = min(1.0, tile.vegetation + growth_rate)

# Decaimiento vegetal
elif vegetation > 0.1:
    tile.vegetation = max(0.0, tile.vegetation - 0.02)
```

#### Factor estacional

| Estación | Factor de crecimiento |
|----------|----------------------|
| SPRING | 1.5 |
| SUMMER | 1.2 |
| AUTUMN | 0.8 |
| WINTER | 0.3 |

#### Reglas de escala lenta

```python
# Erosión en pendientes
if slope > 0.3 and height > 100.0:
    erosion_rate = slope * 5.0
    if vegetation > 0.5:
        erosion_rate *= 0.3  # La vegetación protege
    tile.height = max(0.0, tile.height - erosion_rate)

# Sedimentación cerca del agua
if height < 50.0 and water > 0.3:
    tile.height = min(200.0, tile.height + 2.0)
```

---

### 8.5. CatastropheEvent - Modelo de Datos de Catástrofes

**📁 Archivo**: `systems/environment/catastrophe_model.py`
**🌍 Equivalencia real**: El registro histórico de un desastre natural, con todos sus metadatos para análisis posterior.

#### Tipos de catástrofe (enum `CatastropheType`)

| Tipo | Valor | Descripción |
|------|-------|-------------|
| `EARTHQUAKE` | Terremoto | Actividad sísmica |
| `VOLCANIC_ERUPTION` | Erupción volcánica | Actividad volcánica |
| `FLOOD` | Inundación | Exceso de agua |
| `METEORITE` | Impacto de meteorito | Evento extraterrestre |
| `FIRE` | Incendio | Destrucción por fuego |
| `DROUGHT` | Sequía | Falta prolongada de agua |
| `STORM` | Tormenta / huracán | Evento meteorológico extremo |
| `LANDSLIDE` | Deslizamiento de tierra | Movimiento de masas |

#### Niveles de severidad (enum `CatastropheSeverity`)

| Nivel | Umbral de intensidad | Descripción |
|-------|---------------------|-------------|
| `MINOR` | < 0.35 | Efectos locales |
| `MODERATE` | 0.35 - 0.60 | Efectos regionales |
| `MAJOR` | 0.60 - 0.85 | Efectos extensos |
| `CATASTROPHIC` | ≥ 0.85 | Efectos masivos |

#### Estructura de `CatastropheEvent`

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `event_id` | `int` | Identificador único (auto-generado) |
| `catastrophe_type` | `CatastropheType` | Tipo de catástrofe |
| `severity` | `CatastropheSeverity` | Nivel de severidad |
| `epicenter_x`, `epicenter_y` | `int` | Coordenadas del epicentro |
| `radius` | `int` | Radio de efecto en tiles |
| `intensity` | `float` | Intensidad [0.0, 1.0] |
| `occurred_day` | `float` | Día simulado en que ocurrió |
| `tiles_affected` | `int` | Número de tiles afectados |
| `description` | `str` | Descripción legible |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `to_dict()` | Serializa para logging o exportación |
| `severity_from_intensity(intensity)` | Determina severidad desde intensidad |
| `generate_catastrophe_id()` | Genera ID único incremental |

#### Ejemplos

```python
from systems.environment.catastrophe_model import (
    CatastropheEvent, CatastropheType, severity_from_intensity,
    generate_catastrophe_id
)

# Crear evento
event = CatastropheEvent(
    event_id=generate_catastrophe_id(),
    catastrophe_type=CatastropheType.EARTHQUAKE,
    severity=severity_from_intensity(0.75),  # MAJOR
    epicenter_x=50,
    epicenter_y=50,
    radius=10,
    intensity=0.75,
    occurred_day=365.0,
    tiles_affected=314,
    description="Terremoto de magnitud alta en (50, 50)"
)

print(event)
# [MAJOR] EARTHQUAKE en (50, 50) radio=10, intensidad=0.75, tiles=314

# Serializar para logging
print(event.to_dict())
```

---

### 9. CatastropheSystem - Simulación de Catástrofes Naturales

**📁 Archivo**: `systems/environment/catastrophe_system.py`
**🌍 Equivalencia real**: Los desastres naturales que moldean el planeta: terremotos, erupciones, inundaciones, incendios, meteoritos.

#### Probabilidades base diarias

| Catástrofe | Probabilidad base |
|------------|-------------------|
| EARTHQUAKE | 0.0001 |
| VOLCANIC_ERUPTION | 0.00005 |
| FLOOD | 0.0005 |
| METEORITE | 0.00001 |
| FIRE | 0.001 |
| DROUGHT | 0.0005 |
| STORM | 0.0008 |
| LANDSLIDE | 0.0003 |

#### Escalado por estación

| Catástrofe | Primavera | Verano | Otoño | Invierno |
|------------|-----------|--------|-------|----------|
| FIRE | x1 | x3 | x1 | x0.1 |
| DROUGHT | x1 | x2.5 | x1 | x0.2 |
| STORM | x1.5 | x1 | x2 | x1 |
| FLOOD | x2 (deshielo) | x1 | x1 | x1 |

#### Efectos específicos por tipo

**EARTHQUAKE:**
```python
height_change = random.uniform(-50, 30) * effect
tile.slope = min(1.0, tile.slope + effect * 0.5)
tile.rockiness = min(1.0, tile.rockiness + effect * 0.3)
tile.vegetation = max(0.0, tile.vegetation - effect * 0.4)
```

**VOLCANIC_ERUPTION:**
- Zona cercana (30% del radio): destrucción total, lava, +height
- Zona externa: ceniza fertilizante (+fertility, +organic_matter)

**METEORITE:**
- Cráter (40% del radio): destrucción total, -height grande
- Zona externa: destrucción severa

**FLOOD:**
- Solo afecta height < 200
- +water, +humidity, -height si hay pendiente

---

### 10. FeedbackSystem - Retroalimentación Organismo-Entorno

**📁 Archivo**: `systems/environment/feedback_system.py`
**🌍 Equivalencia real**: El impacto ecológico de los seres vivos sobre su entorno: las plantas crean suelo fértil, los herbívoros reducen vegetación, los humanos urbanizan.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `impact_calculator` | `OrganismImpactCalculator` | Calculadora de impactos |
| `process_interval` | `float` | Intervalo de procesamiento (5 días) |
| `impact_scale` | `float` | Factor de escala global |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── Si no han pasado 5 días → return
    │
    ├── persons = state.get_all_persons()
    ├── accumulated = impact_calculator.calculate_accumulated(persons, tile_map)
    │
    └── Para cada (x, y), impact en accumulated:
        ├── tile = state.get_tile_at(x, y)
        └── _apply_impact(tile, impact)
```

---

### 11. OrganismImpactCalculator - Impacto de Organismos

**📁 Archivo**: `systems/environment/organism_impact.py`
**🌍 Equivalencia real**: La huella ecológica de cada organismo sobre su entorno inmediato.

#### TileImpact (deltas a aplicar)

| Delta | Rango | Descripción |
|-------|-------|-------------|
| `vegetation_delta` | [-0.1, 0.1] | Cambio en vegetación |
| `organic_matter_delta` | [-0.1, 0.1] | Cambio en materia orgánica |
| `fertility_delta` | [-0.1, 0.1] | Cambio en fertilidad |
| `water_delta` | [-0.1, 0.1] | Cambio en agua |
| `humidity_delta` | [-0.1, 0.1] | Cambio en humedad |
| `height_delta` | [-5.0, 5.0] | Cambio en altura |
| `slope_delta` | [-0.1, 0.1] | Cambio en pendiente |
| `temperature_delta` | [-0.1, 0.1] | Cambio en temperatura |
| `urbanization_delta` | [-0.1, 0.1] | Cambio en urbanización |

#### Impactos por tipo de organismo

| Organismo | Rasgos clave | Impacto |
|-----------|--------------|---------|
| **Plantas** | `photosynthesis > 0.5` | +vegetation, +organic_matter, +fertility, -water |
| **Herbívoros** | `heterotrophy > 0.5`, `speed` | -vegetation, +erosión |
| **Humanos** | `intelligence > 1.0`, `sociability > 0.8` | -vegetation, +fertility (agricultura), +urbanization |
| **Hongos** | `growth_rate > 1.0` | -organic_matter, +fertility (descomposición) |
| **Acuáticos** | `swimming > 1.0` | +water, -height (erosión acuática) |
| **Aves** | `flight > 1.0` | +vegetation en áreas nuevas (dispersión de semillas) |

---

### 12. DensitySystem - Densidad Poblacional

**📁 Archivo**: `systems/environment/density_system.py`
**🌍 Equivalencia real**: La densidad de población en diferentes regiones, usada para calcular presión social y migraciones.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `sector_size` | `int` | Tamaño de sector (default: 10) |

#### Salidas

| Salida | Tipo | Descripción |
|--------|------|-------------|
| `sector_map` | `Dict[Tuple, int]` | Agentes por sector |

#### Ejemplos

```python
density_system = DensitySystem(sector_size=10)
sector_map = density_system.calculate(state)

agents_in_sector = sector_map.get((5, 5), 0)
print(f"Agentes en sector (5,5): {agents_in_sector}")
```

---

### 13. HabitatPreference - Preferencias Ecológicas por Especie

**📁 Archivo**: `systems/environment/habitat_preference.py`
**🌍 Equivalencia real**: El nicho ecológico de una especie: las condiciones ambientales que necesita para prosperar.

#### Estructura de `HabitatPreference`

Cada preferencia tiene un **valor ideal** [0.0, 1.0] y una **tolerancia** [0.0, 1.0]:

| Variable | Ideal [0-1] | Tolerancia [0-1] | Descripción |
|----------|-------------|------------------|-------------|
| `temperature_ideal` / `_tolerance` | Temperatura | Frío (0) ↔ Calor (1) |
| `humidity_ideal` / `_tolerance` | Humedad | Árido (0) ↔ Saturado (1) |
| `water_ideal` / `_tolerance` | Nivel de agua | Seco (0) ↔ Acuático (1) |
| `vegetation_ideal` / `_tolerance` | Vegetación | Desierto (0) ↔ Selva (1) |
| `altitude_ideal` / `_tolerance` | Altitud | Nivel del mar (0) ↔ Montaña (1) |
| `slope_ideal` / `_tolerance` | Pendiente | Plano (0) ↔ Acantilado (1) |
| `fertility_ideal` / `_tolerance` | Fertilidad | Estéril (0) ↔ Fértil (1) |
| `salinity_ideal` / `_tolerance` | Salinidad | Dulce (0) ↔ Salado (1) |
| `rockiness_ideal` / `_tolerance` | Rococidad | Suelo (0) ↔ Rocas (1) |

#### Presets por especie (funciones factory)

| Función | Especie | Características principales |
|---------|---------|----------------------------|
| `create_human_habitat()` | Humano | Llanuras templadas, agua cercana, fertilidad alta |
| `create_fish_habitat()` | Pez | Agua muy alta (0.9), tolerancia amplia a salinidad |
| `create_bird_habitat()` | Aves | Áreas abiertas, vegetación moderada |
| `create_goat_habitat()` | Cabras | Montañoso, pendiente alta, rocoso |
| `create_pine_habitat()` | Pinos | Frío, suelos pobres |
| `create_desert_plant_habitat()` | Plantas desérticas | Calor extremo, poca agua |
| `create_aquatic_plant_habitat()` | Plantas acuáticas | Mucha agua, poca pendiente |
| `create_fungus_habitat()` | Hongos | Humedad alta, materia orgánica |
| `create_bacteria_habitat()` | Bacterias | Muy tolerante a todo |

#### Registro de presets

```python
HABITAT_PRESETS = {
    'human': create_human_habitat,
    'fish': create_fish_habitat,
    'bird': create_bird_habitat,
    'goat': create_goat_habitat,
    'pine': create_pine_habitat,
    'desert_plant': create_desert_plant_habitat,
    'aquatic_plant': create_aquatic_plant_habitat,
    'fungus': create_fungus_habitat,
    'bacteria': create_bacteria_habitat,
}
```

#### Ejemplos

```python
from systems.environment.habitat_preference import (
    create_human_habitat, HABITAT_PRESETS
)

# Obtener preferencia de humano
human_pref = create_human_habitat()
# o desde el registro: HABITAT_PRESETS['human']()

# Ver características
print(human_pref.temperature_ideal)  # 0.5 (templado)
print(human_pref.water_ideal)        # 0.3 (acceso a agua)
print(human_pref.fertility_ideal)    # 0.7 (suelo fértil)
```

#### Consideraciones

- Las preferencias **NO definen biomas directamente**, solo rangos de variables
- La tolerancia indica cuánto puede desviarse el ambiente del ideal
- Los presets son funciones factory, no instancias (se llaman para crear)
- Se pueden crear preferencias personalizadas para especies nuevas

---

### 14. HabitatCompatibility - Cálculo de Compatibilidad

**📁 Archivo**: `systems/environment/habitat_compatibility.py`
**🌍 Equivalencia real**: Un ecólogo que evalúa qué tan adecuado es un lugar específico para una especie concreta.

#### Algoritmo de compatibilidad

Usa una **función gaussiana ponderada** para cada variable:

```
score_variable = exp(-((actual - ideal) / tolerance)²)
```

- Si `actual == ideal` → score = 1.0
- Si `|actual - ideal| == tolerance` → score ≈ 0.37
- Si `|actual - ideal| == 2 * tolerance` → score ≈ 0.018

#### Pesos por variable

| Variable | Peso | Justificación |
|----------|------|---------------|
| Temperatura | 1.5 | Crítico para metabolismo |
| Agua | 1.5 | Crítico para vida |
| Salinidad | 1.3 | Crítico para especies acuáticas |
| Humedad | 1.2 | Muy importante |
| Vegetación | 1.0 | Importante |
| Fertilidad | 1.0 | Importante |
| Altitud | 0.8 | Moderado |
| Pendiente | 0.8 | Moderado |
| Rococidad | 0.7 | Bajo |

#### Niveles de compatibilidad

| Score | Categoría | Descripción |
|-------|-----------|-------------|
| ≥ 0.85 | `ideal` | Perfecto para la especie |
| 0.65 - 0.85 | `good` | Muy bueno |
| 0.45 - 0.65 | `acceptable` | Habitable pero no ideal |
| 0.25 - 0.45 | `poor` | Marginalmente habitable |
| < 0.25 | `inhabitable` | Inhabitable |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `calculate(tile, preference)` | Calcula compatibilidad [0.0, 1.0] |
| `_score_variable(actual, ideal, tolerance)` | Puntuación gaussiana de una variable |
| `_normalize_altitude(height)` | Convierte metros a [0.0, 1.0] |
| `get_compatibility_level(score)` | Convierte score en categoría legible |

#### Ejemplos

```python
from systems.environment.habitat_compatibility import HabitatCompatibility
from systems.environment.habitat_preference import create_human_habitat

# Obtener preferencia de humano
human_pref = create_human_habitat()

# Evaluar compatibilidad con un tile
tile = state.get_tile_at(50, 50)
score = HabitatCompatibility.calculate(tile, human_pref)
level = HabitatCompatibility.get_compatibility_level(score)
print(f"Compatibilidad: {score:.2f} ({level})")
# Ejemplo: Compatibilidad: 0.73 (good)
```

#### Consideraciones

- La altitud se normaliza: -500m → 0.0, 0m → 0.2, 3000m → 1.0
- Si `tolerance <= 0`, solo el valor ideal exacto es aceptable
- El score final es una media ponderada de todas las variables
- Se usa para evaluar destinos migratorios y decisiones de asentamiento

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    WorldConfig (parámetros físicos)             │
│   geological_activity, water_coverage, mean_temperature...      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ configura
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              TileMapInitializer (generación procedural)         │
│   Ruido de Perlin → height, temperature, water, vegetation...   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ genera
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TileMap (colección de tiles)                 │
│                                                                  │
│  Cada Tile tiene:                                               │
│    height, slope, temperature, humidity, water, salinity,       │
│    fertility, vegetation, organic_matter, rockiness,            │
│    urbanization                                                 │
└─────────┬──────────────────────────────────────┬────────────────┘
          │                                      │
          │ consultado por                       │ clasificado por
          ▼                                      ▼
┌──────────────────┐              ┌──────────────────────────────┐
│ Habitat          │              │ BiomeClassifier              │
│ Compatibility    │              │ (clasificación emergente)    │
│                  │              │                              │
│ Usa:             │              │ Usa variables del tile       │
│ HabitatPreference│              │ Retorna Biome                │
│ + variables tile │              │                              │
└──────────────────┘              └──────────────────────────────┘
          │
          │ usado por
          ▼
┌──────────────────┐              ┌──────────────────────────────┐
│ MigrationSystem  │              │ EnvironmentSystem            │
│ (doc 07)         │              │ (clima y estaciones)         │
│                  │              │                              │
│ Valida destinos  │              │ Delegado a:                  │
│ por compatibilidad│              │ EnvironmentDynamics          │
└──────────────────┘              │ (cambios lentos)             │
                                  │                              │
                                  │ Delegado a:                  │
                                  │ CatastropheSystem            │
                                  │ (eventos drásticos)          │
                                  └──────────────┬───────────────┘
                                                 │
                                                 │ crea
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │ CatastropheEvent             │
                                  │ (registro del evento)        │
                                  └──────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# EnvironmentConfig (en SimulationConfig)
config.environment.sector_size = 10
config.environment.carrying_capacity = 200
config.environment.max_agents_per_sector = 8

# TimeConfig (para estaciones)
config.time.season_duration_days = 90.0
config.time.days_per_year = 365.0
```

### Parámetros hardcodeados importantes

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `intervalo_escala_media` | 15 días | Crecimiento vegetal realista |
| `intervalo_escala_lenta` | 180 días | Erosión geológica |
| `intervalo_feedback` | 5 días | Impacto organismo-entorno |
| `umbral_erosion_pendiente` | 0.3 | Solo pendientes pronunciadas |
| `proteccion_vegetacion_erosion` | 0.3 | La vegetación protege |
| `umbral_sedimentacion` | height < 50 | Zonas bajas cerca del agua |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_tile_and_biome.py` | Tile, WorldConfig, BiomeClassifier |
| `tests/unit/test_environment_dynamics.py` | EnvironmentDynamics |
| `tests/unit/testf_catastrophe_system.py` | CatastropheSystem (nota: typo en nombre "testf") |
| `tests/unit/test_feedback_system.py` | FeedbackSystem |
| `tests/unit/test_habitat_compatibility.py` | HabitatCompatibility, HabitatPreference |
| `tests/integration/test_tile_integration.py` | Integración WorldState + EnvironmentContext |

---

## 📝 Ejemplos completos

### Ejemplo 1: Crear un mundo completo

```python
from core.state.world_state import WorldState
from systems.environment.world_config import WorldConfig
from systems.environment.biome_classifier import BiomeClassifier

# Configurar mundo tipo Tierra
world_config = WorldConfig(
    geological_activity=0.4,
    water_coverage=0.71,
    mean_temperature=0.5,
    global_humidity=0.5,
)

# Crear estado y generar mapa
state = WorldState(config=config, width=200, height=200)
state.initialize_tile_map(world_config=world_config, seed=42)

# Explorar biomas
biome_counts = {}
for x in range(200):
    for y in range(200):
        tile = state.get_tile_at(x, y)
        biome = BiomeClassifier.classify(tile)
        biome_counts[biome] = biome_counts.get(biome, 0) + 1

for biome, count in sorted(biome_counts.items(), key=lambda x: -x[1]):
    print(f"{biome.name}: {count} tiles ({count/40000:.1%})")
```

### Ejemplo 2: Evaluar compatibilidad de hábitat

```python
from systems.environment.habitat_compatibility import HabitatCompatibility
from systems.environment.habitat_preference import create_human_habitat, create_fish_habitat

human_pref = create_human_habitat()
fish_pref = create_fish_habitat()

# Evaluar cada tile para ambas especies
best_human_tiles = []
best_fish_tiles = []

for x in range(100):
    for y in range(100):
        tile = state.get_tile_at(x, y)
        if tile:
            human_score = HabitatCompatibility.calculate(tile, human_pref)
            fish_score = HabitatCompatibility.calculate(tile, fish_pref)
            
            best_human_tiles.append((human_score, x, y))
            best_fish_tiles.append((fish_score, x, y))

# Top 10 mejores ubicaciones para humanos
best_human_tiles.sort(reverse=True)
print("Mejores ubicaciones para humanos:")
for score, x, y in best_human_tiles[:10]:
    level = HabitatCompatibility.get_compatibility_level(score)
    print(f"  ({x}, {y}): score={score:.2f} ({level})")
```

### Ejemplo 3: Simular una catástrofe y registrar el evento

```python
from systems.environment.catastrophe_model import (
    CatastropheEvent, CatastropheType, severity_from_intensity,
    generate_catastrophe_id
)

# Crear evento de terremoto
earthquake = CatastropheEvent(
    event_id=generate_catastrophe_id(),
    catastrophe_type=CatastropheType.EARTHQUAKE,
    severity=severity_from_intensity(0.9),  # CATASTROPHIC
    epicenter_x=75,
    epicenter_y=75,
    radius=15,
    intensity=0.9,
    occurred_day=state.world_days_elapsed,
    tiles_affected=0,  # Se calculará tras aplicar
    description="Gran terremoto en la zona montañosa"
)

# Aplicar efectos (lo hace CatastropheSystem)
# ...

# Actualizar tiles afectados
earthquake.tiles_affected = affected_count

# Log del evento
print(earthquake)
# [CATASTROPHIC] EARTHQUAKE en (75, 75) radio=15, intensidad=0.90, tiles=706

# Exportar para análisis
event_data = earthquake.to_dict()
```

### Ejemplo 4: Cambios estacionales y su efecto en vegetación

```python
# Simular un año completo y observar vegetación
vegetation_by_season = {
    "SPRING": [],
    "SUMMER": [],
    "AUTUMN": [],
    "WINTER": []
}

for day in range(365):
    state.step()  # Avanza un día
    
    season = env_system.current_season.name
    tile = state.get_tile_at(50, 50)
    vegetation_by_season[season].append(tile.vegetation)

# Calcular promedio por estación
for season, values in vegetation_by_season.items():
    avg = sum(values) / len(values)
    print(f"{season}: vegetación promedio = {avg:.3f}")

# Resultado esperado:
# SPRING: 0.650 (crecimiento rápido)
# SUMMER: 0.720 (máximo)
# AUTUMN: 0.580 (decaimiento)
# WINTER: 0.450 (mínimo)
```

### Ejemplo 5: Crear preferencia de hábitat personalizada

```python
from systems.environment.habitat_preference import HabitatPreference

# Crear hábitat para una especie voladora de montaña
mountain_bird = HabitatPreference(
    temperature_ideal=0.4,
    temperature_tolerance=0.3,
    humidity_ideal=0.5,
    humidity_tolerance=0.3,
    water_ideal=0.2,
    water_tolerance=0.3,
    vegetation_ideal=0.3,
    vegetation_tolerance=0.3,
    altitude_ideal=0.7,        # Prefiere montañas altas
    altitude_tolerance=0.25,
    slope_ideal=0.4,           # Tolera pendientes
    slope_tolerance=0.3,
    fertility_ideal=0.4,
    fertility_tolerance=0.3,
    salinity_ideal=0.1,
    salinity_tolerance=0.2,
    rockiness_ideal=0.5,       # Prefiere zonas rocosas
    rockiness_tolerance=0.3,
)

# Evaluar compatibilidad
score = HabitatCompatibility.calculate(tile, mountain_bird)
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Biomas emergentes**: no se asignan, se calculan a partir de variables
- **Tres escalas temporales**: rápida (tick), media (15 días), lenta (180 días)
- **Retroalimentación**: los organismos modifican el entorno que los modifica a ellos
- **Catástrofes como motor**: son transformaciones, no errores
- **Hábitats por preferencias**: cada especie define su nicho ecológico
- **Compatibilidad gaussiana**: puntuación continua, no binaria

### Arquitectura de decisión

```
WorldConfig
   ↓
TileMapInitializer (generación procedural)
   ↓
TileMap (colección de tiles)
   ↓
├── BiomeClassifier (clasificación emergente)
├── EnvironmentSystem (clima/estaciones)
│     └── EnvironmentDynamics (cambios lentos)
│           └── CatastropheSystem (eventos drásticos)
│                 └── CatastropheEvent (registro)
├── FeedbackSystem (impacto organismo-entorno)
│     └── OrganismImpactCalculator
├── DensitySystem (presión poblacional)
├── HabitatCompatibility (evaluación de hábitats)
│     └── HabitatPreference (preferencias por especie)
└── EnvironmentContext (interfaz de consulta)
```

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| Intervalos escalados | EnvironmentDynamics | No procesar todo cada tick |
| Sparse grid | TileMap | Solo almacenar tiles existentes |
| Cache de biomas | BiomeClassifier | Recalcular solo si cambian variables |
| Presets como factory | HabitatPreference | Crear bajo demanda |
| Normalización de altitud | HabitatCompatibility | Comparación justa entre zonas |

### Limitaciones
- El mapa es estático en tamaño (no crece ni decrece)
- No hay clima regional (el clima es global por estación)
- Las catástrofes no se propagan (ocurren en un punto y afectan un radio)
- La urbanización no se revierte automáticamente
- No hay estaciones variables (cambio climático simulado)
- Los biomas no se solapan (cada tile tiene un único bioma)
- Las preferencias de hábitat son estáticas (no evolucionan)

### Errores comunes
- ❌ Asignar biomas manualmente (usar `BiomeClassifier.classify()`)
- ❌ Modificar tiles directamente sin pasar por los sistemas
- ❌ Olvidar que las variables de Tile deben estar en [0.0, 1.0] (usar `normalize()`)
- ❌ Asumir que `height` está en [0, 1] (está en metros, puede ser negativo)
- ❌ Crear presets de hábitat como instancias en lugar de llamar a las funciones factory
- ❌ Usar `HabitatCompatibility` sin normalizar la altitud primero

---

## 🎓 Conceptos clave

### ¿Por qué los biomas son emergentes?

**Principio de emergencia**:
- El bioma NO es un dato, es un resultado
- Si cambia la temperatura (p.ej. era glacial), el bioma cambia solo
- Esto permite que catástrofes cambien biomas automáticamente
- El usuario no tiene que mantener coherencia manual

### ¿Por qué tres escalas temporales?

**Principio de realismo temporal**:
- **Rápida**: cosas que pasan cada día (clima, catástrofes)
- **Media**: cosas que tardan semanas/meses (crecer un árbol)
- **Lenta**: cosas que tardan años (erosionar una montaña)

Procesar todo cada tick sería computacionalmente prohibitivo e irreal.

### ¿Por qué retroalimentación?

**Principio de Gaia**:
- Los organismos no son pasivos: modifican su entorno
- Las plantas crean suelo fértil
- Los herbívoros mantienen praderas
- Los humanos urbanizan
- Sin retroalimentación, el mundo sería estático y aburrido

### ¿Por qué catástrofes como eventos registrados?

**Principio de trazabilidad**:
- Cada catástrofe queda registrada con metadatos completos
- Permite análisis posterior (ej: correlación con extinciones)
- Facilita debugging y visualización
- Crea una "historia geológica" del mundo

### ¿Por qué las catástrofes tienen severidad?

**Principio de variabilidad natural**:
- No todos los terremotos son iguales
- La severidad depende de la intensidad
- Efectos diferentes según severidad
- Más realista que un efecto fijo

### ¿Por qué las preferencias de hábitat son continuas?

**Principio de nicho ecológico real**:
- Las especies no viven en un solo bioma
- Tienen rangos de tolerancia, no requisitos exactos
- La función gaussiana modela esta realidad
- Permite transiciones suaves entre biomas

### ¿Por qué pesos diferentes por variable?

**Principio de importancia biológica**:
- La temperatura afecta el metabolismo (crítico)
- El agua es esencial para la vida (crítico)
- La pendiente importa menos (moderado)
- Los pesos reflejan la realidad ecológica

### ¿Por qué los presets son funciones factory?

**Principio de inmutabilidad y flexibilidad**:
- Cada llamada crea una nueva instancia
- Permite modificar sin afectar otros usos
- Más flexible que constantes globales
- Sigue el patrón de diseño factory

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 15 |
| Variables por tile | 11 |
| Tipos de biomas | 15 |
| Tipos de catástrofes | 8 |
| Niveles de severidad | 4 |
| Variables de hábitat | 9 |
| Presets de hábitat | 9 |
| Escalas temporales | 3 |
| Tests cubriendo entorno | ~75 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Clima regional (frentes meteorológicos que se mueven)
- [ ] Estaciones variables (cambio climático simulado)
- [ ] Evolución de preferencias de hábitat
- [ ] Biomas solapables (transiciones suaves)

### Posibles
- [ ] Recursos naturales explotables (minerales, petróleo)
- [ ] Contaminación antropogénica persistente
- [ ] Regeneración natural post-catástrofe (sucesión ecológica)
- [ ] Capas de nieve estacional
- [ ] Corrientes oceánicas
- [ ] Vientos que afectan dispersión de semillas
- [ ] Incendios forestales que se propagan
- [ ] Inundaciones dinámicas (agua que fluye)
- [ ] Terremotos que desencadenan tsunamis
- [ ] Actividad humana que modifica biomas (agricultura, deforestación)
- [ ] Migración de biomas por cambio climático

---

*Documento: 04_ENTORNO.md*
*Versión: 2.0 (actualizado con catastrophe_model, habitat_preference, habitat_compatibility)*
*Última actualización: Agosto 2026*