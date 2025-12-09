# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
"""Test Gemini API connection"""

import httpx
import json
import sys

API_KEY = "AIzaSyAg4xEPKC5hPA8hUcZ0TpN0rFXTQugSrtU"
URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

print("=" * 50)
print("Testing Gemini API...")
print(f"URL: {URL[:80]}...")
print("=" * 50)

try:
    print("\n[1] Sending request...")
    response = httpx.post(
        URL,
        json={"contents": [{"parts": [{"text": "Say hello in Vietnamese"}]}]},
        timeout=30.0
    )
    
    print(f"\n[2] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if "candidates" in data:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n[3] SUCCESS! Response:")
            print(text)
        else:
            print(f"\n[3] Unexpected response format:")
            print(json.dumps(data, indent=2)[:500])
    else:
        print(f"\n[3] ERROR Response:")
        print(response.text[:500])
        
except httpx.TimeoutException:
    print("\n[ERROR] Timeout - API took too long")
except httpx.ConnectError as e:
    print(f"\n[ERROR] Connection failed: {e}")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("Test completed.")
