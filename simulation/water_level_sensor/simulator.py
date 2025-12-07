"""
FloodWatch - Water Level Sensor Simulator
Phiên bản mới với Polygon Flood Zones

Tính năng:
- Sử dụng 15 vùng ngập thực tế TP.HCM
- Mô phỏng triều cường (chu kỳ 15 phút demo)
- Mô phỏng sự kiện mưa (random, kéo dài 4 phút)
- Mực nước biến đổi thực tế theo từng zone
"""

import asyncio
import random
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import aiohttp

from flood_zones import (
    FLOOD_ZONES,
    FloodZone,
    get_severity_from_water_level,
    get_all_zone_ids,
)

logger = logging.getLogger(__name__)


# ============================================================
# CẤU HÌNH SIMULATION
# ============================================================

# Thời gian cập nhật
UPDATE_INTERVAL = 20  # Cập nhật mỗi 20 giây

# Chu kỳ triều cường (demo)
TIDAL_CYCLE_MINUTES = 15  # 15 phút = 1 chu kỳ triều
TIDAL_AMPLITUDE = 0.25    # Biên độ triều: ±25cm

# Sự kiện mưa
RAIN_EVENT_CHANCE = 0.02      # 2% mỗi update cycle để bắt đầu mưa
RAIN_DURATION_MINUTES = 4     # Mỗi trận mưa kéo dài 4 phút
RAIN_INTENSITY_MAX = 0.35     # Mực nước tăng tối đa 35cm do mưa

# Mực nước
WATER_LEVEL_MIN = 0.03  # Tối thiểu 3cm
WATER_LEVEL_MAX = 0.80  # Tối đa 80cm

# Noise để realistic
NOISE_RANGE = 0.02  # ±2cm random noise


# ============================================================
# SIMULATION SCENARIO
# ============================================================

class ScenarioPhase(Enum):
    NORMAL = "normal"
    TIDAL_RISING = "tidal_rising"
    TIDAL_PEAK = "tidal_peak"
    TIDAL_FALLING = "tidal_falling"
    RAIN_START = "rain_start"
    RAIN_PEAK = "rain_peak"
    RAIN_EASING = "rain_easing"
    DRAINING = "draining"


@dataclass
class RainEvent:
    """Sự kiện mưa"""
    start_time: datetime
    duration_minutes: float
    intensity: float  # 0-1
    is_active: bool = True
    
    def get_current_intensity(self, current_time: datetime) -> float:
        """Tính cường độ mưa hiện tại (bell curve)"""
        if not self.is_active:
            return 0.0
        
        elapsed = (current_time - self.start_time).total_seconds() / 60
        if elapsed > self.duration_minutes:
            self.is_active = False
            return 0.0
        
        # Bell curve: peak ở giữa
        progress = elapsed / self.duration_minutes
        # Parabolic: 4 * p * (1 - p) gives max=1 at p=0.5
        curve = 4 * progress * (1 - progress)
        return self.intensity * curve


@dataclass
class ZoneState:
    """Trạng thái của một zone"""
    zone: FloodZone
    current_level: float
    trend: str  # "rising", "falling", "stable"
    last_level: float
    rain_accumulation: float = 0.0


@dataclass
class WaterReading:
    """Reading từ một zone"""
    zone_id: str
    zone_name: str
    value: float
    timestamp: str
    latitude: float
    longitude: float
    district: str
    severity: str
    trend: str


# ============================================================
# SIMULATOR CLASS
# ============================================================

