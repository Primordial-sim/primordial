from core.genetics.species_definition import SpeciesRegistry, SpeciesDefinition
from core.genetics.biological_validator import BiologicalValidator
from core.genetics.realism_index import RealismIndex

print("=" * 70)
print("FASE 3: PLANTILLAS CON HERENCIA")
print("=" * 70)
print()

# Inicializar
SpeciesRegistry.initialize_defaults()

# ========================================
# TEST 1: Ver la jerarquía de plantillas
# ========================================
print("TEST 1: Jerarquía de plantillas")
print("-" * 70)
for template in SpeciesRegistry.get_templates():
    chain = template.get_inheritance_chain()
    chain_str = " -> ".join(chain)
    print(f"  {template.name:20s} [{chain_str}] ({template.get_trait_count()} rasgos)")
print()

# ========================================
# TEST 2: Humano hereda de mamífero
# ========================================
print("TEST 2: Humano (hereda de mamífero)")
print("-" * 70)
human = SpeciesRegistry.get("human")
print(f"  Cadena de herencia: {' -> '.join(human.get_inheritance_chain())}")
print(f"  Rasgos locales: {human.get_local_trait_count()}")
print(f"  Rasgos totales (con heredados): {human.get_trait_count()}")
print(f"  Rasgos totales: {sorted(human.get_all_trait_ids())}")
print()

# ========================================
# TEST 3: Ave hereda de vertebrado
# ========================================
print("TEST 3: Ave (hereda de vertebrado)")
print("-" * 70)
bird = SpeciesRegistry.get("bird")
print(f"  Cadena: {' -> '.join(bird.get_inheritance_chain())}")
print(f"  Rasgos locales: {bird.get_local_trait_count()}")
print(f"  Rasgos totales: {bird.get_trait_count()}")
print(f"  Hereda metabolismo de animal: {bird.has_trait('metabolism')}")
print(f"  Hereda sistema nervioso de vertebrado: {bird.has_trait('nervous_system')}")
print(f"  Tiene vuelo propio: {bird.has_local_trait('flight')}")
print()

# ========================================
# TEST 4: Crear especie personalizada con from_template
# ========================================
print("TEST 4: Crear LOBO desde plantilla mamífero")
print("-" * 70)
wolf = SpeciesDefinition.from_template(
    species_id="wolf",
    name="Lobo",
    base_template="mammal",
    description="Depredador social con excelente olfato.",
    archetype="mammal",
).add_trait("smell", default_value=1.8, weight=1.0) \
 .add_trait("speed", default_value=1.4, weight=0.9) \
 .add_trait("aggressiveness", default_value=1.3, weight=0.9) \
 .add_trait("cooperation", default_value=1.5, weight=1.0)

SpeciesRegistry.register(wolf)
print(f"  Cadena: {' -> '.join(wolf.get_inheritance_chain())}")
print(f"  Rasgos locales: {wolf.get_local_trait_count()}")
print(f"  Rasgos totales: {wolf.get_trait_count()}")

validator = BiologicalValidator()
result = validator.validate_species(wolf)
print(f"  Validación: {result}")
print()

# ========================================
# TEST 5: Plantilla vacía - crear desde cero
# ========================================
print("TEST 5: Especie alienígena desde plantilla VACÍA")
print("-" * 70)
alien = SpeciesDefinition.empty(
    species_id="alien",
    name="Alienígena",
    description="Organismo extraterrestre completamente personalizado.",
).add_trait("bioluminescence", default_value=1.5, weight=1.0) \
 .add_trait("regeneration", default_value=1.8, weight=1.0) \
 .add_trait("empathy", default_value=1.3, weight=0.8) \
 .add_trait("intelligence", default_value=1.6, weight=1.0)

SpeciesRegistry.register(alien)
print(f"  Cadena: {' -> '.join(alien.get_inheritance_chain())}")
print(f"  Rasgos locales: {alien.get_local_trait_count()}")
print(f"  Rasgos totales: {alien.get_trait_count()}")

result = validator.validate_species(alien)
print(f"  Validación: {result}")
print(f"  Reporte:")
for msg in result.messages:
    print(f"    [{msg.severity.name}] {msg.message}")
print()

# ========================================
# TEST 6: Todas las especies
# ========================================
print("TEST 6: Resumen de todas las especies")
print("-" * 70)
for species_id, species in SpeciesRegistry.get_all().items():
    parent = species.parent_template or "—"
    print(f"  {species_id:20s} <- {parent:20s} | {species.get_trait_count():2d} rasgos")
print()

print("=" * 70)
print("✅ FASE 3 completada correctamente")
print("=" * 70)