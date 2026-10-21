"""Test de integración: Smoke test de la migración hexagonal.

Ejecuta 5 ticks de simulación y verifica que el motor funciona correctamente
con coordenadas hexagonales (q, r) en lugar de cartesianas (x, y).
"""

import pytest


@pytest.mark.slow
def test_simulation_engine_smoke_with_hex_coordinates():
    """Ejecuta una simulación mínima y valida el estado hexagonal."""
    from core.engine.simulation_engine import SimulationEngine

    engine = SimulationEngine.create_default(
        width=20,
        height=20,
        founding_population_size=10,
        max_ticks=5,
    )
    engine.initialize()

    # Verificar que todos los agentes tienen q, r válidos
    persons = list(engine.state.get_all_persons())
    assert len(persons) == 10, f"Se esperaban 10 agentes, hay {len(persons)}"

    for p in persons:
        assert hasattr(p, "q"), f"Agente {p.entity_id} no tiene atributo 'q'"
        assert hasattr(p, "r"), f"Agente {p.entity_id} no tiene atributo 'r'"
        assert 0 <= p.q < 20, f"Agente {p.entity_id} tiene q={p.q} fuera de rango"
        assert 0 <= p.r < 20, f"Agente {p.entity_id} tiene r={p.r} fuera de rango"

    # Ejecutar 5 ticks
    for i in range(5):
        state = engine.step()
        assert "agents" in state
        assert "day" in state
        assert len(state["agents"]) > 0, f"Tick {i+1}: no hay agentes"

    # Verificar consistencia del mapa de ocupación
    for p in engine.state.get_all_persons():
        assert engine.state.is_cell_occupied(p.q, p.r), (
            f"Agente {p.entity_id} en ({p.q},{p.r}) no está marcado como ocupado"
        )


def test_world_state_occupancy_uses_q_r():
    """WorldState debe usar coordenadas (q, r) para el mapa de ocupación."""
    from unittest.mock import MagicMock

    from core.config.simulation_config import SimulationConfig
    from core.state.world_state import WorldState

    config = SimulationConfig()
    state = WorldState(config=config, width=10, height=10)

    # Crear un agente de prueba
    from entities.person.person import Person

    config.time.adult_age_days = 18 * 365
    config.time.senior_age_days = 60 * 365

    person = Person(config=config, entity_id=999, q=5, r=7, age=25 * 365)
    state.add_person(person)

    # Verificar que la ocupación usa (q, r)
    assert state.is_cell_occupied(5, 7)
    assert state.get_cell_occupant(5, 7) == 999
    assert not state.is_cell_occupied(0, 0)


def test_movement_system_uses_hexagonal_distance():
    """MovementSystem debe evaluar celdas usando distancia hexagonal."""
    from systems.movement.movement_system import MovementSystem

    # Verificar que las direcciones hexagonales están definidas
    from unittest.mock import MagicMock

    config = MagicMock()
    config.movement.eval_radius = 1
    config.movement.social_distance = 10.0
    config.environment.sector_size = 10
    config.movement.selection_temperature = 2.0

    system = MovementSystem(config=config)

    assert hasattr(system, "hex_directions")
    assert len(system.hex_directions) == 6, "Debe haber 6 direcciones hexagonales"

    # Verificar que las direcciones son las correctas
    expected = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    assert set(system.hex_directions) == set(expected)