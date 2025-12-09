# ======================================================
# FloodWatch - Alert Enhancer Service
# Sử dụng Gemini AI để tạo mô tả cảnh báo thông minh
# ======================================================

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .gemini_service import call_gemini_api

logger = logging.getLogger(__name__)

# Note: call_gemini_api từ gemini_service đã sử dụng:
# - GEMINI_MODEL = "gemini-2.5-flash-lite"
# - GEMINI_API_KEY từ environment variable hoặc default
# - GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1"
# Vậy alert_enhancer đang sử dụng đúng model và API key giống như gemini_service

# ======================================================
# SYSTEM PROMPT
# ======================================================

ALERT_ENHANCER_PROMPT = """Ban la chuyen gia canh bao ngap lut TP.HCM. Nhiem vu cua ban la tao mo ta canh bao thong minh, chi tiet va huu ich cho nguoi dan.

## Vai tro:
- Phan tich du lieu ngap (muc nuoc, vi tri, thoi tiet)
- Tao mo ta canh bao de hieu, co nguyen nhan va du doan
- Dua ra loi khuyen cu the cho nguoi dan

## Quy tac:
1. Luon tra loi bang tieng Viet
2. Ngan gon, suc tich (toi da 200 tu)
3. Su dung emoji phu hop (⚠️, 🔴, 🟠, 🟡, 💡, 🚗, ⏰)
4. Luon de cap:
   - Muc nuoc hien tai (m)
   - Nguyen nhan (mua, trieu cuong, he thong thoat nuoc)
   - Du doan dien bien (tang/giam, thoi gian)
   - Loi khuyen cu the
5. Neu khong co du lieu, hay noi ro
6. Uu tien an toan cua nguoi dan

## Format:
- Bat dau voi emoji va muc do canh bao
- Mo ta tinh trang hien tai
- Nguyen nhan (neu biet)
- Du doan dien bien (neu co)
- Loi khuyen cu the

## Vi du:
⚠️ NGAP NGHIEM TRONG! Muc nuoc dang o muc 1.2m tai Quan 12 - muc nguy hiem! 
Dua tren du lieu lich su, khu vuc nay thuong ngap sau hon khi mua keo dai. 
Hien tai dang co mua to (45mm/h) va trieu cuong, du kien muc nuoc co the 
tang them 0.3-0.5m trong 2 gio toi. 🚗 Khuyen cao: Tranh tuyen duong 
Nguyen Van Qua, su dung duong cao toc thay the.
"""

# ======================================================
# ALERT ENHANCEMENT FUNCTIONS
# ======================================================

def build_alert_context(
    water_level: float,
    location: str = None,
    district: str = None,
    severity: str = None,
    weather_data: Dict = None,
    flood_data: Dict = None,
    trend: str = None
) -> str:
    """Xây dựng context string từ dữ liệu cảnh báo."""
    context_parts = []
    
    # Thông tin cơ bản
    context_parts.append("## Thong tin canh bao:")
    context_parts.append(f"- Muc nuoc: {water_level}m")
    if severity:
        context_parts.append(f"- Muc do: {severity}")
    if location:
        context_parts.append(f"- Vi tri: {location}")
    if district:
        context_parts.append(f"- Quan/Huyen: {district}")
    if trend:
        context_parts.append(f"- Xu huong: {trend}")
    
    # Thông tin thời tiết
    if weather_data:
        context_parts.append("\n## Du lieu thoi tiet:")
        if weather_data.get("condition"):
            context_parts.append(f"- Tinh trang: {weather_data.get('condition')}")
        if weather_data.get("temperature"):
            context_parts.append(f"- Nhiet do: {weather_data.get('temperature')}°C")
        if weather_data.get("humidity"):
            context_parts.append(f"- Do am: {weather_data.get('humidity')}%")
        if weather_data.get("rainfall"):
            context_parts.append(f"- Luong mua: {weather_data.get('rainfall')}mm/h")
        if weather_data.get("windSpeed"):
            context_parts.append(f"- Gio: {weather_data.get('windSpeed')} km/h")
        
        # Dự báo mưa
        if weather_data.get("forecast"):
            rain_forecast = [f for f in weather_data["forecast"] if f.get("pop", 0) > 50]
            if rain_forecast:
                context_parts.append(f"- Du bao mua: {rain_forecast[0].get('pop')}% luc {rain_forecast[0].get('hour')}")
    
    # Thông tin ngập lụt
    if flood_data:
        context_parts.append("\n## Tinh hinh ngap xung quanh:")
        if flood_data.get("nearby_floods"):
            context_parts.append(f"- So diem ngap gan do: {flood_data.get('nearby_floods')}")
        if flood_data.get("average_water_level"):
            context_parts.append(f"- Muc nuoc trung binh khu vuc: {flood_data.get('average_water_level')}m")
    
    context_parts.append(f"\n*Cap nhat: {datetime.now().strftime('%H:%M %d/%m/%Y')}*")
    
    return "\n".join(context_parts)

