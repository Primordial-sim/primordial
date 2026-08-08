"""Módulo responsable del registro histórico y rastreo de linajes biológicos y adoptivos.

Consolida el árbol genealógico global, persistiendo en memoria a los agentes
fallecidos y detectando eventos macro-históricos como la extinción de ramas.

CORRECCIONES APLICADAS (Auditoría):
- Registro de matrimonios y divorcios en HistoricalPersonNode.spouses
- Prevención de duplicados en children y adoptive_children
- birth_tick más robusto
- Almacenamiento explícito de age_at_death para estadísticas fiables
"""

import logging
from collections import deque
from typing import Dict, List, Optional, Set, Any

from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig


class HistoricalPersonNode:
    """Estructura de datos pura para almacenar el historial de una entidad."""
    
    def __init__(self, entity_id: int, name: str, gender: str, birth_tick: float) -> None:
        """Inicializa un nodo histórico desvinculado de dependencias lógicas."""
        self.entity_id = entity_id
        self.name = name
        self.gender = gender
        self.birth_tick = birth_tick
        self.death_tick: Optional[float] = None
        self.age_at_death: Optional[float] = None  # CORRECCIÓN: Edad explícita al morir
        self.is_alive = True
        
        # Relaciones topológicas (Grafo familiar bidireccional)
        self.biological_parents: List[int] = []
        self.adoptive_parents: List[int] = []
        self.children: List[int] = []
        self.adoptive_children: List[int] = []
        self.spouses: List[int] = []  # CORRECCIÓN: Ahora se usa activamente
        
        # Datos de jerarquía y linaje
        self.lineage_id: Optional[int] = None
        self.generation_index: int = 0
        
        # Snapshot fenotípico para analítica post-mortem
        self.longevity: float = 1.0
        self.sociability: float = 0.5
        self.temperament: float = 0.5


class Lineage:
    """Contenedor analítico para agrupar entidades bajo un mismo ancestro fundador."""
    
    def __init__(self, lineage_id: int, founder_id: int) -> None:
        self.lineage_id = lineage_id
        self.founder_id = founder_id
        self.members: Set[int] = {founder_id}
        self.is_extinct = False


