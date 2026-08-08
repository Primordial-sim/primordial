"""Tests unitarios para is_orientation_compatible().

Verifica la compatibilidad de orientaciones sexuales usando
la escala Kinsey (0-6).
"""

import pytest

from systems.relationships.relationship_model import (
    SexualOrientation,
    is_orientation_compatible,
)


class TestOrientationCompatibility:
    """Tests de compatibilidad de orientación sexual."""

    def test_hetero_hetero_compatible(self):
        """Dos heterosexuales son compatibles."""
        score = is_orientation_compatible(
            SexualOrientation.HETEROSEXUAL,
            SexualOrientation.HETEROSEXUAL,
        )
        assert score > 0.0

    def test_hetero_homo_incompatible(self):
        """Heterosexual + Homosexual = incompatible (score 0)."""
        score = is_orientation_compatible(
            SexualOrientation.HETEROSEXUAL,
            SexualOrientation.HOMOSEXUAL,
        )
        assert score == 0.0

    def test_homo_hetero_incompatible(self):
        """Homosexual + Heterosexual = incompatible (simétrico)."""
        score = is_orientation_compatible(
            SexualOrientation.HOMOSEXUAL,
            SexualOrientation.HETEROSEXUAL,
        )
        assert score == 0.0

    def test_bisexual_with_anyone(self):
        """Un bisexual es compatible con cualquier orientación."""
        for orientation in SexualOrientation:
            score = is_orientation_compatible(
                SexualOrientation.BISEXUAL,
                orientation,
            )
            assert score > 0.0, f"Bisexual debería ser compatible con {orientation}"

    def test_symmetry(self):
        """La compatibilidad es simétrica: f(a,b) == f(b,a)."""
        orientations = list(SexualOrientation)
        for o1 in orientations:
            for o2 in orientations:
                assert is_orientation_compatible(o1, o2) == is_orientation_compatible(o2, o1), \
                    f"Asimetría detectada: {o1} vs {o2}"

    def test_score_range(self):
        """El score siempre está en [0.0, 1.0]."""
        for o1 in SexualOrientation:
            for o2 in SexualOrientation:
                score = is_orientation_compatible(o1, o2)
                assert 0.0 <= score <= 1.0, \
                    f"Score fuera de rango: {score} para {o1} vs {o2}"

    def test_same_orientation_max_compatibility(self):
        """La misma orientación produce la máxima compatibilidad."""
        for orientation in SexualOrientation:
            score = is_orientation_compatible(orientation, orientation)
            # diff = 0, así que score = 1.0 - (0 / (tolerance + 3)) = 1.0
            assert score == pytest.approx(1.0), \
                f"Misma orientación {orientation} debería dar score 1.0"

    def test_kinsey_distance_reduces_compatibility(self):
        """Mayor distancia en la escala Kinsey = menor compatibilidad."""
        # Hetero (0) vs Mostly Hetero (1) → diff = 1
        score_near = is_orientation_compatible(
            SexualOrientation.HETEROSEXUAL,
            SexualOrientation.MOSTLY_HETERO,
        )
        # Hetero (0) vs Bisexual (3) → diff = 3
        score_far = is_orientation_compatible(
            SexualOrientation.HETEROSEXUAL,
            SexualOrientation.BISEXUAL,
        )
        assert score_near > score_far

    def test_extreme_diff_incompatible(self):
        """diff > 6.0 produce incompatibilidad (aunque no existe en Kinsey 0-6)."""
        # El máximo diff posible en Kinsey es 6 (HETERO vs HOMO)
        score = is_orientation_compatible(
            SexualOrientation.HETEROSEXUAL,
            SexualOrientation.HOMOSEXUAL,
        )
        assert score == 0.0

    def test_mostly_hetero_with_homo_low_compatibility(self):
        """Mostly Hetero (1) vs Homosexual (6) tiene baja compatibilidad."""
        score = is_orientation_compatible(
            SexualOrientation.MOSTLY_HETERO,
            SexualOrientation.HOMOSEXUAL,
        )
        # diff = 5, no es 0 pero es bajo
        assert score < 0.5