"""Módulo de fachada para la resolución de parentescos y árboles genealógicos.

Expone una API limpia para consultas analíticas complejas, estadísticas de linaje
y validación de leyes sociales sin exponer el grafo subyacente.

CORRECCIONES APLICADAS (Auditoría):
- _get_all_ancestors() protegido con conjunto de visitados (evita recursión infinita)
- get_lineage_statistics() usa age_at_death explícito
- Método iterativo BFS para ancestros (más robusto que recursión)
"""

from typing import Dict, Any, Set, List
from collections import deque
from systems.genealogy.genealogy_system import GenealogySystem


class AncestryQueries:
    """Servicio para aislar consultas complejas y estadísticas del sistema central."""

    def __init__(self, genealogy_system: GenealogySystem) -> None:
        """Inicializa el servicio vinculándolo al motor genealógico central."""
        self._genealogy = genealogy_system

    def is_forbidden_marriage(self, id_a: int, id_b: int) -> bool:
        """Determina si una unión está biológicamente prohibida por consanguinidad."""
        limit = self._genealogy.config.genealogy.consanguinity_limit
        return self._genealogy.is_consanguineous(id_a, id_b, limit=limit)

    def get_kinship_degree(self, id_a: int, id_b: int) -> int:
        """Calcula y retorna el grado exacto de parentesco biológico."""
        return self._genealogy.get_degree_of_kinship(id_a, id_b)

    def calculate_lineage_success(self, founder_id: int, vivos_ids: Set[int]) -> Dict[str, Any]:
        """Calcula el éxito reproductivo de un individuo para el motor evolutivo.
        
        Args:
            founder_id: ID del individuo a analizar.
            vivos_ids: Set con los IDs de las entidades actualmente vivas.
            
        Returns:
            Diccionario con métricas de éxito genético.
        """
        descendants = self._genealogy.get_all_descendants(founder_id)
        adoptive_descendants = self._genealogy.get_adoptive_descendants(founder_id)
        all_descendants = descendants | adoptive_descendants
        descendencia_viva = len([d for d in all_descendants if d in vivos_ids])
        
        return {
            "total_descendencia_historica": len(all_descendants),
            "total_descendencia_viva": descendencia_viva,
            "tasa_supervivencia": descendencia_viva / max(1, len(all_descendants))
        }

    def get_lineage_statistics(self, lineage_id: int) -> Dict[str, Any]:
        """Genera un reporte automático completo sobre una familia entera.
        
        CORRECCIÓN: Usa age_at_death explícito en lugar de calcularlo desde ticks.
        """
        if lineage_id not in self._genealogy.lineages:
            return {"error": "Linaje no encontrado"}
            
        lineage = self._genealogy.lineages[lineage_id]
        miembros_ids = lineage.members
        
        vivos = 0
        muertos = 0
        edades_al_morir: List[float] = []
        generaciones_alcanzadas: Set[int] = set()
        
        for m_id in miembros_ids:
            if m_id in self._genealogy.registry:
                node = self._genealogy.registry[m_id]
                generaciones_alcanzadas.add(node.generation_index)
                
                if node.is_alive:
                    vivos += 1
                else:
                    muertos += 1
                    # CORRECCIÓN: Usar age_at_death explícito si está disponible
                    if node.age_at_death is not None:
                        edades_al_morir.append(node.age_at_death)
                    elif node.death_tick is not None and node.birth_tick is not None:
                        # Fallback: calcular desde ticks (menos preciso)
                        edades_al_morir.append(node.death_tick - node.birth_tick)

        avg_lifespan = sum(edades_al_morir) / len(edades_al_morir) if edades_al_morir else 0.0

        return {
            "lineage_id": lineage_id,
            "founder_id": lineage.founder_id,
            "is_extinct": lineage.is_extinct,
            "total_members": len(miembros_ids),
            "alive_members": vivos,
            "deceased_members": muertos,
            "generations_span": max(generaciones_alcanzadas) if generaciones_alcanzadas else 0,
            "average_historical_lifespan_days": avg_lifespan
        }

    def analyze_inbreeding_risk(self, entity_id: int) -> float:
        """Detecta eventos genealógicos de riesgo (Endogamia/Cuello de botella).
        
        Calcula un coeficiente simplificado basado en el solapamiento de 
        ancestros paternos y maternos. Retorna [0.0 - 1.0].
        """
        if entity_id not in self._genealogy.registry:
            return 0.0
            
        node = self._genealogy.registry[entity_id]
        if len(node.biological_parents) != 2:
            return 0.0
            
        padre_id, madre_id = node.biological_parents
        
        # CORRECCIÓN: Usar método iterativo con visitados
        ancestros_padre = self._get_all_ancestors(padre_id)
        ancestros_madre = self._get_all_ancestors(madre_id)
        
        if not ancestros_padre or not ancestros_madre:
            return 0.0
            
        solapamiento = ancestros_padre.intersection(ancestros_madre)
        total_unicos = ancestros_padre.union(ancestros_madre)
        
        return len(solapamiento) / max(1, len(total_unicos))

    def _get_all_ancestors(self, entity_id: int) -> Set[int]:
        """Algoritmo iterativo (BFS) para extraer la línea ascendente completa.
        
        CORRECCIÓN: Protegido con conjunto de visitados para evitar recursión
        infinita en caso de ciclos genealógicos accidentales.
        """
        ancestors: Set[int] = set()
        queue: deque = deque([entity_id])
        visited: Set[int] = {entity_id}  # CORRECCIÓN: Conjunto de visitados
        
        while queue:
            current_id = queue.popleft()
            
            if current_id not in self._genealogy.registry:
                continue
                
            node = self._genealogy.registry[current_id]
            
            # Solo considerar padres biológicos para análisis genético
            for parent_id in node.biological_parents:
                if parent_id not in visited:
                    visited.add(parent_id)
                    ancestors.add(parent_id)
                    queue.append(parent_id)
        
        return ancestors

    def get_all_ancestors_recursive_safe(self, entity_id: int, max_depth: int = 10) -> Set[int]:
        """Versión recursiva con límite de profundidad como alternativa.
        
        Útil cuando se necesita controlar explícitamente la profundidad
        del análisis genealógico.
        """
        return self._get_ancestors_recursive(entity_id, max_depth, set())

    def _get_ancestors_recursive(self, entity_id: int, depth: int, visited: Set[int]) -> Set[int]:
        """Helper recursivo con protección contra ciclos y límite de profundidad."""
        if depth <= 0 or entity_id in visited:
            return set()
            
        visited.add(entity_id)
        ancestors: Set[int] = set()
        
        if entity_id not in self._genealogy.registry:
            return ancestors
            
        node = self._genealogy.registry[entity_id]
        
        for parent_id in node.biological_parents:
            ancestors.add(parent_id)
            ancestors.update(self._get_ancestors_recursive(parent_id, depth - 1, visited))
        
        return ancestors