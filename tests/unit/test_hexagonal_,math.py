"""Test unitario: Validación matemática de coordenadas hexagonales axiales.

Verifica que las fórmulas de distancia y vecindad hexagonal que usaremos
en la migración son correctas antes de tocar el motor.
"""

import pytest


def get_hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Calcula la distancia hexagonal entre dos celdas axiales."""
    dq = q1 - q2
    dr = r1 - r2
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def get_hex_neighbors(q: int, r: int, radius: int) -> list:
    """Genera todas las celdas vecinas en un radio dado (incluye el centro)."""
    neighbors = []
    for dq in range(-radius, radius + 1):
        dr_min = max(-radius, -dq - radius)
        dr_max = min(radius, -dq + radius)
        for dr in range(dr_min, dr_max + 1):
            neighbors.append((q + dq, r + dr))
    return neighbors


# Direcciones hexagonales axiales (los 6 vecinos directos)
HEX_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


class TestHexagonalDistance:
    """Tests para la función de distancia hexagonal."""

    def test_distance_to_self_is_zero(self):
        """La distancia de una celda a sí misma debe ser 0."""
        assert get_hex_distance(0, 0, 0, 0) == 0
        assert get_hex_distance(5, 3, 5, 3) == 0
        assert get_hex_distance(-10, 7, -10, 7) == 0

    @pytest.mark.parametrize("dq,dr", HEX_DIRECTIONS)
    def test_adjacent_cells_have_distance_one(self, dq, dr):
        """Las 6 celdas adyacentes directas deben tener distancia 1."""
        assert get_hex_distance(0, 0, dq, dr) == 1

    def test_distance_two_cases(self):
        """Celdas a distancia 2 deben dar 2."""
        assert get_hex_distance(0, 0, 2, 0) == 2
        assert get_hex_distance(0, 0, 1, 1) == 2
        assert get_hex_distance(0, 0, 0, 2) == 2
        assert get_hex_distance(0, 0, -1, 2) == 2
        assert get_hex_distance(0, 0, -2, 2) == 2
        assert get_hex_distance(0, 0, -2, 0) == 2

    def test_symmetry(self):
        """La distancia debe ser simétrica: d(A,B) = d(B,A)."""
        pairs = [
            ((0, 0), (3, 2)),
            ((5, 5), (2, 7)),
            ((10, 0), (0, 10)),
            ((-3, 4), (7, -2)),
        ]
        for (q1, r1), (q2, r2) in pairs:
            assert get_hex_distance(q1, r1, q2, r2) == get_hex_distance(q2, r2, q1, r1)

    def test_triangle_inequality(self):
        """La distancia debe cumplir la desigualdad triangular: d(A,C) <= d(A,B) + d(B,C)."""
        a, b, c = (0, 0), (2, 1), (3, 3)
        d_ab = get_hex_distance(*a, *b)
        d_bc = get_hex_distance(*b, *c)
        d_ac = get_hex_distance(*a, *c)
        assert d_ac <= d_ab + d_bc


class TestHexagonalNeighbors:
    """Tests para el bucle de vecindad hexagonal."""

    def test_radius_zero_returns_only_center(self):
        """Radio 0 debe devolver solo la celda central."""
        neighbors = get_hex_neighbors(5, 5, 0)
        assert neighbors == [(5, 5)]

    def test_radius_one_has_seven_cells(self):
        """Radio 1 debe devolver exactamente 7 celdas (centro + 6 vecinos)."""
        neighbors = get_hex_neighbors(0, 0, 1)
        assert len(neighbors) == 7
        assert (0, 0) in neighbors
        for dq, dr in HEX_DIRECTIONS:
            assert (dq, dr) in neighbors

    def test_radius_two_has_nineteen_cells(self):
        """Radio 2 debe devolver exactamente 19 celdas."""
        neighbors = get_hex_neighbors(0, 0, 2)
        assert len(neighbors) == 19

    def test_radius_three_has_thirty_seven_cells(self):
        """Radio 3 debe devolver exactamente 37 celdas."""
        neighbors = get_hex_neighbors(0, 0, 3)
        assert len(neighbors) == 37

    def test_radius_formula(self):
        """Verifica la fórmula general: 3*r*(r+1) + 1 celdas en radio r."""
        for r in range(6):
            expected = 3 * r * (r + 1) + 1
            assert len(get_hex_neighbors(0, 0, r)) == expected

    def test_neighbors_offset_by_center(self):
        """Los vecinos deben desplazarse correctamente según el centro."""
        center_q, center_r = 10, 20
        neighbors = get_hex_neighbors(center_q, center_r, 1)
        assert (center_q, center_r) in neighbors
        for dq, dr in HEX_DIRECTIONS:
            assert (center_q + dq, center_r + dr) in neighbors