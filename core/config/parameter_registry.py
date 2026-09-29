"""Registry de parámetros con validación, metadata e historial.

Responsabilidad:
Envolver SimulationConfig añadiendo:
- Validación de tipos y rangos [min, max]
- Metadata descriptiva (descripciones, categorías)
- Auto-descubrimiento de parámetros
- Historial de cambios
- Listado filtrado por categoría

Filosofía:
No reemplaza SimulationConfig, la potencia. Todos los sistemas siguen
leyendo self.config.X.Y directamente; el registry solo añade validación
cuando se modifica un parámetro desde la GUI, triggers o mods.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from core.config.simulation_config import SimulationConfig


@dataclass
class ParameterSpec:
    """Especificación de un parámetro validable.
    
    Attributes:
        path: Ruta completa (ej: "diseases.transmission_factor")
        category: Categoría (ej: "diseases")
        description: Descripción legible
        value_type: Tipo esperado (int, float, bool)
        min_value: Valor mínimo permitido (None = sin límite)
        max_value: Valor máximo permitido (None = sin límite)
        default_value: Valor por defecto
    """
    path: str
    category: str
    description: str
    value_type: Type
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Any = None


class ParameterRegistry:
    """Registry validado sobre SimulationConfig.
    
    Uso:
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        
        # Auto-descubrir todos los parámetros de una categoría
        registry.auto_discover("diseases")
        
        # Registrar un parámetro específico con rango
        registry.register("diseases.transmission_factor", ParameterSpec(
            path="diseases.transmission_factor",
            category="diseases",
            description="Factor de transmisión de enfermedades",
            value_type=float,
            min_value=0.0,
            max_value=1.0,
            default_value=0.3
        ))
        
        # Modificar con validación
        registry.set("diseases.transmission_factor", 0.5)  # ✅ OK
        registry.set("diseases.transmission_factor", 2.0)  # ❌ Rechazado
        
        # Consultar historial
        print(registry.history)
    """
    
    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el registry sobre una configuración existente.
        
        Args:
            config: La configuración maestra de la simulación.
        """
        self.config = config
        self.specs: Dict[str, ParameterSpec] = {}
        self.history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("ParameterRegistry")
    
    def register(self, spec: ParameterSpec) -> None:
        """Registra un parámetro con su metadata de validación.
        
        Args:
            spec: Especificación completa del parámetro.
        """
        self.specs[spec.path] = spec
    
    def auto_discover(self, category: str) -> int:
        """Auto-descubre todos los parámetros numéricos y booleanos de una categoría.
        
        Args:
            category: Nombre de la categoría (ej: "diseases", "reproduction")
            
        Returns:
            Número de parámetros descubiertos y registrados.
        """
        target = getattr(self.config, category, None)
        if target is None:
            self.logger.warning(f"Categoría '{category}' no existe en SimulationConfig")
            return 0
        
        discovered = 0
        for attr_name in dir(target):
            if attr_name.startswith('_'):
                continue
            
            value = getattr(target, attr_name, None)
            if callable(value):
                continue
            
            # Solo registrar tipos primitivos
            if not isinstance(value, (int, float, bool)):
                continue
            
            path = f"{category}.{attr_name}"
            
            # No sobreescribir specs ya registradas manualmente
            if path in self.specs:
                continue
            
            # Inferir spec del valor actual
            spec = ParameterSpec(
                path=path,
                category=category,
                description=f"{category}.{attr_name}",
                value_type=type(value),
                min_value=None,
                max_value=None,
                default_value=value
            )
            self.specs[path] = spec
            discovered += 1
        
        self.logger.info(f"Auto-descubiertos {discovered} parámetros en '{category}'")
        return discovered
    
    def set(self, path: str, value: Any) -> bool:
        """Establece un parámetro con validación de tipo y rango.
        
        Args:
            path: Ruta del parámetro (ej: "diseases.transmission_factor")
            value: Nuevo valor
            
        Returns:
            True si se aplicó correctamente, False si falló la validación.
        """
        # Validar formato del path
        if '.' not in path:
            self.logger.error(f"Path inválido '{path}': debe ser 'category.key'")
            return False
        
        category, key = path.split('.', 1)
        
        # Validación si hay spec registrado
        if path in self.specs:
            spec = self.specs[path]
            
            # Validar tipo
            if not isinstance(value, spec.value_type):
                self.logger.warning(
                    f"Tipo incorrecto para {path}: esperado {spec.value_type.__name__}, "
                    f"recibido {type(value).__name__}"
                )
                return False
            
            # Validar rango mínimo
            if spec.min_value is not None and value < spec.min_value:
                self.logger.warning(
                    f"Valor {value} fuera de rango para {path}: "
                    f"mínimo {spec.min_value}"
                )
                return False
            
            # Validar rango máximo
            if spec.max_value is not None and value > spec.max_value:
                self.logger.warning(
                    f"Valor {value} fuera de rango para {path}: "
                    f"máximo {spec.max_value}"
                )
                return False
        
        # Delegar a SimulationConfig
        success = self.config.set_parameter(category, key, value)
        
        if success:
            self.history.append({
                'path': path,
                'value': value,
                'timestamp': datetime.now().isoformat()
            })
        
        return success
    
    def get(self, path: str, default: Any = None) -> Any:
        """Lee un parámetro de forma segura.
        
        Args:
            path: Ruta del parámetro (ej: "diseases.transmission_factor")
            default: Valor por defecto si no existe
            
        Returns:
            El valor actual del parámetro, o default si no existe.
        """
        if '.' not in path:
            return default
        
        category, key = path.split('.', 1)
        return self.config.get_parameter(category, key, default)
    
    def reset(self, path: str) -> bool:
        """Resetea un parámetro a su valor por defecto.
        
        Args:
            path: Ruta del parámetro
            
        Returns:
            True si se reseteó correctamente, False si no hay default registrado.
        """
        if path not in self.specs:
            return False
        
        spec = self.specs[path]
        return self.set(path, spec.default_value)
    
    def reset_all(self) -> int:
        """Resetea todos los parámetros registrados a sus valores por defecto.
        
        Returns:
            Número de parámetros reseteados.
        """
        reset_count = 0
        for path, spec in self.specs.items():
            if self.set(path, spec.default_value):
                reset_count += 1
        return reset_count
    
    def list_parameters(self, category: Optional[str] = None) -> List[str]:
        """Lista todos los parámetros registrados, opcionalmente filtrados por categoría.
        
        Args:
            category: Si se especifica, solo devuelve parámetros de esa categoría.
            
        Returns:
            Lista de paths de parámetros.
        """
        if category is None:
            return list(self.specs.keys())
        
        return [path for path in self.specs if path.startswith(f"{category}.")]
    
    def get_spec(self, path: str) -> Optional[ParameterSpec]:
        """Obtiene la especificación de un parámetro.
        
        Args:
            path: Ruta del parámetro
            
        Returns:
            La ParameterSpec si existe, None si no.
        """
        return self.specs.get(path)