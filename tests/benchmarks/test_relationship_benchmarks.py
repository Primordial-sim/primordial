"""Benchmarks sintéticos para el sistema de relaciones cognitivas (Fase 0, 1 y 2).

Valida que la arquitectura de memoria basada en recuerdos escala correctamente
y que los mecanismos cognitivos (sesgos, contexto, etiquetas, narrativas) 
funcionan según las especificaciones del Documento de Diseño v1.0.
"""

from __future__ import annotations

import random
import time
from typing import List

from systems.relationships.relationship_model import (
    MemoryCategory,
    MemoryRole,
    PersonalMemory,
    Relationship,
    RelationshipEventType,
    WorldEvent,
    BiasEngine,
    GoalFilter,
    RelationshipEvaluator,
    LabelGenerator,
    Narrative,
)
from systems.relationships.narrative_engine import NarrativeEngine


# =============================================================================
# UTILIDADES DE GENERACIÓN SINTÉTICA
# =============================================================================

def _create_synthetic_memory(
    owner_id: int,
    partner_id: int,
    day: float,
    event_id: int,
    category: MemoryCategory = MemoryCategory.SOCIAL,
    valence: float = 0.5,
) -> PersonalMemory:
    """Crea un recuerdo sintético con parámetros controlados para testing."""
    base_weights = {
        MemoryCategory.SOCIAL: 15.0,
        MemoryCategory.COOPERATION: 30.0,
        MemoryCategory.CONFLICT: 35.0,
        MemoryCategory.ROMANTIC: 45.0,
        MemoryCategory.FAMILY: 60.0,
        MemoryCategory.SURVIVAL: 70.0,
        MemoryCategory.LEGAL: 85.0,
        MemoryCategory.TRAUMA: 80.0,
    }
    personal_weight = base_weights.get(category, 30.0) * random.uniform(0.8, 1.2)

    half_lives = {
        MemoryCategory.SOCIAL: 90.0,
        MemoryCategory.COOPERATION: 180.0,
        MemoryCategory.CONFLICT: 240.0,
        MemoryCategory.ROMANTIC: 365.0,
        MemoryCategory.FAMILY: 730.0,
        MemoryCategory.SURVIVAL: 1000.0,
        MemoryCategory.LEGAL: float('inf'),
        MemoryCategory.TRAUMA: float('inf'),
    }

    return PersonalMemory(
        world_event_id=event_id,
        owner_id=owner_id,
        partner_id=partner_id,
        perceived_intensity=0.7,
        emotional_valence=valence,
        personal_weight=personal_weight,
        category=category,
        day=day,
        context="benchmark",
        event_type="synthetic_event",
        source_system="BenchmarkSystem",
        role=MemoryRole.NORMAL,
        half_life_days=half_lives.get(category, 90.0),
    )


def _populate_relationship(
    rel: Relationship,
    num_memories: int,
    current_day: float,
    realistic_ages: bool = False,
) -> None:
    """Rellena una relación con recuerdos sintéticos."""
    for i in range(num_memories):
        if realistic_ages and random.random() < 0.3:
            days_ago = random.uniform(3650, 7300)
        else:
            days_ago = (num_memories - i) * random.uniform(0.5, 10.0)
        
        day = current_day - days_ago
        
        if random.random() < 0.2:
            category = MemoryCategory.CONFLICT
            valence = -0.6
        elif random.random() < 0.3:
            category = MemoryCategory.COOPERATION
            valence = 0.7
        else:
            category = MemoryCategory.SOCIAL
            valence = 0.4
            
        memory = _create_synthetic_memory(
            owner_id=rel.owner_id,
            partner_id=rel.partner_id,
            day=max(0.0, day),
            event_id=i,
            category=category,
            valence=valence,
        )
        rel.add_memory(memory, current_day)


# =============================================================================
# BENCHMARKS FASE 0: RENDIMIENTO BASE
# =============================================================================

def benchmark_memory_creation(num_memories: int = 1000) -> float:
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    current_day = 1000.0

    start = time.perf_counter()
    for i in range(num_memories):
        memory = _create_synthetic_memory(1, 2, current_day - (num_memories - i), i)
        rel.add_memory(memory, current_day)
    elapsed = time.perf_counter() - start

    per_memory_us = (elapsed / num_memories) * 1_000_000
    print(f"[Benchmark 0.1] Crear {num_memories} recuerdos: {elapsed:.4f}s ({per_memory_us:.2f} μs/recuerdo)")
    return elapsed


def benchmark_metric_queries(num_queries: int = 1000, num_memories: int = 300) -> float:
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    _populate_relationship(rel, num_memories, current_day=1000.0)

    current_day = 1000.0
    rel.get_familiarity(current_day)

    start = time.perf_counter()
    for _ in range(num_queries):
        _ = rel.get_familiarity(current_day)
        _ = rel.get_labels(current_day)
    elapsed = time.perf_counter() - start

    per_query_us = (elapsed / (num_queries * 2)) * 1_000_000
    print(f"[Benchmark 0.2] {num_queries} consultas (2 métricas c/u) con {num_memories} recuerdos: {elapsed:.6f}s ({per_query_us:.2f} μs/consulta)")
    return elapsed


