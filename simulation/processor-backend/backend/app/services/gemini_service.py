# ======================================================
# FloodWatch - Gemini AI Service
# Google Gemini API Integration for Weather Chatbot
# ======================================================

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
import json

logger = logging.getLogger(__name__)

# ======================================================
# CONFIGURATION
# ======================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAg4xEPKC5hPA8hUcZ0TpN0rFXTQugSrtU")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1"
GEMINI_MODEL = "gemini-1.5-flash"  # Stable model - alternatives: gemini-pro, gemini-1.5-pro

# ======================================================
# SYSTEM PROMPTS
# ======================================================

WEATHER_ASSISTANT_PROMPT = """Bạn là trợ lý AI thời tiết chuyên nghiệp của ứng dụng FloodWatch - hệ thống cảnh báo ngập lụt TP.HCM.

## Vai trò của bạn:
- Cung cấp thông tin thời tiết chính xác cho các quận huyện TP.HCM
- Cảnh báo mưa lớn và nguy cơ ngập lụt
- Đưa ra lời khuyên an toàn khi di chuyển
- Giải thích các hiện tượng thời tiết bằng ngôn ngữ dễ hiểu

## Quy tắc trả lời:
1. Luôn trả lời bằng tiếng Việt
2. Sử dụng emoji phù hợp để trực quan hơn
3. Ngắn gọn, súc tích (tối đa 200 từ)
4. Luôn đề cập đến nguồn dữ liệu nếu có
5. Nếu không chắc chắn, hãy nói rõ
6. Ưu tiên an toàn của người dùng

## Các quận dễ ngập ở TP.HCM:
- Quận 12, Bình Thạnh, Thủ Đức: Ngập do triều cường và mưa
- Quận 8, Quận 6: Vùng trũng thấp
- Gò Vấp, Tân Bình: Ngập cục bộ khi mưa to

## Format trả lời:
- Sử dụng bullet points khi liệt kê
- Bold (**text**) cho thông tin quan trọng
- Thêm emoji ở đầu các mục chính
"""

# ======================================================
# MESSAGE HISTORY MANAGEMENT
# ======================================================

class ConversationManager:
    """Manage conversation history for context."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": role,
            "parts": [{"text": content}]
        })
        
        # Giữ chỉ max_history messages gần nhất
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history."""
        return self.conversations.get(session_id, [])
    
    def clear_history(self, session_id: str):
        """Clear conversation history."""
        if session_id in self.conversations:
            del self.conversations[session_id]

# Global conversation manager
conversation_manager = ConversationManager()

# ======================================================
# GEMINI API FUNCTIONS
# ======================================================