async def enhance_alert_description(
    water_level: float,
    location: str = None,
    district: str = None,
    severity: str = None,
    weather_data: Dict = None,
    flood_data: Dict = None,
    trend: str = None,
    fallback_description: str = None
) -> str:
    """
    Tạo mô tả cảnh báo thông minh bằng Gemini AI.
    
    Args:
        water_level: Mực nước (mét)
        location: Địa chỉ/vị trí
        district: Quận/huyện
        severity: Mức độ nghiêm trọng (Severe/High/Moderate/Low)
        weather_data: Dữ liệu thời tiết
        flood_data: Dữ liệu ngập lụt xung quanh
        trend: Xu hướng (rising/stable/falling)
        fallback_description: Mô tả mặc định nếu Gemini lỗi
    
    Returns:
        Mô tả cảnh báo thông minh từ Gemini hoặc fallback
    """
    try:
        # Xây dựng context
        context = build_alert_context(
            water_level=water_level,
            location=location,
            district=district,
            severity=severity,
            weather_data=weather_data,
            flood_data=flood_data,
            trend=trend
        )
        
        # Tạo prompt
        prompt = f"""Hay tao mo ta canh bao thong minh dua tren thong tin sau:

{context}

Yeu cau:
1. Mo ta ngan gon, de hieu (toi da 200 tu)
2. De cap muc nuoc, nguyen nhan, du doan
3. Dua ra loi khuyen cu the
4. Su dung emoji phu hop
5. Tra loi bang tieng Viet"""
        
        messages = [{"role": "user", "parts": [{"text": prompt}]}]
        
        # Gọi Gemini API (sử dụng cùng model và API key từ gemini_service)
        response = await call_gemini_api(
            messages=messages,
            system_instruction=ALERT_ENHANCER_PROMPT,
            temperature=0.7,
            max_tokens=300
        )
        
        if response:
            logger.info("Alert description enhanced successfully by Gemini")
            return response.strip()
        else:
            logger.warning("Gemini API failed, using fallback description")
            return fallback_description or generate_fallback_description(
                water_level, severity, location, district
            )
            
    except Exception as e:
        logger.error(f"Error enhancing alert description: {e}")
        return fallback_description or generate_fallback_description(
            water_level, severity, location, district
        )

def generate_fallback_description(
    water_level: float,
    severity: str = None,
    location: str = None,
    district: str = None
) -> str:
    """Tạo mô tả cảnh báo mặc định khi Gemini lỗi."""
    
    # Xác định mức độ
    if water_level >= 1.0:
        level_emoji = "🔴"
        level_text = "NGHIÊM TRỌNG"
        advice = "Không nên di chuyển qua khu vực này. Tìm đường thay thế."
    elif water_level >= 0.5:
        level_emoji = "🟠"
        level_text = "CAO"
        advice = "Cần thận trọng khi di chuyển. Xe máy có thể bị kẹt."
    elif water_level >= 0.2:
        level_emoji = "🟡"
        level_text = "TRUNG BÌNH"
        advice = "Lưu ý khi di chuyển. Mang theo áo mưa."
    else:
        level_emoji = "🟢"
        level_text = "THẤP"
        advice = "Tình trạng ổn định. Vẫn nên theo dõi."
    
    location_text = location or district or "khu vực này"
    
    description = f"{level_emoji} Cảnh báo ngập {level_text}! "
    description += f"Mực nước đạt {water_level:.1f}m tại {location_text}. "
    description += f"💡 {advice}"
    
    return description

# ======================================================
# BATCH ENHANCEMENT
# ======================================================

async def enhance_multiple_alerts(
    alerts: List[Dict[str, Any]],
    weather_data: List[Dict] = None,
    flood_data: Dict = None
) -> List[Dict[str, Any]]:
    """
    Tăng cường mô tả cho nhiều cảnh báo cùng lúc.
    
    Args:
        alerts: Danh sách cảnh báo
        weather_data: Dữ liệu thời tiết cho các quận
        flood_data: Dữ liệu ngập lụt tổng thể
    
    Returns:
        Danh sách cảnh báo đã được tăng cường
    """
    enhanced_alerts = []
    
    for alert in alerts:
        try:
            # Lấy thông tin từ alert
            water_level = alert.get("waterLevel", alert.get("water_level", 0))
            location = alert.get("location", alert.get("address"))
            district = alert.get("district")
            severity = alert.get("severity", alert.get("riskLevel"))
            trend = alert.get("trend", alert.get("waterTrend"))
            
            # Tìm dữ liệu thời tiết cho quận này
            alert_weather = None
            if weather_data and district:
                alert_weather = next(
                    (w for w in weather_data if w.get("district") == district or w.get("location") == district),
                    None
                )
            
            # Tăng cường mô tả
            enhanced_description = await enhance_alert_description(
                water_level=water_level,
                location=location,
                district=district,
                severity=severity,
                weather_data=alert_weather,
                flood_data=flood_data,
                trend=trend,
                fallback_description=alert.get("description")
            )
            
            # Cập nhật alert
            enhanced_alert = {
                **alert,
                "description": enhanced_description,
                "enhanced": True
            }
            enhanced_alerts.append(enhanced_alert)
            
        except Exception as e:
            logger.error(f"Error enhancing alert {alert.get('id')}: {e}")
            # Giữ nguyên alert nếu lỗi
            enhanced_alerts.append({
                **alert,
                "enhanced": False
            })
    
    return enhanced_alerts

