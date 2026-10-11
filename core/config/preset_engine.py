"""Sistema de presets para configuración bidireccional de la simulación.

Permite al usuario controlar parámetros complejos mediante sliders de alto nivel,
mientras el sistema ajusta automáticamente los parámetros internos del motor
a través del ParameterRegistry (o en memoria si no hay registry).
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from core.config.parameter_registry import ParameterRegistry


@dataclass
class ParameterMapping:
    """Define cómo un parámetro interno se mapea desde/hacia un preset."""
    
    parameter_id: str
    min_value: float
    max_value: float
    default_value: float
    inverse: bool = False
    
    def from_preset_value(self, preset_value: float) -> float:
        normalized = preset_value / 100.0
        if self.inverse:
            return self.max_value - (self.max_value - self.min_value) * normalized
        else:
            return self.min_value + (self.max_value - self.min_value) * normalized
    
    def to_preset_value(self, parameter_value: float) -> float:
        if self.max_value == self.min_value:
            return 0.0
        
        if self.inverse:
            normalized = (self.max_value - parameter_value) / (self.max_value - self.min_value)
        else:
            normalized = (parameter_value - self.min_value) / (self.max_value - self.min_value)
            
        return max(0.0, min(100.0, normalized * 100.0))


@dataclass
class PresetDefinition:
    """Define un preset completo con sus parámetros mapeados."""
    
    name: str
    description: str
    parameters: Dict[str, ParameterMapping] = field(default_factory=dict)
    
    def add_parameter(
        self,
        parameter_id: str,
        min_value: float,
        max_value: float,
        default_value: float,
        inverse: bool = False
    ) -> 'PresetDefinition':
        self.parameters[parameter_id] = ParameterMapping(
            parameter_id=parameter_id,
            min_value=min_value,
            max_value=max_value,
            default_value=default_value,
            inverse=inverse
        )
        return self
    
    def calculate_parameters(self, preset_value: float) -> Dict[str, float]:
        return {
            param_id: mapping.from_preset_value(preset_value)
            for param_id, mapping in self.parameters.items()
        }
    
    def calculate_preset_value(self, current_parameters: Dict[str, float]) -> float:
        if not self.parameters:
            return 0.0
        
        total = 0.0
        for param_id, mapping in self.parameters.items():
            current_value = current_parameters.get(param_id, mapping.default_value)
            preset_value = mapping.to_preset_value(current_value)
            total += preset_value
        
        return total / len(self.parameters)


class PresetEngine:
    """Motor que gestiona los presets y su lógica bidireccional."""
    
    def __init__(self, registry: Optional['ParameterRegistry'] = None):
        self._registry = registry
        self._presets: Dict[str, PresetDefinition] = {}
        self._current_values: Dict[str, float] = {}
        self._current_parameters: Dict[str, float] = {}
    
    def register_preset(self, preset: PresetDefinition) -> None:
        self._presets[preset.name] = preset
        self._current_values[preset.name] = 50.0
        
        if self._registry:
            for param_id, mapping in preset.parameters.items():
                current = self._registry.get(param_id)
                if current is None:
                    self._registry.set(param_id, mapping.default_value)
        else:
            for param_id, mapping in preset.parameters.items():
                if param_id not in self._current_parameters:
                    self._current_parameters[param_id] = mapping.default_value
    
    def get_preset(self, name: str) -> Optional[PresetDefinition]:
        return self._presets.get(name)
    
    def set_preset_value(self, preset_name: str, value: float) -> Dict[str, float]:
        if preset_name not in self._presets:
            raise ValueError(f"Preset '{preset_name}' no encontrado")
        
        value = max(0.0, min(100.0, value))
        self._current_values[preset_name] = value
        
        preset = self._presets[preset_name]
        new_parameters = preset.calculate_parameters(value)
        
        if self._registry:
            for param_id, new_value in new_parameters.items():
                self._registry.set(param_id, new_value)
        else:
            self._current_parameters.update(new_parameters)
        
        return new_parameters
    
    def get_preset_value(self, preset_name: str) -> float:
        if preset_name not in self._presets:
            raise ValueError(f"Preset '{preset_name}' no encontrado")
        
        preset = self._presets[preset_name]
        
        if self._registry:
            current_params = {}
            for param_id in preset.parameters:
                val = self._registry.get(param_id)
                if val is not None:
                    current_params[param_id] = val
            
            if current_params:
                calculated_value = preset.calculate_preset_value(current_params)
                self._current_values[preset_name] = calculated_value
                return calculated_value
        else:
            current_params = {k: v for k, v in self._current_parameters.items() if k in preset.parameters}
            if current_params:
                calculated_value = preset.calculate_preset_value(current_params)
                self._current_values[preset_name] = calculated_value
                return calculated_value
        
        return self._current_values.get(preset_name, 50.0)
    
    def set_parameter(self, parameter_id: str, value: float) -> None:
        if self._registry:
            self._registry.set(parameter_id, value)
        else:
            self._current_parameters[parameter_id] = value
        
        for preset_name, preset in self._presets.items():
            if parameter_id in preset.parameters:
                if self._registry:
                    current_params = {}
                    for param_id in preset.parameters:
                        val = self._registry.get(param_id)
                        if val is not None:
                            current_params[param_id] = val
                else:
                    current_params = {k: v for k, v in self._current_parameters.items() if k in preset.parameters}
                
                if current_params:
                    calculated_value = preset.calculate_preset_value(current_params)
                    self._current_values[preset_name] = calculated_value
    
    def get_parameter(self, parameter_id: str) -> Optional[float]:
        if self._registry:
            return self._registry.get(parameter_id)
        return self._current_parameters.get(parameter_id)
    
    def get_all_parameters(self) -> Dict[str, float]:
        if self._registry:
            all_params = {}
            for preset in self._presets.values():
                for param_id in preset.parameters:
                    val = self._registry.get(param_id)
                    if val is not None:
                        all_params[param_id] = val
            return all_params
        return self._current_parameters.copy()
    
    def get_all_presets(self) -> Dict[str, PresetDefinition]:
        return self._presets.copy()


# ============================================================================
# FUNCIONES DE CREACIÓN DE PRESETS (MAPEADOS A SIMULATIONCONFIG REAL)
# ============================================================================

def create_fertility_preset() -> PresetDefinition:
    return PresetDefinition(
        name="fertilidad",
        description="Controla la facilidad con la que la población crece",
    ).add_parameter(
        parameter_id="reproduction.base_conception_chance",
        min_value=0.01, max_value=0.5, default_value=0.15
    ).add_parameter(
        parameter_id="reproduction.min_fertility_age_days",
        min_value=4000.0, max_value=8000.0, default_value=6570.0, inverse=True
    ).add_parameter(
        parameter_id="reproduction.max_fertility_age_days",
        min_value=14000.0, max_value=20000.0, default_value=16425.0
    )


def create_mortality_preset() -> PresetDefinition:
    return PresetDefinition(
        name="mortalidad",
        description="Controla la vulnerabilidad general ante amenazas",
    ).add_parameter(
        parameter_id="mortality.infant_mortality_rate",
        min_value=0.001, max_value=0.1, default_value=0.02
    ).add_parameter(
        parameter_id="mortality.sickness_penalty_multiplier",
        min_value=1.0, max_value=5.0, default_value=2.5
    ).add_parameter(
        parameter_id="mortality.hard_cap_age_days",
        min_value=30000.0, max_value=50000.0, default_value=41975.0, inverse=True
    )


def create_lifespan_preset() -> PresetDefinition:
    return PresetDefinition(
        name="esperanza_vida",
        description="Controla cuánto tiempo tienden a vivir los agentes",
    ).add_parameter(
        parameter_id="time.senior_age_days",
        min_value=15000.0, max_value=30000.0, default_value=21900.0
    ).add_parameter(
        parameter_id="mortality.base_life_expectancy_days",
        min_value=15000.0, max_value=40000.0, default_value=25550.0
    )


def create_migration_preset() -> PresetDefinition:
    return PresetDefinition(
        name="migracion",
        description="Controla la tendencia a explorar y mudarse a nuevas zonas",
    ).add_parameter(
        parameter_id="free_will.migration_action_threshold",
        min_value=0.5, max_value=0.95, default_value=0.85, inverse=True
    ).add_parameter(
        parameter_id="free_will.migration_chance_multiplier",
        min_value=0.1, max_value=2.0, default_value=0.2
    )


def create_immunity_preset() -> PresetDefinition:
    return PresetDefinition(
        name="inmunidad",
        description="Controla la capacidad de combatir y resistir infecciones",
    ).add_parameter(
        parameter_id="diseases.base_recovery_chance",
        min_value=0.05, max_value=0.5, default_value=0.15
    ).add_parameter(
        parameter_id="diseases.immunity_clamping",
        min_value=0.01, max_value=0.5, default_value=0.1
    )


def create_recovery_preset() -> PresetDefinition:
    return PresetDefinition(
        name="recuperacion",
        description="Controla la rapidez con la que los agentes sanan de enfermedades",
    ).add_parameter(
        parameter_id="diseases.base_recovery_chance",
        min_value=0.05, max_value=0.5, default_value=0.15
    ).add_parameter(
        parameter_id="aging.sickness_aging_factor",
        min_value=0.1, max_value=0.8, default_value=0.3, inverse=True
    )


def create_crowding_preset() -> PresetDefinition:
    return PresetDefinition(
        name="hacinamiento",
        description="Controla la tolerancia a la densidad de población",
    ).add_parameter(
        parameter_id="environment.max_agents_per_sector",
        min_value=2.0, max_value=20.0, default_value=8.0
    ).add_parameter(
        parameter_id="environment.carrying_capacity",
        min_value=50.0, max_value=500.0, default_value=200.0
    )


def create_sociability_preset() -> PresetDefinition:
    return PresetDefinition(
        name="sociabilidad",
        description="Controla la tendencia a buscar interacción y vínculos",
    ).add_parameter(
        parameter_id="free_will.sociability_weight",
        min_value=0.0, max_value=1.0, default_value=0.3
    ).add_parameter(
        parameter_id="relationships.affinity_weight",
        min_value=0.1, max_value=1.0, default_value=0.60
    )


def create_aggression_preset() -> PresetDefinition:
    return PresetDefinition(
        name="agresividad",
        description="Controla la tendencia al conflicto y la rebeldía",
    ).add_parameter(
        parameter_id="free_will.aggressiveness_weight",
        min_value=0.0, max_value=1.0, default_value=0.3
    ).add_parameter(
        parameter_id="free_will.rebellion_action_threshold",
        min_value=0.5, max_value=0.95, default_value=0.8, inverse=True
    )


def create_cooperation_preset() -> PresetDefinition:
    return PresetDefinition(
        name="cooperacion",
        description="Controla la tendencia a priorizar el bienestar del grupo",
    ).add_parameter(
        parameter_id="free_will.cooperation_action_threshold",
        min_value=0.3, max_value=0.9, default_value=0.6, inverse=True
    ).add_parameter(
        parameter_id="adoptions.motivation_cooperation_weight",
        min_value=0.0, max_value=50.0, default_value=15.0
    )


def create_curiosity_preset() -> PresetDefinition:
    return PresetDefinition(
        name="curiosidad",
        description="Controla la tendencia a explorar lo desconocido",
    ).add_parameter(
        parameter_id="free_will.curiosity_weight",
        min_value=0.0, max_value=1.0, default_value=0.4
    ).add_parameter(
        parameter_id="free_will.exploration_action_threshold",
        min_value=0.4, max_value=0.95, default_value=0.7, inverse=True
    )


def create_emotional_stability_preset() -> PresetDefinition:
    return PresetDefinition(
        name="estabilidad_emocional",
        description="Controla la resistencia al trauma y la plasticidad del carácter",
    ).add_parameter(
        parameter_id="cognition.max_trauma_cap",
        min_value=0.2, max_value=1.0, default_value=1.0, inverse=True
    ).add_parameter(
        parameter_id="parental_influence.base_personality_plasticity",
        min_value=0.01, max_value=0.2, default_value=0.05, inverse=True
    )


def create_mutation_rate_preset() -> PresetDefinition:
    return PresetDefinition(
        name="tasa_mutacion",
        description="Controla la frecuencia de nuevas variaciones genéticas",
    ).add_parameter(
        parameter_id="mutation.probability",
        min_value=0.0, max_value=0.2, default_value=0.05
    ).add_parameter(
        parameter_id="reproduction.mutation_factor",
        min_value=0.0, max_value=0.2, default_value=0.05
    )


def register_all_presets(engine: PresetEngine) -> None:
    """Registra los 13 presets principales en el motor."""
    engine.register_preset(create_fertility_preset())
    engine.register_preset(create_mortality_preset())
    engine.register_preset(create_lifespan_preset())
    engine.register_preset(create_migration_preset())
    engine.register_preset(create_immunity_preset())
    engine.register_preset(create_recovery_preset())
    engine.register_preset(create_crowding_preset())
    engine.register_preset(create_sociability_preset())
    engine.register_preset(create_aggression_preset())
    engine.register_preset(create_cooperation_preset())
    engine.register_preset(create_curiosity_preset())
    engine.register_preset(create_emotional_stability_preset())
    engine.register_preset(create_mutation_rate_preset())