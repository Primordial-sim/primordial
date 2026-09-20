"""Sistema de Energía.

Gestiona el metabolismo energético de todos los organismos:
1. Genera energía por fotosíntesis (plantas y organismos fotosintéticos)
2. Aplica el coste metabólico basal (mantenimiento del organismo)
3. Gestiona el estado de inanición (starvation)
4. Calcula el riesgo de muerte por inanición

Flujo de energía en el ecosistema:
  Sol → Plantas (fotosíntesis) → Herbívoros (comen plantas) → Carnívoros (cazan)

Filosofía: "La energía es el recurso fundamental de la vida. Sin energía,
no hay movimiento, reproducción ni supervivencia."
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from core.state.world_state import WorldState
    from core.state.pending_changes import PendingChanges
    from systems.environment.environment_context import EnvironmentContext
    from entities.person.person import Person


class EnergySystem:
    """Sistema que gestiona el metabolismo energético de los organismos.
    
    Responsabilidades:
    - Fotosíntesis: Plantas y organismos fotosintéticos generan energía del sol
    - Metabolismo basal: Todos los organismos gastan energía por mantenimiento
    - Inanición: Sin energía, los organismos mueren
    
    Uso:
        energy_system = EnergySystem(config)
        
        # En cada tick de simulación:
        energy_system.process(state, pending, delta_days, context)
    """
    
    _logger = logging.getLogger("EnergySystem")
    
    def __init__(self, config) -> None:
        """Inicializa el sistema de energía.
        
        Args:
            config: Configuración de la simulación.
        """
        self.config = config
        
        # Parámetros de metabolismo
        # NOTA: Valores conservadores hasta que implementemos fuentes de comida
        # 0.1 energía/día = ~1000 días hasta agotar 100 de energía
        self.basal_metabolic_rate: float = 0.1  # Energía gastada por día en reposo
        self.starvation_death_threshold: float = 30.0  # Días sin energía antes de morir
        self.starvation_damage_rate: float = 0.05  # Daño por día de inanición
        
        # Parámetros de fotosíntesis
        self.photosynthesis_rate: float = 5.0  # Energía generada por día en condiciones óptimas
        self.photosynthesis_light_factor: float = 1.0  # Factor de luz (0-1)
        
        # Estadísticas
        self._total_starvation_deaths: int = 0
        self._total_energy_processed: int = 0
        self._total_photosynthesis_events: int = 0
    
    def process(
        self,
        state: 'WorldState',
        pending: 'PendingChanges',
        delta_days: float,
        context: 'EnvironmentContext',
    ) -> None:
        """Procesa el metabolismo energético para todos los organismos.
        
        Args:
            state: Estado del mundo con agentes.
            pending: Buffer de cambios pendientes.
            delta_days: Días transcurridos desde el último tick.
            context: Contexto ambiental.
        """
        persons = list(state.get_all_persons())
        if not persons:
            return
        
        starvation_deaths = 0
        photosynthesis_count = 0
        
        for person in persons:
            # 1. Generar energía por fotosíntesis (si aplica)
            if self._is_photosynthetic(person):
                energy_generated = self._calculate_photosynthesis(person, state, delta_days)
                person.add_energy(energy_generated)
                photosynthesis_count += 1
            
            # 2. Aplicar metabolismo basal
            metabolic_cost = self._calculate_metabolic_cost(person, delta_days)
            person.spend_energy(metabolic_cost)
            
            # 3. Avanzar contador de inanición
            person.advance_starvation(delta_days)
            
            # 4. NUEVO: Sincronizar energía física con emoción de energía
            self._sync_energy_with_emotions(person)
            
            # 4. Verificar muerte por inanición
            if self._check_starvation_death(person, delta_days):
                pending.register_death(
                    entity_id=person.entity_id,
                    reason="inanicion",
                )
                starvation_deaths += 1
                self._total_starvation_deaths += 1
                
                self._logger.debug(
                    f"💀 Muerte por inanición: {person.species} (entity_id={person.entity_id})"
                )
        
        self._total_energy_processed += len(persons)
        self._total_photosynthesis_events += photosynthesis_count
        
        if starvation_deaths > 0 or photosynthesis_count > 0:
            self._logger.debug(
                f"⚡ Energía: {len(persons)} organismos procesados, "
                f"{photosynthesis_count} fotosíntesis, "
                f"{starvation_deaths} muertes por inanición"
            )
    
    # =========================================================================
    # FOTOSÍNTESIS
    # =========================================================================
    
    def _is_photosynthetic(self, person: 'Person') -> bool:
        """Verifica si un organismo es fotosintético.
        
        Consulta el rasgo 'diet' del genoma para determinar si el organismo
        puede realizar fotosíntesis.
        
        Args:
            person: El organismo a verificar.
            
        Returns:
            True si el organismo es fotosintético, False en caso contrario.
        """
        try:
            # Consultar el rasgo de dieta del genoma
            diet = person.genome.get_trait_value("diet")
            if diet is not None:
                # PHOTOSYNTHETIC = 0.0 en nuestra escala de dieta
                # Verificar si el valor indica fotosíntesis
                return diet <= 0.1  # Valores muy bajos indican fotosíntesis
            
            # Si no hay rasgo de dieta, verificar por especie
            species = person.species.lower()
            photosynthetic_species = [
                "grass", "tree", "shrub", "flower", "algae",
                "plant", "fern", "moss", "cactus",
            ]
            return any(ps in species for ps in photosynthetic_species)
            
        except (AttributeError, TypeError):
            return False
    
    def _calculate_photosynthesis(
        self,
        person: 'Person',
        state: 'WorldState',
        delta_days: float,
    ) -> float:
        """Calcula la energía generada por fotosíntesis.
        
        La fotosíntesis depende de:
        - Luz solar (estación, hora del día)
        - Agua disponible en el tile
        - Temperatura adecuada
        
        Args:
            person: El organismo fotosintético.
            state: Estado del mundo (para consultar tiles).
            delta_days: Días transcurridos.
            
        Returns:
            Cantidad de energía generada.
        """
        # Energía base por fotosíntesis
        energy = self.photosynthesis_rate * delta_days
        
        # Modificador por luz (simplificado: asumimos luz diurna promedio)
        # En el futuro se puede consultar la hora del día y la estación
        light_factor = self._get_light_factor(person, state)
        energy *= light_factor
        
        # Modificador por agua en el tile
        water_factor = self._get_water_factor(person, state)
        energy *= water_factor
        
        # Modificador por temperatura
        temp_factor = self._get_temperature_factor(person, state)
        energy *= temp_factor
        
        return max(0.0, energy)
    
    def _get_light_factor(self, person: 'Person', state: 'WorldState') -> float:
        """Obtiene el factor de luz basado en la posición del organismo.
        
        Simplificado: asume luz diurna promedio.
        En el futuro se puede consultar la hora del día, estación, nubosidad.
        
        Args:
            person: El organismo.
            state: Estado del mundo.
            
        Returns:
            Factor de luz (0.0 a 1.0).
        """
        # Por defecto: luz plena
        # TODO: Consultar hora del día, estación, nubosidad
        return 0.8  # 80% de luz promedio
    
    def _get_water_factor(self, person: 'Person', state: 'WorldState') -> float:
        """Obtiene el factor de agua basado en el tile del organismo.
        
        Args:
            person: El organismo.
            state: Estado del mundo.
            
        Returns:
            Factor de agua (0.0 a 1.0).
        """
        try:
            tile = state.get_tile_at(int(person.x), int(person.y))
            if tile is not None:
                water = getattr(tile, 'water', 0.5)
                # Las plantas necesitan algo de agua, pero no demasiada
                if water < 0.1:
                    return 0.3  # Muy seco
                elif water > 0.8:
                    return 0.5  # Inundado
                else:
                    return 1.0  # Agua adecuada
        except (AttributeError, TypeError):
            pass
        
        return 0.7  # Por defecto
    
    def _get_temperature_factor(self, person: 'Person', state: 'WorldState') -> float:
        """Obtiene el factor de temperatura basado en el tile del organismo.
        
        Args:
            person: El organismo.
            state: Estado del mundo.
            
        Returns:
            Factor de temperatura (0.0 a 1.0).
        """
        try:
            tile = state.get_tile_at(int(person.x), int(person.y))
            if tile is not None:
                temp = getattr(tile, 'temperature', 0.5)
                # Las plantas funcionan mejor en temperaturas moderadas
                if temp < 0.1:
                    return 0.2  # Muy frío
                elif temp > 0.9:
                    return 0.4  # Muy caliente
                elif 0.3 <= temp <= 0.7:
                    return 1.0  # Temperatura óptima
                else:
                    return 0.7  # Temperatura aceptable
        except (AttributeError, TypeError):
            pass
        
        return 0.7  # Por defecto

        # =========================================================================
    # SINCRONIZACIÓN CON EMOCIONES
    # =========================================================================

    def _sync_energy_with_emotions(self, person: 'Person') -> None:
        """Sincroniza el nivel de energía física con la emoción de energía.
        
        Un organismo con poca energía física se siente débil y desmotivado.
        Un organismo con mucha energía se siente vigoroso.
        
        La sincronización es directa: el ratio de energía (0.0 a 1.0)
        se refleja en la emoción de energía (0.0 a 1.0).
        
        Args:
            person: El organismo a sincronizar.
        """
        # Solo sincronizar si el agente tiene emociones
        emotions = getattr(person, '_emotions', None)
        if emotions is None or not isinstance(emotions, dict):
            return
        
        # Verificar que la emoción "energy" existe
        if "energy" not in emotions:
            return
        
        # Obtener el ratio de energía física (0.0 a 1.0)
        target_energy = person.energy_ratio
        
        # Obtener la emoción actual de energía
        current_emotion = emotions.get("energy", 1.0)
        
        # Calcular la diferencia y actualizar
        # Transición suave: mover un 20% hacia el objetivo cada tick
        # Esto evita cambios bruscos que podrían causar inestabilidad
        delta = (target_energy - current_emotion) * 0.2
        
        # Aplicar el cambio usando el método existente
        if hasattr(person, 'update_emotion'):
            person.update_emotion("energy", delta)
        else:
            # Fallback: actualizar directamente
            emotions["energy"] = max(0.0, min(1.0, current_emotion + delta))
    
    # =========================================================================
    # METABOLISMO
    # =========================================================================
    
    def _calculate_metabolic_cost(
        self,
        person: 'Person',
        delta_days: float,
    ) -> float:
        """Calcula el coste metabólico de un organismo.
        
        El coste metabólico depende de:
        - Tasa metabólica basal (mantenimiento)
        - Tamaño corporal (organismos más grandes gastan más)
        - Estado reproductivo (embarazo aumenta el gasto)
        - Enfermedad (estar enfermo aumenta el gasto)
        
        Args:
            person: El organismo a procesar.
            delta_days: Días transcurridos.
            
        Returns:
            Cantidad de energía a gastar.
        """
        # Coste base
        cost = self.basal_metabolic_rate * delta_days
        
        # Modificador por tamaño corporal (basado en genoma)
        size_factor = self._get_size_factor(person)
        cost *= size_factor
        
        # Modificador por embarazo
        if person.is_pregnant:
            cost *= 1.3  # 30% más de gasto durante el embarazo
        
                # Modificador por enfermedad
        if person.is_sick:
            cost *= 1.2  # 20% más de gasto por enfermedad
        
        # NUEVO: Modificador por estrés alto
        # El estrés crónico aumenta el metabolismo (respuesta de lucha o huida)
        emotions = getattr(person, '_emotions', None)
        if emotions is not None and isinstance(emotions, dict):
            stress = emotions.get("stress", 0.0)
            if stress > 0.7:
                cost *= 1.15  # 15% más de gasto por estrés alto
                
        return cost
    
    def _get_size_factor(self, person: 'Person') -> float:
        """Obtiene el factor de tamaño basado en el genoma.
        
        Los organismos más grandes tienen mayor metabolismo.
        
        Args:
            person: El organismo.
            
        Returns:
            Factor multiplicador (0.5 para pequeños, 2.0 para grandes).
        """
        try:
            body_size = getattr(person.genome, 'body_size', None)
            if body_size is not None:
                return 0.5 + (body_size * 1.5)
        except (AttributeError, TypeError):
            pass
        
        return 1.0  # Por defecto: tamaño medio
    
    # =========================================================================
    # INANICIÓN
    # =========================================================================
    
    def _check_starvation_death(
        self,
        person: 'Person',
        delta_days: float,
    ) -> bool:
        """Verifica si un organismo debe morir por inanición.
        
        La probabilidad de muerte aumenta con los días de inanición:
        - Días 0-30: Riesgo creciente
        - Día 30+: Muerte casi segura
        
        Args:
            person: El organismo a verificar.
            delta_days: Días transcurridos.
            
        Returns:
            True si el organismo debe morir, False en caso contrario.
        """
        starvation_days = person.starvation_days
        
        # Si no está en inanición, no hay riesgo
        if starvation_days <= 0:
            return False
        
        # Calcular probabilidad de muerte basada en días de inanición
        if starvation_days < self.starvation_death_threshold:
            risk_factor = starvation_days / self.starvation_death_threshold
            death_probability = risk_factor * self.starvation_damage_rate * delta_days
        else:
            days_over = starvation_days - self.starvation_death_threshold
            death_probability = 0.5 + (days_over * 0.1)
        
        # Tirada aleatoria
        roll = random.random()
        return roll < death_probability
    
    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================
    
    def get_summary(self) -> Dict[str, int]:
        """Retorna un resumen de las estadísticas del sistema."""
        return {
            "total_energy_processed": self._total_energy_processed,
            "total_starvation_deaths": self._total_starvation_deaths,
            "total_photosynthesis_events": self._total_photosynthesis_events,
        }
    
    def __repr__(self) -> str:
        return (
            f"EnergySystem("
            f"processed={self._total_energy_processed}, "
            f"photosynthesis={self._total_photosynthesis_events}, "
            f"starvation_deaths={self._total_starvation_deaths})"
        )