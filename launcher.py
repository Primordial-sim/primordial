"""Punto de entrada de la aplicación."""

from __future__ import annotations

import argparse
import logging
import re

from core.engine.simulation_engine import SimulationEngine


class RelevantEventsFilter(logging.Filter):
    """Solo permite pasar logs que contengan eventos relevantes."""
    
    RELEVANT_PATTERNS = [
        r"👶",           # Nacimientos
        r"⚰️",           # Muertes
        r"❤️",           # Matrimonios
        r"💔",           # Divorcios
        r"🚶",           # Migraciones
        r"🎯",           # Motivaciones activas
        r"🎓",           # Aprendizaje
        r"🤒",           # Contagios
        r"🚨",           # Brotes
        r"🌍",           # Cambios de estación
        r"👋",           # Encuentros entre agentes
        r"🤝",           # Relaciones UNKNOWN → ACQUAINTANCE
        r"👥",           # Amistades
        r"💕",           # Interés romántico
        r"🏠",           # Convivencia
        r"💍",           # Relaciones consolidadas
        r"📊",           # Diagnóstico de relaciones
        r"🔍",           # Debug de relaciones
      #  r"🧠",           # Experiencias relacionales (NUEVO)
        r"INFORME EVOLUTIVO",
        r"RESUMEN EJECUTIVO",
        r"ERROR",
        r"WARNING",
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return any(re.search(pattern, message) for pattern in self.RELEVANT_PATTERNS)


def main() -> None:
    """Crea el motor por defecto y arranca la simulación."""
    
    # =====================================================================
    # PARSER DE ARGUMENTOS
    # =====================================================================
    parser = argparse.ArgumentParser(
        description="Simulador de Vida Evolutiva",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python launcher.py
  python launcher.py --config scenario_extreme.json
  python launcher.py --config config/alta_densidad.json --population 200
  python launcher.py --population 100 --width 50 --height 50 --verbose
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Ruta al archivo JSON de configuración (ej: scenario_extreme.json)"
    )
    parser.add_argument(
        "--population", "-p",
        type=int,
        default=50,
        help="Población inicial (default: 50)"
    )
    parser.add_argument(
        "--width", "-w",
        type=int,
        default=100,
        help="Anchura del mundo (default: 100)"
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=100,
        help="Altura del mundo (default: 100)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Activar logging detallado (DEBUG)"
    )
    
    args = parser.parse_args()
    
    # =====================================================================
    # CONFIGURACIÓN DE LOGGING
    # =====================================================================
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # Handler para consola (solo eventos relevantes)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    console.setFormatter(formatter)
    if not args.verbose:
        console.addFilter(RelevantEventsFilter())
    logger.addHandler(console)
    
    # Handler para archivo (TAMBIÉN filtrado)
    file_handler = logging.FileHandler("simulacion.txt", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    file_handler.setFormatter(formatter)
    if not args.verbose:
        file_handler.addFilter(RelevantEventsFilter())
    logger.addHandler(file_handler)
    
    # =====================================================================
    # LOG DE CONFIGURACIÓN
    # =====================================================================
    logger.info("=" * 65)
    logger.info("🚀 INICIANDO SIMULADOR DE VIDA EVOLUTIVA")
    logger.info("=" * 65)
    logger.info("📋 Configuración:")
    logger.info("   • Población inicial: %d agentes", args.population)
    logger.info("   • Tamaño del mundo: %dx%d", args.width, args.height)
    if args.config:
        logger.info("   • Archivo de configuración: %s", args.config)
    else:
        logger.info("   • Archivo de configuración: (usando defaults)")
    logger.info("   • Logging detallado: %s", "ACTIVADO" if args.verbose else "desactivado")
    logger.info("=" * 65)
    
    # =====================================================================
    # CREAR Y EJECUTAR MOTOR
    # =====================================================================
    engine = SimulationEngine.create_default(
        config_path=args.config,
        width=args.width,
        height=args.height,
        founding_population_size=args.population,
    )
    engine.run()


if __name__ == "__main__":
    main()