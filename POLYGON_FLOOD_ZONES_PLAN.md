# 🌊 Phương án Polygon Flood Zones - FloodWatch

> **Mục tiêu**: Thay thế các vùng tròn (circle) không thực tế bằng polygon zones dựa trên dữ liệu ngập thực tế của TP.HCM, kết hợp với circle nhỏ cho báo cáo cộng đồng.

---

## 📋 Mục lục

1. [Tổng quan phương án](#1-tổng-quan-phương-án)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Định nghĩa Flood Zones](#3-định-nghĩa-flood-zones)
4. [Thiết kế Simulation](#4-thiết-kế-simulation)
5. [Thay đổi Frontend](#5-thay-đổi-frontend)
6. [Thay đổi Data Format](#6-thay-đổi-data-format)
7. [Kế hoạch triển khai](#7-kế-hoạch-triển-khai)

---

## 1. Tổng quan phương án

### 1.1 Vấn đề hiện tại

```
❌ Hiện tại: Vùng ngập = Vòng tròn với bán kính 250-800m
   - Không thực tế (nước không lan tròn đều)
   - Bán kính quá lớn
   - Không phản ánh địa hình thực tế
```

### 1.2 Giải pháp: Hybrid Polygon System

```
✅ Giải pháp:
   - Sensor Zones: Polygon thực tế cho các khu vực hay ngập
   - Community Reports: Circle nhỏ (30-80m) cho báo cáo người dân
```

### 1.3 So sánh trực quan

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRƯỚC                                   │
│                                                                 │
│              ╭───────────────╮                                  │
│             ╱                 ╲     ← Vòng tròn lớn             │
│            │        ●         │       không thực tế             │
│             ╲                 ╱                                  │
│              ╰───────────────╯                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                          SAU                                    │
│                                                                 │
│         ╔══════════════════╗                                    │
│         ║    POLYGON       ║  ← Vùng ngập thực tế               │
│         ║   (theo đường)   ║    dạng dải dọc đường              │
│         ╚══════════════════╝                                    │
│                                                                 │
│              ⬤  ← Circle nhỏ (50m) cho báo cáo người dân       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Kiến trúc hệ thống

### 2.1 Những gì GIỮ NGUYÊN

| Component | Trạng thái | Ghi chú |
|-----------|------------|---------|
| Orion-LD | ✅ Giữ nguyên | Context broker không đổi |
| Backend FastAPI | ✅ Giữ nguyên | API endpoints không đổi |
| WebSocket | ✅ Giữ nguyên | Real-time push không đổi |
| useFloodData hook | ✅ Giữ nguyên | Hook lấy data không đổi |

### 2.2 Những gì THAY ĐỔI

| Component | Thay đổi | Chi tiết |
|-----------|----------|----------|
| Simulator | 🔧 Sửa | Tạo data gắn với polygon zones |
| LeafletMap | 🔧 Sửa | Thêm logic vẽ polygon |
| Types | 🔧 Sửa | Thêm polygon field |
| flood-zones.ts | ➕ Mới | Define các polygon zones |

### 2.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │ flood-zones  │ ← Định nghĩa polygon zones                    │
│  │    (new)     │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Simulator   │───►│ Orion-LD │───►│ Backend  │              │
│  │   (sửa)      │    │  (giữ)   │    │  (giữ)   │              │
│  └──────────────┘    └──────────┘    └────┬─────┘              │
│                                           │                     │
│                                           ▼                     │
│                                    ┌──────────────┐             │
│                                    │  WebSocket   │             │
│                                    │    (giữ)     │             │
│                                    └──────┬───────┘             │
│                                           │                     │
│                                           ▼                     │
│  ┌──────────────┐                  ┌──────────────┐             │
│  │ flood-zones  │◄────────────────►│ LeafletMap   │             │
│  │  (frontend)  │  Lookup polygon  │    (sửa)     │             │
│  └──────────────┘                  └──────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Định nghĩa Flood Zones

### 3.1 Danh sách 15 Flood Zones thực tế TPHCM

Dựa trên dữ liệu ngập thực tế từ các nguồn:
- Báo cáo triều cường TP.HCM
- Danh sách điểm ngập của Sở GTVT
- Thông tin từ VnExpress, Báo Mới

#### **Nhóm 1: Vùng ven sông, ảnh hưởng triều cường**

| Zone ID | Tên | Quận | Mức nguy cơ | Mực nước thường |
|---------|-----|------|-------------|-----------------|
| `zone-q4-tran-xuan-soan` | Đường Trần Xuân Soạn | Quận 4 | 🔴 Severe | 0.3 - 0.5m |
| `zone-q7-huynh-tan-phat` | Đường Huỳnh Tấn Phát | Quận 7 | 🔴 Severe | 0.25 - 0.45m |
| `zone-q8-au-duong-lan` | Đường Âu Dương Lân | Quận 8 | 🟠 High | 0.2 - 0.4m |
| `zone-nhabe-nguyen-binh` | Đường Nguyễn Bình | Nhà Bè | 🔴 Severe | 0.3 - 0.5m |

#### **Nhóm 2: Vùng trũng, nền yếu**

| Zone ID | Tên | Quận | Mức nguy cơ | Mực nước thường |
|---------|-----|------|-------------|-----------------|
| `zone-binhchanh-quoc-lo-50` | Quốc lộ 50 | Bình Chánh | 🟠 High | 0.15 - 0.35m |
| `zone-binhchanh-an-suong` | Ngã tư An Sương | Bình Chánh | 🟠 High | 0.2 - 0.35m |
| `zone-q8-pham-hung` | Đường Phạm Hùng | Quận 8 | 🟠 High | 0.2 - 0.4m |

#### **Nhóm 3: Nội đô, ngập cục bộ khi mưa**

| Zone ID | Tên | Quận | Mức nguy cơ | Mực nước thường |
|---------|-----|------|-------------|-----------------|
| `zone-q1-calmette` | Đường Calmette | Quận 1 | 🟡 Medium | 0.1 - 0.25m |
| `zone-q1-nguyen-thai-binh` | Đường Nguyễn Thái Bình | Quận 1 | 🟡 Medium | 0.1 - 0.2m |
| `zone-q1-co-giang` | Đường Cô Giang | Quận 1 | 🟡 Medium | 0.1 - 0.25m |
| `zone-binhthanh-xo-viet-nghe-tinh` | Xô Viết Nghệ Tĩnh | Bình Thạnh | 🟠 High | 0.15 - 0.3m |

#### **Nhóm 4: Thủ Đức và vùng phụ cận**

| Zone ID | Tên | Quận | Mức nguy cơ | Mực nước thường |
|---------|-----|------|-------------|-----------------|
| `zone-thuduc-do-xuan-hop` | Đường Đỗ Xuân Hợp | Thủ Đức | 🟠 High | 0.15 - 0.35m |
| `zone-thuduc-nguyen-duy-trinh` | Đường Nguyễn Duy Trinh | Thủ Đức | 🟡 Medium | 0.1 - 0.25m |
| `zone-govap-pham-van-dong` | Đường Phạm Văn Đồng | Gò Vấp | 🟡 Medium | 0.1 - 0.25m |
| `zone-tanbinh-truong-chinh` | Đường Trường Chinh | Tân Bình | 🟡 Medium | 0.1 - 0.2m |

### 3.2 Cấu trúc dữ liệu Flood Zone

```typescript
// client/src/data/flood-zones.ts

export interface FloodZone {
  id: string;
  name: string;
  district: string;
  
  // Polygon coordinates [lat, lng][]
  polygon: [number, number][];
  
  // Điểm trung tâm (để đặt marker/sensor)
  center: [number, number];
  
  // Đặc tính địa hình
  properties: {
    elevation: "low" | "medium" | "high";
    nearRiver: boolean;
    drainage: "poor" | "moderate" | "good";
  };
  
  // Tham số simulation
  simulation: {
    baseLevel: number;        // Mực nước cơ bản (m)
    tidalSensitivity: number; // Độ nhạy triều (0-1)
    rainSensitivity: number;  // Độ nhạy mưa (0-1)
    drainRate: number;        // Tốc độ thoát nước (0-1)
  };
  
  // Mức nguy cơ mặc định
  defaultRisk: "low" | "medium" | "high" | "severe";
}

export const FLOOD_ZONES: Record<string, FloodZone> = {
  "zone-q4-tran-xuan-soan": {
    id: "zone-q4-tran-xuan-soan",
    name: "Đường Trần Xuân Soạn",
    district: "Quận 4",
    polygon: [
      [10.7573, 106.7015],
      [10.7582, 106.7028],
      [10.7612, 106.7045],
      [10.7621, 106.7038],
      [10.7615, 106.7022],
      [10.7585, 106.7008],
      [10.7573, 106.7015],
    ],
    center: [10.7595, 106.7025],
    properties: {
      elevation: "low",
      nearRiver: true,
      drainage: "poor",
    },
    simulation: {
      baseLevel: 0.15,
      tidalSensitivity: 0.9,
      rainSensitivity: 0.8,
      drainRate: 0.5,
    },
    defaultRisk: "severe",
  },
  
  // ... các zone khác
};
```

### 3.3 Bản đồ tổng quan các Zone

```
┌─────────────────────────────────────────────────────────────────┐
│                    TP. HỒ CHÍ MINH                              │
│                                                                 │
│                         ┌─────┐                                 │
│                         │Tân  │ ← zone-tanbinh-truong-chinh     │
│                         │Bình │                                 │
│     ┌─────┐             └──┬──┘                                 │
│     │Bình │                │        ┌──────┐                    │
│     │Chánh│◄───────────────┼───────►│Gò Vấp│                    │
│     └──┬──┘                │        └──────┘                    │
│        │                   │           │                        │
│        │              ┌────┴────┐      │     ┌────────┐         │
│        │              │ Quận 1  │◄─────┼────►│Bình    │         │
│        │              │(3 zones)│      │     │Thạnh   │         │
│        │              └────┬────┘      │     └────────┘         │
│        │                   │           │                        │
│   ┌────┴────┐         ┌────┴────┐      │     ┌────────┐         │
│   │ Quận 8  │◄───────►│ Quận 4  │      └────►│Thủ Đức │         │
│   │(2 zones)│         │(1 zone) │            │(2 zones)│        │
│   └────┬────┘         └────┬────┘            └────────┘         │
│        │                   │                                    │
│        │              ┌────┴────┐                               │
│        └─────────────►│ Quận 7  │                               │
│                       │(1 zone) │                               │
│                       └────┬────┘                               │
│                            │                                    │
│                       ┌────┴────┐                               │
│                       │ Nhà Bè  │                               │
│                       │(1 zone) │                               │
│                       └─────────┘                               │
│                                                                 │
│  🔴 Severe (4)  🟠 High (5)  🟡 Medium (6)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Thiết kế Simulation

### 4.1 Các yếu tố ảnh hưởng mực nước

```
┌─────────────────────────────────────────────────────────────────┐
│                  YẾU TỐ ẢNH HƯỞNG MỰC NƯỚC                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🌙 TRIỀU CƯỜNG                                                 │
│     - Chu kỳ thực tế: ~12 giờ                                   │
│     - Chu kỳ demo: 15-20 phút                                   │
│     - Ảnh hưởng: Vùng ven sông (tidalSensitivity cao)           │
│     - Pattern: sin wave, dâng từ từ → đỉnh → rút từ từ          │
│                                                                 │
│  🌧️ MƯA LỚN                                                     │
│     - Thời gian thực: 30-60 phút                                │
│     - Thời gian demo: 3-5 phút                                  │
│     - Ảnh hưởng: Tất cả zones (rainSensitivity)                 │
│     - Pattern: dâng nhanh → đỉnh → rút chậm                     │
│                                                                 │
│  💧 THOÁT NƯỚC                                                  │
│     - Phụ thuộc: drainRate của từng zone                        │
│     - Vùng trũng: rút chậm (drainRate thấp)                     │
│     - Vùng cao: rút nhanh (drainRate cao)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Cấu hình Simulation

```python
# ============================================================
# CẤU HÌNH SIMULATION
# ============================================================

# Thời gian cập nhật
UPDATE_INTERVAL = 20              # Cập nhật mỗi 20 giây

# Chu kỳ triều cường (demo)
TIDAL_CYCLE_MINUTES = 15          # 15 phút = 1 chu kỳ triều
TIDAL_AMPLITUDE = 0.25            # Biên độ triều: ±25cm

# Sự kiện mưa
RAIN_EVENT_INTERVAL = 8           # Mưa random mỗi ~8 phút
RAIN_DURATION_MINUTES = 4         # Mỗi trận mưa kéo dài 4 phút
RAIN_INTENSITY_MAX = 0.35         # Mực nước tăng tối đa 35cm

# Mực nước
WATER_LEVEL_MIN = 0.03            # Tối thiểu 3cm
WATER_LEVEL_MAX = 0.80            # Tối đa 80cm

# Noise để realistic
NOISE_RANGE = 0.02                # ±2cm random noise

# Severity thresholds
SEVERITY_THRESHOLDS = {
    "low": (0.0, 0.15),           # 0-15cm
    "medium": (0.15, 0.25),       # 15-25cm
    "high": (0.25, 0.40),         # 25-40cm
    "severe": (0.40, float('inf')) # >40cm
}
```

### 4.3 Các kịch bản Simulation

```python
class SimulationScenario:
    """
    3 kịch bản chính, tự động xoay vòng
    """
    
    NORMAL = {
        "name": "Bình thường",
        "description": "Mực nước ổn định, thấp",
        "duration_minutes": 5,
        "water_level_modifier": 0.0,
    }
    
    TIDAL = {
        "name": "Triều cường", 
        "description": "Nước dâng do triều",
        "phases": [
            {"name": "rising", "duration_min": 6, "rate": +0.04},
            {"name": "peak", "duration_min": 3, "rate": 0.0},
            {"name": "falling", "duration_min": 6, "rate": -0.03},
        ],
        "affected_zones": ["nearRiver = true"],
    }
    
    HEAVY_RAIN = {
        "name": "Mưa lớn",
        "description": "Ngập do mưa",
        "phases": [
            {"name": "start", "duration_min": 1, "rate": +0.06},
            {"name": "peak", "duration_min": 2, "rate": +0.10},
            {"name": "easing", "duration_min": 1, "rate": +0.02},
            {"name": "draining", "duration_min": 4, "rate": -0.04},
        ],
        "affected_zones": ["all"],
    }
```

### 4.4 Công thức tính mực nước

```python
def calculate_water_level(zone: FloodZone, scenario: str, elapsed_time: float) -> float:
    """
    Tính mực nước cho một zone tại thời điểm t
    """
    base = zone.simulation.baseLevel
    
    # 1. Yếu tố triều cường (sin wave)
    tidal_cycle = (elapsed_time / (TIDAL_CYCLE_MINUTES * 60)) * 2 * math.pi
    tidal_effect = TIDAL_AMPLITUDE * math.sin(tidal_cycle) * zone.simulation.tidalSensitivity
    
    # 2. Yếu tố mưa (nếu đang có sự kiện mưa)
    rain_effect = 0.0
    if is_raining:
        rain_effect = current_rain_intensity * zone.simulation.rainSensitivity
    
    # 3. Yếu tố thoát nước (giảm dần sau mưa)
    drain_effect = calculate_drain(zone.simulation.drainRate, time_since_rain)
    
    # 4. Noise ngẫu nhiên
    noise = random.uniform(-NOISE_RANGE, NOISE_RANGE)
    
    # Tổng hợp
    water_level = base + tidal_effect + rain_effect - drain_effect + noise
    
    # Clamp trong khoảng hợp lệ
    return max(WATER_LEVEL_MIN, min(water_level, WATER_LEVEL_MAX))
```

### 4.5 Timeline Demo điển hình (30 phút)

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIMELINE DEMO 30 PHÚT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Thời gian   Sự kiện              Mực nước TB    Severity       │
│  ─────────────────────────────────────────────────────────────  │
│  00:00       Khởi động            0.08m          🟢 Low         │
│  00:00-05:00 Bình thường          0.05-0.12m     🟢 Low         │
│  ─────────────────────────────────────────────────────────────  │
│  05:00       🌙 Triều bắt đầu                                   │
│  05:00-11:00 Triều dâng           0.15→0.35m     🟡→🟠          │
│  11:00-14:00 Đỉnh triều           0.30-0.40m     🟠 High        │
│  14:00-20:00 Triều rút            0.35→0.15m     🟠→🟡          │
│  ─────────────────────────────────────────────────────────────  │
│  20:00       🌧️ Mưa lớn bắt đầu                                 │
│  20:00-22:00 Mưa to               0.20→0.45m     🟡→🔴          │
│  22:00-24:00 Đỉnh ngập            0.40-0.55m     🔴 Severe      │
│  24:00-30:00 Thoát nước           0.50→0.20m     🔴→🟡          │
│  ─────────────────────────────────────────────────────────────  │
│  30:00       Về bình thường       0.10m          🟢 Low         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Biểu đồ mực nước:

0.6m ┤                              ╭─╮
     │                             ╱   ╲
0.5m ┤                            ╱     ╲
     │                           ╱       ╲
0.4m ┤              ╭────╮      ╱         ╲
     │             ╱      ╲    ╱           ╲
0.3m ┤           ╱        ╲  ╱             ╲
     │          ╱          ╲╱               ╲
0.2m ┤        ╱                              ╲
     │       ╱                                ╲
0.1m ┤──────╱                                  ╲────
     │
0.0m ┼─────┬─────┬─────┬─────┬─────┬─────┬─────┬────►
     0     5    10    15    20    25    30   (phút)
         
         │←── Triều ──→│    │←─── Mưa ───→│
```

---

## 5. Thay đổi Frontend

### 5.1 Cập nhật LeafletMap.tsx

```typescript
// LeafletMap.tsx - Thêm logic vẽ polygon

import { FLOOD_ZONES } from "@/data/flood-zones";

// Trong useEffect vẽ flood zones:
floodPoints.forEach((point) => {
  const zoneId = point.zoneId;
  const zone = zoneId ? FLOOD_ZONES[zoneId] : null;
  
  if (zone && point.type === "sensor") {
    // ========================================
    // VẼ POLYGON cho sensor zones
    // ========================================
    const polygon = L.polygon(zone.polygon, {
      color: severityColors[point.severity],
      fillColor: severityColors[point.severity],
      fillOpacity: 0.25,
      weight: 2,
      opacity: 0.8,
    });
    
    polygon.bindPopup(`
      <div class="p-2">
        <p class="font-semibold">${zone.name}</p>
        <p class="text-sm text-muted">${zone.district}</p>
        <p>Mực nước: ${point.waterLevel}m</p>
      </div>
    `);
    
    polygon.on("click", () => onSelectPoint(point));
    polygon.addTo(map);
    polygonsRef.current.push(polygon);
    
    // Marker tại center
    const marker = L.marker(zone.center, {
      icon: createCustomIcon(point.severity, "sensor"),
    });
    marker.addTo(map);
    markersRef.current.push(marker);
    
  } else {
    // ========================================
    // VẼ CIRCLE NHỎ cho community reports
    // ========================================
    const radius = point.type === "community" ? 50 : 80; // 50-80m
    
    const circle = L.circle([point.lat, point.lng], {
      radius: radius,
      color: severityColors[point.severity],
      fillColor: severityColors[point.severity],
      fillOpacity: 0.4,
      weight: 2,
    });
    
    circle.addTo(map);
    circlesRef.current.push(circle);
    
    // Marker
    const marker = L.marker([point.lat, point.lng], {
      icon: createCustomIcon(point.severity, point.type),
    });
    marker.addTo(map);
    markersRef.current.push(marker);
  }
});
```

### 5.2 Cập nhật Types

```typescript
// types/index.ts

export interface FloodPoint {
  id: string;
  lat: number;
  lng: number;
  severity: "severe" | "high" | "medium" | "low";
  type: "sensor" | "community";
  waterLevel: number;
  location: string;
  updatedAt: string;
  
  // NEW: Zone reference (cho sensor)
  zoneId?: string;
  zoneName?: string;
  
  // NEW: Trend
  trend?: "rising" | "falling" | "stable";
}
```

### 5.3 Cấu trúc thư mục mới

```
client/src/
├── components/
│   └── map/
│       ├── LeafletMap.tsx      # 🔧 Sửa: thêm polygon logic
│       └── FloodMap.tsx        # ✅ Giữ nguyên
├── data/
│   └── flood-zones.ts          # ➕ MỚI: định nghĩa zones
├── types/
│   └── index.ts                # 🔧 Sửa: thêm zoneId, trend
└── hooks/
    └── useFloodData.ts         # ✅ Giữ nguyên
```

---

## 6. Thay đổi Data Format

### 6.1 Entity format trong Orion-LD

```json
{
  "id": "urn:ngsi-ld:WaterLevelObserved:zone-q4-tran-xuan-soan",
  "type": "WaterLevelObserved",
  
  "zoneId": {
    "type": "Property",
    "value": "zone-q4-tran-xuan-soan"
  },
  
  "zoneName": {
    "type": "Property", 
    "value": "Đường Trần Xuân Soạn"
  },
  
  "district": {
    "type": "Property",
    "value": "Quận 4"
  },
  
  "location": {
    "type": "GeoProperty",
    "value": {
      "type": "Point",
      "coordinates": [106.7025, 10.7595]
    }
  },
  
  "waterLevel": {
    "type": "Property",
    "value": 0.35,
    "unitCode": "MTR",
    "observedAt": "2024-12-07T10:30:00Z"
  },
  
  "waterTrend": {
    "type": "Property",
    "value": "rising"
  },
  
  "reportType": {
    "type": "Property",
    "value": "sensor"
  }
}
```

### 6.2 WebSocket message format

```json
{
  "type": "flood_update",
  "data": {
    "id": "zone-q4-tran-xuan-soan",
    "zoneId": "zone-q4-tran-xuan-soan",
    "zoneName": "Đường Trần Xuân Soạn",
    "lat": 10.7595,
    "lng": 106.7025,
    "waterLevel": 0.35,
    "severity": "high",
    "trend": "rising",
    "type": "sensor",
    "location": "Đường Trần Xuân Soạn, Quận 4",
    "updatedAt": "10:30"
  }
}
```

---

## 7. Kế hoạch triển khai

### 7.1 Các bước thực hiện

```
┌─────────────────────────────────────────────────────────────────┐
│                    KẾ HOẠCH TRIỂN KHAI                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BƯỚC 1: Tạo flood-zones.ts (Frontend)                         │
│  ────────────────────────────────────────                       │
│  - Định nghĩa 15 polygon zones                                  │
│  - Tọa độ polygon thực tế                                       │
│  - Tham số simulation cho mỗi zone                              │
│  Thời gian: ~1 giờ                                              │
│                                                                 │
│  BƯỚC 2: Cập nhật Simulator (Python)                            │
│  ────────────────────────────────────────                       │
│  - Import flood zones data                                      │
│  - Logic triều cường + mưa                                      │
│  - Tạo entity cho mỗi zone                                      │
│  Thời gian: ~1-2 giờ                                            │
│                                                                 │
│  BƯỚC 3: Cập nhật LeafletMap (Frontend)                         │
│  ────────────────────────────────────────                       │
│  - Thêm logic vẽ polygon                                        │
│  - Giữ circle cho community reports                             │
│  - Style cho polygon                                            │
│  Thời gian: ~1 giờ                                              │
│                                                                 │
│  BƯỚC 4: Test & Điều chỉnh                                      │
│  ────────────────────────────────────────                       │
│  - Chạy simulation                                              │
│  - Kiểm tra hiển thị polygon                                    │
│  - Tinh chỉnh tham số                                           │
│  Thời gian: ~30 phút                                            │
│                                                                 │
│  TỔNG THỜI GIAN: ~3-4 giờ                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Checklist triển khai

- [ ] **Bước 1: flood-zones.ts**
  - [ ] Tạo file `client/src/data/flood-zones.ts`
  - [ ] Định nghĩa interface FloodZone
  - [ ] Thêm 15 zones với polygon coordinates
  - [ ] Thêm simulation parameters

- [ ] **Bước 2: Simulator**
  - [ ] Tạo file `flood_zones.py` trong simulator
  - [ ] Sửa `simulator.py` để dùng zones
  - [ ] Implement tidal cycle logic
  - [ ] Implement rain event logic
  - [ ] Test với Orion-LD

- [ ] **Bước 3: Frontend**
  - [ ] Cập nhật types với zoneId, trend
  - [ ] Import FLOOD_ZONES trong LeafletMap
  - [ ] Thêm polygon drawing logic
  - [ ] Giảm circle radius cho community
  - [ ] Style polygon với severity colors

- [ ] **Bước 4: Testing**
  - [ ] Chạy docker-compose
  - [ ] Verify polygon hiển thị đúng
  - [ ] Verify mực nước thay đổi hợp lý
  - [ ] Verify severity colors đúng
  - [ ] Test responsive trên mobile

---

## 📎 Phụ lục

### A. Tọa độ polygon mẫu

```typescript
// Ví dụ polygon cho Đường Trần Xuân Soạn, Q4
// Dạng dải dọc theo đường
const TRAN_XUAN_SOAN_POLYGON = [
  [10.7568, 106.7012],  // Điểm 1 - đầu đường
  [10.7575, 106.7018],  // Điểm 2
  [10.7585, 106.7025],  // Điểm 3
  [10.7598, 106.7035],  // Điểm 4
  [10.7612, 106.7048],  // Điểm 5 - cuối đường
  [10.7618, 106.7042],  // Điểm 6 - bên kia đường
  [10.7605, 106.7030],  // Điểm 7
  [10.7592, 106.7020],  // Điểm 8
  [10.7580, 106.7012],  // Điểm 9
  [10.7568, 106.7012],  // Đóng polygon
];
```

### B. Severity thresholds

| Severity | Mực nước | Màu | Mô tả |
|----------|----------|-----|-------|
| Low | 0 - 15cm | 🟢 #22c55e | An toàn, nước rút |
| Medium | 15 - 25cm | 🟡 #eab308 | Cẩn thận, ngập nhẹ |
| High | 25 - 40cm | 🟠 #f97316 | Nguy hiểm, hạn chế đi lại |
| Severe | > 40cm | 🔴 #ef4444 | Rất nguy hiểm, không đi qua |

### C. Tham khảo

- Danh sách điểm ngập TPHCM: Sở GTVT TP.HCM
- Dữ liệu triều cường: Đài Khí tượng Thủy văn Nam Bộ
- Bản đồ ngập: VnExpress, Báo Mới

---

> **Ghi chú**: File này là tài liệu thiết kế. Khi triển khai, các tọa độ polygon cần được điều chỉnh chính xác hơn dựa trên bản đồ thực tế.
