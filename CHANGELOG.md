# Changelog

Todos los cambios notables de **Primordial** se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionamiento Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- `robots.txt`, `sitemap.xml` y `404.html` personalizada para GitHub Pages (SEO y experiencia de usuario)

## [0.4.0] - 2026-09-25

### Añadido
- **Mecanismos ecológicos con implementación específica** (antes placeholders en `MechanismFactory`):
  - `AmbushMechanism`: emboscada sigilosa (camuflaje e instinto depredador vs visión, oído y olfato de la presa)
  - `PackHuntingMechanism`: caza en manada; la coordinación (`pack_behavior`, `cooperation`) compensa presas mayores y el botín se reparte (70% individual)
  - `TerritorialDisplayMechanism`: competencia ritualizada sin muertes; el perdedor paga retirada y estrés
  - `ChemicalSuppressionMechanism`: alelopatía; la muerte del objetivo emerge por inanición, no se registra directamente
  - `FilterFeedingMechanism`: filtrado pasivo de nutrientes; el recurso agotado muere como en el pastoreo
- **Puente epidemiológico**: `InfectionMechanism` inocula ahora patógenos reales en el huésped vía `DiseaseSystem`, con familia `Parasite_{especie}` y sin reinfección de familias activas
- 42 tests nuevos (mecanismos ecológicos y sistema de métricas); la suite pasa de 372 a 414 tests
- `tests/unit/test_metrics_system.py`: primera suite dedicada al `MetricsSystem` (ecología, espacial, genética, exportación)
- **Web oficial** desplegada en GitHub Pages: [primordial-sim.github.io/primordial](https://primordial-sim.github.io/primordial/)
- Estructura profesional de sitio estático: HTML/CSS/JS separados, metadatos Open Graph

### Cambiado
- `MechanismFactory`: `AMBUSH`, `PACK_HUNTING`, `FILTER_FEEDING`, `TERRITORIAL_DISPLAY` y `CHEMICAL_SUPPRESSION` despachan ahora sus mecanismos específicos en lugar de placeholders
- Documentación `20_ECOLOGIA.md` actualizada a la versión 3.0 con el catálogo de rasgos por mecanismo y el puente epidemiológico
- README: visión del usuario como "arquitecto de mundos" (creación del mundo + control de parámetros en vivo), URLs del repositorio corregidas, badge de la web oficial y contadores de tests sincronizados

### Eliminado
- Tests obsoletos que codificaban los placeholders (`test_ambush_maps_to_hunt`, `test_pack_hunting_maps_to_hunt`)

## [0.3.0] - 2026-09-21

### Añadido
- **Profesionalización del repositorio**:
  - README.md completo con descripción del proyecto, características, instalación y roadmap
  - Archivo `LICENSE` (MIT) para uso open source
  - `pyproject.toml` con metadatos del proyecto y configuración de empaquetado
  - `CONTRIBUTING.md` con guía para contribuidores
  - `CODE_OF_CONDUCT.md` basado en Contributor Covenant v2.0
  - Plantillas de GitHub Issues: Bug Report y Feature Request
  - Plantilla de Pull Request con checklist de revisión
- **Organización GitHub**: Migración del repositorio a `primordial-sim/primordial`
- **Naming**: Renombrado del proyecto a "Primordial"

### Cambiado
- Movido `exportar_proyecto.py` a `tools/` para limpieza de estructura
- Actualizado `.gitignore` para prevenir commits de reportes CSV temporales
- Añadidas métricas de ecología al `MetricsSystem`:
  - Total de encuentros ecológicos
  - Total de relaciones ejecutadas (por tipo)
  - Contadores de depredaciones, herbivoría, mutualismo y competencia
  - Parejas de relaciones cacheadas

### Eliminado
- Reportes CSV temporales (`reporte_simulacion_*.csv`) del control de versiones

## [0.2.0] - 2026-09-05

### Añadido
- **Sistema de ecología evolutiva**:
  - 8 tipos de relaciones ecológicas: Depredación, Herbivoría, Mutualismo, Competencia, Parasitismo, Comensalismo, Amensalismo, Neutralismo
  - Inferencia automática de relaciones desde perfiles biológicos
  - Sistema de inferencia ecológica (`EcologicalRelationshipSystem`)
- **Mecanismos de interacción ecológica**:
  - `HuntMechanism` - Caza activa con persecución
  - `PackHuntingMechanism` - Caza coordinada en manada
  - `GrazingMechanism` - Pastoreo de vegetación
  - `PollinationMechanism` - Polinización mutualista
  - `SeedDispersalMechanism` - Dispersión de semillas
  - `ScavengingMechanism` - Carroñeo
  - `InfectionMechanism` - Infección parasitaria
  - `ResourceConsumptionMechanism` - Competencia por recursos
  - `MechanismFactory` - Despacho dinámico de mecanismos
- **Sistema de energía**:
  - Gestión de energía por organismo
  - Fotosíntesis para productores
  - Metabolismo y gasto energético
  - Inanición y muerte por falta de energía
- **Detección ecológica**:
  - Detección de amenazas (presas detectan depredadores)
  - Detección de presas (carnívoros buscan presas)
  - Detección de vegetación (herbívoros buscan plantas)
- **Optimización de rendimiento**:
  - `SpatialGrid` para búsquedas espaciales O(1)
  - Eliminación de relaciones bidireccionales duplicadas
  - Caché de relaciones ecológicas inferidas

### Cambiado
- Refactorización de sistemas de movimiento para usar `SpatialGrid`
- Mejora de rendimiento en fase de ecología (~19% más rápido)

## [0.1.0] - 2026-06-12

### Añadido
- **Versión inicial del proyecto**:
  - Motor de simulación multi-agente con arquitectura de fases
  - Sistema genético universal con 20+ rasgos heredables
  - Sistema de taxonomía y clasificación de especies
  - Mundo con tiles y biomas dinámicos
- **Sistemas de simulación**:
  - Sistema temporal (envejecimiento, estaciones)
  - Sistema ambiental (biomas, presión social)
  - Sistema de movimiento y pathfinding
  - Sistema de relaciones sociales (amistad, matrimonio, divorcio)
  - Sistema de reproducción (concepción, gestación, nacimiento)
  - Sistema de mortalidad (curvas de supervivencia Gompertz)
  - Sistema de epidemiología (patógenos, contagios)
  - Sistema de genealogía (linajes, generaciones)
- **Métricas poblacionales**:
  - Recolección de métricas multidimensionales
  - Exportación a JSON para análisis
- **Testing**:
  - Suite inicial de tests unitarios
  - Tests de integración básicos

---

## 📖 Convenciones de versionado

Este proyecto sigue el [Versionamiento Semántico](https://semver.org/lang/es/):

- **MAJOR** (X.0.0): Cambios incompatibles con versiones anteriores
- **MINOR** (0.X.0): Nuevas funcionalidades compatibles
- **PATCH** (0.0.X): Correcciones de bugs compatibles

### Tipos de cambios documentados

| Tipo | Descripción |
|------|-------------|
| **Añadido** | Nuevas funcionalidades |
| **Cambiado** | Modificaciones en funcionalidades existentes |
| **Obsoleto** | Funcionalidades que serán eliminadas pronto |
| **Eliminado** | Funcionalidades removidas |
| **Corregido** | Bugs corregidos |
| **Seguridad** | Parches de seguridad |

---

## 🔗 Enlaces

- [Comparar versiones](https://github.com/primordial-sim/primordial/compare)
- [Ver todos los commits](https://github.com/primordial-sim/primordial/commits/main)

[Unreleased]: https://github.com/primordial-sim/primordial/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/primordial-sim/primordial/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/primordial-sim/primordial/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/primordial-sim/primordial/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/primordial-sim/primordial/releases/tag/v0.1.0