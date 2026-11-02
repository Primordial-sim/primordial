"""Sistema de Energía.

Gestiona el metabolismo energético de todos los organismos:
1. Genera energía por fotosíntesis (plantas y organismos fotosintéticos)
2. Forrajeo pasivo para heterótrofos en tiles con recursos
3. Aplica el coste metabólico basal (mantenimiento del organismo)
4. Gestiona el estado de inanición (starvation)
5. Calcula el riesgo de muerte por inanición

Flujo de energía en el ecosistema:
Sol → Plantas (fotosíntesis) → Herbívoros (comen plantas) → Carnívoros (cazan)

Filosofía: "La energía es el recurso fundamental de la vida. Sin energía,
no hay movimiento, reproducción ni supervivencia."
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from core.state.pending_changes import PendingChanges
    from core.state.world_state import WorldState
    from entities.person.person import Person
    from systems.environment.environment_context import EnvironmentContext


class EnergySystem:
    """Sistema que gestiona el metabolismo energético de los organismos."""

    _logger = logging.getLogger("EnergySystem")

    def __init__(self, config) -> None:
        self.config = config

        # Parámetros de metabolismo
        self.basal_metabolic_rate: float = 0.05  # REDUCIDO: 0.1 → 0.05
        self.starvation_death_threshold: float = 30.0
        self.starvation_damage_rate: float = 0.05

        # Parámetros de fotosíntesis
        self.photosynthesis_rate: float = 8.0  # AUMENTADO: 5.0 → 8.0
        self.photosynthesis_light_factor: float = 1.0

        # NUEVO: Parámetros de forrajeo pasivo
        self.passive_foraging_rate: float = 0.05
        self.foraging_vegetation_threshold: float = 0.3

        # Estadísticas
        self._total_starvation_deaths: int = 0
        self._total_energy_processed: int = 0
        self._total_photosynthesis_events: int = 0
        self._total_foraging_events: int = 0

    def _get_param(self, name: str, default: float) -> float:
        """Lee un parámetro de energía desde la config en caliente."""
        if self.config is not None:
            energy_cfg = getattr(self.config, "energy", None)
            if energy_cfg is not None:
                return getattr(energy_cfg, name, default)
        return default

    def process(
        self,
        state: "WorldState",
        pending: "PendingChanges",
        delta_days: float,
        context: "EnvironmentContext",
    ) -> None:
        """Procesa el metabolismo energético para todos los organismos."""
        persons = list(state.get_all_persons())
        if not persons:
            return

        starvation_deaths = 0
        photosynthesis_count = 0
        foraging_count = 0

        for person in persons:
            # 1. Generar energía por fotosíntesis (si aplica)
            if self._is_photosynthetic(person):
                energy_generated = self._calculate_photosynthesis(
                    person, state, delta_days
                )
                person.add_energy(energy_generated)
                photosynthesis_count += 1

            # 2. NUEVO: Forrajeo pasivo para heterótrofos
            elif not getattr(person, "is_sick", False):
                foraging_gained = self._apply_passive_foraging(
                    person, state, delta_days
                )
                if foraging_gained > 0:
                    foraging_count += 1

            # 3. Aplicar metabolismo basal
            metabolic_cost = self._calculate_metabolic_cost(person, delta_days)
            person.spend_energy(metabolic_cost)

            # 4. Avanzar contador de inanición
            person.advance_starvation(delta_days)

            # 5. Sincronizar energía física con emoción de energía
            self._sync_energy_with_emotions(person)

            # 6. Verificar muerte por inanición
            if self._check_starvation_death(person, delta_days):
                pending.register_death(
                    entity_id=person.entity_id,
                    reason="inanicion",
                )
                starvation_deaths += 1
                self._total_starvation_deaths += 1
                self._logger.debug(
                    "💀 Muerte por inanición: %s (entity_id=%d)",
                    person.species,
                    person.entity_id,
                )

        self._total_energy_processed += len(persons)
        self._total_photosynthesis_events += photosynthesis_count
        self._total_foraging_events += foraging_count

        if starvation_deaths > 0 or photosynthesis_count > 0 or foraging_count > 0:
            self._logger.debug(
                "⚡ Energía: %d organismos procesados, "
                "%d fotosíntesis, "
                "%d forrajes, "
                "%d muertes por inanición",
                len(persons),
                photosynthesis_count,
                foraging_count,
                starvation_deaths,
            )

    # =========================================================================
    # NUEVO: FORRAJEO PASIVO
    # =========================================================================

    def _apply_passive_foraging(
        self,
        person: "Person",
        state: "WorldState",
        delta_days: float,
    ) -> float:
        """Aplica forrajeo pasivo para organismos heterótrofos.

        Los organismos en tiles con vegetación suficiente obtienen
        energía automáticamente, simulando la búsqueda de alimento.
        """
        from systems.environment.tile import Tile

        tile = state.get_tile_at(int(person.q), int(person.r))
        if tile is None:
            return 0.0

        vegetation = getattr(tile, "vegetation", 0.0)

        # Salvaguarda: un objeto no numérico no es un recurso consumible
        if isinstance(vegetation, bool) or not isinstance(
            vegetation, (int, float)
        ):
            return 0.0

        vegetation = max(0.0, min(1.0, float(vegetation)))

        threshold = float(
            self._get_param(
                "foraging_vegetation_threshold",
                self.foraging_vegetation_threshold,
            )
        )
        if vegetation < threshold:
            return 0.0

        base_rate = float(
            self._get_param(
                "passive_foraging_rate", self.passive_foraging_rate
            )
        )
        if base_rate <= 0.0 or delta_days <= 0.0:
            return 0.0

        energy_gained = (base_rate + vegetation * 0.1) * delta_days
        person.add_energy(energy_gained)

        # Agotar el recurso solo si es un Tile real
        if isinstance(tile, Tile):
            tile.vegetation = max(
                0.0, tile.vegetation - 0.001 * delta_days
            )

        return energy_gained

    # =========================================================================
    # FOTOSÍNTESIS
    # =========================================================================

    def _is_photosynthetic(self, person: "Person") -> bool:
        """Verifica si un organismo es fotosintético."""
        try:
            diet = person.genome.get_trait_value("diet")
            if diet is not None:
                return diet <= 0.1

            species = person.species.lower()
            photosynthetic_species = [
                "grass", "tree", "shrub", "flower", "algae",
                "plant", "fern", "moss", "cactus",
            ]
            return any(ps in species for ps in photosynthetic_species)
        except (AttributeError, TypeError):
            return False

    def _calculate_photosynthesis(
        self,
        person: "Person",
        state: "WorldState",
        delta_days: float,
    ) -> float:
        """Calcula la energía generada por fotosíntesis."""
        energy = (
            self._get_param("photosynthesis_rate", self.photosynthesis_rate)
            * delta_days
        )

        light_factor = self._get_light_factor(person, state)
        energy *= light_factor

        water_factor = self._get_water_factor(person, state)
        energy *= water_factor

        temp_factor = self._get_temperature_factor(person, state)
        energy *= temp_factor

        return max(0.0, energy)

    def _get_light_factor(self, person: "Person", state: "WorldState") -> float:
        """Obtiene el factor de luz."""
        return 0.8

    def _get_water_factor(self, person: "Person", state: "WorldState") -> float:
        """Obtiene el factor de agua basado en el tile del organismo."""
        try:
            tile = state.get_tile_at(int(person.q), int(person.r))
            if tile is not None:
                water = getattr(tile, "water", 0.5)
                if water < 0.1:
                    return 0.3
                elif water > 0.8:
                    return 0.5
                else:
                    return 1.0
        except (AttributeError, TypeError):
            pass
        return 0.7

    def _get_temperature_factor(self, person: "Person", state: "WorldState") -> float:
        """Obtiene el factor de temperatura basado en el tile del organismo."""
        try:
            tile = state.get_tile_at(int(person.q), int(person.r))
            if tile is not None:
                temp = getattr(tile, "temperature", 0.5)
                if temp < 0.1:
                    return 0.2
                elif temp > 0.9:
                    return 0.4
                elif 0.3 <= temp <= 0.7:
                    return 1.0
                else:
                    return 0.7
        except (AttributeError, TypeError):
            pass
        return 0.7

    # =========================================================================
    # SINCRONIZACIÓN CON EMOCIONES
    # =========================================================================

    def _sync_energy_with_emotions(self, person: "Person") -> None:
        """Sincroniza el nivel de energía física con la emoción de energía."""
        emotions = getattr(person, "_emotions", None)
        if emotions is None or not isinstance(emotions, dict):
            return

        if "energy" not in emotions:
            return

        target_energy = person.energy_ratio
        current_emotion = emotions.get("energy", 1.0)

        delta = (target_energy - current_emotion) * 0.2

        if hasattr(person, "update_emotion"):
            person.update_emotion("energy", delta)
        else:
            emotions["energy"] = max(0.0, min(1.0, current_emotion + delta))

    # =========================================================================
    # METABOLISMO
    # =========================================================================

    def _calculate_metabolic_cost(
        self,
        person: "Person",
        delta_days: float,
    ) -> float:
        """Calcula el coste metabólico de un organismo."""
        cost = (
            self._get_param("basal_metabolic_rate", self.basal_metabolic_rate)
            * delta_days
        )

        size_factor = self._get_size_factor(person)
        cost *= size_factor

        if person.is_pregnant:
            cost *= 1.3

        if person.is_sick:
            cost *= 1.2

        emotions = getattr(person, "_emotions", None)
        if emotions is not None and isinstance(emotions, dict):
            stress = emotions.get("stress", 0.0)
            if stress > 0.7:
                cost *= 1.15

        return cost

    def _get_size_factor(self, person: "Person") -> float:
        """Obtiene el factor de tamaño basado en el genoma."""
        try:
            body_size = getattr(person.genome, "body_size", None)
            if body_size is not None:
                return 0.5 + (body_size * 1.5)
        except (AttributeError, TypeError):
            pass
        return 1.0

    # =========================================================================
    # INANICIÓN
    # =========================================================================

    def _check_starvation_death(
        self,
        person: "Person",
        delta_days: float,
    ) -> bool:
        """Verifica si un organismo debe morir por inanición."""
        starvation_days = person.starvation_days

        if starvation_days <= 0:
            return False

        threshold = self._get_param(
            "starvation_death_threshold", self.starvation_death_threshold
        )
        damage_rate = self._get_param(
            "starvation_damage_rate", self.starvation_damage_rate
        )

        if starvation_days < threshold:
            risk_factor = starvation_days / threshold
            death_probability = risk_factor * damage_rate * delta_days
        else:
            days_over = starvation_days - threshold
            death_probability = 0.5 + (days_over * 0.1)

        roll = random.random()
        return roll < death_probability

    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================

    def get_summary(self) -> Dict[str, int]:
        """Retorna un resumen de las estadísticas del sistema."""
        return {
            "total_energy_processed": self._total_energy_processed,
            "total_starvation_deaths": self._total_starvation_deaths,
            "total_photosynthesis_events": self._total_photosynthesis_events,
            "total_foraging_events": self._total_foraging_events,
        }

    def __repr__(self) -> str:
        return (
            f"EnergySystem("
            f"processed={self._total_energy_processed}, "
            f"photosynthesis={self._total_photosynthesis_events}, "
            f"foraging={self._total_foraging_events}, "
            f"starvation_deaths={self._total_starvation_deaths})"
        )