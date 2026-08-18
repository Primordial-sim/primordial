"""Módulo de Estado Global Determinista de la Simulación.

Responsabilidad: 
Mantener la fuente de verdad de las entidades físicas. Extrae los datos del 
búfer transaccional ('pending') y los consolida alterando los objetos en memoria 
una vez por ciclo. Dispara eventos para la interfaz o métricas.

Integra con el sistema de memoria cognitiva para:
- Detectar muertes y generar recuerdos de duelo para familiares/amigos
- Registrar nacimientos y crear recuerdos para los padres

Integra con el sistema de núcleos residenciales para:
- Crear núcleos al formar parejas (matrimonios)
- Añadir miembros al nacer o ser adoptados
- Separar núcleos en divorcios
- Eliminar miembros al fallecer
- Actualizar centros de núcleos cada tick

Integra con el sistema de ocupación de casillas para:
- Garantizar la regla fundamental: 1 agente = 1 casilla
- Rastrear qué agente ocupa cada posición del mundo

NOTA: La importación de CognitiveMemorySystem se hace localmente en los métodos
para evitar dependencias circulares.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.config.simulation_config import SimulationConfig
from core.state.world_grid import WorldGrid
from entities.person.person import Person
from systems.environment.epidemiological_map import EpidemiologicalMap
from systems.social.residential_nucleus import (
    ResidentialNucleus,
    NucleusMemberRole,
    NucleusType,
)

# Eventos poblacionales importados
from events.population.adoption_completed import AdoptionCompletedEvent
from events.population.divorce_occurred import DivorceOccurredEvent
from events.population.marriage_created import MarriageCreatedEvent
from events.population.person_born import PersonBornEvent
from events.population.person_died import PersonDiedEvent


class WorldState:
    """Contenedor de la realidad simulada. Garantiza aislamiento en la lectura."""

    def __init__(self, config: SimulationConfig, width: int, height: int) -> None:
        """Inicializa el estado del mundo y sus dimensiones espaciales."""
        self.logger = logging.getLogger("WorldState")
        self.config = config
        self.width = width
        self.height = height
        
        self.persons: Dict[int, Person] = {}      
        self._last_entity_id: int = 0 
        
        self.world_grid = WorldGrid(width, height)
        self.epidemiological_map = EpidemiologicalMap(config.environment.max_viral_load)
        self.world_days_elapsed: float = 0.0
        
        # =====================================================================
        # NÚCLEOS RESIDENCIALES (FASE A)
        # =====================================================================
        self._nuclei: Dict[int, ResidentialNucleus] = {}
        self._agent_to_nucleus: Dict[int, int] = {}  # agent_id -> nucleus_id
        
        # =====================================================================
        # OCUPACIÓN DE CASILLAS (FASE C)
        # Regla fundamental: 1 agente = 1 casilla
        # =====================================================================
        self._cell_occupancy: Dict[Tuple[int, int], Optional[int]] = {}
        
    def get_next_entity_id(self) -> int:
        """Genera de forma segura e incremental el ID único para nuevos agentes."""
        self._last_entity_id += 1
        return self._last_entity_id

    def add_person(self, person: Person) -> None:
        """Registra una nueva entidad en el plano físico del mundo."""
        self.persons[person.entity_id] = person
        if person.entity_id > self._last_entity_id:
            self._last_entity_id = person.entity_id
        
        # FASE C: Ocupar la casilla del nuevo agente
        self.occupy_cell(int(person.x), int(person.y), person.entity_id)
        
        # FASE A: Si el agente no tiene núcleo, crear uno individual
        if not hasattr(person, 'nucleus_id') or person.nucleus_id is None:
            self._create_single_nucleus(person.entity_id)

    def get_person(self, entity_id: int) -> Optional[Person]:
        """Devuelve una persona por su ID con máxima eficiencia de acceso O(1)."""
        return self.persons.get(entity_id)
        
    def get_person_by_id(self, entity_id: int) -> Optional[Person]:
        """Alias de compatibilidad para evitar roturas de código heredado."""
        return self.get_person(entity_id)

    def get_all_persons(self) -> Any:
        """Retorna una vista instantánea de todos los agentes vivos (O(1), sin copiar)."""
        return self.persons.values()

    def apply_commit(
        self, pending: Any, event_bus: Any = None, current_tick: int = 0
    ) -> None:
        """Aplica los cambios del búfer de forma atómica (Fase de Consolidación)."""
        
        # =====================================================================
        # 1. MUERTES
        # =====================================================================
        current_day = self.world_days_elapsed
        
        for entity_id, reason in pending.deaths.items():
            if entity_id in self.persons:
                p = self.persons.pop(entity_id)
                
                # FASE C: Liberar la casilla del agente fallecido
                self.free_cell(int(p.x), int(p.y))
                
                # FASE A: Eliminar al agente de su núcleo
                self._handle_death_in_nucleus(entity_id)
                
                # Generar recuerdos de duelo
                self._generate_grief_memories(entity_id, p, current_day, pending)
                
                if event_bus:
                    event_bus.publish(
                        PersonDiedEvent(entity_id, int(p.age), reason, current_tick)
                    )

        # =====================================================================
        # 2. ENVEJECIMIENTO FÍSICO
        # =====================================================================
        for entity_id, days in pending.age_increments.items():
            person = self.get_person(entity_id)
            if person:
                person.add_age(days)

        # =====================================================================
        # 3. SALUD MÉDICA AVANZADA
        # =====================================================================
        for entity_id, pathogen in pending.infections:
            p = self.get_person(entity_id)
            if p:
                p.infect(pathogen)
                
        for entity_id, pathogen_id in pending.recoveries:
            p = self.get_person(entity_id)
            if p:
                p.recover(pathogen_id)

        # =====================================================================
        # 4. EMBARAZOS Y NACIMIENTOS
        # =====================================================================
        for entity_id, data in pending.pregnancy_updates.items():
            madre = self.get_person(entity_id)
            if madre:
                madre.update_pregnancy(
                    data["is_pregnant"], 
                    data.get("pregnancy_days", 0.0),
                    data.get("litter_size", 1),
                )
                if data.get("failed_increment", 0) > 0:
                    for _ in range(data["failed_increment"]):  
                        madre.add_failed_pregnancy()

        for data in pending.births:
            new_id = self.get_next_entity_id()
            baby_genome = data.get("genome")
            
            # Envolver coordenadas de nacimiento como toroide
            birth_x = int(data["x"]) % self.width
            birth_y = int(data["y"]) % self.height
            
            newborn = Person(
                config=self.config,
                entity_id=new_id, 
                x=birth_x, 
                y=birth_y, 
                age=0.0, 
                genome=baby_genome,
                species=getattr(baby_genome, 'species_baseline', 'human'),
            )
            
            mother_id = data["mother_id"]
            father_id = data["father_id"]
            newborn.set_parents(mother_id, father_id)
            self.add_person(newborn)
            
            # FASE C: Ocupar la casilla del recién nacido (con wrapping aplicado)
            self.occupy_cell(birth_x, birth_y, new_id)
                            
            madre = self.get_person(mother_id)
            padre = self.get_person(father_id) if father_id else None
            
            if madre:
                madre.add_biological_child()
            if padre:
                padre.add_biological_child()
            
            # FASE A: Añadir al recién nacido al núcleo de los padres
            self._handle_birth_in_nucleus(new_id, mother_id, father_id)
            
            # Registrar recuerdos del nacimiento
            self._register_birth_memories(new_id, madre, padre, current_day, pending)
            
            if event_bus:
                gender = getattr(newborn, 'gender', 'indefinido')
                event_bus.publish(
                    PersonBornEvent(
                        new_id, mother_id, father_id, data["x"], data["y"],
                        gender, current_tick,
                    )
                )

        # =====================================================================
        # 5. ADOPCIONES LEGALES
        # =====================================================================
        for adoption in pending.adoptions:
            child = self.get_person(adoption["child_id"])
            parent_a = self.get_person(adoption["parent_a"])
            parent_b = (
                self.get_person(adoption["parent_b"])
                if adoption["parent_b"]
                else None
            )
            
            is_single_parent = adoption.get("is_single_parent", False)

            if child and parent_a:
                parent_a.add_child()
                child.add_adoptive_parent(parent_a.entity_id)
                
                if parent_b: 
                    parent_b.add_child()
                    child.add_adoptive_parent(parent_b.entity_id)
                
                # FASE A: Añadir al niño adoptado al núcleo de los padres
                self._handle_adoption_in_nucleus(
                    child.entity_id, parent_a.entity_id,
                    parent_b.entity_id if parent_b else None,
                )
                    
                if event_bus:
                    event_bus.publish(
                        AdoptionCompletedEvent(
                            child.entity_id, 
                            parent_a.entity_id, 
                            getattr(parent_b, 'entity_id', None), 
                            current_tick,
                            is_single_parent,
                        )
                    )
        
        # =====================================================================
        # 6. RELACIONES Y MOVIMIENTOS ESPACIALES
        # =====================================================================
        for entity_id, (new_x, new_y) in pending.movements.items():
            p = self.get_person(entity_id)
            if p:
                # Envolver como toroide: si sale por un lado, aparece por el otro
                wrapped_x = int(new_x) % self.width
                wrapped_y = int(new_y) % self.height
                
                # FASE C: Liberar casilla antigua y ocupar la nueva
                old_x, old_y = int(p.x), int(p.y)
                self.free_cell(old_x, old_y)
                
                p.set_position(wrapped_x, wrapped_y)
                
                self.occupy_cell(wrapped_x, wrapped_y, entity_id)

        # Divorcios
        for p_a_id, p_b_id in pending.divorces:
            pa = self.get_person(p_a_id)
            pb = self.get_person(p_b_id)
            
            if pa and pa.partner_id == p_b_id:
                pa.register_divorce()
            if pb and pb.partner_id == p_a_id:
                pb.register_divorce()
            
            # FASE A: Separar el núcleo en dos
            self._handle_divorce_in_nucleus(p_a_id, p_b_id)
            
            if event_bus: 
                event_bus.publish(
                    DivorceOccurredEvent(p_a_id, p_b_id, "separacion_natural", current_tick)
                )

        # Matrimonios
        for p_a_id, p_b_id in pending.marriages.items():
            pa = self.get_person(p_a_id)
            pb = self.get_person(p_b_id)
            
            if pa and pb:
                pa.register_marriage(p_b_id)
                pb.register_marriage(p_a_id)
                
                # FASE A: Crear o fusionar núcleos para la pareja
                self._handle_marriage_in_nucleus(p_a_id, p_b_id)
                
                if event_bus and p_a_id < p_b_id:
                    event_bus.publish(MarriageCreatedEvent(p_a_id, p_b_id, current_tick))

        # =====================================================================
        # 7. PSICOLOGÍA TRANSACCIONAL
        # =====================================================================
        # 7a. Actualizaciones de memoria
        for entity_id, memory_changes in pending.memory_updates.items():
            person = self.get_person(entity_id)
            if person:
                for key, value in memory_changes.items():
                    person.memory[key] = value

        # 7b. Actualizaciones de emociones
        for entity_id, emotion_changes in pending.emotion_updates.items():
            person = self.get_person(entity_id)
            if person:
                for emotion_name, amount in emotion_changes:
                    person.update_emotion(emotion_name, amount)

        # 7c. Actualizaciones de flags de libre albedrío
        for entity_id, flag_changes in pending.free_will_flags_updates.items():
            person = self.get_person(entity_id)
            if person:
                if "free_will_flags" not in person.memory or not isinstance(person.memory["free_will_flags"], dict):
                    person.memory["free_will_flags"] = {}
                
                for flag_name, flag_value in flag_changes.items():
                    person.memory["free_will_flags"][flag_name] = flag_value
        
        # 7d. Actualizaciones de motivaciones continuas
        for entity_id, motivation_changes in pending.motivation_updates.items():
            person = self.get_person(entity_id)
            if person and hasattr(person, '_motivations'):
                for key, value in motivation_changes.items():
                    # Detectar si es un set absoluto (prefijo __set__)
                    if key.startswith("__set__"):
                        motivation_name = key[7:]  # Quitar prefijo "__set__"
                        if motivation_name in person._motivations:
                            person._motivations[motivation_name] = max(0.0, min(1.0, value))
                    else:
                        # Es un delta acumulativo
                        if key in person._motivations:
                            new_value = person._motivations[key] + value
                            person._motivations[key] = max(0.0, min(1.0, new_value))

        # =====================================================================
        # 8. ACTUALIZACIÓN FINAL DEL TICK
        # =====================================================================
        
        # FASE A: Actualizar centros de todos los núcleos
        self.update_nuclei_centers()
        
        # FASE C: Verificar consistencia de ocupación
        self._verify_occupancy_consistency()

    # =========================================================================
    # GESTIÓN DE NÚCLEOS RESIDENCIALES (FASE A)
    # =========================================================================
    
    def _create_single_nucleus(self, agent_id: int) -> ResidentialNucleus:
        """Crea un núcleo individual para un agente sin núcleo."""
        nucleus = ResidentialNucleus.create_single(agent_id)
        self.register_nucleus(nucleus)
        
        person = self.get_person(agent_id)
        if person:
            person.nucleus_id = nucleus.nucleus_id
        
        self.logger.debug(
            "🏠 Núcleo individual %d creado para agente %d",
            nucleus.nucleus_id, agent_id,
        )
        return nucleus
    
    def _handle_marriage_in_nucleus(self, agent_a_id: int, agent_b_id: int) -> None:
        """Maneja la creación/fusión de núcleos al producirse un matrimonio."""
        nucleus_a_id = self._agent_to_nucleus.get(agent_a_id)
        nucleus_b_id = self._agent_to_nucleus.get(agent_b_id)
        
        # Caso 1: Ambos ya están en el mismo núcleo (convivían antes)
        if nucleus_a_id is not None and nucleus_a_id == nucleus_b_id:
            nucleus = self._nuclei.get(nucleus_a_id)
            if nucleus:
                nucleus.on_marriage(agent_a_id, agent_b_id)
            return
        
        # Caso 2: Ambos tienen núcleos diferentes → fusionar
        if nucleus_a_id is not None and nucleus_b_id is not None:
            nucleus_a = self._nuclei.get(nucleus_a_id)
            nucleus_b = self._nuclei.get(nucleus_b_id)
            
            if nucleus_a and nucleus_b:
                # Mover todos los miembros del núcleo B al núcleo A
                for member_id in list(nucleus_b.get_members()):
                    role = nucleus_b.get_member_role(member_id)
                    # CORRECCIÓN: Si el rol es None, usar rol por defecto
                    if role is None:
                        role = NucleusMemberRole.OTHER
                    nucleus_b.remove_member(member_id)
                    nucleus_a.add_member(member_id, role)
                    self._agent_to_nucleus[member_id] = nucleus_a_id
                    
                    person = self.get_person(member_id)
                    if person:
                        person.nucleus_id = nucleus_a_id
                
                # Eliminar el núcleo B vacío
                self.unregister_nucleus(nucleus_b_id)
                nucleus_a.on_marriage(agent_a_id, agent_b_id)
                
                self.logger.info(
                    "💍 Fusión de núcleos: %d + %d → %d (matrimonio %d-%d)",
                    nucleus_a_id, nucleus_b_id, nucleus_a_id, agent_a_id, agent_b_id,
                )
            return
        
        # Caso 3: Solo uno tiene núcleo → añadir al otro
        if nucleus_a_id is not None:
            nucleus = self._nuclei.get(nucleus_a_id)
            if nucleus:
                nucleus.add_member(agent_b_id, NucleusMemberRole.PARTNER)
                self._agent_to_nucleus[agent_b_id] = nucleus_a_id
                person_b = self.get_person(agent_b_id)
                if person_b:
                    person_b.nucleus_id = nucleus_a_id
                nucleus.on_marriage(agent_a_id, agent_b_id)
            return
        
        if nucleus_b_id is not None:
            nucleus = self._nuclei.get(nucleus_b_id)
            if nucleus:
                nucleus.add_member(agent_a_id, NucleusMemberRole.PARTNER)
                self._agent_to_nucleus[agent_a_id] = nucleus_b_id
                person_a = self.get_person(agent_a_id)
                if person_a:
                    person_a.nucleus_id = nucleus_b_id
                nucleus.on_marriage(agent_a_id, agent_b_id)
            return
        
        # Caso 4: Ninguno tiene núcleo → crear uno nuevo de pareja
        nucleus = ResidentialNucleus.create_couple(agent_a_id, agent_b_id)
        self.register_nucleus(nucleus)
        
        person_a = self.get_person(agent_a_id)
        person_b = self.get_person(agent_b_id)
        if person_a:
            person_a.nucleus_id = nucleus.nucleus_id
        if person_b:
            person_b.nucleus_id = nucleus.nucleus_id
        
        self.logger.info(
            "💍 Nuevo núcleo de pareja %d creado (%d-%d)",
            nucleus.nucleus_id, agent_a_id, agent_b_id,
        )
    
    def _handle_birth_in_nucleus(
        self, newborn_id: int, mother_id: int, father_id: Optional[int]
    ) -> None:
        """Añade al recién nacido al núcleo de sus padres."""
        # Determinar el núcleo: priorizar el de la madre, luego el del padre
        nucleus_id = self._agent_to_nucleus.get(mother_id)
        if nucleus_id is None and father_id is not None:
            nucleus_id = self._agent_to_nucleus.get(father_id)
        
        if nucleus_id is not None:
            nucleus = self._nuclei.get(nucleus_id)
            if nucleus:
                nucleus.on_birth(newborn_id)
                self._agent_to_nucleus[newborn_id] = nucleus_id
                
                newborn = self.get_person(newborn_id)
                if newborn:
                    newborn.nucleus_id = nucleus_id
        else:
            # Si los padres no tienen núcleo, crear uno familiar
            nucleus = ResidentialNucleus.create_family(mother_id, father_id, [newborn_id])
            self.register_nucleus(nucleus)
            
            self._agent_to_nucleus[mother_id] = nucleus.nucleus_id
            mother = self.get_person(mother_id)
            if mother:
                mother.nucleus_id = nucleus.nucleus_id
            
            if father_id is not None:
                self._agent_to_nucleus[father_id] = nucleus.nucleus_id
                father = self.get_person(father_id)
                if father:
                    father.nucleus_id = nucleus.nucleus_id
            
            self._agent_to_nucleus[newborn_id] = nucleus.nucleus_id
            newborn = self.get_person(newborn_id)
            if newborn:
                newborn.nucleus_id = nucleus.nucleus_id
    
    def _handle_adoption_in_nucleus(
        self, child_id: int, parent_a_id: int, parent_b_id: Optional[int]
    ) -> None:
        """Añade al niño adoptado al núcleo de sus padres adoptivos."""
        # Determinar el núcleo: priorizar el de parent_a
        nucleus_id = self._agent_to_nucleus.get(parent_a_id)
        if nucleus_id is None and parent_b_id is not None:
            nucleus_id = self._agent_to_nucleus.get(parent_b_id)
        
        if nucleus_id is not None:
            nucleus = self._nuclei.get(nucleus_id)
            if nucleus:
                nucleus.add_member(child_id, NucleusMemberRole.CHILD)
                self._agent_to_nucleus[child_id] = nucleus_id
                
                child = self.get_person(child_id)
                if child:
                    child.nucleus_id = nucleus_id
        else:
            # Si los padres no tienen núcleo, crear uno familiar
            nucleus = ResidentialNucleus.create_family(parent_a_id, parent_b_id, [child_id])
            self.register_nucleus(nucleus)
            
            self._agent_to_nucleus[parent_a_id] = nucleus.nucleus_id
            parent_a = self.get_person(parent_a_id)
            if parent_a:
                parent_a.nucleus_id = nucleus.nucleus_id
            
            if parent_b_id is not None:
                self._agent_to_nucleus[parent_b_id] = nucleus.nucleus_id
                parent_b = self.get_person(parent_b_id)
                if parent_b:
                    parent_b.nucleus_id = nucleus.nucleus_id
            
            self._agent_to_nucleus[child_id] = nucleus.nucleus_id
            child = self.get_person(child_id)
            if child:
                child.nucleus_id = nucleus.nucleus_id
    
    def _handle_death_in_nucleus(self, deceased_id: int) -> None:
        """Elimina al agente fallecido de su núcleo."""
        nucleus_id = self._agent_to_nucleus.get(deceased_id)
        if nucleus_id is None:
            return
        
        nucleus = self._nuclei.get(nucleus_id)
        if nucleus is None:
            # Limpiar referencia huérfana
            if deceased_id in self._agent_to_nucleus:
                del self._agent_to_nucleus[deceased_id]
            return
        
        nucleus.on_death(deceased_id)
        if deceased_id in self._agent_to_nucleus:
            del self._agent_to_nucleus[deceased_id]
        
        # Si el núcleo queda vacío, eliminarlo
        if nucleus.is_empty:
            self.unregister_nucleus(nucleus_id)
    
    def _handle_divorce_in_nucleus(self, agent_a_id: int, agent_b_id: int) -> None:
        """Separa el núcleo en dos tras un divorcio.
        
        Estrategia: agent_a mantiene el núcleo original, agent_b se lleva
        la mitad de los hijos (los más pequeños se quedan con agent_a).
        """
        nucleus_id = self._agent_to_nucleus.get(agent_a_id)
        if nucleus_id is None:
            return
        
        nucleus = self._nuclei.get(nucleus_id)
        if nucleus is None:
            return
        
        # agent_b sale del núcleo original
        nucleus.remove_member(agent_b_id)
        if agent_b_id in self._agent_to_nucleus:
            del self._agent_to_nucleus[agent_b_id]
        
        # Determinar qué hijos se van con agent_b
        # CORRECCIÓN: Filtrar solo hijos que aún existen en el mundo
        children_in_nucleus = [
            m_id for m_id in nucleus.get_members()
            if nucleus.get_member_role(m_id) == NucleusMemberRole.CHILD
            and self.get_person(m_id) is not None
        ]
        
        # CORRECCIÓN: Ordenar por edad usando una función segura
        def _get_age_safe(cid: int) -> float:
            person = self.get_person(cid)
            if person is not None:
                return person.age
            return 0.0
        
        children_sorted = sorted(children_in_nucleus, key=_get_age_safe)
        
        # La primera mitad se queda con agent_a, la segunda mitad va con agent_b
        mid = len(children_sorted) // 2
        children_with_b = children_sorted[mid:]
        
        # Crear nuevo núcleo para agent_b
        nucleus_b = ResidentialNucleus.create_single(agent_b_id)
        
        # Mover hijos a núcleo_b
        for child_id in children_with_b:
            nucleus.remove_member(child_id)
            nucleus_b.add_member(child_id, NucleusMemberRole.CHILD)
            self._agent_to_nucleus[child_id] = nucleus_b.nucleus_id
            
            child = self.get_person(child_id)
            if child:
                child.nucleus_id = nucleus_b.nucleus_id
        
        # Actualizar nucleus_id de agent_b
        self._agent_to_nucleus[agent_b_id] = nucleus_b.nucleus_id
        person_b = self.get_person(agent_b_id)
        if person_b:
            person_b.nucleus_id = nucleus_b.nucleus_id
        
        self.register_nucleus(nucleus_b)
        
        self.logger.info(
            "💔 Divorcio: Núcleo %d dividido → %d (agente %d) + %d (agente %d)",
            nucleus_id, nucleus_id, agent_a_id, nucleus_b.nucleus_id, agent_b_id,
        )

    # =========================================================================
    # API PÚBLICA DE NÚCLEOS (FASE A)
    # =========================================================================
    
    def register_nucleus(self, nucleus: ResidentialNucleus) -> None:
        """Registra un nuevo núcleo residencial."""
        self._nuclei[nucleus.nucleus_id] = nucleus
        for agent_id in nucleus.get_members():
            self._agent_to_nucleus[agent_id] = nucleus.nucleus_id

    def unregister_nucleus(self, nucleus_id: int) -> None:
        """Elimina un núcleo del registro."""
        if nucleus_id in self._nuclei:
            nucleus = self._nuclei[nucleus_id]
            for agent_id in nucleus.get_members():
                if agent_id in self._agent_to_nucleus:
                    del self._agent_to_nucleus[agent_id]
            del self._nuclei[nucleus_id]

    def get_nucleus(self, nucleus_id: int) -> Optional[ResidentialNucleus]:
        """Retorna un núcleo por su ID."""
        return self._nuclei.get(nucleus_id)

    def get_nucleus_for_agent(self, agent_id: int) -> Optional[ResidentialNucleus]:
        """Retorna el núcleo al que pertenece un agente."""
        nucleus_id = self._agent_to_nucleus.get(agent_id)
        if nucleus_id is not None:
            return self._nuclei.get(nucleus_id)
        return None

    def get_nucleus_id_for_agent(self, agent_id: int) -> Optional[int]:
        """Retorna el ID del núcleo de un agente."""
        return self._agent_to_nucleus.get(agent_id)

    def assign_agent_to_nucleus(self, agent_id: int, nucleus_id: int) -> None:
        """Asigna un agente a un núcleo existente."""
        self._agent_to_nucleus[agent_id] = nucleus_id
        if nucleus_id in self._nuclei:
            self._nuclei[nucleus_id].add_member(agent_id, NucleusMemberRole.OTHER)
        
        person = self.get_person(agent_id)
        if person:
            person.nucleus_id = nucleus_id

    def remove_agent_from_nucleus(self, agent_id: int) -> None:
        """Elimina un agente de su núcleo actual."""
        nucleus_id = self._agent_to_nucleus.get(agent_id)
        if nucleus_id is not None and nucleus_id in self._nuclei:
            self._nuclei[nucleus_id].remove_member(agent_id)
            del self._agent_to_nucleus[agent_id]
            
            person = self.get_person(agent_id)
            if person:
                person.nucleus_id = None

            # Si el núcleo queda vacío, eliminarlo
            if self._nuclei[nucleus_id].is_empty:
                del self._nuclei[nucleus_id]

    def update_nuclei_centers(self) -> None:
        """Actualiza los centros de todos los núcleos.
        
        Debe llamarse una vez por tick después de aplicar movimientos.
        """
        positions = {}
        for person in self.get_all_persons():
            positions[person.entity_id] = (person.x, person.y)
        
        for nucleus in self._nuclei.values():
            nucleus.update_center(positions)

    def get_all_nuclei(self) -> List[ResidentialNucleus]:
        """Retorna todos los núcleos registrados."""
        return list(self._nuclei.values())

    def get_nucleus_count(self) -> int:
        """Retorna el número de núcleos activos."""
        return len(self._nuclei)

    def get_nuclei_summary(self) -> Dict[str, int]:
        """Retorna un resumen de los núcleos por tipo."""
        summary: Dict[str, int] = {}
        for nucleus in self._nuclei.values():
            type_name = nucleus.nucleus_type.value
            summary[type_name] = summary.get(type_name, 0) + 1
        return summary

    # =========================================================================
    # OCUPACIÓN DE CASILLAS (FASE C)
    # =========================================================================
    
    def is_cell_occupied(self, x: int, y: int) -> bool:
        """Verifica si una casilla está ocupada por algún agente."""
        cell = (int(x), int(y))
        return cell in self._cell_occupancy and self._cell_occupancy[cell] is not None

    def get_cell_occupant(self, x: int, y: int) -> Optional[int]:
        """Retorna el entity_id del agente que ocupa la casilla, o None."""
        return self._cell_occupancy.get((int(x), int(y)))

    def occupy_cell(self, x: int, y: int, entity_id: int) -> None:
        """Marca una casilla como ocupada por un agente."""
        self._cell_occupancy[(int(x), int(y))] = entity_id

    def free_cell(self, x: int, y: int) -> None:
        """Libera una casilla (cuando un agente muere o se mueve)."""
        cell = (int(x), int(y))
        if cell in self._cell_occupancy:
            del self._cell_occupancy[cell]

    def rebuild_occupancy_map(self) -> None:
        """Reconstruye el mapa de ocupación desde las posiciones actuales.
        
        Debe llamarse al inicializar el mundo o tras cargar una partida.
        """
        self._cell_occupancy.clear()
        for person in self.get_all_persons():
            cell = (int(person.x), int(person.y))
            self._cell_occupancy[cell] = person.entity_id
        
        self.logger.info(
            "🗺️ Mapa de ocupación reconstruido: %d casillas ocupadas",
            len(self._cell_occupancy),
        )

    def _verify_occupancy_consistency(self) -> None:
        """Verifica que no haya dos agentes en la misma casilla.
        
        Si detecta inconsistencias, reconstruye el mapa de ocupación.
        Esto no debería ocurrir si el sistema funciona correctamente,
        pero sirve como salvaguarda.
        """
        seen_cells: Dict[Tuple[int, int], int] = {}
        conflicts = 0
        
        for person in self.get_all_persons():
            cell = (int(person.x), int(person.y))
            if cell in seen_cells:
                conflicts += 1
                self.logger.warning(
                    "⚠️ Conflicto de ocupación: casilla %s tiene agentes %d y %d",
                    cell, seen_cells[cell], person.entity_id,
                )
            else:
                seen_cells[cell] = person.entity_id
        
        if conflicts > 0:
            self.logger.warning(
                "⚠️ %d conflictos de ocupación detectados. Reconstruyendo mapa.",
                conflicts,
            )
            self.rebuild_occupancy_map()

    # =========================================================================
    # MÉTODOS AUXILIARES PARA GENERAR RECUERDOS
    # =========================================================================
    
    def _generate_grief_memories(
        self,
        deceased_id: int,
        deceased: Person,
        current_day: float,
        pending: Any,
    ) -> None:
        """Genera recuerdos de duelo para personas que tenían relación con el fallecido.
        
        IMPORTACIÓN LOCAL: Se importa CognitiveMemorySystem aquí para evitar
        dependencia circular con world_state.
        """
        from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
        
        for person in self.get_all_persons():
            if person.entity_id == deceased_id:
                continue
            
            if not hasattr(person, 'memory') or not isinstance(person.memory, dict):
                continue
            
            episodic = person.memory.get("episodic", {})
            if not isinstance(episodic, dict):
                continue
            
            for mem_type in [
                CognitiveMemorySystem.TYPE_COMPANION,
                CognitiveMemorySystem.TYPE_MARRIAGE,
                CognitiveMemorySystem.TYPE_CHILD,
                CognitiveMemorySystem.TYPE_CONFLICT,
                CognitiveMemorySystem.TYPE_EXPERIENCE,
            ]:
                key = f"{mem_type}_{deceased_id}"
                if key in episodic:
                    existing_memory = episodic[key]
                    relationship_intensity = existing_memory.get('intensity', 0.5)
                    grief_intensity = min(1.0, relationship_intensity * 1.2)
                    
                    CognitiveMemorySystem.add_memory(
                        person=person,
                        mem_type=CognitiveMemorySystem.TYPE_DEATH,
                        target_id=str(deceased_id),
                        intensity=grief_intensity,
                        valence=-1,
                        context="duelo",
                        current_day=current_day,
                        pending=pending,
                    )
                    
                    self.logger.debug(
                        "🕊️ Duelo generado: Agente %s recuerda muerte de %s (intensidad: %.2f)",
                        person.entity_id,
                        deceased_id,
                        grief_intensity,
                    )
                    break

    def _register_birth_memories(
        self,
        newborn_id: int,
        mother: Optional[Person],
        father: Optional[Person],
        current_day: float,
        pending: Any,
    ) -> None:
        """Registra recuerdos del nacimiento para los padres.
        
        IMPORTACIÓN LOCAL: Se importa CognitiveMemorySystem aquí para evitar
        dependencia circular con world_state.
        """
        from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
        
        if mother is not None:
            CognitiveMemorySystem.add_memory(
                person=mother,
                mem_type=CognitiveMemorySystem.TYPE_CHILD,
                target_id=str(newborn_id),
                intensity=1.0,
                valence=1,
                context="nacimiento",
                current_day=current_day,
                pending=pending,
            )
            
            self.logger.debug(
                "👶 Madre %s recuerda nacimiento de hijo %s",
                mother.entity_id,
                newborn_id,
            )
        
        if father is not None:
            CognitiveMemorySystem.add_memory(
                person=father,
                mem_type=CognitiveMemorySystem.TYPE_CHILD,
                target_id=str(newborn_id),
                intensity=0.9,
                valence=1,
                context="nacimiento",
                current_day=current_day,
                pending=pending,
            )
            
            self.logger.debug(
                "👶 Padre %s recuerda nacimiento de hijo %s",
                father.entity_id,
                newborn_id,
            )