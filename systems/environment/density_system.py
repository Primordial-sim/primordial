"""Módulo de servicios espaciales para consultas de densidad poblacional.

Provee algoritmos de búsqueda y consulta de densidad espacial.
Aunque su método process() está vacío (no modifica estado), proporciona
métodos de utilidad que otros sistemas pueden usar como dependencias inyectadas.

MIGRACIÓN HEXAGONAL:
- Coordenadas (x, y) → (q, r)
- Los sectores ahora se calculan con q // sector_size, r // sector_size
"""

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class DensitySystem:
    """Provee algoritmos de búsqueda y consulta de densidad espacial."""

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el sistema vinculándolo a la configuración central.
        
        Args:
            config: Configuración centralizada de la simulación.
        """
        self.config = config

    def get_density_factor(self, q: int, r: int, context: EnvironmentContext) -> float:
        """Calcula matemáticamente la ocupación real de un sector en base a su capacidad.
        
        HEX: Usa coordenadas hexagonales (q, r) en lugar de cartesianas (x, y).
        
        Args:
            q: Coordenada Q (hexagonal).
            r: Coordenada R (hexagonal).
            context: Contexto ambiental del tick.
            
        Returns:
            Factor de densidad (0.0 = vacío, 1.0 = capacidad máxima, >1.0 = sobrepoblado).
        """
        env_cfg = self.config.environment

        # HEX: Convertir coordenadas hexagonales a coordenadas de sector
        sector_q = q // env_cfg.sector_size
        sector_r = r // env_cfg.sector_size

        # Consultamos el censo del sector en O(1) gracias al mapa del contexto
        agents = context.sector_map.get((sector_q, sector_r), [])

        # Retornamos el factor (0.0 = vacío, >1.0 = sobrepoblado)
        return len(agents) / max(1, env_cfg.max_agents_per_sector)

    def find_best_nearby_cell(
        self,
        q: int,
        r: int,
        radius: int,
        mode: str,
        width: int,
        height: int,
        context: EnvironmentContext,
    ) -> tuple:
        """Busca la coordenada óptima en un radio dado según criterios de densidad.
        
        HEX: Usa coordenadas hexagonales (q, r) y busca en un patrón hexagonal.
        
        Args:
            q: Coordenada Q de origen (hexagonal).
            r: Coordenada R de origen (hexagonal).
            radius: Radio de búsqueda en celdas hexagonales.
            mode: 'min' (huida/aislamiento), 'max' (búsqueda de comunidad/gregarismo).
            width: Ancho del mapa.
            height: Alto del mapa.
            context: Contexto ambiental del tick.
            
        Returns:
            Tupla (q, r) de la mejor celda encontrada.
        """
        best_cell = (q, r)
        best_value = self.get_density_factor(q, r, context)

        # HEX: Bucle de rango hexagonal en lugar de cuadrado
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                nq = q + dq
                nr = r + dr

                # Descartamos coordenadas fuera de los límites del mapa
                if 0 <= nq < width and 0 <= nr < height:
                    current_value = self.get_density_factor(nq, nr, context)

                    if mode == "min" and current_value < best_value:
                        best_value = current_value
                        best_cell = (nq, nr)
                    elif mode == "max" and current_value > best_value:
                        best_value = current_value
                        best_cell = (nq, nr)

        return best_cell

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Cumple el contrato de la interfaz base sin realizar mutaciones directas.
        
        DensitySystem es un sistema de consulta, no modifica estado.
        Su propósito es proveer métodos de utilidad a otros sistemas.
        """