class Simulator:
    """
    Simulator tạo dữ liệu mực nước thực tế cho 15 polygon zones:
    - Triều cường: chu kỳ sin, ảnh hưởng zones ven sông
    - Mưa: random events, ảnh hưởng tất cả zones
    - Thoát nước: phụ thuộc drain_rate của từng zone
    """

    def __init__(self, interval: int = UPDATE_INTERVAL):
        self.interval = interval
        self.running = False
        self.start_time: datetime | None = None
        
        # Khởi tạo state cho mỗi zone
        self.zone_states: dict[str, ZoneState] = {}
        for zone_id, zone in FLOOD_ZONES.items():
            self.zone_states[zone_id] = ZoneState(
                zone=zone,
                current_level=zone.simulation.base_level,
                trend="stable",
                last_level=zone.simulation.base_level,
            )
        
        # Rain events
        self.current_rain: RainEvent | None = None
        self.rain_cooldown = 0  # Cooldown sau mưa (số update cycles)
        
        # Orion-LD connection
        self.orion = "http://orion-ld:1026/ngsi-ld/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
        }
        self.session: aiohttp.ClientSession | None = None
        
        logger.info(f"Initialized simulator with {len(FLOOD_ZONES)} zones, {interval}s interval")

    def _calculate_tidal_effect(self, elapsed_seconds: float, zone: FloodZone) -> float:
        """
        Tính hiệu ứng triều cường
        - Chu kỳ sin với period = TIDAL_CYCLE_MINUTES
        - Ảnh hưởng theo tidalSensitivity của zone
        """
        cycle_progress = (elapsed_seconds / (TIDAL_CYCLE_MINUTES * 60)) * 2 * math.pi
        tidal_wave = math.sin(cycle_progress)
        return TIDAL_AMPLITUDE * tidal_wave * zone.simulation.tidal_sensitivity

    def _calculate_rain_effect(self, zone: FloodZone, state: ZoneState) -> float:
        """
        Tính hiệu ứng mưa
        - Dựa trên current_rain intensity và rainSensitivity của zone
        - Tích lũy dần khi mưa, thoát dần khi ngưng
        """
        if self.current_rain and self.current_rain.is_active:
            now = datetime.now(timezone.utc)
            rain_intensity = self.current_rain.get_current_intensity(now)
            
            # Tích lũy nước mưa
            accumulation_rate = rain_intensity * zone.simulation.rain_sensitivity * 0.15
            state.rain_accumulation = min(
                state.rain_accumulation + accumulation_rate,
                RAIN_INTENSITY_MAX
            )
        else:
            # Thoát nước dần
            drain_amount = zone.simulation.drain_rate * 0.03
            state.rain_accumulation = max(0, state.rain_accumulation - drain_amount)
        
        return state.rain_accumulation

    def _maybe_start_rain(self):
        """Random check để bắt đầu sự kiện mưa"""
        if self.current_rain and self.current_rain.is_active:
            return  # Đang mưa rồi
        
        if self.rain_cooldown > 0:
            self.rain_cooldown -= 1
            return
        
        if random.random() < RAIN_EVENT_CHANCE:
            self.current_rain = RainEvent(
                start_time=datetime.now(timezone.utc),
                duration_minutes=RAIN_DURATION_MINUTES + random.uniform(-1, 1),
                intensity=random.uniform(0.6, 1.0),
            )
            self.rain_cooldown = int((RAIN_DURATION_MINUTES * 60 / self.interval) * 2)
            logger.info(f"🌧️ MƯA BẮT ĐẦU! Intensity: {self.current_rain.intensity:.2f}")

    def generate_reading(self, zone_id: str) -> WaterReading:
        """Sinh reading cho một zone"""
        state = self.zone_states[zone_id]
        zone = state.zone
        
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # 1. Base level
        base = zone.simulation.base_level
        
        # 2. Tidal effect
        tidal = self._calculate_tidal_effect(elapsed, zone)
        
        # 3. Rain effect
        rain = self._calculate_rain_effect(zone, state)
        
        # 4. Random noise
        noise = random.uniform(-NOISE_RANGE, NOISE_RANGE)
        
        # Tổng hợp
        new_level = base + tidal + rain + noise
        new_level = max(WATER_LEVEL_MIN, min(new_level, WATER_LEVEL_MAX))
        new_level = round(new_level, 2)
        
        # Xác định trend
        change = new_level - state.last_level
        if change > 0.02:
            trend = "rising"
        elif change < -0.02:
            trend = "falling"
        else:
            trend = "stable"
        
        # Cập nhật state
        state.last_level = state.current_level
        state.current_level = new_level
        state.trend = trend
        
        # Severity
        severity = get_severity_from_water_level(new_level)
        
        return WaterReading(
            zone_id=zone_id,
            zone_name=zone.name,
            value=new_level,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=zone.center[0],
            longitude=zone.center[1],
            district=zone.district,
            severity=severity,
            trend=trend,
        )

    async def create_entity(self, zone_id: str):
        """Tạo entity trên Orion-LD nếu chưa tồn tại"""
        entity_id = f"urn:ngsi-ld:WaterLevelObserved:{zone_id}"
        url = f"{self.orion}/entities/{entity_id}"
        
        try:
            r = await self.session.get(url, headers=self.headers)
            if r.status == 200:
                logger.debug(f"Entity {zone_id} already exists")
                return
        except Exception:
            pass
        
        zone = FLOOD_ZONES[zone_id]
        entity = {
            "id": entity_id,
            "type": "WaterLevelObserved",
            
            "zoneId": {
                "type": "Property",
                "value": zone_id
            },
            
            "zoneName": {
                "type": "Property",
                "value": zone.name
            },
            
            "district": {
                "type": "Property",
                "value": zone.district
            },
            
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": [zone.center[1], zone.center[0]]  # [lng, lat]
                }
            },
            
            "waterLevel": {
                "type": "Property",
                "value": zone.simulation.base_level,
                "unitCode": "MTR"
            },
            
            "waterTrend": {
                "type": "Property",
                "value": "stable"
            },
            
            "reportType": {
                "type": "Property",
                "value": "sensor"
            }
        }
        
        try:
            await self.session.post(
                f"{self.orion}/entities",
                headers=self.headers,
                json=entity
            )
            logger.info(f"✅ Created entity: {zone.name} ({zone.district})")
        except Exception as e:
            logger.error(f"Failed to create entity {zone_id}: {e}")

    async def update_entity(self, reading: WaterReading):
        """Cập nhật entity trên Orion-LD"""
        entity_id = f"urn:ngsi-ld:WaterLevelObserved:{reading.zone_id}"
        url = f"{self.orion}/entities/{entity_id}/attrs"
        
        body = {
            "waterLevel": {
                "type": "Property",
                "value": reading.value,
                "unitCode": "MTR",
                "observedAt": reading.timestamp
            },
            "waterTrend": {
                "type": "Property",
                "value": reading.trend
            },
            "district": {
                "type": "Property",
                "value": reading.district
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": [reading.longitude, reading.latitude]
                }
            }
        }
        
        try:
            await self.session.patch(url, headers=self.headers, json=body)
            
            # Log với emoji theo severity
            severity_emoji = {
                "severe": "🔴",
                "high": "🟠", 
                "medium": "🟡",
                "low": "🟢"
            }
            trend_arrow = {"rising": "↑", "falling": "↓", "stable": "→"}
            
            logger.info(
                f"{severity_emoji.get(reading.severity, '⚪')} "
                f"[{reading.zone_name}] "
                f"{reading.value:.2f}m {trend_arrow.get(reading.trend, '')} "
                f"({reading.severity})"
            )
        except Exception as e:
            logger.error(f"Failed to update {reading.zone_id}: {e}")

    async def simulate_zone(self, zone_id: str):
        """Vòng lặp mô phỏng cho một zone"""
        await self.create_entity(zone_id)
        
        while self.running:
            reading = self.generate_reading(zone_id)
            await self.update_entity(reading)
            await asyncio.sleep(self.interval)

    async def start(self):
        """Bắt đầu mô phỏng tất cả zones"""
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        
        zone_ids = get_all_zone_ids()
        
        logger.info("=" * 60)
        logger.info("🌊 FloodWatch Polygon Zone Simulator Started")
        logger.info(f"   Zones: {len(zone_ids)}")
        logger.info(f"   Update interval: {self.interval}s")
        logger.info(f"   Tidal cycle: {TIDAL_CYCLE_MINUTES} minutes")
        logger.info(f"   Rain duration: ~{RAIN_DURATION_MINUTES} minutes")
        logger.info("=" * 60)
        
        # List all zones
        for zone_id in zone_ids:
            zone = FLOOD_ZONES[zone_id]
            risk_emoji = {
                "severe": "🔴", "high": "🟠", 
                "medium": "🟡", "low": "🟢"
            }
            logger.info(
                f"   {risk_emoji.get(zone.default_risk, '⚪')} "
                f"{zone.name} ({zone.district})"
            )
        
        logger.info("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Tạo task cho mỗi zone
            tasks = []
            for zone_id in zone_ids:
                tasks.append(asyncio.create_task(self.simulate_zone(zone_id)))
            
            # Task để check rain events
            async def rain_checker():
                while self.running:
                    self._maybe_start_rain()
                    await asyncio.sleep(self.interval)
            
            tasks.append(asyncio.create_task(rain_checker()))
            
            await asyncio.gather(*tasks)

    async def stop(self):
        """Dừng mô phỏng"""
        self.running = False
        logger.info("Simulator stopped")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    sim = Simulator(interval=UPDATE_INTERVAL)
    
    try:
        asyncio.run(sim.start())
    except KeyboardInterrupt:
        asyncio.run(sim.stop())
