"""Servidor WebSocket que integra el SimulationEngine real con Godot.

Soporte para escenarios:
    python tools/ws_server_real.py                      # Usa humanos por defecto
    python tools/ws_server_real.py --scenario scenarios/birds.json
    python tools/ws_server_real.py --scenario scenarios/mixed.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import argparse
from typing import Any, Set, Optional, TYPE_CHECKING

# CORRECCIÓN CRÍTICA: Añadir la raíz del proyecto al sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import websockets

# TYPE_CHECKING: Imports solo para type hints (no en tiempo de ejecución)
if TYPE_CHECKING:
    from core.engine.scenario_loader import Scenario

# Import real (solo lo que se usa en tiempo de ejecución)
from core.engine.simulation_engine import SimulationEngine
from core.engine.scenario_loader import ScenarioLoader

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

HOST = "localhost"
PORT = 8765

# Intervalo entre ticks en segundos (0.1 = 10 FPS)
TICK_INTERVAL = 0.1

# Configuración por defecto (si no se especifica escenario)
DEFAULT_SPECIES_ID = "human"
DEFAULT_POPULATION_SIZE = 50
DEFAULT_WORLD_WIDTH = 100
DEFAULT_WORLD_HEIGHT = 100

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WSServerReal")


class RealSimulationServer:
    """Servidor WebSocket que integra el SimulationEngine real."""
    
    def __init__(
        self, 
        host: str = HOST, 
        port: int = PORT, 
        scenario: Optional['Scenario'] = None
    ):
        self.host = host
        self.port = port
        self.connected_clients: Set[Any] = set()
        self.scenario = scenario
        
        # Crear el motor de simulación
        logger.info("🔧 Creando motor de simulación...")
        
        if scenario is not None:
            logger.info("📂 Usando escenario: %s", scenario.name)
            logger.info("   Especies: %s", 
                       ", ".join(f"{s.count}x {s.species_id}" for s in scenario.species))
            self.engine = SimulationEngine.create_from_scenario(scenario)
        else:
            logger.info("📂 Usando configuración por defecto (humanos)")
            self.engine = SimulationEngine.create_default(
                width=DEFAULT_WORLD_WIDTH,
                height=DEFAULT_WORLD_HEIGHT,
                founding_population_size=DEFAULT_POPULATION_SIZE,
                max_ticks=None,
            )
        
        # Inicializar la simulación (sin ejecutar ticks)
        self.engine.initialize()
        logger.info("✅ Motor de simulación inicializado")
        
        # Variables de control
        self._running = True
        self._paused = False
        self._tick_interval = TICK_INTERVAL
    
    async def handle_connection(self, websocket: Any) -> None:
        """Maneja una conexión WebSocket individual."""
        client_id = f"client_{id(websocket)}"
        self.connected_clients.add(websocket)
        logger.info(f"✅ {client_id} conectado. Total: {len(self.connected_clients)}")
        
        try:
            # Enviar el estado inicial al nuevo cliente
            initial_state = self.engine.get_visualization_state()
            await websocket.send(json.dumps(initial_state))
            
            # Mantener la conexión abierta para recibir comandos
            while self._running:
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=1.0
                    )
                    await self._handle_client_message(websocket, message)
                except asyncio.TimeoutError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"❌ {client_id} desconectado.")
        except Exception as e:
            logger.error(f"Error con {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def _handle_client_message(self, websocket: Any, message: str) -> None:
        """Procesa comandos enviados por el cliente (Godot)."""
        try:
            data = json.loads(message)
            command = data.get("type", "")
            
            if command == "pause":
                self._paused = True
                logger.info("⏸️  Simulación pausada")
                await self._broadcast_status("paused")
                
            elif command == "resume":
                self._paused = False
                logger.info("▶️  Simulación reanudada")
                await self._broadcast_status("running")
                
            elif command == "set_speed":
                speed = data.get("speed", 1.0)
                self._tick_interval = TICK_INTERVAL / speed
                logger.info(f"⚡ Velocidad cambiada a {speed}x")
                await self._broadcast_status(f"speed:{speed}")
                
            elif command == "step":
                if self._paused:
                    try:
                        state = self.engine.step()
                        if self.connected_clients:
                            message_state = json.dumps(state)
                            await asyncio.gather(
                                *[client.send(message_state) for client in self.connected_clients],
                                return_exceptions=True
                            )
                        logger.info("⏭️  Avanzado 1 tick (paso a paso)")
                    except Exception as e:
                        logger.error(f"Error en step: {e}")
                
        except json.JSONDecodeError:
            logger.warning(f"Mensaje inválido recibido: {message}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    async def _broadcast_status(self, status: str) -> None:
        """Envía un mensaje de estado a todos los clientes conectados."""
        message = json.dumps({"type": "status", "status": status})
        
        for client in list(self.connected_clients):
            try:
                await client.send(message)
            except Exception:
                pass
    
    async def simulation_loop(self) -> None:
        """Bucle principal que ejecuta la simulación tick por tick."""
        logger.info("🚀 Iniciando bucle de simulación...")
        logger.info(f"   Intervalo de tick: {self._tick_interval}s")
        
        while self._running:
            if not self._paused:
                try:
                    state = self.engine.step()
                    
                    if self.connected_clients:
                        message = json.dumps(state)
                        await asyncio.gather(
                            *[client.send(message) for client in self.connected_clients],
                            return_exceptions=True
                        )
                        
                except Exception as e:
                    logger.error(f"Error en tick de simulación: {e}", exc_info=True)
            
            await asyncio.sleep(self._tick_interval)
    
    async def start(self) -> None:
        """Inicia el servidor WebSocket y el bucle de simulación."""
        logger.info(f"🌐 Servidor WebSocket iniciando en ws://{self.host}:{self.port}")
        logger.info("   Esperando conexiones de Godot...")
        
        def signal_handler(sig, frame):
            logger.info("\n🛑 Señal de terminación recibida. Deteniendo servidor...")
            self._running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await self.simulation_loop()


def main() -> None:
    """Punto de entrada del servidor."""
    parser = argparse.ArgumentParser(
        description="Servidor WebSocket para el simulador de vida"
    )
    parser.add_argument(
        "--scenario", "-s",
        type=str,
        help="Ruta al archivo JSON del escenario",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=PORT,
        help=f"Puerto del servidor (por defecto: {PORT})",
    )
    args = parser.parse_args()
    
    scenario = None
    if args.scenario:
        try:
            scenario = ScenarioLoader.load(args.scenario)
            logger.info("📂 Escenario cargado: %s", scenario.name)
            logger.info("   Total de agentes: %d", scenario.total_population)
        except FileNotFoundError:
            logger.error("❌ Archivo de escenario no encontrado: %s", args.scenario)
            return
        except ValueError as e:
            logger.error("❌ Escenario inválido: %s", e)
            return
        except Exception as e:
            logger.error("❌ Error inesperado al cargar escenario: %s", e)
            return
    
    server = RealSimulationServer(port=args.port, scenario=scenario)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("🛑 Servidor detenido por el usuario.")


if __name__ == "__main__":
    main()