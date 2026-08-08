"""Módulo de Búfer Atómico Universal del ciclo de ejecución.

Actúa como un 'Staging Area' (zona de pruebas) donde los sistemas registran 
sus intenciones sin alterar el mundo real. Esto garantiza que el orden de 
ejecución de los sistemas no cause efectos secundarios indeseados y que 
los datos fluyan de forma segura hacia la fase de consolidación (commit).

FASE 0: Se añade soporte transaccional para la adición de recuerdos relacionales.
"""

from typing import Any, Dict, List, Optional, Tuple

from systems.diseases.pathogen import Pathogen


class PendingChanges:
    """Contenedor de mutaciones encoladas para el estado del mundo."""

    def __init__(self) -> None:
        """Inicializa todas las colecciones transaccionales vacías."""
        self.movements: Dict[int, Tuple[int, int]] = {}
        
        # Colecciones médicas
        self.infections: List[Tuple[int, Pathogen]] = []
        self.recoveries: List[Tuple[int, str]] = []
        
        # Colecciones sociales
        self.divorces: List[Tuple[int, int]] = []
        self.marriages: Dict[int, int] = {}
        self.adoptions: List[Dict[str, Any]] = []
        
        # Colecciones biológicas
        self.pregnancy_updates: Dict[int, Dict[str, Any]] = {}
        self.births: List[Dict[str, Any]] = []
        self.age_increments: Dict[int, float] = {}
        self.deaths: Dict[int, str] = {} 
        self.days_to_add: float = 0.0
        
        # Colecciones psicológicas (Emociones y Memoria)
        self.emotion_updates: Dict[int, List[Tuple[str, float]]] = {}
        self.memory_updates: Dict[int, Dict[str, Any]] = {}
        
        # Colecciones de Libre Albedrío (Flags transaccionales - legacy)
        self.free_will_flags_updates: Dict[int, Dict[str, bool]] = {}
        
        # Colecciones de Motivaciones Continuas
        self.motivation_updates: Dict[int, Dict[str, float]] = {}
        
    # ==========================================
    # SALUD Y EPIDEMIOLOGÍA
    # ==========================================
    def register_infection(self, entity_id: int, pathogen: Pathogen) -> None:
        """Encola el contagio de un agente con una cepa viral específica."""
        self.infections.append((entity_id, pathogen))

    def register_recovery(self, entity_id: int, pathogen_id: str) -> None:
        """Encola la curación y la consiguiente adquisición de inmunidad."""
        self.recoveries.append((entity_id, pathogen_id))

    # ==========================================
    # ESPACIO Y TIEMPO
    # ==========================================
    def register_movement(self, entity_id: int, x: int, y: int) -> None:
        """Registra una intención de desplazamiento espacial validada."""
        self.movements[entity_id] = (x, y)

    def register_time_pass(self, days: float) -> None:
        """Suma tiempo al reloj biológico global (si aplica)."""
        self.days_to_add += days

    def register_age_increment(self, entity_id: int, increment_days: float) -> None:
        """Acumula los días envejecidos o el desgaste celular en este ciclo."""
        if entity_id not in self.age_increments:
            self.age_increments[entity_id] = 0.0
        self.age_increments[entity_id] += float(increment_days)

    # ==========================================
    # DINÁMICAS POBLACIONALES
    # ==========================================
    def register_death(self, entity_id: int, reason: str = "Desconocido") -> None:
        """Marca una entidad para ser eliminada con diagnóstico forense."""
        if entity_id not in self.deaths:
            self.deaths[entity_id] = reason

    def register_birth(
        self,
        mother_id: int,
        father_id: Optional[int],
        x: int,
        y: int,
        genome: Any,
    ) -> None:
        """Registra un nacimiento pendiente con el ADN recombinado multiespecie."""
        self.births.append({
            "mother_id": mother_id,
            "father_id": father_id,
            "x": x,
            "y": y,
            "genome": genome,
        })

    def register_pregnancy_update(
        self,
        entity_id: int,
        is_pregnant: bool,
        pregnancy_days: float,
        failed_increment: int = 0,
        litter_size: int = 1,
    ) -> None:
        """Registra el avance de gestación o abortos, soportando camadas."""
        self.pregnancy_updates[entity_id] = {
            "is_pregnant": is_pregnant,
            "pregnancy_days": float(pregnancy_days),
            "failed_increment": int(failed_increment),
            "litter_size": int(litter_size),
        }

        # ==========================================
    # MIGRACIONES (Fase de Corrección)
    # ==========================================
    def set_migration_target(self, entity_id: int, target: Tuple[float, float]) -> None:
        """Establece un destino de migración para un agente."""
        if not hasattr(self, 'migration_targets'):
            self.migration_targets: Dict[int, Tuple[float, float]] = {}
        self.migration_targets[entity_id] = target

    def get_migration_target(self, entity_id: int) -> Optional[Tuple[float, float]]:
        """Obtiene el destino de migración de un agente."""
        if not hasattr(self, 'migration_targets'):
            return None
        return self.migration_targets.get(entity_id)

    def clear_migration_target(self, entity_id: int) -> None:
        """Limpia el destino de migración de un agente."""
        if hasattr(self, 'migration_targets') and entity_id in self.migration_targets:
            del self.migration_targets[entity_id]

    # ==========================================
    # RELACIONES Y LEGALIDAD
    # ==========================================
    def register_marriage(self, p1: int, p2: int) -> None:
        """Registra la intención de matrimonio simétrico."""
        self.marriages[p1] = p2

    def register_divorce(self, p1: int, p2: int) -> None:
        """Registra una ruptura o viudedad atómica para limpiar el grafo social."""
        self.divorces.append((p1, p2))

    def register_adoption(
        self,
        child_id: int,
        parent_a: int,
        parent_b: Optional[int] = None,
        is_single_parent: bool = False,
    ) -> None:
        """Añade una transferencia de filiación legal a la cola transaccional."""
        self.adoptions.append({
            "child_id": child_id,
            "parent_a": parent_a,
            "parent_b": parent_b,
            "is_single_parent": is_single_parent,
        })

    # ==========================================
    # PSICOLOGÍA Y MEMORIA TRANSACCIONAL
    # ==========================================
    def register_emotion_update(
        self, entity_id: int, emotion: str, amount: float
    ) -> None:
        """Encola un cambio en el estado emocional de una entidad."""
        if entity_id not in self.emotion_updates:
            self.emotion_updates[entity_id] = []
        self.emotion_updates[entity_id].append((emotion, amount))

    def register_memory_update(
        self, entity_id: int, key: str, value: Any
    ) -> None:
        """Encola un cambio en la memoria cognitiva de una entidad."""
        if entity_id not in self.memory_updates:
            self.memory_updates[entity_id] = {}
        self.memory_updates[entity_id][key] = value

    # ==========================================
    # LIBRE ALBEDRÍO TRANSACCIONAL (Legacy)
    # ==========================================
    def register_free_will_flag(
        self, entity_id: int, flag_name: str, value: bool
    ) -> None:
        """Encola un cambio en los flags de libre albedrío de una entidad."""
        if entity_id not in self.free_will_flags_updates:
            self.free_will_flags_updates[entity_id] = {}
        self.free_will_flags_updates[entity_id][flag_name] = value

    def consume_free_will_flag(
        self, entity_id: int, flag_name: str
    ) -> None:
        """Consume un impulso de libre albedrío (lo desactiva transaccionalmente)."""
        self.register_free_will_flag(entity_id, flag_name, False)

    # ==========================================
    # MOTIVACIONES CONTINUAS TRANSACCIONALES
    # ==========================================
    def register_motivation_update(
        self, entity_id: int, motivation_name: str, delta: float
    ) -> None:
        """Encola un cambio incremental en una motivación continua."""
        if entity_id not in self.motivation_updates:
            self.motivation_updates[entity_id] = {}
        current_delta = self.motivation_updates[entity_id].get(motivation_name, 0.0)
        self.motivation_updates[entity_id][motivation_name] = current_delta + delta

    def set_motivation(
        self, entity_id: int, motivation_name: str, value: float
    ) -> None:
        """Establece un valor absoluto para una motivación (no acumulativo)."""
        if entity_id not in self.motivation_updates:
            self.motivation_updates[entity_id] = {}
        self.motivation_updates[entity_id][f"__set__{motivation_name}"] = value

    def get_pending_motivation_deltas(
        self, entity_id: int
    ) -> Dict[str, float]:
        """Obtiene todos los deltas pendientes de motivaciones para una entidad."""
        return self.motivation_updates.get(entity_id, {})

        # ==========================================
    # CICLO DE VIDA DEL BÚFER
    # ==========================================
    def clear(self) -> None:
        """Limpia el búfer reasignando las colecciones (Memory-Safe)."""
        self.movements.clear()
        self.infections.clear()
        self.recoveries.clear()
        self.divorces.clear()
        self.marriages.clear()
        self.pregnancy_updates.clear()
        self.births.clear()
        self.age_increments.clear()
        self.adoptions.clear()
        self.deaths.clear()
        self.days_to_add = 0.0
        self.emotion_updates.clear()
        self.memory_updates.clear()
        self.free_will_flags_updates.clear()
        self.motivation_updates.clear() 
        if hasattr(self, 'migration_targets'):
            self.migration_targets.clear()