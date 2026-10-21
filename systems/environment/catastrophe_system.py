"""Sistema de eventos catastróficos.

Gestiona la ocurrencia, ejecución y registro de catástrofes naturales
que alteran drásticamente el entorno.

Cada tipo de catástrofe tiene:
- Una probabilidad base (escalada por WorldConfig)
- Un radio de efecto
- Efectos específicos sobre las variables del tile
- Una severidad calculada

Principio: "Las catástrofes son el motor de cambio geológico y ecológico."

MIGRACIÓN HEXAGONAL:
- Epicentros usan coordenadas hexagonales (q, r)
- Bucles de iteración usan patrón hexagonal
- Vecinos hexagonales para cálculos de gradiente
"""

from __future__ import annotations

import logging
import math
import random
from typing import List, Optional, TYPE_CHECKING

from systems.environment.catastrophe_model import (
    CatastropheType,
    CatastropheEvent,
    generate_catastrophe_id,
    severity_from_intensity,
)

if TYPE_CHECKING:
    from core.state.world_state import WorldState
    from systems.environment.world_config import WorldConfig
    from systems.environment.environment_system import Season


class CatastropheSystem:
    """Gestiona todos los tipos de catástrofes del mundo."""

    # Historial máximo de catástrofes registradas
    MAX_HISTORY = 500

    def __init__(
        self, world_config: Optional["WorldConfig"] = None
    ) -> None:
        """Inicializa el sistema de catástrofes.

        Args:
            world_config: Configuración física del mundo.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Referencia a WorldConfig (se actualiza en process)
        self.world_config = world_config

        # Historial de catástrofes ocurridas
        self.history: List[CatastropheEvent] = []

        # Probabilidades base diarias
        self.base_probabilities = {
            CatastropheType.EARTHQUAKE: 0.0001,
            CatastropheType.VOLCANIC_ERUPTION: 0.00005,
            CatastropheType.FLOOD: 0.0005,
            CatastropheType.METEORITE: 0.00001,
            CatastropheType.FIRE: 0.001,
            CatastropheType.DROUGHT: 0.0005,
            CatastropheType.STORM: 0.0008,
            CatastropheType.LANDSLIDE: 0.0003,
        }

    def process(
        self,
        state: "WorldState",
        delta_days: float,
        current_season: "Season",
        world_config: Optional["WorldConfig"] = None,
    ) -> List[CatastropheEvent]:
        """Evalúa y ejecuta catástrofes para el tick actual.

        Args:
            state: Estado del mundo con tile_map.
            delta_days: Días transcurridos.
            current_season: Estación actual.
            world_config: Configuración física del mundo.

        Returns:
            Lista de catástrofes ocurridas en este tick.
        """
        if not state.has_tile_map():
            return []

        if world_config is not None:
            self.world_config = world_config

        occurred_events: List[CatastropheEvent] = []

        # Evaluar cada tipo de catástrofe
        for catastrophe_type in CatastropheType:
            probability = self._calculate_probability(
                catastrophe_type, delta_days, current_season
            )

            if random.random() < probability:
                event = self._execute_catastrophe(
                    state=state,
                    catastrophe_type=catastrophe_type,
                    current_day=getattr(state, "world_days_elapsed", 0.0),
                )
                if event is not None:
                    occurred_events.append(event)
                    self._register_event(event)

        return occurred_events

    def _calculate_probability(
        self,
        catastrophe_type: CatastropheType,
        delta_days: float,
        current_season: "Season",
    ) -> float:
        """Calcula la probabilidad de una catástrofe escalada por WorldConfig.

        Args:
            catastrophe_type: Tipo de catástrofe.
            delta_days: Días transcurridos.
            current_season: Estación actual.

        Returns:
            Probabilidad ajustada para este tick.
        """
        from systems.environment.environment_system import Season

        base = self.base_probabilities[catastrophe_type]
        multiplier = 1.0

        # Escalado por WorldConfig
        if self.world_config is not None:
            if catastrophe_type in [
                CatastropheType.EARTHQUAKE,
                CatastropheType.VOLCANIC_ERUPTION,
            ]:
                # Actividad geológica afecta terremotos y volcanes
                multiplier *= 0.5 + self.world_config.geological_activity * 2.0
            elif catastrophe_type == CatastropheType.FLOOD:
                # Cobertura de agua y humedad afectan inundaciones
                multiplier *= 0.5 + self.world_config.water_coverage
                multiplier *= 0.5 + self.world_config.global_humidity
            elif catastrophe_type == CatastropheType.LANDSLIDE:
                # Tasa de erosión afecta deslizamientos
                multiplier *= 0.5 + self.world_config.erosion_rate * 2.0
            elif catastrophe_type == CatastropheType.STORM:
                # Humedad global afecta tormentas
                multiplier *= 0.5 + self.world_config.global_humidity * 1.5

        # Escalado por estación
        if catastrophe_type == CatastropheType.FIRE:
            if current_season == Season.SUMMER:
                multiplier *= 3.0
            elif current_season == Season.WINTER:
                multiplier *= 0.1
        elif catastrophe_type == CatastropheType.DROUGHT:
            if current_season == Season.SUMMER:
                multiplier *= 2.5
            elif current_season == Season.WINTER:
                multiplier *= 0.2
        elif catastrophe_type == CatastropheType.STORM:
            if current_season == Season.AUTUMN:
                multiplier *= 2.0
            elif current_season == Season.SPRING:
                multiplier *= 1.5
        elif catastrophe_type == CatastropheType.FLOOD:
            if current_season == Season.SPRING:
                multiplier *= 2.0  # Deshielo

        return base * multiplier * delta_days

    def _execute_catastrophe(
        self,
        state: "WorldState",
        catastrophe_type: CatastropheType,
        current_day: float,
    ) -> Optional[CatastropheEvent]:
        """Ejecuta una catástrofe específica y retorna el evento.

        HEX: Los epicentros usan coordenadas hexagonales (q, r).

        Args:
            state: Estado del mundo.
            catastrophe_type: Tipo de catástrofe a ejecutar.
            current_day: Día simulado actual.

        Returns:
            CatastropheEvent con los detalles, o None si no se pudo ejecutar.
        """
        # HEX: Elegir epicentro aleatorio usando coordenadas hexagonales
        q = random.randint(0, state.width - 1)
        r = random.randint(0, state.height - 1)

        # Ejecutar según tipo
        if catastrophe_type == CatastropheType.EARTHQUAKE:
            return self._execute_earthquake(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.VOLCANIC_ERUPTION:
            return self._execute_volcanic_eruption(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.FLOOD:
            return self._execute_flood(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.METEORITE:
            return self._execute_meteorite(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.FIRE:
            return self._execute_fire(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.DROUGHT:
            return self._execute_drought(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.STORM:
            return self._execute_storm(state, q, r, current_day)
        elif catastrophe_type == CatastropheType.LANDSLIDE:
            return self._execute_landslide(state, q, r, current_day)

        return None

    # =========================================================================
    # EJECUCIÓN DE CADA TIPO DE CATÁSTROFE
    # =========================================================================

    def _execute_earthquake(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Terremoto: altera alturas y pendientes en una zona.

        HEX: Usa coordenadas hexagonales y patrón hexagonal para el radio.
        """
        intensity = random.uniform(0.3, 1.0)
        radius = int(5 + intensity * 15)  # Radio 5-20
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal en lugar de cuadrado
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                # Efecto disminuye con la distancia
                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Cambios de altura (subsidencia o elevación)
                height_change = random.uniform(-50, 30) * effect
                tile.height += height_change

                # Aumentar pendiente (terreno se fractura)
                tile.slope = min(1.0, tile.slope + effect * 0.5)

                # Aumentar rocosidad (rocas expuestas)
                tile.rockiness = min(1.0, tile.rockiness + effect * 0.3)

                # Reducir vegetación (destrucción)
                tile.vegetation = max(0.0, tile.vegetation - effect * 0.4)

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.EARTHQUAKE,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,  # HEX: Coordenada Q
            epicenter_y=r,   # HEX: Coordenada R
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"Terremoto de magnitud {intensity * 10:.1f} en ({q}, {r})",
        )

        self.logger.warning(f"🌋 {event}")
        return event

    def _execute_volcanic_eruption(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Erupción volcánica: lava, ceniza, fertilización.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.4, 1.0)
        radius = int(3 + intensity * 10)  # Radio 3-13
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Zona cercana al volcán: destrucción total
                if dist < radius * 0.3:
                    tile.vegetation = 0.0
                    tile.organic_matter = 0.0
                    tile.height += 100 * effect  # Elevación por lava
                    tile.rockiness = 1.0
                    tile.temperature = min(1.0, tile.temperature + 0.3)
                else:
                    # Zona externa: ceniza fertilizante
                    tile.vegetation = max(0.0, tile.vegetation - effect * 0.3)
                    tile.fertility = min(1.0, tile.fertility + effect * 0.4)
                    tile.organic_matter = min(
                        1.0, tile.organic_matter + effect * 0.2
                    )

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.VOLCANIC_ERUPTION,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"Erupción volcánica VEI {int(intensity * 8)} en ({q}, {r})",
        )

        self.logger.warning(f"🌋 {event}")
        return event

    def _execute_flood(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Inundación: aumenta agua en zonas bajas.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.3, 0.9)
        radius = int(8 + intensity * 20)  # Radio 8-28
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Solo afecta zonas bajas (no montañas)
                if tile.height < 200.0:
                    # Aumentar agua
                    tile.water = min(1.0, tile.water + effect * 0.6)
                    tile.humidity = min(1.0, tile.humidity + effect * 0.4)

                    # Erosión por agua
                    if tile.slope > 0.2:
                        tile.height -= effect * 10
                        tile.slope = max(0.0, tile.slope - effect * 0.1)

                    # Reducir vegetación (ahogamiento)
                    if tile.water > 0.7:
                        tile.vegetation = max(
                            0.0, tile.vegetation - effect * 0.3
                        )

                    tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.FLOOD,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"Inundación severa en ({q}, {r})",
        )

        self.logger.warning(f"🌊 {event}")
        return event

    def _execute_meteorite(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Meteorito: devastación puntual extrema.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.5, 1.0)
        radius = int(2 + intensity * 8)  # Radio 2-10
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Cráter: destrucción total
                if dist < radius * 0.4:
                    tile.vegetation = 0.0
                    tile.organic_matter = 0.0
                    tile.fertility = 0.0
                    tile.height -= 200 * effect  # Cráter profundo
                    tile.rockiness = 1.0
                    tile.water = 0.0
                else:
                    # Zona de impacto: destrucción severa
                    tile.vegetation = max(0.0, tile.vegetation - effect * 0.8)
                    tile.organic_matter = max(
                        0.0, tile.organic_matter - effect * 0.5
                    )
                    tile.height -= 50 * effect

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.METEORITE,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"💥 Impacto de meteorito en ({q}, {r})",
        )

        self.logger.warning(f"☄️ {event}")
        return event

    def _execute_fire(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Incendio: destruye vegetación.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.3, 1.0)
        radius = int(3 + intensity * 10)  # Radio 3-13
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None or tile.vegetation < 0.2:
                    continue  # Solo afecta zonas con vegetación

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Reducir vegetación drásticamente
                tile.vegetation = max(0.0, tile.vegetation - effect * 0.8)
                tile.organic_matter = max(
                    0.0, tile.organic_matter - effect * 0.5
                )

                # Cenizas fertilizan el suelo
                tile.fertility = min(1.0, tile.fertility + effect * 0.2)

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.FIRE,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"🔥 Incendio forestal en ({q}, {r})",
        )

        self.logger.warning(f"🔥 {event}")
        return event

    def _execute_drought(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Sequía: reduce agua y humedad.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.3, 0.9)
        radius = int(10 + intensity * 20)  # Radio 10-30
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Reducir agua y humedad
                tile.water = max(0.0, tile.water - effect * 0.5)
                tile.humidity = max(0.0, tile.humidity - effect * 0.4)

                # Reducir vegetación si hay poca agua
                if tile.water < 0.3:
                    tile.vegetation = max(
                        0.0, tile.vegetation - effect * 0.3
                    )

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.DROUGHT,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"🏜️ Sequía severa en ({q}, {r})",
        )

        self.logger.warning(f"🏜️ {event}")
        return event

    def _execute_storm(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> CatastropheEvent:
        """Tormenta: vientos fuertes, lluvia, erosión.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.
        """
        intensity = random.uniform(0.3, 1.0)
        radius = int(5 + intensity * 15)  # Radio 5-20
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Aumentar agua y humedad (lluvia)
                tile.water = min(1.0, tile.water + effect * 0.3)
                tile.humidity = min(1.0, tile.humidity + effect * 0.4)

                # Viento daña vegetación alta
                if tile.vegetation > 0.6:
                    tile.vegetation = max(
                        0.0, tile.vegetation - effect * 0.3
                    )

                # Erosión por viento y lluvia
                if tile.slope > 0.3:
                    tile.height -= effect * 5
                    tile.slope = max(0.0, tile.slope - effect * 0.05)

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.STORM,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"⛈️ Tormenta severa en ({q}, {r})",
        )

        self.logger.warning(f"⛈️ {event}")
        return event

    def _execute_landslide(
        self, state: "WorldState", q: int, r: int, current_day: float
    ) -> Optional[CatastropheEvent]:
        """Deslizamiento: movimiento de tierra en pendientes.

        HEX: Usa coordenadas hexagonales y patrón hexagonal.

        Returns:
            CatastropheEvent si ocurre, None si no hay pendiente adecuada.
        """
        # Solo ocurre en zonas con pendiente alta
        tile = state.get_tile_at(q, r)
        if tile is None or tile.slope < 0.4:
            # Buscar una zona con pendiente alta cerca
            found = False
            # HEX: Buscar en vecinos hexagonales
            hex_directions = [
                (1, 0), (1, -1), (0, -1),
                (-1, 0), (-1, 1), (0, 1)
            ]

            for search_radius in range(1, 11):
                if found:
                    break
                for dq, dr in hex_directions:
                    search_q = q + dq * search_radius
                    search_r = r + dr * search_radius
                    t = state.get_tile_at(search_q, search_r)
                    if t is not None and t.slope > 0.4:
                        q, r = search_q, search_r
                        found = True
                        break

            if not found:
                # No hay pendiente alta: no ocurre deslizamiento
                return None

        intensity = random.uniform(0.3, 0.9)
        radius = int(2 + intensity * 6)  # Radio 2-8
        tiles_affected = 0

        # HEX: Iterar en patrón hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                dist = self._hex_distance(0, 0, dq, dr)
                if dist > radius:
                    continue

                tile = state.get_tile_at(q + dq, r + dr)
                if tile is None:
                    continue

                distance_factor = 1.0 - (dist / radius)
                effect = intensity * distance_factor

                # Reducir altura y pendiente (la tierra se desplaza)
                tile.height -= effect * 30
                tile.slope = max(0.0, tile.slope - effect * 0.3)

                # Reducir vegetación
                tile.vegetation = max(0.0, tile.vegetation - effect * 0.5)

                # Aumentar rocosidad (rocas expuestas)
                tile.rockiness = min(1.0, tile.rockiness + effect * 0.3)

                tiles_affected += 1

        event = CatastropheEvent(
            event_id=generate_catastrophe_id(),
            catastrophe_type=CatastropheType.LANDSLIDE,
            severity=severity_from_intensity(intensity),
            epicenter_x=q,
            epicenter_y=r,
            radius=radius,
            intensity=intensity,
            occurred_day=current_day,
            tiles_affected=tiles_affected,
            description=f"⛰️ Deslizamiento de tierra en ({q}, {r})",
        )

        self.logger.warning(f"⛰️ {event}")
        return event

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def _hex_distance(self, q1: int, r1: int, q2: int, r2: int) -> float:
        """Calcula la distancia hexagonal entre dos celdas axiales.

        Fórmula: (abs(dq) + abs(dr) + abs(dq + dr)) // 2

        Args:
            q1, r1: Coordenadas del primer punto.
            q2, r2: Coordenadas del segundo punto.

        Returns:
            Distancia hexagonal entre los dos puntos.
        """
        dq = q1 - q2
        dr = r1 - r2
        return float((abs(dq) + abs(dr) + abs(dq + dr)) // 2)

    # =========================================================================
    # REGISTRO Y CONSULTA
    # =========================================================================

    def _register_event(self, event: CatastropheEvent) -> None:
        """Registra un evento en el historial."""
        self.history.append(event)

        # Limitar el historial
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY :]

    def get_history(self) -> List[CatastropheEvent]:
        """Retorna el historial completo de catástrofes."""
        return list(self.history)

    def get_recent_events(self, count: int = 10) -> List[CatastropheEvent]:
        """Retorna los N eventos más recientes."""
        return self.history[-count:] if self.history else []

    def get_events_by_type(
        self, catastrophe_type: CatastropheType
    ) -> List[CatastropheEvent]:
        """Retorna todos los eventos de un tipo específico."""
        return [
            e for e in self.history if e.catastrophe_type == catastrophe_type
        ]

    def get_event_count(self) -> int:
        """Retorna el número total de catástrofes registradas."""
        return len(self.history)

    def get_event_count_by_type(self) -> dict:
        """Retorna el conteo de catástrofes por tipo."""
        counts = {}
        for event in self.history:
            type_name = event.catastrophe_type.name
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def get_summary(self) -> dict:
        """Retorna un resumen de la actividad catastrófica."""
        return {
            "total_events": len(self.history),
            "by_type": self.get_event_count_by_type(),
            "recent": [str(e) for e in self.get_recent_events(5)],
        }