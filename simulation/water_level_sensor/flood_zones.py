"""
FloodWatch - Định nghĩa các vùng ngập thực tế TP.HCM

Dữ liệu dựa trên:
- Báo cáo triều cường TP.HCM
- Danh sách điểm ngập của Sở GTVT
- Thông tin từ VnExpress, Báo Mới
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Literal

RiskLevel = Literal["low", "medium", "high", "severe"]
Elevation = Literal["low", "medium", "high"]
Drainage = Literal["poor", "moderate", "good"]


@dataclass
class FloodZoneProperties:
    elevation: Elevation
    near_river: bool
    drainage: Drainage


@dataclass
class FloodZoneSimulation:
    base_level: float       # Mực nước cơ bản (m)
    tidal_sensitivity: float  # Độ nhạy triều (0-1)
    rain_sensitivity: float   # Độ nhạy mưa (0-1)
    drain_rate: float        # Tốc độ thoát nước (0-1)


@dataclass
class FloodZone:
    id: str
    name: str
    district: str
    polygon: List[Tuple[float, float]]  # [lat, lng][]
    center: Tuple[float, float]         # [lat, lng]
    properties: FloodZoneProperties
    simulation: FloodZoneSimulation
    default_risk: RiskLevel


# ============================================
# 15 FLOOD ZONES THỰC TẾ TPHCM
# ============================================

FLOOD_ZONES: Dict[str, FloodZone] = {
    # ========================================
    # NHÓM 1: Vùng ven sông, ảnh hưởng triều cường (Severe)
    # ========================================
    
    "zone-q4-tran-xuan-soan": FloodZone(
        id="zone-q4-tran-xuan-soan",
        name="Đường Trần Xuân Soạn",
        district="Quận 4",
        polygon=[
            (10.7568, 106.7012),
            (10.7575, 106.7018),
            (10.7585, 106.7028),
            (10.7598, 106.7040),
            (10.7612, 106.7055),
            (10.7620, 106.7048),
            (10.7608, 106.7035),
            (10.7595, 106.7022),
            (10.7582, 106.7012),
            (10.7568, 106.7012),
        ],
        center=(10.7592, 106.7030),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=True,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.15,
            tidal_sensitivity=0.9,
            rain_sensitivity=0.8,
            drain_rate=0.3,
        ),
        default_risk="severe",
    ),

    "zone-q7-huynh-tan-phat": FloodZone(
        id="zone-q7-huynh-tan-phat",
        name="Đường Huỳnh Tấn Phát",
        district="Quận 7",
        polygon=[
            (10.7320, 106.7180),
            (10.7335, 106.7195),
            (10.7360, 106.7220),
            (10.7380, 106.7240),
            (10.7390, 106.7230),
            (10.7372, 106.7210),
            (10.7350, 106.7188),
            (10.7332, 106.7170),
            (10.7320, 106.7180),
        ],
        center=(10.7355, 106.7205),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=True,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.12,
            tidal_sensitivity=0.85,
            rain_sensitivity=0.75,
            drain_rate=0.35,
        ),
        default_risk="severe",
    ),

    "zone-q8-au-duong-lan": FloodZone(
        id="zone-q8-au-duong-lan",
        name="Đường Âu Dương Lân",
        district="Quận 8",
        polygon=[
            (10.7380, 106.6550),
            (10.7395, 106.6565),
            (10.7420, 106.6590),
            (10.7440, 106.6610),
            (10.7450, 106.6600),
            (10.7432, 106.6580),
            (10.7410, 106.6558),
            (10.7390, 106.6540),
            (10.7380, 106.6550),
        ],
        center=(10.7415, 106.6575),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=True,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.10,
            tidal_sensitivity=0.80,
            rain_sensitivity=0.85,
            drain_rate=0.4,
        ),
        default_risk="high",
    ),

    "zone-nhabe-nguyen-binh": FloodZone(
        id="zone-nhabe-nguyen-binh",
        name="Đường Nguyễn Bình",
        district="Nhà Bè",
        polygon=[
            (10.6850, 106.7320),
            (10.6870, 106.7340),
            (10.6900, 106.7375),
            (10.6920, 106.7395),
            (10.6932, 106.7382),
            (10.6912, 106.7360),
            (10.6885, 106.7332),
            (10.6862, 106.7310),
            (10.6850, 106.7320),
        ],
        center=(10.6890, 106.7355),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=True,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.18,
            tidal_sensitivity=0.95,
            rain_sensitivity=0.7,
            drain_rate=0.25,
        ),
        default_risk="severe",
    ),

    # ========================================
    # NHÓM 2: Vùng trũng, nền yếu (High)
    # ========================================

    "zone-binhchanh-quoc-lo-50": FloodZone(
        id="zone-binhchanh-quoc-lo-50",
        name="Quốc lộ 50",
        district="Bình Chánh",
        polygon=[
            (10.6980, 106.6150),
            (10.6995, 106.6175),
            (10.7020, 106.6210),
            (10.7040, 106.6240),
            (10.7055, 106.6228),
            (10.7035, 106.6200),
            (10.7010, 106.6165),
            (10.6990, 106.6140),
            (10.6980, 106.6150),
        ],
        center=(10.7015, 106.6190),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=False,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.08,
            tidal_sensitivity=0.3,
            rain_sensitivity=0.9,
            drain_rate=0.35,
        ),
        default_risk="high",
    ),

    "zone-binhchanh-an-suong": FloodZone(
        id="zone-binhchanh-an-suong",
        name="Ngã tư An Sương",
        district="Bình Chánh",
        polygon=[
            (10.8620, 106.6150),
            (10.8640, 106.6170),
            (10.8665, 106.6195),
            (10.8680, 106.6180),
            (10.8665, 106.6160),
            (10.8645, 106.6140),
            (10.8625, 106.6135),
            (10.8620, 106.6150),
        ],
        center=(10.8650, 106.6165),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="poor",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.08,
            tidal_sensitivity=0.2,
            rain_sensitivity=0.85,
            drain_rate=0.45,
        ),
        default_risk="high",
    ),

    "zone-q8-pham-hung": FloodZone(
        id="zone-q8-pham-hung",
        name="Đường Phạm Hùng",
        district="Quận 8",
        polygon=[
            (10.7220, 106.6780),
            (10.7238, 106.6800),
            (10.7260, 106.6830),
            (10.7280, 106.6855),
            (10.7295, 106.6842),
            (10.7275, 106.6820),
            (10.7252, 106.6792),
            (10.7235, 106.6770),
            (10.7220, 106.6780),
        ],
        center=(10.7258, 106.6812),
        properties=FloodZoneProperties(
            elevation="low",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.10,
            tidal_sensitivity=0.5,
            rain_sensitivity=0.85,
            drain_rate=0.4,
        ),
        default_risk="high",
    ),

    # ========================================
    # NHÓM 3: Nội đô, ngập cục bộ khi mưa (Medium)
    # ========================================

    "zone-q1-calmette": FloodZone(
        id="zone-q1-calmette",
        name="Đường Calmette",
        district="Quận 1",
        polygon=[
            (10.7695, 106.6980),
            (10.7705, 106.6992),
            (10.7720, 106.7008),
            (10.7735, 106.7022),
            (10.7745, 106.7012),
            (10.7732, 106.6998),
            (10.7715, 106.6982),
            (10.7705, 106.6972),
            (10.7695, 106.6980),
        ],
        center=(10.7720, 106.6995),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.05,
            tidal_sensitivity=0.3,
            rain_sensitivity=0.7,
            drain_rate=0.6,
        ),
        default_risk="medium",
    ),

    "zone-q1-nguyen-thai-binh": FloodZone(
        id="zone-q1-nguyen-thai-binh",
        name="Đường Nguyễn Thái Bình",
        district="Quận 1",
        polygon=[
            (10.7720, 106.6950),
            (10.7732, 106.6962),
            (10.7748, 106.6978),
            (10.7760, 106.6968),
            (10.7748, 106.6955),
            (10.7735, 106.6942),
            (10.7720, 106.6950),
        ],
        center=(10.7740, 106.6960),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.05,
            tidal_sensitivity=0.25,
            rain_sensitivity=0.65,
            drain_rate=0.65,
        ),
        default_risk="medium",
    ),

    "zone-q1-co-giang": FloodZone(
        id="zone-q1-co-giang",
        name="Đường Cô Giang",
        district="Quận 1",
        polygon=[
            (10.7660, 106.6920),
            (10.7672, 106.6935),
            (10.7688, 106.6952),
            (10.7702, 106.6968),
            (10.7712, 106.6958),
            (10.7698, 106.6942),
            (10.7682, 106.6925),
            (10.7670, 106.6912),
            (10.7660, 106.6920),
        ],
        center=(10.7685, 106.6940),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.05,
            tidal_sensitivity=0.3,
            rain_sensitivity=0.7,
            drain_rate=0.55,
        ),
        default_risk="medium",
    ),

    "zone-binhthanh-xo-viet-nghe-tinh": FloodZone(
        id="zone-binhthanh-xo-viet-nghe-tinh",
        name="Xô Viết Nghệ Tĩnh",
        district="Bình Thạnh",
        polygon=[
            (10.8020, 106.7050),
            (10.8040, 106.7068),
            (10.8065, 106.7090),
            (10.8085, 106.7110),
            (10.8098, 106.7098),
            (10.8078, 106.7078),
            (10.8055, 106.7058),
            (10.8035, 106.7042),
            (10.8020, 106.7050),
        ],
        center=(10.8058, 106.7075),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.08,
            tidal_sensitivity=0.4,
            rain_sensitivity=0.8,
            drain_rate=0.5,
        ),
        default_risk="high",
    ),

    # ========================================
    # NHÓM 4: Thủ Đức và vùng phụ cận (Medium-High)
    # ========================================

    "zone-thuduc-do-xuan-hop": FloodZone(
        id="zone-thuduc-do-xuan-hop",
        name="Đường Đỗ Xuân Hợp",
        district="Thủ Đức",
        polygon=[
            (10.8180, 106.7650),
            (10.8200, 106.7680),
            (10.8225, 106.7715),
            (10.8248, 106.7745),
            (10.8262, 106.7732),
            (10.8240, 106.7702),
            (10.8218, 106.7670),
            (10.8195, 106.7640),
            (10.8180, 106.7650),
        ],
        center=(10.8220, 106.7692),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.08,
            tidal_sensitivity=0.3,
            rain_sensitivity=0.75,
            drain_rate=0.5,
        ),
        default_risk="high",
    ),

    "zone-thuduc-nguyen-duy-trinh": FloodZone(
        id="zone-thuduc-nguyen-duy-trinh",
        name="Đường Nguyễn Duy Trinh",
        district="Thủ Đức",
        polygon=[
            (10.7880, 106.7820),
            (10.7900, 106.7845),
            (10.7925, 106.7875),
            (10.7945, 106.7900),
            (10.7960, 106.7888),
            (10.7940, 106.7862),
            (10.7918, 106.7835),
            (10.7895, 106.7810),
            (10.7880, 106.7820),
        ],
        center=(10.7918, 106.7855),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.06,
            tidal_sensitivity=0.25,
            rain_sensitivity=0.7,
            drain_rate=0.55,
        ),
        default_risk="medium",
    ),

    "zone-govap-pham-van-dong": FloodZone(
        id="zone-govap-pham-van-dong",
        name="Đường Phạm Văn Đồng",
        district="Gò Vấp",
        polygon=[
            (10.8380, 106.6820),
            (10.8400, 106.6845),
            (10.8425, 106.6875),
            (10.8448, 106.6902),
            (10.8462, 106.6890),
            (10.8440, 106.6862),
            (10.8418, 106.6835),
            (10.8395, 106.6810),
            (10.8380, 106.6820),
        ],
        center=(10.8420, 106.6855),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.06,
            tidal_sensitivity=0.2,
            rain_sensitivity=0.7,
            drain_rate=0.6,
        ),
        default_risk="medium",
    ),

    "zone-tanbinh-truong-chinh": FloodZone(
        id="zone-tanbinh-truong-chinh",
        name="Đường Trường Chinh",
        district="Tân Bình",
        polygon=[
            (10.8120, 106.6420),
            (10.8138, 106.6445),
            (10.8160, 106.6475),
            (10.8180, 106.6502),
            (10.8195, 106.6490),
            (10.8175, 106.6462),
            (10.8152, 106.6435),
            (10.8135, 106.6412),
            (10.8120, 106.6420),
        ],
        center=(10.8158, 106.6455),
        properties=FloodZoneProperties(
            elevation="medium",
            near_river=False,
            drainage="moderate",
        ),
        simulation=FloodZoneSimulation(
            base_level=0.05,
            tidal_sensitivity=0.15,
            rain_sensitivity=0.65,
            drain_rate=0.65,
        ),
        default_risk="medium",
    ),
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_all_zone_ids() -> List[str]:
    """Lấy danh sách tất cả zone IDs"""
    return list(FLOOD_ZONES.keys())


def get_zone_by_id(zone_id: str) -> FloodZone | None:
    """Lấy zone theo ID"""
    return FLOOD_ZONES.get(zone_id)


def get_zones_by_district(district: str) -> List[FloodZone]:
    """Lấy tất cả zones theo district"""
    return [z for z in FLOOD_ZONES.values() if z.district == district]


def get_zones_by_risk(risk: RiskLevel) -> List[FloodZone]:
    """Lấy tất cả zones theo risk level"""
    return [z for z in FLOOD_ZONES.values() if z.default_risk == risk]


def get_tidal_sensitive_zones() -> List[FloodZone]:
    """Lấy tất cả zones ảnh hưởng bởi triều cường"""
    return [z for z in FLOOD_ZONES.values() if z.properties.near_river]


def get_zone_stats() -> dict:
    """Thống kê tổng quan"""
    zones = list(FLOOD_ZONES.values())
    return {
        "total": len(zones),
        "severe": len([z for z in zones if z.default_risk == "severe"]),
        "high": len([z for z in zones if z.default_risk == "high"]),
        "medium": len([z for z in zones if z.default_risk == "medium"]),
        "low": len([z for z in zones if z.default_risk == "low"]),
        "tidal_affected": len([z for z in zones if z.properties.near_river]),
        "districts": list(set(z.district for z in zones)),
    }


# ============================================
# SEVERITY THRESHOLDS
# ============================================

SEVERITY_THRESHOLDS = {
    "low": (0.0, 0.15),      # 0-15cm
    "medium": (0.15, 0.25),  # 15-25cm
    "high": (0.25, 0.40),    # 25-40cm
    "severe": (0.40, float('inf')),  # >40cm
}


def get_severity_from_water_level(water_level: float) -> RiskLevel:
    """Xác định mức độ nguy hiểm từ mực nước"""
    if water_level >= 0.40:
        return "severe"
    elif water_level >= 0.25:
        return "high"
    elif water_level >= 0.15:
        return "medium"
    else:
        return "low"


# Export as list for iteration
FLOOD_ZONES_LIST = list(FLOOD_ZONES.values())
