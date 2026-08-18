"""Cargador y validador de escenarios de simulación.

Un escenario define qué especies participan, cuántos individuos hay de cada
una, y los parámetros globales de la simulación.

Formato:
    {
        "name": "Nombre del escenario",
        "description": "Descripción breve",
        "species": [{"id": "human", "count": 50}],
        "world": {"width": 100, "height": 100},
        "simulation": {"max_ticks": 1000, "delta_days": 1.0, "total_days": 3650},
        "environment": {"sector_size": 10}
    }
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.genetics.species_definition import SpeciesDefinition, SpeciesRegistry


@dataclass
class SpeciesConfig:
    """Configuración de una especie dentro de un escenario."""
    species_id: str
    count: int
    # Extensiones futuras:
    # min_age, max_age, initial_position, custom_traits...


@dataclass
class WorldConfig:
    """Configuración del mundo del escenario."""
    width: int = 100
    height: int = 100


@dataclass
class SimulationConfig:
    """Configuración de la ejecución."""
    max_ticks: Optional[int] = None
    delta_days: float = 1.0
    total_days: float = 3650.0


@dataclass
class EnvironmentConfig:
    """Configuración ambiental."""
    sector_size: int = 10


@dataclass
class Scenario:
    """Escenario completo de simulación."""
    name: str
    description: str
    species: List[SpeciesConfig]
    world: WorldConfig
    simulation: SimulationConfig
    environment: EnvironmentConfig
    raw: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_population(self) -> int:
        """Población total del escenario."""
        return sum(s.count for s in self.species)
    
    def __repr__(self) -> str:
        species_summary = ", ".join(f"{s.count}x {s.species_id}" for s in self.species)
        return f"Scenario('{self.name}': {species_summary})"


class ScenarioLoader:
    """Carga y valida escenarios desde archivos JSON."""
    
    _logger = logging.getLogger("ScenarioLoader")
    
    @classmethod
    def load(cls, filepath: str) -> Scenario:
        """Carga un escenario desde un archivo JSON.
        
        Args:
            filepath: Ruta al archivo JSON del escenario.
            
        Returns:
            Escenario validado.
            
        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el escenario es inválido.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Escenario no encontrado: {filepath}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls._parse(data, filepath)
    
    @classmethod
    def _parse(cls, data: Dict[str, Any], filepath: str) -> Scenario:
        """Parsea y valida los datos del escenario."""
        # Asegurar que SpeciesRegistry esté inicializado
        if not SpeciesRegistry.get_all():
            SpeciesRegistry.initialize_defaults()
        
        # Validar campos obligatorios
        if "name" not in data:
            raise ValueError(f"El escenario {filepath} no tiene campo 'name'")
        
        if "species" not in data:
            raise ValueError(f"El escenario {filepath} no tiene campo 'species'")
        
        # Parsear especies
        species_configs = []
        for species_data in data["species"]:
            species_id = species_data.get("id")
            count = species_data.get("count", 0)
            
            if not species_id:
                raise ValueError(f"Especie sin ID en {filepath}")
            
            # Validar que la especie existe
            if not SpeciesRegistry.has(species_id):
                available = ", ".join(SpeciesRegistry.get_all().keys())
                raise ValueError(
                    f"Especie '{species_id}' no encontrada. "
                    f"Arquetipos disponibles: {available}"
                )
            
            if count <= 0:
                raise ValueError(f"Count debe ser > 0 para '{species_id}'")
            
            species_configs.append(SpeciesConfig(
                species_id=species_id,
                count=count,
            ))
        
        # Parsear world
        world_data = data.get("world", {})
        world_config = WorldConfig(
            width=world_data.get("width", 100),
            height=world_data.get("height", 100),
        )
        
        # Parsear simulation
        sim_data = data.get("simulation", {})
        sim_config = SimulationConfig(
            max_ticks=sim_data.get("max_ticks"),
            delta_days=sim_data.get("delta_days", 1.0),
            total_days=sim_data.get("total_days", 3650.0),
        )
        
        # Parsear environment
        env_data = data.get("environment", {})
        env_config = EnvironmentConfig(
            sector_size=env_data.get("sector_size", 10),
        )
        
        scenario = Scenario(
            name=data["name"],
            description=data.get("description", ""),
            species=species_configs,
            world=world_config,
            simulation=sim_config,
            environment=env_config,
            raw=data,
        )
        
        cls._logger.info("✅ Escenario cargado: %s", scenario)
        return scenario
    
    @classmethod
    def list_scenarios(cls, directory: str = "scenarios") -> List[str]:
        """Lista todos los archivos de escenario en un directorio."""
        path = Path(directory)
        if not path.exists():
            return []
        return sorted(str(p) for p in path.glob("*.json"))