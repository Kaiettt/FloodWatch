# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import asyncio
import logging
import signal
from typing import List

from simulation.water_level_sensor.simulator import WaterLevelSimulator
from simulation.camera_stream.simulator import CameraStreamSimulator
from simulation.crowd_report.simulator import CrowdReportSimulator
from simulation.weather_observation.simulator import WeatherSimulator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimulationManager:
    def __init__(self):
        self.simulators: List[object] = []
        self.running = False
        
    async def start(self):
        """Initialize and start all simulators."""
        self.running = True
        
        # Initialize all simulators
        self.simulators = [
            WaterLevelSimulator(),
            CameraStreamSimulator(),
            CrowdReportSimulator(),
            WeatherSimulator()
        ]
        
        # Start all simulators
        for simulator in self.simulators:
            if hasattr(simulator, 'start'):
                await simulator.start()
                logger.info(f"Started {simulator.__class__.__name__}")
        
        # Keep the service running
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop all simulators gracefully."""
        self.running = False
        for simulator in reversed(self.simulators):
            if hasattr(simulator, 'stop'):
                await simulator.stop()
        logger.info("All simulators stopped")

async def shutdown(signal, loop, manager):
    """Handle shutdown signals."""
    logger.info(f"Received exit signal {signal.name}...")
    await manager.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    manager = SimulationManager()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, 
            lambda s=sig: asyncio.create_task(shutdown(s, loop, manager))
        )
    
    try:
        loop.run_until_complete(manager.start())
    except Exception as e:
        logger.error(f"Error in simulation: {e}", exc_info=True)
    finally:
        loop.run_until_complete(manager.stop())
        loop.close()
        logger.info("Simulation service stopped")
