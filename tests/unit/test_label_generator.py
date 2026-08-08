"""Tests unitarios para LabelGenerator.generate().

Verifica que las etiquetas emergen correctamente según los umbrales
de peso acumulado por categoría de memoria.
"""

import pytest

from systems.relationships.relationship_model import (
    LabelGenerator,
    MemoryCategory,
    MemoryRole,
)


class TestLabelGenerator:
    """Tests de generación de etiquetas emergentes."""

    def test_empty_relationship_unknown(self, make_relationship):
        """Una relación sin memorias produce la etiqueta 'Desconocido'."""
        rel = make_relationship(memories=[])
        labels = LabelGenerator.generate(rel, 0.0)
        assert labels == ["Desconocido"]

    def test_low_weight_relationship_acquaintance(self, make_relationship, make_memory):
        """Una relación con memorias de bajo peso produce 'Conocido'."""
        # 1 memoria de cooperación con peso bajo (< 80)
        mem = make_memory(weight=20.0, day=0.0, category=MemoryCategory.COOPERATION)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Conocido" in labels

    def test_romantic_high_weight_amante(self, make_relationship, make_memory):
        """romantic_weight > 250 produce la etiqueta 'Amante'."""
        mem = make_memory(weight=300.0, day=0.0, category=MemoryCategory.ROMANTIC)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Amante" in labels

    def test_romantic_medium_weight_interes(self, make_relationship, make_memory):
        """80 < romantic_weight <= 250 produce 'Interés Romántico'."""
        mem = make_memory(weight=120.0, day=0.0, category=MemoryCategory.ROMANTIC)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Interés Romántico" in labels
        assert "Amante" not in labels

    def test_conflict_high_weight_rival(self, make_relationship, make_memory):
        """conflict_weight > 150 produce la etiqueta 'Rival'."""
        mem = make_memory(
            weight=200.0, day=0.0,
            category=MemoryCategory.CONFLICT, valence=-1.0,
        )
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Rival" in labels

    def test_conflict_and_cooperation_rival_respetado(self, make_relationship, make_memory):
        """conflict > 60 y cooperation > 60 produce 'Rival Respetado'."""
        mem_conflict = make_memory(
            weight=80.0, day=0.0,
            category=MemoryCategory.CONFLICT, valence=-1.0,
        )
        mem_coop = make_memory(
            weight=80.0, day=0.0,
            category=MemoryCategory.COOPERATION, valence=1.0,
        )
        rel = make_relationship(memories=[mem_conflict, mem_coop])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Rival Respetado" in labels

    def test_cooperation_high_weight_amigo(self, make_relationship, make_memory):
        """cooperation > 200 y conflict < 100 produce 'Amigo'."""
        mem = make_memory(weight=250.0, day=0.0, category=MemoryCategory.COOPERATION)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Amigo" in labels

    def test_cooperation_medium_weight_aliado(self, make_relationship, make_memory):
        """80 < cooperation <= 200 produce 'Aliado'."""
        mem = make_memory(weight=120.0, day=0.0, category=MemoryCategory.COOPERATION)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Aliado" in labels
        assert "Amigo" not in labels

    def test_family_high_weight_familia_elegida(self, make_relationship, make_memory):
        """family_weight > 150 produce 'Familia Elegida'."""
        mem = make_memory(weight=200.0, day=0.0, category=MemoryCategory.FAMILY)
        rel = make_relationship(memories=[mem])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Familia Elegida" in labels

    def test_multiple_labels_can_coexist(self, make_relationship, make_memory):
        """Un agente puede tener múltiples etiquetas simultáneamente."""
        mem_romantic = make_memory(weight=300.0, day=0.0, category=MemoryCategory.ROMANTIC)
        mem_coop = make_memory(weight=250.0, day=0.0, category=MemoryCategory.COOPERATION)
        rel = make_relationship(memories=[mem_romantic, mem_coop])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Amante" in labels
        assert "Amigo" in labels

    def test_decay_affects_labels(self, make_relationship, make_memory):
        """Las etiquetas cambian cuando las memorias decaen."""
        # Memoria romántica con half_life corta
        mem = make_memory(
            weight=300.0, day=0.0, half_life=30.0,
            category=MemoryCategory.ROMANTIC,
        )
        rel = make_relationship(memories=[mem])
        
        # En el día 0: debería ser Amante
        labels_day0 = LabelGenerator.generate(rel, 0.0)
        assert "Amante" in labels_day0
        
        # Tras 10 half_lives (300 días): peso ≈ 0.29, ya no es Amante
        labels_late = LabelGenerator.generate(rel, 300.0)
        assert "Amante" not in labels_late

    def test_cooperation_with_high_conflict_not_amigo(self, make_relationship, make_memory):
        """cooperation > 200 pero conflict >= 100 NO produce 'Amigo'."""
        mem_coop = make_memory(weight=250.0, day=0.0, category=MemoryCategory.COOPERATION)
        mem_conflict = make_memory(
            weight=120.0, day=0.0,
            category=MemoryCategory.CONFLICT, valence=-1.0,
        )
        rel = make_relationship(memories=[mem_coop, mem_conflict])
        labels = LabelGenerator.generate(rel, 0.0)
        assert "Amigo" not in labels