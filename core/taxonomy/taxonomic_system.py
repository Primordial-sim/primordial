"""Sistema Taxonómico.

Árbol taxonómico global editable en runtime.
Solo clasifica especies, NO decide capacidades.

Filosofía:
- La taxonomía es INFORMATIVA, no prescriptiva
- Las capacidades salen de la genética (Genome)
- El sistema debe ser editable para soportar evolución
- Las consultas deben ser rápidas y flexibles
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
import logging

from core.taxonomy.taxonomic_node import TaxonomicNode, TaxonomicRank


class TaxonomicSystem:
    """Árbol taxonómico global.
    
    Uso:
        taxonomy = TaxonomicSystem.get_default()
        
        # Consultas
        is_mammal = taxonomy.is_descendant_of("wolf", "mammalia")
        ancestors = taxonomy.get_ancestors("wolf")
        mammals = taxonomy.get_all_by_rank(TaxonomicRank.CLASS)
        
        # Edición en runtime (para evolución)
        taxonomy.register(TaxonomicNode(
            taxon_id="canis_lupus_familiaris",
            name="Perro doméstico",
            parent_id="canis_lupus",
            rank=TaxonomicRank.SUBSPECIES,
        ))
    """
    
    _default_instance: Optional['TaxonomicSystem'] = None
    _logger = logging.getLogger("TaxonomicSystem")
    
    def __init__(self) -> None:
        self._nodes: Dict[str, TaxonomicNode] = {}
        self._children: Dict[str, List[str]] = {}  # parent_id → [child_ids]
    
    # =========================================================================
    # CONSTRUCTOR DE INSTANCIA POR DEFECTO
    # =========================================================================
    
    @classmethod
    def get_default(cls) -> 'TaxonomicSystem':
        """Retorna la instancia por defecto con la taxonomía precargada."""
        if cls._default_instance is None:
            cls._default_instance = cls()
            cls._default_instance._initialize_default_taxonomy()
        return cls._default_instance
    
    # =========================================================================
    # GESTIÓN DE NODOS (editable en runtime)
    # =========================================================================
    
    def register(self, node: TaxonomicNode) -> None:
        """Registra un nuevo nodo taxonómico.
        
        Args:
            node: El nodo a registrar.
            
        Raises:
            ValueError: Si el taxon_id ya existe o el padre no existe.
        """
        if node.taxon_id in self._nodes:
            raise ValueError(f"El taxón '{node.taxon_id}' ya está registrado")
        
        if node.parent_id is not None and node.parent_id not in self._nodes:
            raise ValueError(f"El padre '{node.parent_id}' no existe")
        
        self._nodes[node.taxon_id] = node
        
        # Actualizar índice de hijos
        if node.parent_id is not None:
            if node.parent_id not in self._children:
                self._children[node.parent_id] = []
            self._children[node.parent_id].append(node.taxon_id)
        
        self._logger.debug(f"Taxón registrado: {node.taxon_id} [{node.rank.name}]")
    
    def unregister(self, taxon_id: str) -> None:
        """Elimina un nodo taxonómico (y todos sus descendientes).
        
        Args:
            taxon_id: ID del taxón a eliminar.
            
        Raises:
            ValueError: Si el taxón no existe.
        """
        if taxon_id not in self._nodes:
            raise ValueError(f"El taxón '{taxon_id}' no existe")
        
        # Eliminar todos los descendientes primero
        descendants = self.get_descendants(taxon_id)
        for desc_id in descendants:
            del self._nodes[desc_id]
            if desc_id in self._children:
                del self._children[desc_id]
        
        # Eliminar el nodo
        node = self._nodes[taxon_id]
        del self._nodes[taxon_id]
        
        # Eliminar de la lista de hijos del padre
        if node.parent_id and node.parent_id in self._children:
            self._children[node.parent_id].remove(taxon_id)
        
        self._logger.debug(f"Taxón eliminado: {taxon_id}")
    
    def get(self, taxon_id: str) -> Optional[TaxonomicNode]:
        """Obtiene un nodo por su ID."""
        return self._nodes.get(taxon_id)
    
    def has(self, taxon_id: str) -> bool:
        """Verifica si un taxón existe."""
        return taxon_id in self._nodes
    
    # =========================================================================
    # CONSULTAS JERÁRQUICAS
    # =========================================================================
    
    def get_ancestors(self, taxon_id: str) -> List[TaxonomicNode]:
        """Retorna la cadena de ancestros (de más específico a más general).
        
        Ejemplo:
            get_ancestors("canis_lupus") → 
            [canis_lupus, canis, canidae, carnivora, mammalia, vertebrata, animalia, life]
        """
        if taxon_id not in self._nodes:
            return []
        
        ancestors = []
        current = self._nodes[taxon_id]
        
        while current is not None:
            ancestors.append(current)
            if current.parent_id is None:
                break
            current = self._nodes.get(current.parent_id)
        
        return ancestors
    
    def get_descendants(self, taxon_id: str) -> List[str]:
        """Retorna todos los IDs de descendientes (recursivo).
        
        Ejemplo:
            get_descendants("mammalia") → 
            [carnivora, canidae, canis, canis_lupus, primates, hominidae, ...]
        """
        if taxon_id not in self._nodes:
            return []
        
        descendants = []
        queue = [taxon_id]
        
        while queue:
            current_id = queue.pop(0)
            children = self._children.get(current_id, [])
            
            for child_id in children:
                descendants.append(child_id)
                queue.append(child_id)
        
        return descendants
    
    def get_children(self, taxon_id: str) -> List[TaxonomicNode]:
        """Retorna los hijos directos de un taxón."""
        if taxon_id not in self._children:
            return []
        return [self._nodes[cid] for cid in self._children[taxon_id] if cid in self._nodes]
    
    def is_descendant_of(self, taxon_id: str, ancestor_id: str) -> bool:
        """Verifica si un taxón desciende de otro.
        
        Ejemplo:
            is_descendant_of("canis_lupus", "mammalia") → True
            is_descendant_of("canis_lupus", "plantae") → False
        """
        ancestors = self.get_ancestors(taxon_id)
        ancestor_ids = {a.taxon_id for a in ancestors}
        return ancestor_id in ancestor_ids
    
    def get_all_by_rank(self, rank: TaxonomicRank) -> List[TaxonomicNode]:
        """Retorna todos los nodos de un rango específico.
        
        Ejemplo:
            get_all_by_rank(TaxonomicRank.CLASS) → 
            [mammalia, aves, reptilia, amphibia, pisces, insecta]
        """
        return [node for node in self._nodes.values() if node.rank == rank]
    
    def get_kingdom_of(self, taxon_id: str) -> Optional[TaxonomicNode]:
        """Retorna el reino de un taxón."""
        for ancestor in self.get_ancestors(taxon_id):
            if ancestor.rank == TaxonomicRank.KINGDOM:
                return ancestor
        return None
    
    def get_class_of(self, taxon_id: str) -> Optional[TaxonomicNode]:
        """Retorna la clase de un taxón."""
        for ancestor in self.get_ancestors(taxon_id):
            if ancestor.rank == TaxonomicRank.CLASS:
                return ancestor
        return None
    
    # =========================================================================
    # CONSULTAS POR PATRÓN
    # =========================================================================
    
    def search_by_name(self, query: str) -> List[TaxonomicNode]:
        """Busca taxones por nombre (case-insensitive)."""
        query_lower = query.lower()
        return [
            node for node in self._nodes.values()
            if query_lower in node.name.lower() or query_lower in node.taxon_id.lower()
        ]
    
    def get_statistics(self) -> Dict[str, int]:
        """Retorna estadísticas del árbol taxonómico."""
        stats = {rank.name: 0 for rank in TaxonomicRank}
        for node in self._nodes.values():
            stats[node.rank.name] += 1
        stats["TOTAL"] = len(self._nodes)
        return stats
    
    # =========================================================================
    # INICIALIZACIÓN DE TAXONOMÍA POR DEFECTO
    # =========================================================================
    
    def _initialize_default_taxonomy(self) -> None:
        """Registra la taxonomía biológica estándar."""
        
        # =====================================================================
        # DOMAIN: Life
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="life",
            name="Vida",
            parent_id=None,
            rank=TaxonomicRank.DOMAIN,
            description="Todos los organismos vivos",
        ))
        
        # =====================================================================
        # KINGDOMS
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="animalia",
            name="Animales",
            parent_id="life",
            rank=TaxonomicRank.KINGDOM,
            description="Organismos multicelulares heterótrofos",
        ))
        self.register(TaxonomicNode(
            taxon_id="plantae",
            name="Plantas",
            parent_id="life",
            rank=TaxonomicRank.KINGDOM,
            description="Organismos fotosintéticos multicelulares",
        ))
        self.register(TaxonomicNode(
            taxon_id="fungi",
            name="Hongos",
            parent_id="life",
            rank=TaxonomicRank.KINGDOM,
            description="Organismos heterótrofos por absorción",
        ))
        self.register(TaxonomicNode(
            taxon_id="bacteria",
            name="Bacterias",
            parent_id="life",
            rank=TaxonomicRank.KINGDOM,
            description="Organismos unicelulares procariotas",
        ))
        self.register(TaxonomicNode(
            taxon_id="protista",
            name="Protistas",
            parent_id="life",
            rank=TaxonomicRank.KINGDOM,
            description="Organismos eucariotas unicelulares",
        ))
        
        # =====================================================================
        # PHYLUMS (Animalia)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="vertebrata",
            name="Vertebrados",
            parent_id="animalia",
            rank=TaxonomicRank.PHYLUM,
            description="Animales con columna vertebral",
        ))
        self.register(TaxonomicNode(
            taxon_id="arthropoda",
            name="Artrópodos",
            parent_id="animalia",
            rank=TaxonomicRank.PHYLUM,
            description="Animales con exoesqueleto y patas articuladas",
        ))
        self.register(TaxonomicNode(
            taxon_id="mollusca",
            name="Moluscos",
            parent_id="animalia",
            rank=TaxonomicRank.PHYLUM,
            description="Animales de cuerpo blando (caracoles, pulpos)",
        ))
        
        # =====================================================================
        # CLASSES (Vertebrata)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="mammalia",
            name="Mamíferos",
            parent_id="vertebrata",
            rank=TaxonomicRank.CLASS,
            description="Vertebrados de sangre caliente con glándulas mamarias",
        ))
        self.register(TaxonomicNode(
            taxon_id="aves",
            name="Aves",
            parent_id="vertebrata",
            rank=TaxonomicRank.CLASS,
            description="Vertebrados con plumas y pico",
        ))
        self.register(TaxonomicNode(
            taxon_id="reptilia",
            name="Reptiles",
            parent_id="vertebrata",
            rank=TaxonomicRank.CLASS,
            description="Vertebrados de sangre fría con escamas",
        ))
        self.register(TaxonomicNode(
            taxon_id="amphibia",
            name="Anfibios",
            parent_id="vertebrata",
            rank=TaxonomicRank.CLASS,
            description="Vertebrados con vida dual agua/tierra",
        ))
        self.register(TaxonomicNode(
            taxon_id="pisces",
            name="Peces",
            parent_id="vertebrata",
            rank=TaxonomicRank.CLASS,
            description="Vertebrados acuáticos con branquias",
        ))
        
        # =====================================================================
        # CLASSES (Arthropoda)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="insecta",
            name="Insectos",
            parent_id="arthropoda",
            rank=TaxonomicRank.CLASS,
            description="Artrópodos con 6 patas",
        ))
        self.register(TaxonomicNode(
            taxon_id="arachnida",
            name="Arácnidos",
            parent_id="arthropoda",
            rank=TaxonomicRank.CLASS,
            description="Artrópodos con 8 patas (arañas, escorpiones)",
        ))
        
        # =====================================================================
        # ORDERS (Mammalia)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="carnivora",
            name="Carnívoros",
            parent_id="mammalia",
            rank=TaxonomicRank.ORDER,
            description="Mamíferos depredadores",
        ))
        self.register(TaxonomicNode(
            taxon_id="primates",
            name="Primates",
            parent_id="mammalia",
            rank=TaxonomicRank.ORDER,
            description="Mamíferos con manos prensiles",
        ))
        self.register(TaxonomicNode(
            taxon_id="rodentia",
            name="Roedores",
            parent_id="mammalia",
            rank=TaxonomicRank.ORDER,
            description="Mamíferos con dientes incisivos crecientes",
        ))
        self.register(TaxonomicNode(
            taxon_id="cetacea",
            name="Cetáceos",
            parent_id="mammalia",
            rank=TaxonomicRank.ORDER,
            description="Mamíferos acuáticos (ballenas, delfines)",
        ))
        self.register(TaxonomicNode(
            taxon_id="chiroptera",
            name="Murciélagos",
            parent_id="mammalia",
            rank=TaxonomicRank.ORDER,
            description="Mamíferos voladores",
        ))
        
        # =====================================================================
        # FAMILIES (Carnivora)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="canidae",
            name="Cánidos",
            parent_id="carnivora",
            rank=TaxonomicRank.FAMILY,
            description="Perros, lobos, zorros",
        ))
        self.register(TaxonomicNode(
            taxon_id="felidae",
            name="Félidos",
            parent_id="carnivora",
            rank=TaxonomicRank.FAMILY,
            description="Gatos, leones, tigres",
        ))
        self.register(TaxonomicNode(
            taxon_id="ursidae",
            name="Úrsidos",
            parent_id="carnivora",
            rank=TaxonomicRank.FAMILY,
            description="Osos",
        ))
        
        # =====================================================================
        # FAMILIES (Primates)
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="hominidae",
            name="Homínidos",
            parent_id="primates",
            rank=TaxonomicRank.FAMILY,
            description="Grandes simios y humanos",
        ))
        
        # =====================================================================
        # GENUS
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="canis",
            name="Canis",
            parent_id="canidae",
            rank=TaxonomicRank.GENUS,
            description="Perros, lobos, coyotes",
            scientific_name="Canis",
        ))
        self.register(TaxonomicNode(
            taxon_id="felis",
            name="Felis",
            parent_id="felidae",
            rank=TaxonomicRank.GENUS,
            description="Gatos pequeños",
            scientific_name="Felis",
        ))
        self.register(TaxonomicNode(
            taxon_id="homo",
            name="Homo",
            parent_id="hominidae",
            rank=TaxonomicRank.GENUS,
            description="Humanos y especies cercanas",
            scientific_name="Homo",
        ))
        
        # =====================================================================
        # SPECIES
        # =====================================================================
        self.register(TaxonomicNode(
            taxon_id="canis_lupus",
            name="Lobo",
            parent_id="canis",
            rank=TaxonomicRank.SPECIES,
            description="Lobo gris",
            scientific_name="Canis lupus",
        ))
        self.register(TaxonomicNode(
            taxon_id="homo_sapiens",
            name="Humano",
            parent_id="homo",
            rank=TaxonomicRank.SPECIES,
            description="Ser humano moderno",
            scientific_name="Homo sapiens",
        ))
        
        self._logger.info(
            f"Taxonomía por defecto inicializada: {len(self._nodes)} taxones"
        )
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def __len__(self) -> int:
        return len(self._nodes)
    
    def __contains__(self, taxon_id: str) -> bool:
        return taxon_id in self._nodes
    
    def __repr__(self) -> str:
        return f"TaxonomicSystem({len(self._nodes)} taxones)"