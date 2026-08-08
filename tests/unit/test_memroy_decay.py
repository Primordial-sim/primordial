"""Tests unitarios para PersonalMemory.current_weight().

Verifica el decaimiento exponencial de las memorias:
- Fórmula: weight * exp(-days_ago * ln(2) / half_life_days)
- Memorias landmark, TRAUMA y ANCHOR no decaen
- El caché funciona correctamente
- El peso nunca es negativo
"""

import math
import pytest

from systems.relationships.relationship_model import (
    MemoryCategory,
    MemoryRole,
)


class TestMemoryDecay:
    """Tests del decaimiento temporal de memorias."""

    def test_no_decay_at_same_day(self, make_memory):
        """El peso no decae si se evalúa en el mismo día de creación."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        assert mem.current_weight(0.0) == pytest.approx(100.0)

    def test_half_life_decay(self, make_memory):
        """El peso se reduce exactamente a la mitad tras half_life_days."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        weight_at_half_life = mem.current_weight(90.0)
        assert weight_at_half_life == pytest.approx(50.0, rel=1e-6)

    def test_double_half_life_decay(self, make_memory):
        """Tras dos half_lives, el peso es 1/4 del original."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        weight = mem.current_weight(180.0)
        assert weight == pytest.approx(25.0, rel=1e-6)

    def test_exponential_formula(self, make_memory):
        """Verifica la fórmula exponencial completa."""
        mem = make_memory(weight=100.0, day=10.0, half_life=90.0)
        days_ago = 50.0 - 10.0  # 40 días
        expected = 100.0 * math.exp(-days_ago * math.log(2) / 90.0)
        assert mem.current_weight(50.0) == pytest.approx(expected, rel=1e-6)

    def test_landmark_no_decay(self, make_memory):
        """Las memorias landmark no decaen nunca."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0, is_landmark=True)
        assert mem.current_weight(3650.0) == pytest.approx(100.0)  # 10 años después

    def test_trauma_role_no_decay(self, make_memory):
        """Las memorias con rol TRAUMA no decaen."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0, role=MemoryRole.TRAUMA)
        assert mem.current_weight(3650.0) == pytest.approx(100.0)

    def test_anchor_role_no_decay(self, make_memory):
        """Las memorias con rol ANCHOR no decaen."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0, role=MemoryRole.ANCHOR)
        assert mem.current_weight(3650.0) == pytest.approx(100.0)

    def test_weight_never_negative(self, make_memory):
        """El peso nunca debe ser negativo, incluso tras mucho tiempo."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        weight = mem.current_weight(100000.0)  # ~274 años
        assert weight >= 0.0

    def test_cache_same_day(self, make_memory):
        """Llamar current_weight dos veces el mismo día usa el caché."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        w1 = mem.current_weight(45.0)
        w2 = mem.current_weight(45.0)
        assert w1 == pytest.approx(w2)

    def test_cache_invalidates_on_different_day(self, make_memory):
        """El caché se invalida al evaluar en un día diferente."""
        mem = make_memory(weight=100.0, day=0.0, half_life=90.0)
        w1 = mem.current_weight(45.0)
        w2 = mem.current_weight(90.0)
        assert w2 < w1  # Debe haber más decaimiento

    def test_zero_weight_memory(self, make_memory):
        """Una memoria con peso 0 siempre retorna 0."""
        mem = make_memory(weight=0.0, day=0.0, half_life=90.0)
        assert mem.current_weight(100.0) == pytest.approx(0.0)

    def test_very_short_half_life(self, make_memory):
        """Una half_life muy corta produce decaimiento rápido."""
        mem = make_memory(weight=100.0, day=0.0, half_life=1.0)
        assert mem.current_weight(1.0) == pytest.approx(50.0, rel=1e-6)
        assert mem.current_weight(10.0) == pytest.approx(100.0 / 1024.0, rel=1e-3)