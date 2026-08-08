"""Punto de entrada de la aplicación."""

from __future__ import annotations

import argparse
import logging
import re
import random

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
        r"🧠",           # Experiencias relacionales 
        r"✨",           # Experiencias generadas
        r"INFORME EVOLUTIVO",
        r"RESUMEN EJECUTIVO",
        r"ERROR",
        r"WARNING",
        r"🔄",           # Reevaluaciones
        r"🏁",           # Llegadas de migración
        r"💑",           # Progresión de relaciones
        r"🎂",           # Cumpleaños/madurez
        r"👴",           # Senectud
        r"⚠️",           # Abortos, mortalidad fetal
        r"📜",           # Eventos históricos (linajes extintos)
        r"🛑",           # Cuellos de botella
        r"👑",           # Linajes dominantes
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
  # Ejecución básica con defaults
  python launcher.py

  # Prueba de integración mínima (Fase 2 de validación)
  python launcher.py --population 50 --ticks 50 --seed 42 --verbose

  # Prueba de emergencia (Fase 3 de validación)
  python launcher.py --population 200 --ticks 500 --seed 123 --verbose

  # Simulación larga con exportación de métricas
  python launcher.py --population 500 --ticks 5000 --seed 7 --export results.json
  
  # Usar archivo de configuración externo
  python launcher.py --config scenario_extreme.json --population 200 --ticks 1000
        """
    )
    
    # --- Parámetros de mundo ---
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
    
    # --- NUEVO: Parámetros de ejecución ---
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        default=None,
        help="Número de ticks a ejecutar (default: según config o infinito hasta condición de parada)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Semilla aleatoria para reproducibilidad (default: None = aleatorio)"
    )
    
    parser.add_argument(
        "--export", "-e",
        type=str,
        default="simulation_metrics.json",
        help="Ruta del archivo JSON de exportación de métricas (default: simulation_metrics.json)"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Desactivar la exportación de métricas al finalizar"
    )
    parser.add_argument(
        "--snapshot-interval",
        type=int,
        default=None,
        help="Intervalo de snapshots de métricas en días (default: según config)"
    )
    
    # --- Parámetros de logging ---
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Activar logging detallado (DEBUG)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Modo silencioso: solo errores críticos"
    )
    
    args = parser.parse_args()
    
    # =====================================================================
    # SEMILLA ALEATORIA (Reproducibilidad)
    # =====================================================================
    if args.seed is not None:
        random.seed(args.seed)
        # Si numpy está disponible, también fijar su semilla
        try:
            import numpy as np
            np.random.seed(args.seed)
        except ImportError:
            pass
    
    # =====================================================================
    # CONFIGURACIÓN DE LOGGING
    # =====================================================================
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Handler para consola (filtrado según verbose)
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    if not args.verbose and not args.quiet:
        console.addFilter(RelevantEventsFilter())
    logger.addHandler(console)
    
    # Handler para archivo
    file_handler = logging.FileHandler("simulacion.txt", mode="w", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    if not args.verbose and not args.quiet:
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
    if args.ticks is not None:
        logger.info("   • Ticks a ejecutar: %d", args.ticks)
    else:
        logger.info("   • Ticks a ejecutar: (según config / hasta condición de parada)")
    if args.seed is not None:
        logger.info("   • Semilla aleatoria: %d (reproducible)", args.seed)
    else:
        logger.info("   • Semilla aleatoria: (aleatorio)")
    if args.config:
        logger.info("   • Archivo de configuración: %s", args.config)
    else:
        logger.info("   • Archivo de configuración: (usando defaults)")
    if not args.no_export:
        logger.info("   • Exportación de métricas: %s", args.export)
    else:
        logger.info("   • Exportación de métricas: DESACTIVADA")
    logger.info("   • Logging: %s", 
                "DETALLADO" if args.verbose else ("SILENCIOSO" if args.quiet else "normal"))
    logger.info("=" * 65)
    
    # =====================================================================
    # CREAR MOTOR
    # =====================================================================
    engine = SimulationEngine.create_default(
        config_path=args.config,
        width=args.width,
        height=args.height,
        founding_population_size=args.population,
        max_ticks=args.ticks,              # NUEVO
        export_path=args.export if not args.no_export else None,  # NUEVO
        snapshot_interval=args.snapshot_interval,  # NUEVO
    )
    
    # =====================================================================
    # EJECUTAR SIMULACIÓN
    # =====================================================================
    try:
        engine.run()
        logger.info("=" * 65)
        logger.info("✅ SIMULACIÓN FINALIZADA CORRECTAMENTE")
        logger.info("=" * 65)
    except KeyboardInterrupt:
        logger.warning("⚠️  Simulación interrumpida por el usuario (Ctrl+C)")
        logger.info("Exportando estado final...")
        if not args.no_export and hasattr(engine, 'export_metrics'):
            engine.export_metrics(args.export)
    except Exception as e:
        logger.error("❌ ERROR CRÍTICO en la simulación: %s", str(e))
        logger.exception("Traceback completo:")
        raise


if __name__ == "__main__":
    main()