async def call_gemini_api(
    messages: List[Dict],
    system_instruction: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Optional[str]:
    """Call Gemini API with messages."""
    
    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    request_body = {
        "contents": messages,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.95,
            "topK": 40
        }
    }
    
    if system_instruction:
        request_body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
    
    try:
        logger.info(f"Calling Gemini API: {GEMINI_MODEL}")
        logger.info(f"API Key (last 8 chars): ...{GEMINI_API_KEY[-8:]}")
        logger.info(f"Request URL: {url[:80]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request_body)
            logger.info(f"Raw response status: {response.status_code}")
            
            # Log response status
            logger.info(f"Gemini API response status: {response.status_code}")
            
            # Check for errors before raise_for_status
            if response.status_code != 200:
                logger.error(f"Gemini API error response: {response.text}")
                return None
            
            data = response.json()
            
            # Extract text from response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        logger.info("Gemini API response received successfully")
                        return parts[0]["text"]
            
            # Check for blocked content
            if "promptFeedback" in data:
                feedback = data["promptFeedback"]
                if feedback.get("blockReason"):
                    logger.warning(f"Content blocked: {feedback.get('blockReason')}")
                    return "Xin lỗi, tôi không thể trả lời câu hỏi này."
            
            logger.warning(f"Unexpected Gemini response format: {data}")
            return None
            
    except httpx.TimeoutException:
        logger.error("Gemini API timeout after 30s")
        return None
    except httpx.ConnectError as e:
        logger.error(f"Gemini API connection error (check network/DNS): {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__} - {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None

# ======================================================
# CHAT FUNCTIONS
# ======================================================

def build_weather_context(weather_data: List[Dict], flood_data: Dict = None) -> str:
    """Build context string from weather and flood data."""
    context_parts = []
    
    if weather_data:
        context_parts.append("## Dữ liệu thời tiết hiện tại TP.HCM:")
        for w in weather_data[:10]:  # Limit to 10 districts
            forecast_info = ""
            if w.get("forecast"):
                rain_hours = [f for f in w["forecast"] if f.get("pop", 0) > 50]
                if rain_hours:
                    forecast_info = f" | Dự báo mưa: {rain_hours[0].get('pop')}% lúc {rain_hours[0].get('hour')}"
            
            context_parts.append(
                f"- **{w.get('location')}**: {w.get('temperature')}°C, "
                f"{w.get('conditionText', w.get('condition'))}, "
                f"Độ ẩm: {w.get('humidity')}%, "
                f"Gió: {w.get('windSpeed')} km/h"
                f"{forecast_info}"
            )
    
    if flood_data:
        context_parts.append("\n## Dữ liệu ngập lụt:")
        if flood_data.get("severe"):
            context_parts.append(f"- 🔴 Ngập nghiêm trọng: {flood_data.get('severe')} điểm")
        if flood_data.get("high"):
            context_parts.append(f"- 🟠 Ngập cao: {flood_data.get('high')} điểm")
        if flood_data.get("rainyDistricts"):
            context_parts.append(f"- 🌧️ Quận đang mưa: {', '.join(flood_data.get('rainyDistricts', []))}")
    
    context_parts.append(f"\n*Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}*")
    
    return "\n".join(context_parts)

async def chat_with_weather_ai(
    user_message: str,
    session_id: str = "default",
    weather_data: List[Dict] = None,
    flood_data: Dict = None
) -> Dict[str, Any]:
    """
    Chat với AI về thời tiết với context.
    
    Args:
        user_message: Tin nhắn của người dùng
        session_id: ID session để tracking conversation
        weather_data: Dữ liệu thời tiết hiện tại
        flood_data: Dữ liệu ngập lụt
    
    Returns:
        Dict với response và metadata
    """
    
    # Build system prompt với context
    system_prompt = WEATHER_ASSISTANT_PROMPT
    
    if weather_data or flood_data:
        context = build_weather_context(weather_data, flood_data)
        system_prompt += f"\n\n## Dữ liệu thực tế hiện tại:\n{context}"
    
    # Add user message to history
    conversation_manager.add_message(session_id, "user", user_message)
    
    # Get conversation history
    messages = conversation_manager.get_history(session_id)
    
    # Call Gemini API
    response_text = await call_gemini_api(
        messages=messages,
        system_instruction=system_prompt,
        temperature=0.7,
        max_tokens=1024
    )
    
    if response_text:
        # Add assistant response to history
        conversation_manager.add_message(session_id, "model", response_text)
        
        return {
            "success": True,
            "response": response_text,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        # Fallback response
        fallback = get_fallback_response(user_message)
        return {
            "success": False,
            "response": fallback,
            "session_id": session_id,
            "error": "Gemini API không phản hồi",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# ======================================================
# FALLBACK RESPONSES
# ======================================================

def get_fallback_response(user_message: str) -> str:
    """Get fallback response when Gemini API fails."""
    
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["thời tiết", "nhiệt độ", "nắng", "mát"]):
        return """🌤️ **Thông tin thời tiết TP.HCM:**

Xin lỗi, tôi không thể kết nối với dữ liệu thời tiết lúc này.

Bạn có thể:
• Xem thẻ thời tiết bên trái để cập nhật nhanh
• Thử lại sau vài giây
• Kiểm tra kết nối internet

⚠️ Nếu bạn cần thông tin khẩn cấp về ngập lụt, vui lòng gọi đường dây nóng: **1900-xxxx**"""

    if any(word in message_lower for word in ["mưa", "mưa to", "mưa lớn"]):
        return """🌧️ **Thông tin về mưa:**

Hiện tại tôi không thể truy cập dữ liệu mưa real-time.

**Các quận hay ngập khi mưa to tại TP.HCM:**
• Quận 12, Thủ Đức - triều cường + mưa
• Quận 8, Quận 6 - vùng trũng
• Bình Thạnh, Gò Vấp - ngập cục bộ

💡 **Khuyến cáo:** Tránh di chuyển qua vùng ngập khi mưa to."""

    if any(word in message_lower for word in ["ngập", "lụt", "nước", "ngập lụt"]):
        return """🌊 **Cảnh báo ngập lụt:**

Tôi không thể lấy dữ liệu ngập lụt real-time lúc này.

**Biện pháp an toàn:**
1. 🚗 Không cố lái xe qua vùng ngập
2. 📱 Theo dõi cảnh báo từ ứng dụng
3. 🏠 Di chuyển đồ đạc lên cao nếu ở vùng trũng
4. 📞 Liên hệ cứu hộ nếu cần: **114**

Vui lòng thử lại sau để xem dữ liệu mới nhất."""

    return """👋 Xin chào! Tôi là trợ lý thời tiết AI của FloodWatch.

Hiện tại tôi gặp sự cố kết nối. Bạn có thể hỏi tôi về:

• ☀️ Thời tiết các quận TP.HCM
• 🌧️ Dự báo mưa trong 5 giờ tới
• 🌊 Cảnh báo ngập lụt
• 🛣️ Tư vấn di chuyển an toàn

Vui lòng thử lại câu hỏi của bạn!"""

# ======================================================
# QUICK ACTIONS
# ======================================================

async def get_weather_advice(weather_data: List[Dict]) -> str:
    """Get quick weather advice based on current conditions."""
    
    if not weather_data:
        return "Không có dữ liệu thời tiết để phân tích."
    
    prompt = f"""Dựa trên dữ liệu thời tiết sau, hãy đưa ra 3 lời khuyên ngắn gọn (mỗi lời khuyên 1 dòng) cho người dân TP.HCM:

{build_weather_context(weather_data)}

Trả lời với format:
1. [emoji] Lời khuyên 1
2. [emoji] Lời khuyên 2
3. [emoji] Lời khuyên 3"""

    messages = [{"role": "user", "parts": [{"text": prompt}]}]
    
    response = await call_gemini_api(
        messages=messages,
        system_instruction="Bạn là chuyên gia thời tiết. Trả lời ngắn gọn, thực tế.",
        temperature=0.5,
        max_tokens=300
    )
    
    return response or "Không thể tạo lời khuyên lúc này."

async def analyze_flood_risk(weather_data: List[Dict], flood_data: Dict) -> str:
    """Analyze flood risk based on weather and flood data."""
    
    prompt = f"""Phân tích nguy cơ ngập lụt dựa trên dữ liệu sau:

{build_weather_context(weather_data, flood_data)}

Hãy đưa ra:
1. Đánh giá mức độ nguy cơ (Thấp/Trung bình/Cao/Rất cao)
2. Các quận cần chú ý
3. Khuyến cáo ngắn gọn

Format: bullet points, có emoji."""

    messages = [{"role": "user", "parts": [{"text": prompt}]}]
    
    response = await call_gemini_api(
        messages=messages,
        system_instruction="Bạn là chuyên gia cảnh báo thiên tai. Ưu tiên an toàn người dân.",
        temperature=0.3,
        max_tokens=500
    )
    
    return response or "Không thể phân tích nguy cơ ngập lúc này."

# ======================================================
# UTILITY FUNCTIONS
# ======================================================

def clear_session(session_id: str):
    """Clear conversation history for a session."""
    conversation_manager.clear_history(session_id)
    logger.info(f"Cleared session: {session_id}")

def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get info about a conversation session."""
    history = conversation_manager.get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "has_history": len(history) > 0
    }
