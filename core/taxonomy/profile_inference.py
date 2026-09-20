"""Inferencia de perfiles biológicos desde rasgos genéticos.

El sistema infiere el perfil de una especie basándose en sus rasgos
genéticos. Esto mantiene la coherencia con el núcleo genético:
las capacidades salen de la genética, no de reglas fijas.

Filosofía: "Inferimos patrones típicos, no imponemos restricciones."
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.taxonomy.profile_enums import (
    DietType,
    ReproductionType,
    DevelopmentType,
    HabitatType,
    LocomotionType,
    SocialStructureType,
    ThermoregulationType,
    BodySizeCategory,
    ActivityPattern,
)
from core.taxonomy.species_profile import SpeciesProfile

if TYPE_CHECKING:
    from core.genetics.species_definition import SpeciesDefinition


class ProfileInference:
    """Infiere el perfil biológico de una especie desde sus rasgos genéticos."""
    
    def infer(self, species: SpeciesDefinition) -> SpeciesProfile:
        """Infiere el perfil biológico de una especie.
        
        Args:
            species: La definición de especie con sus rasgos.
            
        Returns:
            SpeciesProfile inferido.
        """
        diet = self._infer_diet(species)
        habitat = self._infer_habitat(species)
        locomotion = self._infer_locomotion(species)
        social = self._infer_social_structure(species)
        thermoregulation = self._infer_thermoregulation(species)
        body_size = self._infer_body_size(species)
        reproduction, development = self._infer_reproduction(species)
        activity = self._infer_activity_pattern(species)
        
        return SpeciesProfile(
            taxonomy_id=species.species_id,
            body_size_category=body_size,
            thermoregulation=thermoregulation,
            diet=diet,
            reproduction=reproduction,
            development=development,
            habitat=habitat,
            locomotion=locomotion,
            social_structure=social,
            activity_pattern=activity,
            notes="Perfil inferido desde rasgos genéticos",
        )
    
    def _is_microorganism(self, species: SpeciesDefinition) -> bool:
        """Verifica si es un microorganismo (bacteria, protista)."""
        division_speed = self._get_trait(species, "division_speed")
        return division_speed > 0.5
    
    def _is_fungus_or_plant(self, species: SpeciesDefinition) -> bool:
        """Verifica si es hongo o planta (organismos sésiles)."""
        photosynthesis = self._get_trait(species, "photosynthesis")
        symbiosis = self._get_trait(species, "symbiosis")
        return photosynthesis > 0.5 or symbiosis > 1.0
    
    def _infer_diet(self, species: SpeciesDefinition) -> DietType:
        """Infiere el tipo de dieta desde rasgos genéticos."""
        photosynthesis = self._get_trait(species, "photosynthesis")
        heterotrophy = self._get_trait(species, "heterotrophy")
        symbiosis = self._get_trait(species, "symbiosis")
        division_speed = self._get_trait(species, "division_speed")
    
        # Fotosintético (plantas, algas)
        if photosynthesis > 1.0:
            return DietType.PHOTOSYNTHETIC
    
        # Detritívoro (hongos, descomponedores)
        if symbiosis > 1.0 and heterotrophy > 1.0:
            return DietType.DETRITIVORE
    
        # Bacterias: quimiosintéticas o heterótrofas
        if division_speed > 0.5:
            return DietType.CHEMOSYNTHETIC
    
        # Herbívoro, carnívoro u omnívoro según dieta
        diet_value = self._get_trait(species, "diet", default=1.0)
    
        if diet_value < 0.5:
            return DietType.HERBIVORE
        elif diet_value >= 1.5:            # ← CAMBIO: >= en lugar de >
            return DietType.CARNIVORE
        else:
            return DietType.OMNIVORE
    
    def _infer_habitat(self, species: SpeciesDefinition) -> HabitatType:
        """Infiere el hábitat principal desde rasgos genéticos."""
        swimming = self._get_trait(species, "swimming")
        flight = self._get_trait(species, "flight")
        burrowing = self._get_trait(species, "burrowing")
        
        # Microorganismos: terrestres por defecto
        if self._is_microorganism(species):
            return HabitatType.TERRESTRIAL
        
        # Hongos y plantas: terrestres por defecto
        if self._is_fungus_or_plant(species):
            return HabitatType.TERRESTRIAL
        
        # Anfibios: vida dual (nadan y tienen healing alto)
        healing = self._get_trait(species, "healing")
        if swimming > 0.8 and healing > 1.0:
            return HabitatType.AMPHIBIOUS
        
        # Acuático si nada mucho
        if swimming > 1.0:
            return HabitatType.AQUATIC
        
        # Aéreo si vuela mucho
        if flight > 1.0:
            return HabitatType.AERIAL
        
        # Subterráneo si excava mucho
        if burrowing > 1.0:
            return HabitatType.SUBTERRANEAN
        
        # Terrestre por defecto
        return HabitatType.TERRESTRIAL
    
    def _infer_locomotion(self, species: SpeciesDefinition) -> LocomotionType:
        """Infiere la locomoción principal desde rasgos genéticos."""
        mobility = self._get_trait(species, "mobility", default=1.0)
        flight = self._get_trait(species, "flight")
        swimming = self._get_trait(species, "swimming")
        burrowing = self._get_trait(species, "burrowing")
        climbing = self._get_trait(species, "climbing")
        speed = self._get_trait(species, "speed")
        
        # Hongos y plantas: sésiles
        if self._is_fungus_or_plant(species):
            return LocomotionType.SESSILE
        
        # Microorganismos: derivan con corrientes
        if self._is_microorganism(species):
            return LocomotionType.DRIFTING
        
        # Sésil si no se mueve
        if mobility < 0.2:
            return LocomotionType.SESSILE
        
        # Vuelo si tiene flight alto
        if flight > 1.0:
            return LocomotionType.FLYING
        
        # Natación si tiene swimming alto
        if swimming > 1.0:
            return LocomotionType.SWIMMING
        
        # Excavación si tiene burrowing alto
        if burrowing > 1.0:
            return LocomotionType.BURROWING
        
        # Escalada si tiene climbing alto
        if climbing > 1.0:
            return LocomotionType.CLIMBING
        
        # Corredor si tiene speed alto
        if speed > 1.2:
            return LocomotionType.RUNNING
        
        # Caminante por defecto
        return LocomotionType.WALKING
    
    def _infer_social_structure(self, species: SpeciesDefinition) -> SocialStructureType:
        """Infiere la estructura social desde rasgos genéticos."""
        sociability = self._get_trait(species, "sociability")
        cooperation = self._get_trait(species, "cooperation")
        territoriality = self._get_trait(species, "territoriality")
        pack_behavior = self._get_trait(species, "pack_behavior", default=0.0)
        
        # Microorganismos: colonia
        if self._is_microorganism(species):
            return SocialStructureType.COLONY
        
        # Colonia si tiene sociabilidad extrema (insectos sociales)
        if sociability > 1.5 and cooperation > 1.2:
            return SocialStructureType.COLONY
        
        # Manada cazadora si tiene pack_behavior alto
        if pack_behavior > 1.0:
            return SocialStructureType.PACK
        
        # Manada herbívora si es social pero no cazador
        if sociability > 1.0:
            return SocialStructureType.HERD
        
        # Pareja si es moderadamente social y territorial
        if sociability > 0.7 and territoriality > 0.8:
            return SocialStructureType.PAIR
        
        # Solitario por defecto
        return SocialStructureType.SOLITARY
    
    def _infer_thermoregulation(self, species: SpeciesDefinition) -> ThermoregulationType:
        """Infiere la termorregulación desde rasgos genéticos.
        
        Lógica mejorada:
        - Hongos, plantas, bacterias: no tienen termorregulación (poikilotherm)
        - Mamíferos y aves: homeotermos (metabolismo alto + sistema nervioso complejo)
        - Reptiles, anfibios, peces: poikilotermos (metabolismo bajo)
        - Insectos: poikilotermos (metabolismo alto por tamaño, no por termorregulación)
        """
        # Hongos, plantas y microorganismos no tienen termorregulación
        if self._is_fungus_or_plant(species) or self._is_microorganism(species):
            return ThermoregulationType.POIKILOTHERM
        
        metabolism = self._get_trait(species, "metabolism")
        nervous_system = self._get_trait(species, "nervous_system")
        flight = self._get_trait(species, "flight")
        
        # Mamíferos y aves son homeotermos
        # Identificación: sistema nervioso complejo + metabolismo alto
        # Nota: Los insectos tienen metabolismo alto pero nervous_system bajo
        if nervous_system > 0.8 and metabolism > 1.0:
            return ThermoregulationType.HOMEOTHERM
        
        # Aves también son homeotermos (identificación por flight)
        if flight > 0.5 and nervous_system > 0.5:
            return ThermoregulationType.HOMEOTHERM
        
        # Reptiles, anfibios, peces, insectos: poikilotermos
        return ThermoregulationType.POIKILOTHERM
    
    def _infer_body_size(self, species: SpeciesDefinition) -> BodySizeCategory:
        """Infiere el tamaño corporal desde rasgos genéticos."""
        # Microorganismos
        if self._is_microorganism(species):
            return BodySizeCategory.MICROSCOPIC
        
        # Hongos y plantas: usar growth_rate como proxy
        if self._is_fungus_or_plant(species):
            growth_rate = self._get_trait(species, "growth_rate")
            if growth_rate > 1.5:
                return BodySizeCategory.MEDIUM
            return BodySizeCategory.SMALL
        
        # Usar tamaño si existe
        size_value = self._get_trait(species, "body_size", default=1.0)
        
        if size_value < 0.3:
            return BodySizeCategory.MICROSCOPIC
        elif size_value < 0.7:
            return BodySizeCategory.SMALL
        elif size_value < 1.3:
            return BodySizeCategory.MEDIUM
        elif size_value < 1.8:
            return BodySizeCategory.LARGE
        else:
            return BodySizeCategory.GIANT
    
    def _infer_reproduction(self, species: SpeciesDefinition) -> tuple:
        """Infiere el tipo de reproducción y desarrollo."""
        division_speed = self._get_trait(species, "division_speed")
        photosynthesis = self._get_trait(species, "photosynthesis")
        symbiosis = self._get_trait(species, "symbiosis")
        swimming = self._get_trait(species, "swimming")
        
        # Bacterias: fisión binaria
        if division_speed > 0.5:
            return ReproductionType.ASEXUAL, DevelopmentType.BINARY_FISSION
        
        # Plantas y hongos: esporas
        if photosynthesis > 0.5 or symbiosis > 1.0:
            return ReproductionType.BOTH, DevelopmentType.SPORES
        
        # Peces y anfibios: ovíparos
        if swimming > 0.8:
            return ReproductionType.SEXUAL, DevelopmentType.OVIPAROUS
        
        # Mamíferos y aves: vivíparos u ovíparos según vuelo
        flight = self._get_trait(species, "flight")
        if flight > 0.5:
            return ReproductionType.SEXUAL, DevelopmentType.OVIPAROUS
        
        # Mamíferos: vivíparos
        return ReproductionType.SEXUAL, DevelopmentType.VIVIPAROUS
    
    def _infer_activity_pattern(self, species: SpeciesDefinition) -> ActivityPattern:
        """Infiere el patrón de actividad desde rasgos genéticos."""
        night_vision = self._get_trait(species, "night_vision")
        
        # Nocturno si tiene visión nocturna alta
        if night_vision > 1.0:
            return ActivityPattern.NOCTURNAL
        
        # Microorganismos y hongos: actividad continua
        if self._is_microorganism(species) or self._is_fungus_or_plant(species):
            return ActivityPattern.CONTINUOUS
        
        # Diurno por defecto
        return ActivityPattern.DIURNAL
    
    def _get_trait(self, species: SpeciesDefinition, trait_id: str, default: float = 0.0) -> float:
        """Obtiene el valor de un rasgo de la especie."""
        config = species.get_trait_config(trait_id)
        if config is not None:
            return config.default_value
        return default