"""CLI para ejecutar escenarios de simulación desde archivos JSON.

Uso:
    python tools/run_scenario.py scenarios/birds.json
    python tools/run_scenario.py scenarios/mixed.json --export report.csv
    python tools/run_scenario.py --list
"""

import argparse
import sys
import os

# Añadir raíz del proyecto al path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.engine.scenario_loader import ScenarioLoader
from core.engine.simulation_engine import SimulationEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta escenarios de simulación desde archivos JSON."
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Ruta al archivo JSON del escenario",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Lista todos los escenarios disponibles",
    )
    parser.add_argument(
        "--export", "-e",
        type=str,
        help="Exporta métricas a un archivo CSV",
    )
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        help="Sobrescribe el número máximo de ticks del escenario",
    )
    
    args = parser.parse_args()
    
    # Listar escenarios
    if args.list:
        scenarios = ScenarioLoader.list_scenarios("scenarios")
        if not scenarios:
            print("⚠️  No se encontraron escenarios en el directorio 'scenarios/'")
            return
        print("\n📋 Escenarios disponibles:")
        print("-" * 50)
        for s in scenarios:
            print(f"  {s}")
        print()
        return
    
    # Requiere escenario
    if not args.scenario:
        parser.print_help()
        print("\n❌ Debes especificar un escenario o usar --list")
        return
    
    # Cargar escenario
    print(f"\n📂 Cargando escenario: {args.scenario}")
    try:
        scenario = ScenarioLoader.load(args.scenario)
    except Exception as e:
        print(f"❌ Error al cargar escenario: {e}")
        return
    
    # Mostrar información del escenario
    print(f"\n{'='*60}")
    print(f"🎬 {scenario.name}")
    print(f"{'='*60}")
    if scenario.description:
        print(f"📝 {scenario.description}")
    print(f"\n🌍 Mundo: {scenario.world.width}x{scenario.world.height}")
    print(f"👥 Especies:")
    for sc in scenario.species:
        print(f"   - {sc.species_id}: {sc.count} individuos")
    print(f"📊 Total: {scenario.total_population} agentes")
    print(f"⏱️  Días por tick: {scenario.simulation.delta_days}")
    print(f"📅 Días totales: {scenario.simulation.total_days}")
    if scenario.simulation.max_ticks:
        print(f"🎯 Máx ticks: {scenario.simulation.max_ticks}")
    print(f"{'='*60}\n")
    
    # Sobrescribir max_ticks si se especificó
    if args.ticks:
        scenario.simulation.max_ticks = args.ticks
        print(f"🎯 Sobrescrito: máx ticks = {args.ticks}")
    
    # Crear y ejecutar simulación
    print("\n🚀 Iniciando simulación...\n")
    engine = SimulationEngine.create_from_scenario(
        scenario=scenario,
        export_path=args.export,
    )
    engine.run()
    
    if args.export:
        print(f"\n💾 Métricas exportadas a: {args.export}")


if __name__ == "__main__":
    main()