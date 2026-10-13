"""Servidor WebSocket con multiplicadores de velocidad y refresco constante."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
import argparse
from typing import Any, Set, Optional, TYPE_CHECKING

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import websockets

if TYPE_CHECKING:
    from core.engine.scenario_loader import Scenario

from core.engine.simulation_engine import SimulationEngine
from core.engine.scenario_loader import ScenarioLoader
from core.config.simulation_config import SimulationConfig
from core.config.parameter_registry import ParameterRegistry
from core.config.preset_engine import PresetEngine, register_all_presets

HOST = "localhost"
PORT = 8765
DEFAULT_POPULATION_SIZE = 50
DEFAULT_WORLD_WIDTH = 100
DEFAULT_WORLD_HEIGHT = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WSServerReal")

class RealSimulationServer:
    def __init__(self, host: str = HOST, port: int = PORT, scenario: Optional['Scenario'] = None):
        self.host = host
        self.port = port
        self.connected_clients: Set[Any] = set()
        
        logger.info("🔧 Inicializando motor...")
        if scenario:
            self.engine = SimulationEngine.create_from_scenario(scenario)
        else:
            self.engine = SimulationEngine.create_default(
                width=DEFAULT_WORLD_WIDTH, height=DEFAULT_WORLD_HEIGHT,
                founding_population_size=DEFAULT_POPULATION_SIZE, max_ticks=None,
            )
        self.engine.initialize()
        
        self.config = self.engine.config if hasattr(self.engine, 'config') else SimulationConfig()
        self.registry = ParameterRegistry(self.config)
        self.preset_engine = PresetEngine(registry=self.registry)
        register_all_presets(self.preset_engine)
        
        self._running = True
        self._paused = False
        
        # --- MULTIPLICADORES DE VELOCIDAD ---
        # 1x = 1 día/seg, 10x = 10 días/seg, 100x = 100 días/seg, 1000x = 1000 días/seg
        self._speed_multiplier = 1
        self._refresh_interval = 1.0  # Siempre 1 segundo entre actualizaciones
        # --------------------------------------

    async def handle_connection(self, websocket: Any) -> None:
        client_id = f"client_{id(websocket)}"
        self.connected_clients.add(websocket)
        logger.info(f"✅ {client_id} conectado.")
        try:
            await websocket.send(json.dumps(self.engine.get_visualization_state()))
            while self._running:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    await self._handle_client_message(websocket, msg)
                except asyncio.TimeoutError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"❌ {client_id} desconectado.")
        finally:
            self.connected_clients.discard(websocket)

    async def _handle_client_message(self, websocket: Any, message: str) -> None:
        try:
            data = json.loads(message)
            cmd = data.get("type", "")
            
            if cmd == "pause":
                self._paused = True
                await self._broadcast_status("paused")
            elif cmd == "resume":
                self._paused = False
                await self._broadcast_status("running")
            elif cmd == "set_speed":
                self._speed_multiplier = int(data.get("multiplier", 1))
                logger.info(f"⚡ Velocidad: {self._speed_multiplier}x ({self._speed_multiplier} días/seg)")
                await self._broadcast_status(f"speed:{self._speed_multiplier}")
            elif cmd == "step":
                if self._paused:
                    self.engine.step()
                    await self._broadcast_state()
            elif cmd == "get_presets":
                presets = [{"id": pid, "name": p.name.replace("_", " ").title(), "value": self.preset_engine.get_preset_value(pid)} 
                           for pid, p in self.preset_engine.get_all_presets().items()]
                await websocket.send(json.dumps({"type": "presets_config", "presets": presets}))
            elif cmd == "set_preset":
                self.preset_engine.set_preset_value(data.get("id"), float(data.get("value", 50.0)))
        except Exception as e:
            logger.error(f"Error mensaje: {e}")

    async def _broadcast_state(self) -> None:
        if not self.connected_clients: return
        try:
            state = self.engine.get_visualization_state()
            msg = json.dumps(state)
            await asyncio.gather(*[c.send(msg) for c in self.connected_clients], return_exceptions=True)
        except Exception as e:
            logger.error(f"Error broadcast: {e}")

    async def _broadcast_status(self, status: str) -> None:
        msg = json.dumps({"type": "status", "status": status})
        for c in list(self.connected_clients):
            try: await c.send(msg)
            except: pass

    async def simulation_loop(self) -> None:
        logger.info("🚀 Bucle iniciado (Multiplicadores con refresco de 1s)")
        
        while self._running:
            if not self._paused:
                frame_start = time.perf_counter()
                
                # Ejecutar tantos pasos como indique el multiplicador
                steps_done = 0
                for _ in range(self._speed_multiplier):
                    self.engine.step()
                    steps_done += 1
                
                # Enviar actualización
                await self._broadcast_state()
                
                # Calcular cuánto tiempo ha pasado
                elapsed = time.perf_counter() - frame_start
                
                # Si tardamos menos de 1 segundo, esperar el resto
                if elapsed < self._refresh_interval:
                    await asyncio.sleep(self._refresh_interval - elapsed)
                else:
                    # Si tardamos más de 1 segundo, logueamos que se alcanzó el límite de CPU
                    actual_speed = steps_done / elapsed
                    logger.warning(f"⚠️ Límite CPU: Objetivo {self._speed_multiplier}x, Real {actual_speed:.0f}x")
            
            # Pequeña pausa para no saturar
            await asyncio.sleep(0.001)

    async def start(self) -> None:
        logger.info(f"🌐 Servidor en ws://{self.host}:{self.port}")
        def signal_handler(sig, frame):
            self._running = False
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await self.simulation_loop()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", "-s", type=str)
    parser.add_argument("--port", "-p", type=int, default=PORT)
    args = parser.parse_args()
    
    scenario = None
    if args.scenario:
        try: scenario = ScenarioLoader.load(args.scenario)
        except Exception as e: logger.error(f"Error escenario: {e}"); return
    
    server = RealSimulationServer(port=args.port, scenario=scenario)
    try: asyncio.run(server.start())
    except KeyboardInterrupt: logger.info("🛑 Detenido.")

if __name__ == "__main__":
    main()