import asyncio
import random
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import aiohttp

logger = logging.getLogger(__name__)

# ============================================================
# BOUNDING BOX 16 + bổ sung Quận 2 (bị thiếu trong bản gốc)
# ============================================================
district_bounds = {
    "Quận 1":      (106.690, 106.710, 10.760, 10.785),
    "Quận 2":      (106.760, 106.820, 10.760, 10.830),  # <-- THÊM
    "Quận 3":      (106.680, 106.700, 10.760, 10.785),
    "Quận 4":      (106.700, 106.720, 10.745, 10.770),
    "Quận 5":      (106.655, 106.675, 10.745, 10.770),
    "Quận 6":      (106.630, 106.660, 10.730, 10.760),
    "Quận 7":      (106.700, 106.740, 10.700, 10.750),
    "Quận 8":      (106.630, 106.680, 10.700, 10.740),
    "Quận 10":     (106.650, 106.680, 10.750, 10.780),
    "Quận 11":     (106.630, 106.670, 10.745, 10.780),
    "Quận 12":     (106.640, 106.750, 10.850, 10.900),
    "Tân Bình":    (106.640, 106.680, 10.780, 10.830),
    "Tân Phú":     (106.610, 106.650, 10.780, 10.830),
    "Phú Nhuận":   (106.670, 106.700, 10.790, 10.810),
    "Bình Thành":  (106.690, 106.740, 10.785, 10.850),
    "Gò Vấp":      (106.650, 106.710, 10.830, 10.900),
    "Thủ Đức":     (106.740, 106.820, 10.800, 10.900)
}

# phân bố theo nguy cơ ngập
district_weights = {
    "Bình Thành": 4, "Gò Vấp": 4, "Quận 6": 4, "Quận 8": 4,
    "Tân Bình": 4, "Tân Phú": 4,
    "Quận 1": 3, "Quận 3": 3, "Quận 5": 3, "Quận 10": 3, "Phú Nhuận": 3,
    "Quận 2": 2, "Quận 7": 2, "Thủ Đức": 2, "Quận 4": 2, "Quận 11": 2
}


def random_point(bounds):
    min_lng, max_lng, min_lat, max_lat = bounds
    return [
        round(random.uniform(min_lng, max_lng), 6),
        round(random.uniform(min_lat, max_lat), 6)
    ]


# ============================================================
# Sinh 50 sensors
# ============================================================
def create_sensors():
    sensors = {}
    districts = list(district_bounds.keys())
    weights = [district_weights.get(d, 1) for d in districts]  # tránh crash

    for i in range(50):
        sensor_id = f"sensor-{10000 + i}"
        district = random.choices(districts, weights)[0]
        coords = random_point(district_bounds[district])

        base = random.uniform(1.0, 2.2)
        var = random.uniform(0.3, 0.7)

        sensors[sensor_id] = {
            "district": district,
            "location": {
                "type": "Point",
                "coordinates": coords
            },
            "base_level": round(base, 2),
            "variation": round(var, 2),
            "alert_threshold": round(base + 1.0, 2)
        }

    return sensors


@dataclass
class WaterReading:
    value: float
    timestamp: str
    latitude: float
    longitude: float
    district: str
    status: str = "ok"


# ============================================================
# SIMULATOR
# ============================================================
class Simulator:

    def __init__(self, interval=60):
        self.interval = interval
        self.sensors = create_sensors()
        self.running = False

        self.orion = "http://orion-ld:1026/ngsi-ld/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
        }

        self.session = None  # dùng 1 session duy nhất

    def generate(self, sid):
        s = self.sensors[sid]
        v = s["base_level"] + random.uniform(-s["variation"], s["variation"])
        v = round(max(v, 0), 2)

        return WaterReading(
            value=v,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=s["location"]["coordinates"][1],
            longitude=s["location"]["coordinates"][0],
            district=s["district"]
        )

    async def create_entity(self, sid):
        url = f"{self.orion}/entities/urn:ngsi-ld:WaterLevelObserved:{sid}"

        r = await self.session.get(url, headers=self.headers)
        if r.status == 200:
            return  # đã tồn tại

        s = self.sensors[sid]
        entity = {
            "id": f"urn:ngsi-ld:WaterLevelObserved:{sid}",
            "type": "WaterLevelObserved",

            "district": {
                "type": "Property",
                "value": s["district"]
            },

            "location": {
                "type": "GeoProperty",
                "value": s["location"]
            },

            "waterLevel": {
                "type": "Property",
                "value": 0.0
            },

            "alertThreshold": {
                "type": "Property",
                "value": s["alert_threshold"]
            }
        }

        await self.session.post(f"{self.orion}/entities",
                                headers=self.headers,
                                json=entity)

    async def update(self, sid, reading: WaterReading):
        url = f"{self.orion}/entities/urn:ngsi-ld:WaterLevelObserved:{sid}/attrs"

        body = {
            "waterLevel": {
                "type": "Property",
                "value": reading.value,
                "unitCode": "MTR",
                "observedAt": reading.timestamp
            },
            "district": {
                "type": "Property",
                "value": reading.district
            },
            "status": {
                "type": "Property",
                "value": reading.status
            },
            "location": {
                "type": "GeoProperty",
                "value": {
                    "type": "Point",
                    "coordinates": [reading.longitude, reading.latitude]
                }
            }
        }

        await self.session.patch(url, headers=self.headers, json=body)

    async def simulate_sensor(self, sid):
        await self.create_entity(sid)

        while self.running:
            reading = self.generate(sid)
            await self.update(sid, reading)
            await asyncio.sleep(self.interval)

    async def start(self):
        self.running = True

        async with aiohttp.ClientSession() as sess:
            self.session = sess
            tasks = [asyncio.create_task(self.simulate_sensor(s)) for s in self.sensors]
            await asyncio.gather(*tasks)

    async def stop(self):
        self.running = False


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sim = Simulator(interval=60)

    try:
        asyncio.run(sim.start())
    except KeyboardInterrupt:
        asyncio.run(sim.stop())
