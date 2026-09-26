"""Tests para el sistema de métricas multidimensionales."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from systems.metrics.metrics_system import MetricsSystem


class _StubGenome:
    """Genoma mínimo con properties numéricas para la introspección."""

    def __init__(self, speed: float = 0.5, strength: float = 0.5) -> None:
        self._speed = speed
        self._strength = strength

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def strength(self) -> float:
        return self._strength


def make_person(entity_id, age=10.0, adult=True, senior=False, genome=None, **overrides):
    """Construye un organismo mock con todos los atributos que lee MetricsSystem."""
    person = MagicMock()
    person.entity_id = entity_id
    person.age = age
    person.is_adult = adult
    person.is_senior = senior
    person.genome = genome if genome is not None else _StubGenome()
    person.is_sick = False
    person.active_infections = {}
    person.memory = {}
    person.emotions = {}
    person.is_pregnant = False
    person.litter_size_gestating = 0
    person.is_fertile = MagicMock(return_value=False)
    person.marital_status = "soltero"
    person.parents = []
    person.adoptive_parents = []
    for key, value in overrides.items():
        setattr(person, key, value)
    return person


def make_state(persons, day):
    """Construye un WorldState mock con los agentes y el día indicados."""
    state = MagicMock()
    state.world_days_elapsed = day
    state.get_all_persons = MagicMock(return_value=persons)
    return state


@pytest.fixture
def config():
    cfg = MagicMock()
    cfg.metrics.snapshot_interval_days = 1.0
    cfg.metrics.max_history_size = 1000
    return cfg


@pytest.fixture
def pending():
    buffer = MagicMock()
    buffer.deaths = set()
    buffer.births = []
    return buffer


@pytest.fixture
def context():
    return SimpleNamespace()


@pytest.fixture
def ecology_system():
    system = MagicMock()
    system.get_summary = MagicMock(return_value={
        "total_encounters": 42,
        "total_relationships_executed": 17,
        "total_predations": 5,
        "total_herbivory": 6,
        "total_mutualism": 3,
        "total_competition": 3,
        "cached_relationship_pairs": 8,
    })
    return system


class TestMetricsSystemBasics:
    """Tests del ciclo de snapshots y demografía."""

    def test_initial_history_empty(self, config):
        """Sin procesar, no hay historial ni último snapshot."""
        system = MetricsSystem(config)
        assert system.history == []
        assert system.get_latest_metrics() == {}

    def test_first_snapshot_records_population(self, config, pending, context):
        """El primer proceso genera un snapshot con la población viva."""
        persons = [make_person(1), make_person(2)]
        system = MetricsSystem(config)

        system.process(make_state(persons, 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        assert len(system.history) == 1
        snapshot = system.get_latest_metrics()
        assert snapshot["population"] == 2
        assert snapshot["day"] == 0.0

    def test_respects_snapshot_interval(self, config, pending, context):
        """No se toma snapshot antes del intervalo configurado."""
        persons = [make_person(1)]
        system = MetricsSystem(config)

        system.process(make_state(persons, 0.0), pending, 1.0, context)  # type: ignore[arg-type]
        system.process(make_state(persons, 0.5), pending, 0.5, context)  # type: ignore[arg-type]
        system.process(make_state(persons, 1.0), pending, 0.5, context)  # type: ignore[arg-type]

        assert len(system.history) == 2
        assert [s["day"] for s in system.history] == [0.0, 1.0]

    def test_excludes_deceased_from_population(self, config, pending, context):
        """Las entidades en pending.deaths no cuentan como población."""
        persons = [make_person(1), make_person(2)]
        pending.deaths = {2}
        system = MetricsSystem(config)

        system.process(make_state(persons, 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        assert system.get_latest_metrics()["population"] == 1

    def test_growth_rate_between_snapshots(self, config, pending, context):
        """La tasa de crecimiento compara poblaciones de snapshots consecutivos."""
        system = MetricsSystem(config)

        system.process(make_state([make_person(1), make_person(2)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]
        system.process(
            make_state([make_person(1), make_person(2), make_person(3), make_person(4)], 1.0),
            pending, 1.0, context,  # type: ignore[arg-type]
        )

        latest = system.get_latest_metrics()
        assert latest["population_delta"] == 2
        assert latest["growth_rate_percent"] == 100.0

    def test_empty_world_does_not_crash(self, config, pending, context):
        """Un mundo extinto (0 organismos) produce snapshot en ceros, no un crash."""
        system = MetricsSystem(config)

        system.process(make_state([], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        snapshot = system.get_latest_metrics()
        assert snapshot["population"] == 0
        assert snapshot["ecology"]["total_encounters"] == 0


class TestEcologyMetrics:
    """Tests específicos de las métricas de ecología."""

    def test_ecology_metrics_copied_from_system(self, config, pending, context, ecology_system):
        """El snapshot copia el resumen completo del sistema de ecología."""
        system = MetricsSystem(config, ecology_system=ecology_system)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        ecology = system.get_latest_metrics()["ecology"]
        assert ecology["total_encounters"] == 42
        assert ecology["total_relationships_executed"] == 17
        assert ecology["total_predations"] == 5
        assert ecology["total_herbivory"] == 6
        assert ecology["total_mutualism"] == 3
        assert ecology["total_competition"] == 3
        assert ecology["cached_relationship_pairs"] == 8

    def test_ecology_metrics_zero_without_system(self, config, pending, context):
        """Sin sistema de ecología inyectado, todas las métricas quedan en cero."""
        system = MetricsSystem(config, ecology_system=None)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        ecology = system.get_latest_metrics()["ecology"]
        assert all(value == 0 for value in ecology.values())

    def test_ecology_metrics_default_missing_keys(self, config, pending, context):
        """Un resumen vacío no rompe el snapshot: todo queda en cero."""
        empty = MagicMock()
        empty.get_summary = MagicMock(return_value={})
        system = MetricsSystem(config, ecology_system=empty)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        ecology = system.get_latest_metrics()["ecology"]
        assert all(value == 0 for value in ecology.values())

    def test_ecology_metrics_partial_summary(self, config, pending, context):
        """Un resumen parcial copia lo presente y deja a cero lo ausente."""
        partial = MagicMock()
        partial.get_summary = MagicMock(return_value={"total_predations": 9})
        system = MetricsSystem(config, ecology_system=partial)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        ecology = system.get_latest_metrics()["ecology"]
        assert ecology["total_predations"] == 9
        assert ecology["total_encounters"] == 0

    def test_ecology_metrics_per_snapshot(self, config, pending, context):
        """Cada snapshot guarda el estado ecológico de su momento."""
        evolving = MagicMock()
        evolving.get_summary = MagicMock(side_effect=[
            {"total_predations": 1},
            {"total_predations": 4},
        ])
        system = MetricsSystem(config, ecology_system=evolving)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]
        system.process(make_state([make_person(1)], 1.0), pending, 1.0, context)  # type: ignore[arg-type]

        assert system.history[0]["ecology"]["total_predations"] == 1
        assert system.history[1]["ecology"]["total_predations"] == 4


class TestOtherDimensions:
    """Tests de dimensiones complementarias del snapshot."""

    def test_spatial_metrics_from_pressure_map(self, config, pending):
        """Las métricas espaciales se derivan del mapa de presión del contexto."""
        context = SimpleNamespace(pressure_map={(0, 0): 2.0, (1, 1): 1.0})
        system = MetricsSystem(config)

        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        spatial = system.get_latest_metrics()["spatial"]
        assert spatial["avg_pressure"] == 1.5
        assert spatial["max_pressure"] == 2.0
        assert spatial["overcrowded_sectors"] == 1

    def test_history_limit_enforced(self, config, pending, context):
        """El historial respeta max_history_size descartando lo más antiguo."""
        config.metrics.max_history_size = 3
        system = MetricsSystem(config)

        for day in range(5):
            system.process(make_state([make_person(1)], float(day)), pending, 1.0, context)  # type: ignore[arg-type]

        assert len(system.history) == 3
        assert [s["day"] for s in system.history] == [2.0, 3.0, 4.0]

    def test_gene_averages_via_introspection(self, config, pending, context):
        """La introspección detecta properties numéricas y calcula media y varianza."""
        persons = [
            make_person(1, genome=_StubGenome(speed=0.4, strength=0.8)),
            make_person(2, genome=_StubGenome(speed=0.6, strength=0.8)),
        ]
        system = MetricsSystem(config)

        system.process(make_state(persons, 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        snapshot = system.get_latest_metrics()
        assert snapshot["gene_averages"]["speed"] == 0.5
        assert snapshot["gene_averages"]["strength"] == 0.8
        assert snapshot["genetic_diversity"]["speed"] == 0.01
        assert snapshot["genetic_diversity"]["strength"] == 0.0

    def test_export_to_json(self, config, pending, context, tmp_path):
        """La exportación JSON vuelca el historial completo y legible."""
        system = MetricsSystem(config)
        system.process(make_state([make_person(1)], 0.0), pending, 1.0, context)  # type: ignore[arg-type]

        filepath = tmp_path / "metrics.json"
        system.export_to_json(str(filepath))

        loaded = json.loads(filepath.read_text(encoding="utf-8"))
        assert loaded == system.history