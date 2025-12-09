# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import httpx
import json

API_KEY = "AIzaSyAg4xEPKC5hPA8hUcZ0TpN0rFXTQugSrtU"
URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

try:
    response = httpx.post(
        URL,
        json={"contents": [{"parts": [{"text": "Hello"}]}]},
        timeout=30.0
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:1000]}")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")
