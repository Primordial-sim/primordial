"""Tests de integración para el sistema de tiles y biomas.

Estos tests validan que el sistema de tiles se integra correctamente
con WorldState y EnvironmentContext, y que la generación procedural
produce resultados coherentes.
"""

import pytest
from core.config.simulation_config import SimulationConfig
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.environment.world_config import WorldConfig
from systems.environment.biome_classifier import Biome


class TestTileIntegration:
    """Tests de integración del sistema de tiles con WorldState."""

    def test_world_state_initializes_tile_map(self):
        """WorldState puede inicializar un mapa de tiles."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)

        # Inicializar mapa de tiles
        state.initialize_tile_map()

        assert state.has_tile_map()
        assert state.tile_map is not None
        assert state.tile_map.get_tile_count() == 50 * 50

    def test_world_state_get_tile_at(self):
        """WorldState puede consultar tiles por coordenadas."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)
        state.initialize_tile_map()

        tile = state.get_tile_at(25, 25)

        assert tile is not None
        assert hasattr(tile, 'temperature')
        assert hasattr(tile, 'water')
        assert hasattr(tile, 'vegetation')

    def test_world_state_custom_world_config(self):
        """WorldState acepta WorldConfig personalizado."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)

        # Crear mundo desértico
        desert_config = WorldConfig(
            mean_temperature=0.9,
            global_humidity=0.2,
            water_coverage=0.3,
        )

        state.initialize_tile_map(world_config=desert_config)

        # Verificar que hay tiles y que el mapa se inicializó
        assert state.has_tile_map()
        assert state.tile_map is not None
        assert state.tile_map.get_tile_count() == 50 * 50


class TestEnvironmentContextTiles:
    """Tests de integración de tiles con EnvironmentContext."""

    def test_environment_context_has_tile_map(self):
        """EnvironmentContext tiene acceso al mapa de tiles."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)
        state.initialize_tile_map()

        context = EnvironmentContext(state=state, config=config)

        assert context.has_tile_map()

    def test_environment_context_get_tile_at(self):
        """EnvironmentContext puede consultar tiles."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)
        state.initialize_tile_map()

        context = EnvironmentContext(state=state, config=config)
        tile = context.get_tile_at(25, 25)

        assert tile is not None
        assert hasattr(tile, 'height')

    def test_environment_context_get_biome_at(self):
        """EnvironmentContext puede consultar biomas."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)
        state.initialize_tile_map()

        context = EnvironmentContext(state=state, config=config)
        biome = context.get_biome_at(25, 25)

        assert biome is not None
        assert isinstance(biome, Biome)

    def test_environment_context_get_biome_name(self):
        """EnvironmentContext puede obtener nombres de biomas."""
        config = SimulationConfig()
        state = WorldState(config=config, width=50, height=50)
        state.initialize_tile_map()

        context = EnvironmentContext(state=state, config=config)
        biome_name = context.get_biome_name_at(25, 25)

        assert isinstance(biome_name, str)
        assert len(biome_name) > 0
        assert biome_name != "unknown"

    def test_biome_variety_in_map(self):
        """El mapa generado tiene variedad de biomas."""
        config = SimulationConfig()
        state = WorldState(config=config, width=100, height=100)
        state.initialize_tile_map(seed=42)

        context = EnvironmentContext(state=state, config=config)

        # Muestrear biomas en diferentes posiciones
        biomes_found = set()
        sample_positions = [
            (10, 10), (50, 50), (90, 90),
            (10, 90), (90, 10), (50, 10),
            (10, 50), (90, 50), (50, 90),
        ]

        for x, y in sample_positions:
            biome = context.get_biome_at(x, y)
            if biome:
                biomes_found.add(biome)

        # Deberíamos encontrar al menos 3 biomas diferentes
        assert len(biomes_found) >= 3

    def test_ocean_tiles_have_high_water(self):
        """Los tiles de océano tienen water alto."""
        config = SimulationConfig()
        state = WorldState(config=config, width=100, height=100)
        state.initialize_tile_map()

        context = EnvironmentContext(state=state, config=config)

        ocean_count = 0
        low_water_count = 0
        for x in range(100):
            for y in range(100):
                biome = context.get_biome_at(x, y)
                if biome in [Biome.OCEAN, Biome.DEEP_OCEAN]:
                    tile = context.get_tile_at(x, y)
                    if tile is not None:
                        if tile.water > 0.7:
                            ocean_count += 1
                        else:
                            low_water_count += 1

        # Debería haber al menos algunos océanos con water alto
        assert ocean_count > 0, (
            f"No se encontraron océanos con water > 0.7. "
            f"Océanos con water bajo: {low_water_count}"
        )

    def test_deterministic_generation_with_seed(self):
        """La generación es determinista con la misma semilla."""
        config = SimulationConfig()

        # Generar dos mapas con la misma semilla
        state1 = WorldState(config=config, width=50, height=50)
        state1.initialize_tile_map(seed=123)
        context1 = EnvironmentContext(state=state1, config=config)

        state2 = WorldState(config=config, width=50, height=50)
        state2.initialize_tile_map(seed=123)
        context2 = EnvironmentContext(state=state2, config=config)

        # Comparar tiles en varias posiciones
        test_positions = [(10, 10), (25, 25), (40, 40)]
        for x, y in test_positions:
            tile1 = context1.get_tile_at(x, y)
            tile2 = context2.get_tile_at(x, y)

            assert tile1 is not None
            assert tile2 is not None
            assert abs(tile1.height - tile2.height) < 0.01
            assert abs(tile1.temperature - tile2.temperature) < 0.01
            assert abs(tile1.water - tile2.water) < 0.01

    def test_different_seeds_produce_different_maps(self):
        """Diferentes semillas producen mapas diferentes."""
        config = SimulationConfig()

        state1 = WorldState(config=config, width=50, height=50)
        state1.initialize_tile_map(seed=123)
        context1 = EnvironmentContext(state=state1, config=config)

        state2 = WorldState(config=config, width=50, height=50)
        state2.initialize_tile_map(seed=456)
        context2 = EnvironmentContext(state=state2, config=config)

        # Al menos algunos tiles deben ser diferentes
        differences = 0
        for x in range(50):
            for y in range(50):
                tile1 = context1.get_tile_at(x, y)
                tile2 = context2.get_tile_at(x, y)

                if tile1 and tile2:
                    if abs(tile1.height - tile2.height) > 10.0:
                        differences += 1

        # Debería haber diferencias significativas
        assert differences > 100