class GenealogySystem:
    """Motor de sincronización histórica y algoritmos de parentesco en grafos."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.registry: Dict[int, HistoricalPersonNode] = {}
        self.lineages: Dict[int, Lineage] = {}
        self._next_lineage_id = 1
        self.total_days_elapsed = 0.0
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, state: WorldState, pending: PendingChanges, 
                delta_days: float, context: EnvironmentContext) -> None:
        """Sincroniza el grafo histórico detectando eventos relevantes."""
        self.total_days_elapsed += delta_days
        
        # 1. SINCRONIZACIÓN DE CENSO (Altas)
        for person in state.get_all_persons():
            if person.entity_id not in self.registry:
                self._sync_new_person(person)

        # 2. PROCESAMIENTO DE ADOPCIONES (con reciprocidad y linaje)
        for adoption in getattr(pending, 'adoptions', []):
            child_id = adoption.get('child_id')
            if child_id in self.registry:
                child_node = self.registry[child_id]
                
                for parent_key in ['parent_a', 'parent_b']:
                    p_id = adoption.get(parent_key)
                    if p_id and p_id in self.registry:
                        parent_node = self.registry[p_id]
                        
                        # CORRECCIÓN: Prevenir duplicados
                        if child_id not in child_node.adoptive_parents:
                            child_node.adoptive_parents.append(p_id)
                        if child_id not in parent_node.adoptive_children:
                            parent_node.adoptive_children.append(child_id)
                        
                        # Herencia de linaje
                        if parent_node.lineage_id is not None:
                            child_node.lineage_id = parent_node.lineage_id
                            if parent_node.lineage_id in self.lineages:
                                self.lineages[parent_node.lineage_id].members.add(child_id)

        # 3. CORRECCIÓN: PROCESAMIENTO DE MATRIMONIOS
        for person_a_id, person_b_id in getattr(pending, 'marriages', {}).items():
            if person_a_id in self.registry and person_b_id in self.registry:
                node_a = self.registry[person_a_id]
                node_b = self.registry[person_b_id]
                
                # CORRECCIÓN: Prevenir duplicados
                if person_b_id not in node_a.spouses:
                    node_a.spouses.append(person_b_id)
                if person_a_id not in node_b.spouses:
                    node_b.spouses.append(person_a_id)

        # 4. CORRECCIÓN: PROCESAMIENTO DE DIVORCIOS
        for divorce in getattr(pending, 'divorces', []):
            if isinstance(divorce, (list, tuple)) and len(divorce) == 2:
                person_a_id, person_b_id = divorce
                if person_a_id in self.registry and person_b_id in self.registry:
                    node_a = self.registry[person_a_id]
                    node_b = self.registry[person_b_id]
                    
                    # Eliminar de la lista de cónyuges activos
                    if person_b_id in node_a.spouses:
                        node_a.spouses.remove(person_b_id)
                    if person_a_id in node_b.spouses:
                        node_b.spouses.remove(person_a_id)

        # 5. PROCESAMIENTO DE FALLECIMIENTOS (Bajas)
        for dead_id in pending.deaths:
            if dead_id in self.registry and self.registry[dead_id].is_alive:
                node = self.registry[dead_id]
                node.is_alive = False
                node.death_tick = self.total_days_elapsed
                # CORRECCIÓN: Almacenar edad explícita al morir
                person = state.get_person_by_id(dead_id)
                if person:
                    node.age_at_death = getattr(person, 'age', 0.0)
                else:
                    # Fallback: calcular desde birth_tick si no hay persona viva
                    node.age_at_death = self.total_days_elapsed - node.birth_tick

        # 6. MANTENIMIENTO DE LINAJES Y DETECCIÓN DE EXTINCIONES
        for lineage in self.lineages.values():
            if not lineage.is_extinct:
                alive_members = any(
                    self.registry[m_id].is_alive 
                    for m_id in lineage.members if m_id in self.registry
                )
                if not alive_members:
                    lineage.is_extinct = True
                    self.logger.info(f"📜 Evento Histórico: El linaje {lineage.lineage_id} "
                                     f"(Fundador {lineage.founder_id}) se ha extinguido.")

    def _sync_new_person(self, person: Any) -> None:
        """Extrae la huella genética y relacional de un agente para el registro."""
        # CORRECCIÓN: birth_tick más robusto
        # Si la persona tiene edad > 1 día, nació antes de la simulación (fundador)
        # Si tiene edad <= 1 día, acaba de nacer en el tick actual
        person_age = getattr(person, 'age', 0.0)
        if person_age <= 1.0:
            birth_tick = self.total_days_elapsed
        else:
            # Para fundadores o entidades cargadas, estimar el nacimiento
            birth_tick = max(0.0, self.total_days_elapsed - person_age)
        
        node = HistoricalPersonNode(
            entity_id=person.entity_id,
            name=getattr(person, 'name', f"Agent_{person.entity_id}"),
            gender=getattr(person, 'gender', 'unknown'),
            birth_tick=birth_tick
        )
        
        if hasattr(person, 'genome'):
            node.longevity = getattr(person.genome, 'longevity', 1.0)
            node.sociability = getattr(person.genome, 'sociability', 0.5)
            node.temperament = getattr(person.genome, 'temperament', 0.5)
        
        father_id = getattr(person, 'father_id', None)
        mother_id = getattr(person, 'mother_id', None)
        
        if father_id is not None and father_id in self.registry:
            node.biological_parents.append(father_id)
            # CORRECCIÓN: Prevenir duplicados
            if person.entity_id not in self.registry[father_id].children:
                self.registry[father_id].children.append(person.entity_id)
                
        if mother_id is not None and mother_id in self.registry:
            node.biological_parents.append(mother_id)
            # CORRECCIÓN: Prevenir duplicados
            if person.entity_id not in self.registry[mother_id].children:
                self.registry[mother_id].children.append(person.entity_id)

        # Sincronizar padres adoptivos iniciales con reciprocidad y linaje
        adoptive_parents = getattr(person, 'adoptive_parents', [])
        for p_id in adoptive_parents:
            if p_id in self.registry:
                # CORRECCIÓN: Prevenir duplicados
                if p_id not in node.adoptive_parents:
                    node.adoptive_parents.append(p_id)
                if node.entity_id not in self.registry[p_id].adoptive_children:
                    self.registry[p_id].adoptive_children.append(node.entity_id)
                
                # Heredar linaje si el padre adoptivo tiene uno
                if self.registry[p_id].lineage_id is not None:
                    node.lineage_id = self.registry[p_id].lineage_id
                    if node.lineage_id in self.lineages:
                        self.lineages[node.lineage_id].members.add(node.entity_id)

        # Resolución de Generación y Linaje
        all_parents = node.biological_parents + node.adoptive_parents
        if not all_parents:
            node.generation_index = 0
            lineage_id = self._next_lineage_id
            self._next_lineage_id += 1
            self.lineages[lineage_id] = Lineage(lineage_id, person.entity_id)
            node.lineage_id = lineage_id
        else:
            parent_gens = [self.registry[p_id].generation_index for p_id in all_parents if p_id in self.registry]
            node.generation_index = max(parent_gens) + 1 if parent_gens else 1
            
            # Hereda linaje del primer padre (biológico o adoptivo) que tenga uno válido
            assigned_lineage = None
            for p_id in all_parents:
                if p_id in self.registry and self.registry[p_id].lineage_id is not None:
                    assigned_lineage = self.registry[p_id].lineage_id
                    break
            
            # Fallback: Si ningún padre tiene linaje, el hijo inicia uno nuevo
            if assigned_lineage is None:
                assigned_lineage = self._next_lineage_id
                self._next_lineage_id += 1
                self.lineages[assigned_lineage] = Lineage(assigned_lineage, person.entity_id)
                
            node.lineage_id = assigned_lineage
            if node.lineage_id in self.lineages:
                self.lineages[node.lineage_id].members.add(person.entity_id)
                
        self.registry[person.entity_id] = node

    def get_degree_of_kinship(self, id_a: int, id_b: int) -> int:
        """Calcula el grado de parentesco civil mediante un algoritmo BFS.
        
        Incluye lazos biológicos y adoptivos para evitar incesto social/legal.
        """
        if id_a not in self.registry or id_b not in self.registry:
            return -1
        if id_a == id_b:
            return 0

        visited: Set[int] = {id_a}
        queue: deque = deque([(id_a, 0)]) 
        
        while queue:
            current_id, dist = queue.popleft()
            if current_id == id_b:
                return dist
                
            node = self.registry[current_id]
            # Parentesco civil incluye padres e hijos biológicos Y adoptivos
            relatives = (node.biological_parents + node.adoptive_parents + 
                         node.children + node.adoptive_children)
            
            for relative_id in relatives:
                if relative_id not in visited:
                    visited.add(relative_id)
                    queue.append((relative_id, dist + 1))
                    
        return -1 

    def is_consanguineous(self, id_a: int, id_b: int, limit: int) -> bool:
        """Evalúa si la distancia genética o civil incurre en prohibición legal."""
        degree = self.get_degree_of_kinship(id_a, id_b)
        if degree == -1:
            return False 
        return degree <= limit

    def get_all_descendants(self, entity_id: int) -> Set[int]:
        """Recupera la totalidad de descendientes biológicos directos e indirectos (BFS)."""
        if entity_id not in self.registry:
            return set()
            
        descendants = set()
        queue: deque = deque(self.registry[entity_id].children)
        
        while queue:
            current = queue.popleft()
            if current not in descendants:
                descendants.add(current)
                if current in self.registry:
                    queue.extend(self.registry[current].children)
                    
        return descendants

    def get_adoptive_descendants(self, entity_id: int) -> Set[int]:
        """Recupera la totalidad de descendientes adoptivos directos e indirectos."""
        if entity_id not in self.registry:
            return set()
            
        descendants = set()
        queue: deque = deque(self.registry[entity_id].adoptive_children)
        
        while queue:
            current = queue.popleft()
            if current not in descendants:
                descendants.add(current)
                if current in self.registry:
                    queue.extend(self.registry[current].children)
                    queue.extend(self.registry[current].adoptive_children)
                    
        return descendants

    def get_lineage_members(self, lineage_id: int) -> Set[int]:
        """Obtiene todos los miembros de un linaje."""
        if lineage_id not in self.lineages:
            return set()
        return self.lineages[lineage_id].members.copy()