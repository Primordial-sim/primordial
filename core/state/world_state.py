"""Módulo de Estado Global Determinista de la Simulación.

Responsabilidad: 
Mantener la fuente de verdad de las entidades físicas. Extrae los datos del 
búfer transaccional ('pending') y los consolida alterando los objetos en memoria 
una vez por ciclo. Dispara eventos para la interfaz o métricas.

Integra con el sistema de memoria cognitiva para:
- Detectar muertes y generar recuerdos de duelo para familiares/amigos
- Registrar nacimientos y crear recuerdos para los padres

NOTA: La importación de CognitiveMemorySystem se hace localmente en los métodos
para evitar dependencias circulares.
"""

import logging
from typing import Any, Dict, List, Optional

from core.config.simulation_config import SimulationConfig
from core.state.world_grid import WorldGrid
from entities.person.person import Person
from systems.environment.epidemiological_map import EpidemiologicalMap

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
        
    def get_next_entity_id(self) -> int:
        """Genera de forma segura e incremental el ID único para nuevos agentes."""
        self._last_entity_id += 1
        return self._last_entity_id

    def add_person(self, person: Person) -> None:
        """Registra una nueva entidad en el plano físico del mundo."""
        self.persons[person.entity_id] = person
        if person.entity_id > self._last_entity_id:
            self._last_entity_id = person.entity_id

    def get_person(self, entity_id: int) -> Optional[Person]:
        """Devuelve una persona por su ID con máxima eficiencia de acceso O(1)."""
        return self.persons.get(entity_id)
        
    def get_person_by_id(self, entity_id: int) -> Optional[Person]:
        """Alias de compatibilidad para evitar roturas de código heredado."""
        return self.get_person(entity_id)

    def get_all_persons(self) -> Any:  # Cambiado de List[Person] a Any para aceptar dict_values
        """Retorna una vista instantánea de todos los agentes vivos (O(1), sin copiar en memoria)."""
        return self.persons.values()

    def apply_commit(
        self, pending: Any, event_bus: Any = None, current_tick: int = 0
    ) -> None:
        """Aplica los cambios del búfer de forma atómica (Fase de Consolidación)."""
        
        # 1. MUERTES
        current_day = self.world_days_elapsed
        
        for entity_id, reason in pending.deaths.items():
            if entity_id in self.persons:
                p = self.persons.pop(entity_id)
                
                # Generar recuerdos de duelo
                self._generate_grief_memories(entity_id, p, current_day, pending)
                
                if event_bus:
                    event_bus.publish(
                        PersonDiedEvent(entity_id, int(p.age), reason, current_tick)
                    )

        # 2. ENVEJECIMIENTO FÍSICO
        for entity_id, days in pending.age_increments.items():
            person = self.get_person(entity_id)
            if person:
                person.add_age(days)

        # 3. SALUD MÉDICA AVANZADA
        for entity_id, pathogen in pending.infections:
            p = self.get_person(entity_id)
            if p:
                p.infect(pathogen)
                
        for entity_id, pathogen_id in pending.recoveries:
            p = self.get_person(entity_id)
            if p:
                p.recover(pathogen_id)

        # 4. EMBARAZOS Y NACIMIENTOS
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
            
            newborn = Person(
                config=self.config,
                entity_id=new_id, 
                x=data["x"], 
                y=data["y"], 
                age=0.0, 
                genome=baby_genome,
                species=getattr(baby_genome, 'species_baseline', 'human'),
            )
            
            mother_id = data["mother_id"]
            father_id = data["father_id"]
            newborn.set_parents(mother_id, father_id)
            self.add_person(newborn)
                            
            madre = self.get_person(mother_id)
            padre = self.get_person(father_id) if father_id else None
            
            if madre:
                madre.add_biological_child()
            if padre:
                padre.add_biological_child()
            
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

        # 5. ADOPCIONES LEGALES
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
        
        # 6. RELACIONES Y MOVIMIENTOS ESPACIALES
        for entity_id, (new_x, new_y) in pending.movements.items():
            p = self.get_person(entity_id)
            if p:
                p.set_position(new_x, new_y)

        for p_a_id, p_b_id in pending.divorces:
            pa = self.get_person(p_a_id)
            pb = self.get_person(p_b_id)
            
            if pa and pa.partner_id == p_b_id:
                pa.register_divorce()
            if pb and pb.partner_id == p_a_id:
                pb.register_divorce()
            
            if event_bus: 
                event_bus.publish(
                    DivorceOccurredEvent(p_a_id, p_b_id, "separacion_natural", current_tick)
                )

        for p_a_id, p_b_id in pending.marriages.items():
            pa = self.get_person(p_a_id)
            pb = self.get_person(p_b_id)
            
            if pa and pb:
                pa.register_marriage(p_b_id)
                pb.register_marriage(p_a_id)
                
                if event_bus and p_a_id < p_b_id:
                    event_bus.publish(MarriageCreatedEvent(p_a_id, p_b_id, current_tick))

        # 7. PSICOLOGÍA TRANSACCIONAL
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
        
        # =====================================================================
        # 7d. NUEVO: Actualizaciones de motivaciones continuas
        # =====================================================================
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
    # MÉTODOS AUXILIARES PARA GENERAR RECUERDOS
    # =====================================================================
    
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
        # Importación local para evitar dependencia circular
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
        # Importación local para evitar dependencia circular
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