def benchmark_scalability(num_relationships: int = 1000, num_memories_per_rel: int = 100) -> float:
    relationships: List[Relationship] = []
    current_day = 10000.0

    for i in range(num_relationships):
        rel = Relationship(owner_id=i, partner_id=i + 100000, start_day=0.0)
        _populate_relationship(rel, num_memories_per_rel, current_day=current_day, realistic_ages=True)
        relationships.append(rel)

    total_memories_before = sum(len(rel.memories) for rel in relationships)
    total_archived = sum(rel.archive_old_memories(current_day) for rel in relationships)
    total_memories_after = sum(len(rel.memories) for rel in relationships)

    print(f"           Archivados {total_archived} recuerdos de {total_memories_before} totales ({total_archived / max(1, total_memories_before) * 100:.1f}%)")
    print(f"           Recuerdos activos después: {total_memories_after}")

    num_queries_per_tick = int(num_relationships * 0.2)
    relationships_to_query = random.sample(relationships, num_queries_per_tick)
    
    start = time.perf_counter()
    for rel in relationships_to_query:
        _ = rel.get_familiarity(current_day)
        _ = rel.get_labels(current_day)
    elapsed = time.perf_counter() - start

    scale_factor = (50000 / num_relationships) * (300 / num_memories_per_rel) * 0.2
    estimated_full = elapsed * scale_factor

    print(f"[Benchmark 0.3] {num_relationships} relaciones × {num_memories_per_rel} recuerdos:")
    print(f"           Consultadas: {num_queries_per_tick} relaciones (20%)")
    print(f"           Tiempo: {elapsed:.4f}s")
    print(f"           Extrapolación a 50,000 × 300 (20% consultadas): {estimated_full:.2f}s (objetivo: < 5.0s)")
    return elapsed


# =============================================================================
# BENCHMARKS FASE 1: COGNICIÓN Y SESGOS
# =============================================================================

def benchmark_cognitive_biases() -> float:
    print("[Benchmark 1.1] Validación de Sesgos Cognitivos")
    
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    current_day = 1000.0
    
    rel.my_narratives.append(Narrative(pattern="Siempre me ayuda", strength=0.8, last_confirmed=current_day - 10))
    
    mem_negative = _create_synthetic_memory(1, 2, current_day - 10, 1, MemoryCategory.CONFLICT, valence=-0.8)
    weight_neg = BiasEngine.apply_biases(mem_negative, None, rel, current_day)
    neg_ratio = weight_neg / mem_negative.personal_weight
    
    mem_positive = _create_synthetic_memory(1, 2, current_day - 10, 2, MemoryCategory.COOPERATION, valence=0.8)
    weight_pos = BiasEngine.apply_biases(mem_positive, None, rel, current_day)
    pos_ratio = weight_pos / mem_positive.personal_weight
    
    rel.partner_is_deceased = True
    mem_negative_post_mortem = _create_synthetic_memory(1, 2, current_day - 10, 3, MemoryCategory.CONFLICT, valence=-0.8)
    weight_pm = BiasEngine.apply_biases(mem_negative_post_mortem, None, rel, current_day)
    pm_ratio = weight_pm / mem_negative_post_mortem.personal_weight
    
    checks = [
        ("Negatividad (×1.8)", 1.7 <= neg_ratio <= 1.9),
        ("Confirmación positiva (×1.5 aprox)", pos_ratio > 1.4),
        ("Idealización Post-Mortem (×0.3 aprox)", 0.25 <= pm_ratio <= 0.35),
    ]
    
    all_passed = True
    for desc, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"           {status}  {desc}")
        if not passed:
            all_passed = False
            
    return 0.0 if all_passed else 1.0


def benchmark_contextual_evaluation() -> float:
    print("[Benchmark 1.2] Evaluación Contextual")
    
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    current_day = 1000.0
    
    rel.add_memory(_create_synthetic_memory(1, 2, current_day - 100, 1, MemoryCategory.COOPERATION, valence=0.8), current_day)
    rel.add_memory(_create_synthetic_memory(1, 2, current_day - 200, 2, MemoryCategory.CONFLICT, valence=-0.9), current_day)
    rel.add_memory(_create_synthetic_memory(1, 2, current_day - 300, 3, MemoryCategory.SOCIAL, valence=0.5), current_day)
    
    score_ayuda = RelationshipEvaluator.evaluate_reliability(rel, context="pedir_ayuda", current_day=current_day)
    score_juego = RelationshipEvaluator.evaluate_reliability(rel, context="juego", current_day=current_day)
    
    passed = score_juego > score_ayuda
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"           {status}  Score 'juego' ({score_juego:.1f}) > Score 'pedir_ayuda' ({score_ayuda:.1f})")
    
    return 0.0 if passed else 1.0


