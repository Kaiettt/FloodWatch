import asyncio
import random
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class WaterLevelReading:
    """Represents a single water level reading."""
    value: float  # in meters
    timestamp: str
    location: Dict[str, float]  # {latitude, longitude}
    sensor_id: str
    status: str = "ok"
    unit: str = "m"

class WaterLevelSimulator:
    """Simulates water level sensors that report to Orion-LD."""
    
    def __init__(self, update_interval: int = 60):
        self.update_interval = update_interval
        self.running = False
        self.sensors = self._initialize_sensors()
        self.orion_url = "http://localhost:1026/ngsi-ld/v1/"
        self.headers = {
            "Content-Type": "application/json",
            "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
        }
    
    def _initialize_sensors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize simulated sensors with their locations."""
        return {
            "sensor-0021": {
                "location": {
                    "type": "Point",
                    "coordinates": [106.7, 10.7]  # Longitude, Latitude
                },
                "base_level": 2.0,  # Base water level in meters
                "variation_range": 0.5,  # Max variation from base level
                "alert_threshold": 3.0  # Water level that triggers alerts
            },
            "sensor-0020": {
                "location": {
                    "type": "Point",
                    "coordinates": [106.71, 10.69]
                },
                "base_level": 1.8,
                "variation_range": 0.7,
                "alert_threshold": 2.8
            }
        }
    
    async def _generate_reading(self, sensor_id: str) -> WaterLevelReading:
        """Generate a simulated water level reading."""
        sensor = self.sensors[sensor_id]
        
        # Simulate water level with some random variation
        variation = random.uniform(-1, 1) * sensor["variation_range"]
        value = max(0, sensor["base_level"] + variation)  # Water level can't be negative
        
        # Simulate occasional sensor errors
        status = "ok"
        if random.random() < 0.05:  # 5% chance of error
            status = "error"
            value = -1  # Invalid reading
        
        return WaterLevelReading(
            value=round(value, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            location={
                "latitude": sensor["location"]["coordinates"][1],
                "longitude": sensor["location"]["coordinates"][0]
            },
            sensor_id=sensor_id,
            status=status
        )
    
    async def _create_entity_if_not_exists(self, sensor_id: str):
        """Create a new water level sensor entity in Orion-LD if it doesn't exist."""
        url = f"{self.orion_url}entities/urn:ngsi-ld:WaterLevelObserved:{sensor_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                # Check if entity exists
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        logger.info(f"Entity {sensor_id} already exists in Orion-LD")
                        return
                
                # Create new entity
                sensor = self.sensors[sensor_id]
                entity = {
                    "id": f"urn:ngsi-ld:WaterLevelObserved:{sensor_id}",
                    "type": "WaterLevelObserved",
                    "location": {
                        "type": "GeoProperty",
                        "value": sensor["location"]
                    },
                    "waterLevel": {
                        "type": "Property",
                        "value": 0.0,
                        "unitCode": "MTR",
                        "observedAt": datetime.now(timezone.utc).isoformat()
                    },
                    "alertThreshold": {
                        "type": "Property",
                        "value": sensor["alert_threshold"],
                        "unitCode": "MTR"
                    },
                    "status": {
                        "type": "Property",
                        "value": "initializing"
                    }
                }
                
                async with session.post(
                    f"{self.orion_url}entities/",
                    headers=self.headers,
                    json=entity
                ) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Created new WaterLevelObserved entity: {sensor_id}")
                    else:
                        logger.error(f"Failed to create entity: {await resp.text()}")
                        
            except Exception as e:
                logger.error(f"Error creating entity: {e}")
    
    async def _update_sensor_data(self, sensor_id: str, reading: WaterLevelReading):
        """Update sensor data in Orion-LD."""
        update_url = f"{self.orion_url}entities/urn:ngsi-ld:WaterLevelObserved:{sensor_id}/attrs"
        
        update_data = {
            "waterLevel": {
                "type": "Property",
                "value": reading.value,
                "unitCode": "MTR",
                "observedAt": reading.timestamp
            },
            "status": {
                "type": "Property",
                "value": reading.status
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": [
                        reading.location["longitude"],
                        reading.location["latitude"]
                    ]
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.patch(
                    update_url,
                    headers=self.headers,
                    json=update_data
                ) as resp:
                    if resp.status == 204:
                        logger.debug(f"Updated {sensor_id} with value: {reading.value}m")
                    else:
                        logger.error(f"Failed to update {sensor_id}: {await resp.text()}")
            except Exception as e:
                logger.error(f"Error updating {sensor_id}: {e}")
    
    async def _simulate_sensor(self, sensor_id: str):
        """Simulate a single sensor's operation."""
        await self._create_entity_if_not_exists(sensor_id)
        
        while self.running:
            try:
                # Generate and send new reading
                reading = await self._generate_reading(sensor_id)
                await self._update_sensor_data(sensor_id, reading)
                
                # Log if water level is above threshold
                if reading.status == "ok" and reading.value >= self.sensors[sensor_id]["alert_threshold"]:
                    logger.warning(
                        f"High water level alert! Sensor {sensor_id}: {reading.value}m "
                        f"(threshold: {self.sensors[sensor_id]['alert_threshold']}m)"
                    )
                
            except Exception as e:
                logger.error(f"Error in sensor {sensor_id} simulation: {e}")
            
            # Wait for next reading
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the water level sensor simulation."""
        self.running = True
        logger.info("Starting water level sensor simulation...")
        
        # Start a task for each sensor
        tasks = [
            asyncio.create_task(self._simulate_sensor(sensor_id))
            for sensor_id in self.sensors
        ]
        
        # Keep the tasks running until stopped
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the simulation."""
        self.running = False
        logger.info("Stopping water level sensor simulation...")

if __name__ == "__main__":
    import logging
    import asyncio

    logging.basicConfig(level=logging.INFO)

    sim = WaterLevelSimulator(update_interval=10)

    try:
        asyncio.run(sim.start())
    except KeyboardInterrupt:
        asyncio.run(sim.stop())
