"""Tests unitarios para Narrative.current_strength().

Verifica el decaimiento temporal de las narrativas relacionales.
"""

import math
import pytest


class TestNarrativeDecay:
    """Tests del decaimiento de narrativas."""

    def test_no_decay_at_confirmation_day(self, make_narrative):
        """La fuerza no decae en el día de confirmación."""
        narr = make_narrative(strength=0.8, last_confirmed=0.0)
        assert narr.current_strength(0.0) == pytest.approx(0.8)

    def test_half_life_decay(self, make_narrative):
        """La fuerza se reduce a la mitad tras half_life_days."""
        narr = make_narrative(strength=0.8, last_confirmed=0.0, half_life_days=1825.0)
        assert narr.current_strength(1825.0) == pytest.approx(0.4, rel=1e-6)

    def test_double_half_life(self, make_narrative):
        """Tras dos half_lives, la fuerza es 1/4."""
        narr = make_narrative(strength=1.0, last_confirmed=0.0, half_life_days=100.0)
        assert narr.current_strength(200.0) == pytest.approx(0.25, rel=1e-6)

    def test_exponential_formula(self, make_narrative):
        """Verifica la fórmula exponencial completa."""
        narr = make_narrative(strength=1.0, last_confirmed=10.0, half_life_days=365.0)
        days_since = 100.0 - 10.0  # 90 días
        expected = 1.0 * math.exp(-days_since * math.log(2) / 365.0)
        assert narr.current_strength(100.0) == pytest.approx(expected, rel=1e-6)

    def test_strength_never_negative(self, make_narrative):
        """La fuerza nunca debe ser negativa."""
        narr = make_narrative(strength=0.5, last_confirmed=0.0, half_life_days=10.0)
        assert narr.current_strength(100000.0) >= 0.0

    def test_strength_bounded_by_initial(self, make_narrative):
        """La fuerza actual nunca supera la fuerza inicial."""
        narr = make_narrative(strength=0.6, last_confirmed=0.0)
        for day in [0.0, 100.0, 1000.0, 10000.0]:
            assert narr.current_strength(day) <= 0.6

    def test_recent_confirmation_stronger(self, make_narrative):
        """Una narrativa confirmada más recientemente es más fuerte."""
        narr_old = make_narrative(strength=0.8, last_confirmed=0.0, half_life_days=365.0)
        narr_new = make_narrative(strength=0.8, last_confirmed=300.0, half_life_days=365.0)
        
        current_day = 400.0
        assert narr_new.current_strength(current_day) > narr_old.current_strength(current_day)