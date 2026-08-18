"""Servidor WebSocket de prueba para la interfaz de Godot.

Este servidor genera agentes ficticios que se mueven aleatoriamente
y envía sus posiciones a cualquier cliente conectado (Godot).

Uso:
    python tools/ws_server.py

Luego abre tu proyecto de Godot y ejecuta la escena principal.
Los agentes deberían aparecer y moverse en la ventana de Godot.
"""

import asyncio
import json
import random
import logging
from typing import List, Dict, Any

import websockets

# Configuración
HOST = "localhost"
PORT = 8765
NUM_AGENTS = 20
TICK_INTERVAL = 0.1  # segundos entre actualizaciones (10 FPS)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WSServer")


class Agent:
    """Agente ficticio que se mueve aleatoriamente."""
    
    def __init__(self, entity_id: int, width: int = 1280, height: int = 720):
        self.entity_id = entity_id
        self.x = random.uniform(50, width - 50)
        self.y = random.uniform(50, height - 50)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.width = width
        self.height = height
    
    def update(self) -> None:
        """Actualiza la posición del agente con rebote en los bordes."""
        self.x += self.vx
        self.y += self.vy
        
        # Rebotar en los bordes
        if self.x <= 0 or self.x >= self.width:
            self.vx = -self.vx
            self.x = max(0, min(self.width, self.x))
        if self.y <= 0 or self.y >= self.height:
            self.vy = -self.vy
            self.y = max(0, min(self.height, self.y))
        
        # Cambio aleatorio de dirección (10% probabilidad)
        if random.random() < 0.1:
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el agente a un diccionario para enviar como JSON."""
        return {
            "id": self.entity_id,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
        }


class SimulationServer:
    """Servidor WebSocket que transmite el estado de la simulación."""
    
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.agents: List[Agent] = [Agent(i) for i in range(NUM_AGENTS)]
        self.connected_clients: set = set()
        self.tick_count = 0
    
    def get_state(self) -> Dict[str, Any]:
        """Genera el estado actual de la simulación como diccionario."""
        self.tick_count += 1
        
        # Actualizar todos los agentes
        for agent in self.agents:
            agent.update()
        
        return {
            "type": "tick",
            "tick": self.tick_count,
            "agents": [agent.to_dict() for agent in self.agents],
        }
    
    async def handle_connection(self, websocket: Any) -> None:
        """Maneja una conexión WebSocket individual."""
        client_id = f"client_{id(websocket)}"
        self.connected_clients.add(websocket)
        logger.info(f"✅ {client_id} conectado. Total: {len(self.connected_clients)}")
        
        try:
            while True:
                # Enviar estado actual
                state = self.get_state()
                await websocket.send(json.dumps(state))
                
                # Esperar el intervalo de tick
                await asyncio.sleep(TICK_INTERVAL)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"❌ {client_id} desconectado.")
        except Exception as e:
            logger.error(f"Error con {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def start(self) -> None:
        """Inicia el servidor WebSocket."""
        logger.info(f"🚀 Iniciando servidor en ws://{self.host}:{self.port}")
        logger.info(f"   Agentes simulados: {NUM_AGENTS}")
        logger.info(f"   Intervalo de tick: {TICK_INTERVAL}s")
        logger.info("   Esperando conexiones de Godot...")
        
        async with websockets.serve(self.handle_connection, self.host, self.port):
            # Mantener el servidor corriendo indefinidamente
            await asyncio.Future()


def main() -> None:
    """Punto de entrada del servidor."""
    server = SimulationServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("🛑 Servidor detenido por el usuario.")


if __name__ == "__main__":
    main()