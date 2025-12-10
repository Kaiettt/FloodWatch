# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1"  # v1beta API
GEMINI_MODEL = "gemini-2.5-flash"  # Stable and fast model

# ======================================================
# SYSTEM PROMPTS
# ======================================================

WEATHER_ASSISTANT_PROMPT = """Ban la tro ly AI thoi tiet chuyen nghiep cua ung dung FloodWatch - he thong canh bao ngap lut TP.HCM.

## Vai tro cua ban:
- Cung cap thong tin thoi tiet chinh xac cho cac quan huyen TP.HCM
- Canh bao mua lon va nguy co ngap lut
- Dua ra loi khuyen an toan khi di chuyen
- Giai thich cac hien tuong thoi tiet bang ngon ngu de hieu

## Quy tac tra loi:
1. Luon tra loi bang tieng Viet
2. Su dung emoji phu hop de truc quan hon
3. Ngan gon, suc tich (toi da 200 tu)
4. Luon de cap den nguon du lieu neu co
5. Neu khong chac chan, hay noi ro
6. Uu tien an toan cua nguoi dung

## Cac quan de ngap o TP.HCM:
- Quan 12, Binh Thanh, Thu Duc: Ngap do trieu cuong va mua
- Quan 8, Quan 6: Vung trung thap
- Go Vap, Tan Binh: Ngap cuc bo khi mua to

## Format tra loi:
- Su dung bullet points khi liet ke
- Bold (**text**) cho thong tin quan trong
- Them emoji o dau cac muc chinh
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
        
        # Keep only max_history messages
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
    max_tokens: int = 1024,
    max_retries: int = 2
) -> Optional[str]:
    """Call Gemini API with messages and retry logic for rate limits."""
    
    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    # Build contents - prepend system instruction as first user message if provided
    contents = []
    if system_instruction:
        # Add system instruction as context in first message
        contents.append({
            "role": "user",
            "parts": [{"text": f"[SYSTEM INSTRUCTION]\n{system_instruction}\n[END SYSTEM INSTRUCTION]\n\nHãy tuân thủ hướng dẫn trên trong tất cả các phản hồi."}]
        })
        contents.append({
            "role": "model", 
            "parts": [{"text": "Tôi hiểu và sẽ tuân thủ các hướng dẫn trên. Tôi sẵn sàng trợ giúp bạn về thời tiết và ngập lụt TP.HCM."}]
        })
    
    # Add actual conversation messages
    contents.extend(messages)
    
    request_body = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.95,
            "topK": 40
        }
    }
    
    import asyncio
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Calling Gemini API: {GEMINI_MODEL} (attempt {attempt + 1}/{max_retries + 1})")
            logger.info(f"API Key (last 8 chars): ...{GEMINI_API_KEY[-8:]}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=request_body)
                logger.info(f"Gemini API response status: {response.status_code}")
                
                # Handle rate limit (429)
                if response.status_code == 429:
                    error_data = response.json()
                    retry_delay = 60  # Default 60s
                    
                    # Try to extract retry delay from response
                    if "error" in error_data and "details" in error_data["error"]:
                        for detail in error_data["error"]["details"]:
                            if detail.get("@type", "").endswith("RetryInfo"):
                                delay_str = detail.get("retryDelay", "60s")
                                retry_delay = int(delay_str.replace("s", "")) + 5  # Add buffer
                    
                    logger.warning(f"Rate limited! Waiting {retry_delay}s before retry...")
                    
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.error("Max retries reached for rate limit")
                        return None
                
                # Check for other errors
                if response.status_code != 200:
                    logger.error(f"Gemini API error: {response.status_code} - {response.text[:500]}")
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
                        return "Xin loi, toi khong the tra loi cau hoi nay."
                
                logger.warning(f"Unexpected Gemini response format: {data}")
                return None
                
        except httpx.TimeoutException:
            logger.error("Gemini API timeout after 60s")
            if attempt < max_retries:
                await asyncio.sleep(5)
                continue
            return None
        except httpx.ConnectError as e:
            logger.error(f"Gemini API connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {type(e).__name__} - {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    return None

# ======================================================
# CHAT FUNCTIONS
# ======================================================

def build_weather_context(weather_data: List[Dict], flood_data: Dict = None) -> str:
    """Build context string from weather and flood data."""
    context_parts = []
    
    if weather_data:
        context_parts.append("## Du lieu thoi tiet hien tai TP.HCM:")
        for w in weather_data[:10]:  # Limit to 10 districts
            forecast_info = ""
            if w.get("forecast"):
                rain_hours = [f for f in w["forecast"] if f.get("pop", 0) > 50]
                if rain_hours:
                    forecast_info = f" | Du bao mua: {rain_hours[0].get('pop')}% luc {rain_hours[0].get('hour')}"
            
            context_parts.append(
                f"- **{w.get('location')}**: {w.get('temperature')}C, "
                f"{w.get('conditionText', w.get('condition'))}, "
                f"Do am: {w.get('humidity')}%, "
                f"Gio: {w.get('windSpeed')} km/h"
                f"{forecast_info}"
            )
    
    if flood_data:
        context_parts.append("\n## Du lieu ngap lut:")
        if flood_data.get("severe"):
            context_parts.append(f"- Ngap nghiem trong: {flood_data.get('severe')} diem")
        if flood_data.get("high"):
            context_parts.append(f"- Ngap cao: {flood_data.get('high')} diem")
        if flood_data.get("rainyDistricts"):
            context_parts.append(f"- Quan dang mua: {', '.join(flood_data.get('rainyDistricts', []))}")
    
    context_parts.append(f"\n*Cap nhat: {datetime.now().strftime('%H:%M %d/%m/%Y')}*")
    
    return "\n".join(context_parts)

async def chat_with_weather_ai(
    user_message: str,
    session_id: str = "default",
    weather_data: List[Dict] = None,
    flood_data: Dict = None
) -> Dict[str, Any]:
    """
    Chat with AI about weather with context.
    
    Args:
        user_message: User message
        session_id: Session ID for tracking conversation
        weather_data: Current weather data
        flood_data: Flood data
    
    Returns:
        Dict with response and metadata
    """
    
    # Build system prompt with context
    system_prompt = WEATHER_ASSISTANT_PROMPT
    
    if weather_data or flood_data:
        context = build_weather_context(weather_data, flood_data)
        system_prompt += f"\n\n## Du lieu thuc te hien tai:\n{context}"
    
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
            "error": "Gemini API khong phan hoi",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# ======================================================
# FALLBACK RESPONSES
# ======================================================

def get_fallback_response(user_message: str) -> str:
    """Get fallback response when Gemini API fails."""
    
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["thoi tiet", "nhiet do", "nang", "mat"]):
        return """Thong tin thoi tiet TP.HCM:

Xin loi, toi khong the ket noi voi du lieu thoi tiet luc nay.

Ban co the:
- Xem the thoi tiet ben trai de cap nhat nhanh
- Thu lai sau vai giay
- Kiem tra ket noi internet

Neu ban can thong tin khan cap ve ngap lut, vui long goi duong day nong: 1900-xxxx"""

    if any(word in message_lower for word in ["mua", "mua to", "mua lon"]):
        return """Thong tin ve mua:

Hien tai toi khong the truy cap du lieu mua real-time.

Cac quan hay ngap khi mua to tai TP.HCM:
- Quan 12, Thu Duc - trieu cuong + mua
- Quan 8, Quan 6 - vung trung
- Binh Thanh, Go Vap - ngap cuc bo

Khuyen cao: Tranh di chuyen qua vung ngap khi mua to."""

    if any(word in message_lower for word in ["ngap", "lut", "nuoc", "ngap lut"]):
        return """Canh bao ngap lut:

Toi khong the lay du lieu ngap lut real-time luc nay.

Bien phap an toan:
1. Khong co lai xe qua vung ngap
2. Theo doi canh bao tu ung dung
3. Di chuyen do dac len cao neu o vung trung
4. Lien he cuu ho neu can: 114

Vui long thu lai sau de xem du lieu moi nhat."""

    return """Xin chao! Toi la tro ly thoi tiet AI cua FloodWatch.

Hien tai toi gap su co ket noi. Ban co the hoi toi ve:

- Thoi tiet cac quan TP.HCM
- Du bao mua trong 5 gio toi
- Canh bao ngap lut
- Tu van di chuyen an toan

Vui long thu lai cau hoi cua ban!"""

# ======================================================
# QUICK ACTIONS
# ======================================================

async def get_weather_advice(weather_data: List[Dict]) -> str:
    """Get quick weather advice based on current conditions."""
    
    if not weather_data:
        return "Khong co du lieu thoi tiet de phan tich."
    
    prompt = f"""Dua tren du lieu thoi tiet sau, hay dua ra 3 loi khuyen ngan gon (moi loi khuyen 1 dong) cho nguoi dan TP.HCM:

{build_weather_context(weather_data)}

Tra loi voi format:
1. [emoji] Loi khuyen 1
2. [emoji] Loi khuyen 2
3. [emoji] Loi khuyen 3"""

    messages = [{"role": "user", "parts": [{"text": prompt}]}]
    
    response = await call_gemini_api(
        messages=messages,
        system_instruction="Ban la chuyen gia thoi tiet. Tra loi ngan gon, thuc te.",
        temperature=0.5,
        max_tokens=300
    )
    
    return response or "Khong the tao loi khuyen luc nay."

async def analyze_flood_risk(weather_data: List[Dict], flood_data: Dict) -> str:
    """Analyze flood risk based on weather and flood data."""
    
    prompt = f"""Phan tich nguy co ngap lut dua tren du lieu sau:

{build_weather_context(weather_data, flood_data)}

Hay dua ra:
1. Danh gia muc do nguy co (Thap/Trung binh/Cao/Rat cao)
2. Cac quan can chu y
3. Khuyen cao ngan gon

Format: bullet points, co emoji."""

    messages = [{"role": "user", "parts": [{"text": prompt}]}]
    
    response = await call_gemini_api(
        messages=messages,
        system_instruction="Ban la chuyen gia canh bao thien tai. Uu tien an toan nguoi dan.",
        temperature=0.3,
        max_tokens=500
    )
    
    return response or "Khong the phan tich nguy co ngap luc nay."

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
