"""Tests para Tile, WorldConfig y BiomeClassifier."""

import pytest
from systems.environment.tile import Tile
from systems.environment.world_config import WorldConfig
from systems.environment.biome_classifier import BiomeClassifier, Biome


class TestTile:
    """Tests para el modelo Tile."""
    
    def test_tile_creation_default(self):
        """Un tile por defecto tiene valores razonables."""
        tile = Tile()
        assert tile.height == 0.0
        assert tile.temperature == 0.5
        assert tile.water == 0.0
    
    def test_tile_creation_custom(self):
        """Un tile puede crearse con valores personalizados."""
        tile = Tile(height=100.0, temperature=0.8, water=0.9)
        assert tile.height == 100.0
        assert tile.temperature == 0.8
        assert tile.water == 0.9
    
    def test_tile_normalize(self):
        """normalize() asegura que los valores estén en [0.0, 1.0]."""
        tile = Tile(temperature=1.5, humidity=-0.2, vegetation=2.0)
        tile.normalize()
        assert tile.temperature == 1.0
        assert tile.humidity == 0.0
        assert tile.vegetation == 1.0
    
    def test_tile_to_dict(self):
        """to_dict() serializa correctamente el tile."""
        tile = Tile(height=50.0, temperature=0.7)
        data = tile.to_dict()
        assert data['height'] == 50.0
        assert data['temperature'] == 0.7
        assert 'water' in data


class TestWorldConfig:
    """Tests para WorldConfig."""
    
    def test_world_config_defaults(self):
        """WorldConfig tiene valores por defecto razonables."""
        config = WorldConfig()
        assert config.gravity == 1.0
        assert config.mean_temperature == 0.5
        assert 0.0 <= config.water_coverage <= 1.0
    
    def test_world_config_custom(self):
        """WorldConfig puede crearse con valores personalizados."""
        config = WorldConfig(gravity=0.5, mean_temperature=0.8)
        assert config.gravity == 0.5
        assert config.mean_temperature == 0.8


class TestBiomeClassifier:
    """Tests para BiomeClassifier."""
    
    def test_classify_deep_ocean(self):
        """Agua profunda + altura negativa = océano profundo."""
        tile = Tile(water=0.95, height=-100.0, salinity=0.9)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.DEEP_OCEAN
    
    def test_classify_ocean(self):
        """Agua alta + salinidad alta = océano."""
        tile = Tile(water=0.85, salinity=0.8, height=-20.0)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.OCEAN
    
    def test_classify_lake(self):
        """Agua alta + salinidad baja = lago."""
        tile = Tile(water=0.8, salinity=0.1, height=50.0)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.LAKE
    
    def test_classify_desert(self):
        """Temperatura alta + humedad baja + sin vegetación = desierto."""
        tile = Tile(temperature=0.8, humidity=0.2, vegetation=0.05, water=0.0)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.DESERT
    
    def test_classify_rainforest(self):
        """Temperatura alta + humedad alta + vegetación densa = selva."""
        tile = Tile(temperature=0.8, humidity=0.8, vegetation=0.9)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.RAINFOREST
    
    def test_classify_forest(self):
        """Vegetación alta = bosque."""
        tile = Tile(vegetation=0.7, temperature=0.5, humidity=0.5)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.FOREST
    
    def test_classify_tundra(self):
        """Temperatura muy baja + poca vegetación = tundra."""
        tile = Tile(temperature=0.2, vegetation=0.1, height=100.0)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.TUNDRA
    
    def test_classify_mountain(self):
        """Altitud alta = montaña."""
        tile = Tile(height=1800.0, temperature=0.3, vegetation=0.2)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.MOUNTAIN
    
    def test_classify_snow_peak(self):
        """Altitud muy alta + frío extremo = pico nevado."""
        tile = Tile(height=2500.0, temperature=0.1)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.SNOW_PEAK
    
    def test_classify_grassland_default(self):
        """Condiciones moderadas = pradera."""
        tile = Tile(temperature=0.5, humidity=0.5, vegetation=0.4)
        biome = BiomeClassifier.classify(tile)
        assert biome == Biome.GRASSLAND
    
    def test_get_biome_name(self):
        """get_biome_name() retorna el nombre como string."""
        tile = Tile(temperature=0.8, humidity=0.2, vegetation=0.05, water=0.0)
        name = BiomeClassifier.get_biome_name(tile)
        assert name == "desert"