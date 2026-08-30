"""Benchmarks para el ExperienceGenerator (Fase 3)."""

from __future__ import annotations

import random
import time
from unittest.mock import Mock
from typing import List

from systems.relationships.experience_generator import ExperienceGenerator
from systems.relationships.relationship_model import (
    Relationship,
    MemoryCategory,
    PersonalMemory,
    MemoryRole,
)


def _create_cooperation_memory(
    owner_id: int,
    partner_id: int,
    day: float,
    event_id: int,
) -> PersonalMemory:
    """Crea un recuerdo de cooperación para testing."""
    return PersonalMemory(
        world_event_id=event_id,
        owner_id=owner_id,
        partner_id=partner_id,
        perceived_intensity=0.7,
        emotional_valence=0.8,
        personal_weight=50.0,
        category=MemoryCategory.COOPERATION,
        day=day,
        context="cooperacion",
        event_type="cooperation",
        source_system="test",
        role=MemoryRole.NORMAL,
        half_life_days=180.0,
    )


def test_experience_generation() -> None:
    """Valida que el ExperienceGenerator genera experiencias basadas en etiquetas."""
    print("[Benchmark 3.1] Validación de ExperienceGenerator")
    
    config = Mock()
    relationship_engine = Mock()
    
    generator = ExperienceGenerator(config, relationship_engine)
    
    # Crear agente mock con relación
    agent = Mock()
    agent.entity_id = 1
    agent.x = 10
    agent.y = 10
    
    # GENÉTICA UNIVERSAL: Configurar genoma mock para SocialCapabilities
    agent.genome = Mock()
    agent.genome.has_trait.return_value = True
    agent.genome.get_trait_value.return_value = 0.9
    
    partner = Mock()
    partner.entity_id = 2
    partner.x = 12
    partner.y = 12
    
    # GENÉTICA UNIVERSAL: Configurar genoma mock para SocialCapabilities
    partner.genome = Mock()
    partner.genome.has_trait.return_value = True
    partner.genome.get_trait_value.return_value = 0.9
    
    # Crear relación con etiqueta "Amigo"
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    
    # Añadir recuerdos para generar etiqueta "Amigo"
    current_day = 15.0
    for i in range(15):
        mem = _create_cooperation_memory(1, 2, float(i), i)
        rel.add_memory(mem, current_day=current_day)
    
    # Verificar que la etiqueta "Amigo" se generó
    labels = rel.get_labels(current_day)
    print(f"           Etiquetas generadas: {labels}")
    
    assert "Amigo" in labels, "No se generó la etiqueta 'Amigo'"
    
    # CORRECCIÓN CRÍTICA: _relationships es ahora Dict[int, Relationship]
    # La clave es partner_id, el valor es el objeto Relationship
    agent._relationships = {rel.partner_id: rel}
    
    # Mock state y pending
    state = Mock()
    state.world_days_elapsed = current_day
    state.get_person_by_id.return_value = partner
    
    pending = Mock()
    pending.deaths = set()
    
    # Forzar generación (aumentar probabilidades temporalmente)
    original_prob = generator.experience_probabilities["Amigo"]["cooperation"]
    generator.experience_probabilities["Amigo"]["cooperation"] = 1.0  # 100%
    
    # Ejecutar
    generator._generate_opportunities(agent, state, pending, current_day)
    
    # Restaurar probabilidad original
    generator.experience_probabilities["Amigo"]["cooperation"] = original_prob
    
    # Validar que se llamó al relationship_engine
    passed = relationship_engine.process_event.called
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"           {status}  ExperienceGenerator genera experiencias basadas en etiquetas")
    
    assert passed, "ExperienceGenerator no genera experiencias basadas en etiquetas"


def benchmark_experience_performance() -> float:
    """Mide el rendimiento del ExperienceGenerator con múltiples agentes."""
    print("[Benchmark 3.2] Rendimiento de ExperienceGenerator")
    
    config = Mock()
    relationship_engine = Mock()
    
    generator = ExperienceGenerator(config, relationship_engine)
    
    # Crear 100 agentes con relaciones
    agents = []
    for i in range(100):
        agent = Mock()
        agent.entity_id = i
        agent.x = random.randint(0, 100)
        agent.y = random.randint(0, 100)
        
        # Crear relación con algunos recuerdos
        rel = Relationship(owner_id=i, partner_id=(i + 1) % 100, start_day=0.0)
        current_day = 5.0
        for j in range(5):
            mem = _create_cooperation_memory(i, (i + 1) % 100, float(j), j)
            rel.add_memory(mem, current_day=current_day)
        
        # CORRECCIÓN CRÍTICA: _relationships es ahora Dict[int, Relationship]
        agent._relationships = {rel.partner_id: rel}
        agents.append(agent)
    
    # Mock state
    state = Mock()
    state.world_days_elapsed = 5.0
    
    def get_person_by_id(pid):
        for a in agents:
            if a.entity_id == pid:
                return a
        return None
    
    state.get_person_by_id.side_effect = get_person_by_id
    
    pending = Mock()
    pending.deaths = set()
    
    # Medir tiempo de procesamiento
    start = time.perf_counter()
    for agent in agents:
        generator._generate_opportunities(agent, state, pending, 5.0)
    elapsed = time.perf_counter() - start
    
    per_agent_us = (elapsed / len(agents)) * 1_000_000
    
    passed = elapsed < 0.1  # Debería procesar 100 agentes en menos de 100ms
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"           {status}  Procesar 100 agentes: {elapsed:.4f}s ({per_agent_us:.2f} μs/agente)")
    
    return 0.0 if passed else 1.0


def run_all_benchmarks() -> None:
    """Ejecuta todos los benchmarks del ExperienceGenerator."""
    print("=" * 70)
    print("BENCHMARKS - ExperienceGenerator (Fase 3)")
    print("=" * 70)
    print()
    
    results = {}
    
    try:
        test_experience_generation()
        results["generation"] = 0.0
    except AssertionError:
        results["generation"] = 1.0
    print()
    
    results["performance"] = benchmark_experience_performance()
    print()
    
    print("=" * 70)
    print("VALIDACIÓN")
    print("=" * 70)
    
    checks = [
        ("Generación de experiencias basada en etiquetas", results["generation"] == 0.0),
        ("Rendimiento aceptable (<100ms para 100 agentes)", results["performance"] == 0.0),
    ]
    
    all_passed = True
    for description, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {description}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 Todos los benchmarks de ExperienceGenerator pasan.")
    else:
        print("⚠️  Algunos benchmarks no pasan.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_benchmarks()