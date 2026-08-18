"""Sistema de Validación Biológica.

FILOSOFÍA: El Validador Biológico es el ÚNICO lugar donde existe
el conocimiento biológico del sistema.

Los rasgos son completamente neutros (no saben qué es un mamífero).
Las plantillas son declarativas (solo dicen qué rasgos activar).
El Validador conoce las reglas de coherencia biológica.

IMPORTANTE: Este sistema NO impide configuraciones. Solo informa.
El usuario decide si continúa con una configuración advertida.

El validador utiliza un sistema de reglas declarativas:
- Incompatibilidades: rasgos que no suelen coexistir
- Dependencias: rasgos que requieren otros rasgos
- Coherencias: combinaciones que refuerzan realismo
- Contradicciones: combinaciones biológicamente imposibles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import logging

from core.genetics.trait import TraitCategory
from core.genetics.trait_library import TraitLibrary
from core.genetics.species_definition import SpeciesDefinition


class ValidationSeverity(Enum):
    """Nivel de severidad de una advertencia."""
    INFO = auto()       # Información: combinación interesante o curiosa
    WARNING = auto()    # Advertencia: combinación inusual pero posible
    ERROR = auto()      # Error: combinación biológicamente contradictoria


@dataclass
class ValidationMessage:
    """Un mensaje de validación individual."""
    severity: ValidationSeverity
    message: str
    trait_ids: List[str] = field(default_factory=list)
    rule_id: str = ""


# =============================================================================
# DEFINICIONES DE REGLAS BIOLÓGICAS
# =============================================================================

@dataclass(frozen=True)
class IncompatibilityRule:
    """Dos rasgos que raramente coexisten en la naturaleza."""
    trait_a: str
    trait_b: str
    severity: ValidationSeverity
    message: str


@dataclass(frozen=True)
class DependencyRule:
    """Un rasgo que requiere otro rasgo para ser coherente."""
    trait: str
    requires: str
    severity: ValidationSeverity
    message: str


@dataclass(frozen=True)
class CategoryRule:
    """Una regla sobre la coherencia de categorías de rasgos."""
    required_category: TraitCategory
    forbidden_category: Optional[TraitCategory]
    min_traits: int
    severity: ValidationSeverity
    message: str


# =============================================================================
# BASE DE DATOS DE REGLAS BIOLÓGICAS
# =============================================================================
# Aquí es donde vive todo el conocimiento biológico del sistema.
# Para añadir una nueva regla, solo añade una línea aquí.

INCOMPATIBILITY_RULES: List[IncompatibilityRule] = [
    # Vuelo y natación son posibles (patos, cormoranes) pero inusuales
    IncompatibilityRule(
        trait_a="flight",
        trait_b="swimming",
        severity=ValidationSeverity.WARNING,
        message="Vuelo y natación avanzada son inusuales juntos. Existen casos (patos, cormoranes) pero requieren adaptaciones especiales.",
    ),
    
    # Fotosíntesis y heterotrofía son contradictorios
    IncompatibilityRule(
        trait_a="photosynthesis",
        trait_b="heterotrophy",
        severity=ValidationSeverity.ERROR,
        message="Fotosíntesis y heterotrofía son estrategias energéticas contradictorias. Los organismos suelen tener una u otra.",
    ),
    
    # Veneno alto y empatía alta son contradictorios
    IncompatibilityRule(
        trait_a="venom",
        trait_b="empathy",
        severity=ValidationSeverity.WARNING,
        message="Veneno y empatía alta son inusuales. Los organismos venenosos suelen ser solitarios.",
    ),
    
    # Visión nocturna y ecolocalización son redundantes
    IncompatibilityRule(
        trait_a="night_vision",
        trait_b="echolocation",
        severity=ValidationSeverity.INFO,
        message="Visión nocturna y ecolocalización son sistemas sensoriales redundantes. Es raro que un organismo use ambos al máximo.",
    ),
    
    # Longevidad extrema y fertilidad alta son inversamente proporcionales
    IncompatibilityRule(
        trait_a="longevity",
        trait_b="fertility",
        severity=ValidationSeverity.INFO,
        message="Longevidad y alta fertilidad suelen ser inversamente proporcionales en la naturaleza (trade-off biológico).",
    ),
    
    # Velocidad extrema y metabolismo bajo son contradictorios
    IncompatibilityRule(
        trait_a="speed",
        trait_b="metabolism",
        severity=ValidationSeverity.WARNING,
        message="Alta velocidad requiere metabolismo alto. Un metabolismo bajo no puede sostener movimientos rápidos.",
    ),
]


DEPENDENCY_RULES: List[DependencyRule] = [
    # Empatía requiere sistema nervioso complejo
    DependencyRule(
        trait="empathy",
        requires="nervous_system",
        severity=ValidationSeverity.ERROR,
        message="La empatía requiere un sistema nervioso complejo. No puede existir sin él.",
    ),
    
    # Inteligencia requiere sistema nervioso
    DependencyRule(
        trait="intelligence",
        requires="nervous_system",
        severity=ValidationSeverity.ERROR,
        message="La inteligencia requiere un sistema nervioso. No puede existir sin él.",
    ),
    
    # Ecolocalización requiere audición
    DependencyRule(
        trait="echolocation",
        requires="hearing",
        severity=ValidationSeverity.ERROR,
        message="La ecolocalización requiere audición. No puede existir sin un sistema auditivo.",
    ),
    
    # Cooperación alta requiere sociabilidad
    DependencyRule(
        trait="cooperation",
        requires="sociability",
        severity=ValidationSeverity.WARNING,
        message="Alta cooperación suele requerir sociabilidad. Es inusual cooperar sin ser social.",
    ),
    
    # Obediencia alta requiere cierto nivel de inteligencia
    DependencyRule(
        trait="obedience",
        requires="intelligence",
        severity=ValidationSeverity.WARNING,
        message="La obediencia requiere cierta capacidad cognitiva para comprender normas.",
    ),
    
    # Vuelo requiere cierto nivel de metabolismo
    DependencyRule(
        trait="flight",
        requires="metabolism",
        severity=ValidationSeverity.WARNING,
        message="El vuelo requiere un metabolismo alto. Es energéticamente muy costoso.",
    ),
    
    # Veneno requiere metabolismo
    DependencyRule(
        trait="venom",
        requires="metabolism",
        severity=ValidationSeverity.INFO,
        message="Producir veneno requiere energía metabólica.",
    ),
]


# Reglas de categorías (qué categorías suelen ir juntas)
CATEGORY_RULES: List[CategoryRule] = [
    # Si tiene rasgos especiales, debería tener biología básica
    CategoryRule(
        required_category=TraitCategory.BIOLOGY,
        forbidden_category=None,
        min_traits=1,
        severity=ValidationSeverity.INFO,
        message="La especie tiene rasgos especiales pero carece de rasgos biológicos fundamentales.",
    ),
]


# =============================================================================
# CLASE PRINCIPAL: VALIDADOR BIOLÓGICO
# =============================================================================

class BiologicalValidator:
    """Valida la coherencia biológica de una definición de especie.
    
    IMPORTANTE: Este sistema NO impide configuraciones. Solo informa.
    El usuario decide si continúa con una configuración advertida.
    
    Uso:
        validator = BiologicalValidator()
        result = validator.validate_species(species)
        
        for msg in result.messages:
            print(f"[{msg.severity.name}] {msg.message}")
    """
    
    _logger = logging.getLogger("BiologicalValidator")
    
    def __init__(self, library: Optional[TraitLibrary] = None) -> None:
        self._library = library or TraitLibrary.get_default()
    
    def validate_species(self, species: SpeciesDefinition) -> ValidationResult:
        """Valida la coherencia biológica de una especie.
        
        Args:
            species: La especie a validar.
            
        Returns:
            ValidationResult con todas las advertencias y errores encontrados.
        """
        result = ValidationResult(species_id=species.species_id)
        
        # Aplicar todas las reglas
        self._check_incompatibilities(species, result)
        self._check_dependencies(species, result)
        self._check_categories(species, result)
        self._check_trait_values(species, result)
        self._check_minimum_traits(species, result)
        
        return result
    
    def _check_incompatibilities(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> None:
        """Verifica incompatibilidades entre rasgos."""
        trait_ids = species.get_all_trait_ids()
        
        for rule in INCOMPATIBILITY_RULES:
            if rule.trait_a in trait_ids and rule.trait_b in trait_ids:
                # Verificar si ambos tienen valores significativos
                config_a = species.get_trait_config(rule.trait_a)
                config_b = species.get_trait_config(rule.trait_b)
                
                value_a = config_a.default_value if config_a else 0.0
                value_b = config_b.default_value if config_b else 0.0
                
                # Solo reportar si ambos tienen valores relevantes
                if value_a > 0.3 and value_b > 0.3:
                    result.messages.append(ValidationMessage(
                        severity=rule.severity,
                        message=rule.message,
                        trait_ids=[rule.trait_a, rule.trait_b],
                        rule_id=f"incompat_{rule.trait_a}_{rule.trait_b}",
                    ))
    
    def _check_dependencies(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> None:
        """Verifica que los rasgos dependientes tengan sus prerrequisitos."""
        trait_ids = species.get_all_trait_ids()
        
        for rule in DEPENDENCY_RULES:
            if rule.trait in trait_ids and rule.requires not in trait_ids:
                config = species.get_trait_config(rule.trait)
                value = config.default_value if config else 0.0
                
                # Solo reportar si el rasgo tiene valor significativo
                if value > 0.3:
                    result.messages.append(ValidationMessage(
                        severity=rule.severity,
                        message=rule.message,
                        trait_ids=[rule.trait],
                        rule_id=f"dep_{rule.trait}_needs_{rule.requires}",
                    ))
    
    def _check_categories(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> None:
        """Verifica coherencia entre categorías de rasgos."""
        trait_ids = species.get_all_trait_ids()
        categories: Dict[TraitCategory, int] = {}
        
        for trait_id in trait_ids:
            trait = self._library.get_trait(trait_id)
            if trait:
                categories[trait.category] = categories.get(trait.category, 0) + 1
        
        # Si tiene rasgos especiales, verificar que tenga biología
        if TraitCategory.SPECIAL in categories:
            if TraitCategory.BIOLOGY not in categories:
                result.messages.append(ValidationMessage(
                    severity=ValidationSeverity.INFO,
                    message="La especie tiene rasgos especiales pero carece de rasgos biológicos fundamentales.",
                    rule_id="special_without_biology",
                ))
    
    def _check_trait_values(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> None:
        """Verifica que los valores de los rasgos estén en rangos razonables."""
        for trait_id in species.get_all_trait_ids():
            config = species.get_trait_config(trait_id)
            trait = self._library.get_trait(trait_id)
            
            if config is None or trait is None:
                continue
            
            # Verificar rango
            if config.default_value < trait.min_value or config.default_value > trait.max_value:
                result.messages.append(ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    message=f"El valor por defecto de '{trait.name}' ({config.default_value}) "
                            f"está fuera del rango [{trait.min_value}, {trait.max_value}].",
                    trait_ids=[trait_id],
                    rule_id=f"range_{trait_id}",
                ))
    
    def _check_minimum_traits(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> None:
        """Verifica que la especie tenga al menos algunos rasgos básicos."""
        trait_count = species.get_trait_count()
        
        if trait_count == 0:
            result.messages.append(ValidationMessage(
                severity=ValidationSeverity.WARNING,
                message="La especie no tiene ningún rasgo. Puede ser válido para pruebas "
                        "pero no para simulación real.",
                rule_id="no_traits",
            ))
        elif trait_count < 3:
            result.messages.append(ValidationMessage(
                severity=ValidationSeverity.INFO,
                message=f"La especie tiene muy pocos rasgos ({trait_count}). "
                        "Puede que el comportamiento sea muy limitado.",
                rule_id="few_traits",
            ))


# =============================================================================
# RESULTADO DE LA VALIDACIÓN
# =============================================================================

@dataclass
class ValidationResult:
    """Resultado completo de la validación de una especie."""
    species_id: str
    messages: List[ValidationMessage] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Verifica si no hay errores (las advertencias no invalidan)."""
        return not any(m.severity == ValidationSeverity.ERROR for m in self.messages)
    
    @property
    def warnings(self) -> List[ValidationMessage]:
        """Retorna solo las advertencias."""
        return [m for m in self.messages if m.severity == ValidationSeverity.WARNING]
    
    @property
    def errors(self) -> List[ValidationMessage]:
        """Retorna solo los errores."""
        return [m for m in self.messages if m.severity == ValidationSeverity.ERROR]
    
    @property
    def info(self) -> List[ValidationMessage]:
        """Retorna solo la información."""
        return [m for m in self.messages if m.severity == ValidationSeverity.INFO]
    
    @property
    def score(self) -> float:
        """Calcula un score de coherencia (0.0 a 1.0)."""
        if not self.messages:
            return 1.0
        
        penalty = 0.0
        for msg in self.messages:
            if msg.severity == ValidationSeverity.ERROR:
                penalty += 0.25
            elif msg.severity == ValidationSeverity.WARNING:
                penalty += 0.10
            else:
                penalty += 0.02
        
        return max(0.0, 1.0 - penalty)
    
    def format_report(self) -> str:
        """Genera un reporte legible de la validación."""
        lines = []
        lines.append(f"Validación de especie: {self.species_id}")
        lines.append("=" * 60)
        
        if not self.messages:
            lines.append("✅ Sin advertencias. Especie biológicamente coherente.")
        else:
            for msg in self.messages:
                severity_symbol = {
                    ValidationSeverity.INFO: "ℹ️",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.ERROR: "❌",
                }[msg.severity]
                
                lines.append(f"{severity_symbol} [{msg.severity.name}] {msg.message}")
        
        lines.append("")
        lines.append(f"Score de coherencia: {self.score:.0%}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (
            f"ValidationResult(species={self.species_id}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.warnings)}, "
            f"score={self.score:.0%})"
        )