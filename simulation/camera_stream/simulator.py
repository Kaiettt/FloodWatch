# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import asyncio
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp
import json
import cv2
import numpy as np
import base64

logger = logging.getLogger(__name__)

class CameraStreamSimulator:
    """Simulates CCTV cameras that provide visual flood monitoring."""
    
    def __init__(self, update_interval: int = 300):  # 5 minutes by default
        self.update_interval = update_interval
        self.running = False
        self.cameras = self._initialize_cameras()
        self.orion_url = "http://orion-ld:1026/ngsi-ld/v1/"
        self.headers = {
            "Content-Type": "application/ld+json",
            "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
        }
        
        # Create sample video directory if it doesn't exist
        self.sample_video_dir = Path("sample_videos")
        self.sample_video_dir.mkdir(exist_ok=True)
    
    def _initialize_cameras(self) -> Dict[str, Dict[str, Any]]:
        """Initialize simulated cameras with their locations and properties."""
        return {
            "cam-001": {
                "location": {
                    "type": "Point",
                    "coordinates": [106.7, 10.7]  # Longitude, Latitude
                },
                "status": "active",
                "flood_risk_level": 0.1,  # 0-1 scale
                "last_alert": None
            },
            "cam-002": {
                "location": {
                    "type": "Point",
                    "coordinates": [106.71, 10.69]
                },
                "status": "active",
                "flood_risk_level": 0.1,
                "last_alert": None
            }
        }
    
    async def _generate_sample_video(self, camera_id: str) -> str:
        """Generate a sample video frame with simulated flood conditions."""
        # Create a simple frame with the camera ID and timestamp
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        camera = self.cameras[camera_id]
        
        # Add camera info
        cv2.putText(frame, f"Camera: {camera_id}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now(timezone.utc).isoformat()
        cv2.putText(frame, timestamp, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Simulate flood water (blue overlay)
        if camera["flood_risk_level"] > 0.3:
            h, w = frame.shape[:2]
            water_height = int(h * camera["flood_risk_level"])
            if water_height > 0:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, h - water_height), (w, h), 
                            (255, 0, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Save frame as image
        output_path = self.sample_video_dir / f"{camera_id}_latest.jpg"
        cv2.imwrite(str(output_path), frame)
        
        return str(output_path)
    
    async def _update_flood_risk(self, camera_id: str):
        """Update the flood risk level for a camera with some randomness."""
        camera = self.cameras[camera_id]
        
        # Random walk the flood risk level
        change = random.uniform(-0.05, 0.1)
        camera["flood_risk_level"] = max(0, min(1, camera["flood_risk_level"] + change))
        
        # Occasionally have a camera go offline
        if random.random() < 0.02:  # 2% chance
            camera["status"] = "offline"
        elif camera["status"] == "offline" and random.random() < 0.2:  # 20% chance to come back online
            camera["status"] = "active"
    
    async def _create_camera_entity(self, camera_id: str):
        """Create a camera entity in Orion-LD if it doesn't exist."""
        url = f"{self.orion_url}entities/urn:ngsi-ld:Camera:{camera_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                # Check if entity exists
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        logger.info(f"Camera entity {camera_id} already exists in Orion-LD")
                        return
                
                # Create new camera entity
                camera = self.cameras[camera_id]
                entity = {
                    "id": f"urn:ngsi-ld:Camera:{camera_id}",
                    "type": "Device",
                    "category": {
                        "type": "Property",
                        "value": ["sensor"]
                    },
                    "deviceCategory": {
                        "type": "Property",
                        "value": ["camera"]
                    },
                    "location": {
                        "type": "GeoProperty",
                        "value": camera["location"]
                    },
                    "status": {
                        "type": "Property",
                        "value": camera["status"]
                    },
                    "floodRiskLevel": {
                        "type": "Property",
                        "value": camera["flood_risk_level"],
                        "unitCode": "C62"  # 0-1 scale
                    },
                    "image": {
                        "type": "Property",
                        "value": "",
                        "observedAt": datetime.now(timezone.utc).isoformat()
                    },
                    "@context": [
                        "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
                    ]
                }
                
                async with session.post(
                    f"{self.orion_url}entities/",
                    headers=self.headers,
                    json=entity
                ) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Created new Camera entity: {camera_id}")
                    else:
                        logger.error(f"Failed to create camera entity: {await resp.text()}")
                        
            except Exception as e:
                logger.error(f"Error creating camera entity: {e}")
    
    async def _update_camera_data(self, camera_id: str, image_path: str):
        """Update camera data in Orion-LD."""
        update_url = f"{self.orion_url}entities/urn:ngsi-ld:Camera:{camera_id}/attrs"
        camera = self.cameras[camera_id]
        
        # In a real system, you would upload the image to a storage service
        # and store the URL. For simulation, we'll just store the local path.
        update_data = {
            "status": {
                "type": "Property",
                "value": camera["status"]
            },
            "floodRiskLevel": {
                "type": "Property",
                "value": camera["flood_risk_level"],
                "unitCode": "C62",
                "observedAt": datetime.now(timezone.utc).isoformat()
            },
            "image": {
                "type": "Property",
                "value": image_path,
                "observedAt": datetime.now(timezone.utc).isoformat()
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
                        logger.debug(f"Updated camera {camera_id} data")
                        
                        # Check if we need to trigger an alert
                        if (camera["flood_risk_level"] > 0.7 and 
                            (camera["last_alert"] is None or 
                             (datetime.now(timezone.utc) - camera["last_alert"]).total_seconds() > 3600)):  # 1 hour cooldown
                            await self._trigger_flood_alert(camera_id)
                            camera["last_alert"] = datetime.now(timezone.utc)
                    else:
                        logger.error(f"Failed to update camera {camera_id}: {await resp.text()}")
            except Exception as e:
                logger.error(f"Error updating camera {camera_id}: {e}")
    
    async def _trigger_flood_alert(self, camera_id: str):
        """Trigger a flood alert for a camera."""
        alert_url = f"{self.orion_url}entities/"
        camera = self.cameras[camera_id]
        alert_id = f"alert-{camera_id}-{int(datetime.now(timezone.utc).timestamp())}"
        
        alert = {
            "id": f"urn:ngsi-ld:Alert:{alert_id}",
            "type": "Alert",
            "category": {
                "type": "Property",
                "value": ["flood"]
            },
            "subCategory": {
                "type": "Property",
                "value": "flood_alert"
            },
            "severity": {
                "type": "Property",
                "value": "high" if camera["flood_risk_level"] > 0.8 else "medium"
            },
            "location": {
                "type": "GeoProperty",
                "value": camera["location"]
            },
            "dateIssued": {
                "type": "Property",
                "value": {
                    "@type": "DateTime",
                    "@value": datetime.now(timezone.utc).isoformat()
                }
            },
            "description": {
                "type": "Property",
                "value": f"Flood alert detected by camera {camera_id}"
            },
            "alertSource": {
                "type": "Property",
                "value": f"urn:ngsi-ld:Camera:{camera_id}"
            },
            "@context": [
                "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    alert_url,
                    headers=self.headers,
                    json=alert
                ) as resp:
                    if resp.status in (200, 201):
                        logger.warning(f"Flood alert created for camera {camera_id}")
                    else:
                        logger.error(f"Failed to create flood alert: {await resp.text()}")
            except Exception as e:
                logger.error(f"Error creating flood alert: {e}")
    
    async def _simulate_camera(self, camera_id: str):
        """Simulate a single camera's operation."""
        await self._create_camera_entity(camera_id)
        
        while self.running:
            try:
                # Only update if camera is active
                if self.cameras[camera_id]["status"] == "active":
                    # Update flood risk level
                    await self._update_flood_risk(camera_id)
                    
                    # Generate and save sample video frame
                    image_path = await self._generate_sample_video(camera_id)
                    
                    # Update camera data in Orion-LD
                    await self._update_camera_data(camera_id, image_path)
                
            except Exception as e:
                logger.error(f"Error in camera {camera_id} simulation: {e}")
            
            # Wait for next update
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the camera stream simulation."""
        self.running = True
        logger.info("Starting camera stream simulation...")
        
        # Start a task for each camera
        tasks = [
            asyncio.create_task(self._simulate_camera(camera_id))
            for camera_id in self.cameras
        ]
        
        # Keep the tasks running until stopped
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the simulation."""
        self.running = False
        logger.info("Stopping camera stream simulation...")
