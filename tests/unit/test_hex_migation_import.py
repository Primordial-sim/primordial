"""Test unitario: Verifica que los archivos modificados en la migración hexagonal
se pueden importar sin errores de sintaxis ni dependencias rotas.
"""

import importlib

import pytest


MODULES_TO_CHECK = [
    ("core.state.world_grid", "WorldGrid"),
    ("core.state.pending_changes", "PendingChanges"),
    ("entities.person.person", "Person"),
    ("systems.environment.tile_map", "TileMap"),
    ("systems.movement.movement_system", "MovementSystem"),
    ("core.state.world_state", "WorldState"),
]


@pytest.mark.parametrize("module_path,description", MODULES_TO_CHECK)
def test_module_imports_successfully(module_path, description):
    """Cada módulo modificado debe poder importarse sin errores."""
    try:
        importlib.import_module(module_path)
    except Exception as e:
        pytest.fail(f"Error importando {description} ({module_path}): {e}")


def test_person_has_q_and_r_attributes():
    """La clase Person debe tener los atributos q y r (no x e y)."""
    from unittest.mock import MagicMock

    from entities.person.person import Person

    config = MagicMock()
    config.time.adult_age_days = 18 * 365
    config.time.senior_age_days = 60 * 365

    person = Person(config=config, entity_id=1, q=5, r=7, age=25 * 365)

    assert hasattr(person, "q"), "Person debe tener atributo 'q'"
    assert hasattr(person, "r"), "Person debe tener atributo 'r'"
    assert person.q == 5
    assert person.r == 7


def test_person_set_position_uses_q_r():
    """set_position debe actualizar q y r, no x e y."""
    from unittest.mock import MagicMock

    from entities.person.person import Person

    config = MagicMock()
    config.time.adult_age_days = 18 * 365
    config.time.senior_age_days = 60 * 365

    person = Person(config=config, entity_id=1, q=0, r=0, age=25 * 365)
    person.set_position(10, 15)

    assert person.q == 10
    assert person.r == 15
    assert not hasattr(person, "x"), "Person no debe tener atributo 'x' tras migración"
    assert not hasattr(person, "y"), "Person no debe tener atributo 'y' tras migración"


def test_pending_changes_register_movement_uses_q_r():
    """register_movement debe aceptar coordenadas (q, r)."""
    from core.state.pending_changes import PendingChanges

    pending = PendingChanges()
    pending.register_movement(entity_id=42, q=7, r=3)

    assert pending.movements[42] == (7, 3)


def test_pending_changes_register_birth_uses_q_r():
    """register_birth debe aceptar coordenadas (q, r)."""
    from core.state.pending_changes import PendingChanges

    pending = PendingChanges()
    pending.register_birth(
        mother_id=1,
        father_id=2,
        q=10,
        r=20,
        genome=None,
    )

    assert len(pending.births) == 1
    assert pending.births[0]["q"] == 10
    assert pending.births[0]["r"] == 20


def test_world_grid_uses_hex_coordinates():
    """WorldGrid debe operar con coordenadas (q, r)."""
    from core.state.world_grid import WorldGrid

    grid = WorldGrid(width=10, height=10)
    grid._cells[(5, 5)] = ["agent_1"]

    assert grid.get_density_at(5, 5) == 1
    assert grid.get_density_at(0, 0) == 0


def test_world_grid_area_density_hexagonal():
    """get_area_density debe usar vecindad hexagonal, no cuadrada."""
    from core.state.world_grid import WorldGrid

    grid = WorldGrid(width=20, height=20)

    # Colocar agentes en el centro y sus 6 vecinos directos
    grid._cells[(10, 10)] = ["center"]
    for dq, dr in [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]:
        grid._cells[(10 + dq, 10 + dr)] = [f"neighbor_{dq}_{dr}"]

    # Radio 1 en hexagonal debe contar 7 celdas (centro + 6 vecinos)
    density = grid.get_area_density(10, 10, radius=1)
    assert density == 7, f"Radio 1 hexagonal debe tener 7 celdas, tiene {density}"