def benchmark_label_generation_by_weight() -> float:
    print("[Benchmark 1.3] Generación de Etiquetas por Pesos")
    
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    current_day = 1000.0
    
    for i in range(3):
        mem = _create_synthetic_memory(1, 2, current_day - (i * 100), i, MemoryCategory.ROMANTIC, valence=0.9)
        mem.personal_weight = 200.0
        rel.add_memory(mem, current_day)
        
    mem_coop = _create_synthetic_memory(1, 2, current_day - 50, 4, MemoryCategory.COOPERATION, valence=0.7)
    mem_coop.personal_weight = 160.0
    rel.add_memory(mem_coop, current_day)
    
    labels = LabelGenerator.generate(rel, current_day)
    
    passed = "Amante" in labels and "Aliado" in labels
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"           {status}  Etiquetas generadas: {', '.join(labels)}")
    
    return 0.0 if passed else 1.0


# =============================================================================
# BENCHMARKS FASE 2: NARRATIVAS COGNITIVAS
# =============================================================================

def benchmark_narrative_engine() -> float:
    print("[Benchmark 2.1] Validación de NarrativeEngine (Patrones y Decaimiento)")
    
    rel = Relationship(owner_id=1, partner_id=2, start_day=0.0)
    current_day = 1000.0
    
    # ========================================================================
    # TEST 1: Detección de patrones complejos (ventanas temporales)
    # ========================================================================
    # Inyectar recuerdos para disparar "Últimamente hay mucha tensión"
    # Necesitamos conflict_weight_recent > 80.0 en los últimos 365 días
    for i in range(5):
        mem = _create_synthetic_memory(1, 2, current_day - (i * 50), i, MemoryCategory.CONFLICT, valence=-0.8)
        mem.personal_weight = 30.0  # 5 * 30 = 150 > 80.0
        rel.add_memory(mem, current_day)
        
    # Verificar que la narrativa compleja se creó
    narratives = [n for n in rel.my_narratives if "tensión" in n.pattern.lower()]
    passed_creation = len(narratives) > 0 and narratives[0].strength >= 0.25
    
    # ========================================================================
    # TEST 2: Decaimiento temporal (validado de forma aislada)
    # ========================================================================
    # Creamos una narrativa manualmente con strength conocida para validar
    # la fórmula matemática sin interferencia del NarrativeEngine
    test_narrative = Narrative(
        pattern="Narrativa de prueba",
        strength=0.25,  # Fuerza inicial conocida
        last_confirmed=current_day,
        half_life_days=1825.0  # 5 años
    )
    
    # Avanzar 1825 días (5 años, que es la half_life_days)
    future_day = current_day + 1825.0
    strength_future = test_narrative.current_strength(future_day)
    
    # Debería ser exactamente la mitad: 0.25 * 0.5 = 0.125
    passed_decay = 0.12 <= strength_future <= 0.13
        
    checks = [
        ("Detección de patrones complejos (ventanas temporales)", passed_creation),
        ("Decaimiento temporal de narrativas (half-life)", passed_decay),
    ]
    
    all_passed = True
    for desc, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"           {status}  {desc}")
        if not passed:
            all_passed = False
            
    return 0.0 if all_passed else 1.0


# =============================================================================
# EJECUCIÓN COMPLETA
# =============================================================================

def run_all_benchmarks() -> None:
    print("=" * 70)
    print("BENCHMARKS SINTÉTICOS - Sistema de Relaciones Cognitivas (Fase 0, 1 y 2)")
    print("=" * 70)
    print()

    results = {}

    print("--- FASE 0: Rendimiento Base ---")
    results["creation"] = benchmark_memory_creation(1000)
    print()
    
    results["queries"] = benchmark_metric_queries(1000, 300)
    print()
    
    results["scale"] = benchmark_scalability(1000, 100)
    print()

    print("--- FASE 1: Cognición y Sesgos ---")
    results["biases"] = benchmark_cognitive_biases()
    print()
    
    results["context"] = benchmark_contextual_evaluation()
    print()
    
    results["labels"] = benchmark_label_generation_by_weight()
    print()

    print("--- FASE 2: Narrativas Cognitivas ---")
    results["narratives"] = benchmark_narrative_engine()
    print()

    # Validación contra objetivos del documento
    print("=" * 70)
    print("VALIDACIÓN CONTRA OBJETIVOS DEL DOCUMENTO")
    print("=" * 70)

    checks = [
        ("Creación 1000 recuerdos < 0.1s", results["creation"] < 0.1),
        ("Consulta 1000 métricas < 0.01s", results["queries"] < 0.01),
        ("Escalabilidad 50k × 300 (20%) < 5.0s", results["scale"] * (50000/1000) * (300/100) * 0.2 < 5.0),
        ("Sesgos cognitivos aplicados correctamente", results["biases"] == 0.0),
        ("Evaluación contextual diferenciada", results["context"] == 0.0),
        ("Etiquetas basadas en pesos, no conteos", results["labels"] == 0.0),
        ("Detección y decaimiento de narrativas complejas", results["narratives"] == 0.0),
    ]

    all_passed = True
    for description, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {description}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 Todos los benchmarks pasan. Fases 0, 1 y 2 validadas para producción.")
    else:
        print("⚠️  Algunos benchmarks no pasan. Revisar implementaciones.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_benchmarks()